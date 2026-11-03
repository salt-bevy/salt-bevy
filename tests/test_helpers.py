"""
Tests for configure_machine/helpers: the salt-call command lines and output
parsing (with the commands faked), the password hash, and install_vgr's
vgr.bat rewrite.
"""
import subprocess

import pytest

from helpers import salt_call_local


# ---- salt_call_local ----

def test_state_apply_command_line(monkeypatch, capsys):
    commands = []
    monkeypatch.setattr(subprocess, 'call', lambda cmd, shell: commands.append(cmd) or 0)
    salt_call_local.state_apply('configure_bevy_member', id='node1', config_dir='/etc/salt',
                                bevy='bevy01', additional_minion_tag='')
    cmd = commands[0]
    assert cmd.startswith('salt-call --local state.apply configure_bevy_member --retcode-passthrough')
    assert '--config-dir=/etc/salt' in cmd
    assert '--file-root' not in cmd and '--pillar-root' not in cmd
    assert '''pillar="{'bevy': 'bevy01', 'additional_minion_tag': ''}"''' in cmd
    assert 'Success' in capsys.readouterr().out


def test_state_apply_passes_the_minion_id(monkeypatch):
    # regression: the command template had no {id}, so --id was dropped
    commands = []
    monkeypatch.setattr(subprocess, 'call', lambda cmd, shell: commands.append(cmd) or 0)
    salt_call_local.state_apply('configure_bevy_member', id='node1')
    assert '--id=node1' in commands[0]


def test_state_apply_reports_failure(monkeypatch, capsys):
    monkeypatch.setattr(subprocess, 'call', lambda cmd, shell: 2)
    salt_call_local.state_apply('')
    assert 'Error 2 occurred while running Salt state "highstate"' in capsys.readouterr().out


def test_salt_call_json_finds_the_json_in_noisy_output(monkeypatch):
    noisy = b'[WARNING ] some deprecation notice\r\n{\r\n    "local": "3008.5"\r\n}\r\n'
    monkeypatch.setattr(subprocess, 'check_output', lambda cmd, shell: noisy)
    assert salt_call_local.salt_call_json('test.version') == {'local': '3008.5'}


def test_salt_call_json_when_salt_call_fails(monkeypatch):
    def fail(cmd, shell):
        raise subprocess.CalledProcessError(127, cmd, output=b'salt-call: not found')
    monkeypatch.setattr(subprocess, 'check_output', fail)
    assert salt_call_local.salt_call_json('test.version') == {}


@pytest.mark.parametrize('answer, expected', [
    ({'local': '3008.5'}, ['3008', 5]),
    ({'local': '3006'}, ['3006', 0]),
    ({'local': '2019.2.8'}, ['2019', 2, '8']),
    ({}, ['', 0, '']),
])
def test_salt_minion_version(monkeypatch, answer, expected):
    monkeypatch.setattr(salt_call_local, 'salt_call_json', lambda command: answer)
    assert salt_call_local.salt_minion_version() == expected


def test_current_salt_meets_the_scripts_minimum(monkeypatch):
    # the bootstrap script compares these lists directly
    monkeypatch.setattr(salt_call_local, 'salt_call_json', lambda command: {'local': '3008.5'})
    minimum = '2018.3.0'.split('.')
    minimum[1] = int(minimum[1])
    assert salt_call_local.salt_minion_version() >= minimum


# ---- pwd_hash ----

def test_make_hash_returns_a_sha512_crypt_hash(monkeypatch):
    from helpers import pwd_hash
    answers = iter(['s3cret', 's3cret'])
    monkeypatch.setattr(pwd_hash.getpass, 'getpass', lambda prompt='': next(answers))
    monkeypatch.setattr('builtins.input', lambda prompt='': '')
    hashed = pwd_hash.make_hash()
    assert hashed.startswith('$6$')
    passlib_hash = pytest.importorskip('passlib.hash')
    assert passlib_hash.sha512_crypt.verify('s3cret', hashed)
    assert not passlib_hash.sha512_crypt.verify('wrong', hashed)


# ---- install_vgr ----

def test_vgr_bat_gets_this_checkouts_path():
    pytest.importorskip('windows_sudo')
    from helpers import install_vgr
    text = install_vgr.build_vgr_bat()
    assert install_vgr.RELATIVE_CWD_LINE not in text
    assert '@set "VAGRANT_CWD={}"'.format(install_vgr.REPO_ROOT) in text

"""
Tests for configure_machine/bootstrap_bevy_member_here.py that need no
terminal, no Salt, and no elevated privileges: its small helpers, the files
it writes, and the parts of its question-and-answer flow that run with
prompts turned off.
"""
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from conftest import BOOTSTRAP


# ---- --help ----

def test_help_works_without_the_prerequisites():
    # --help is checked before the script imports yaml, ifaddr, windows_sudo, etc.
    code = (
        "import runpy, sys\n"
        "for name in ('yaml', 'ifaddr', 'windows_sudo', 'passlib'):\n"
        "    sys.modules[name] = None  # make 'import <name>' fail\n"
        "sys.argv = ['bootstrap_bevy_member_here.py', '--help']\n"
        "runpy.run_path({!r}, run_name='__main__')\n"
    ).format(str(BOOTSTRAP))
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '--file_roots' in result.stdout
    assert 'missing required prerequisite' not in result.stdout


# ---- small helpers ----

@pytest.mark.parametrize('choice, default, expected', [
    ('', False, False),
    ('', True, True),
    ('y', False, True),
    ('Yes', False, True),
    ('n', True, False),
    ('nope', True, False),
    (True, False, True),   # a bool passed straight through
    (None, True, False),
])
def test_affirmative(bootstrap, choice, default, expected):
    assert bootstrap.affirmative(choice, default) is expected


@pytest.mark.parametrize('name, expected', [
    ('', ''), ('False', ''), ('none', ''), ('None', ''), (None, ''), ('vernon', 'vernon'),
])
def test_normalize(bootstrap, name, expected):
    assert bootstrap.normalize(name) == expected


@pytest.mark.parametrize('name, expected', [('', 'None'), ('false', 'None'), ('vernon', 'vernon')])
def test_normalize_literal_none(bootstrap, name, expected):
    assert bootstrap.normalize_literal_none(name) == expected


@pytest.mark.parametrize('stored, expected', [(None, ''), ('', ''), ('None', ''), ('none', ''), ('2', '2')])
def test_minion_tag(bootstrap, stored, expected):
    if stored is not None:
        bootstrap.my_settings['additional_minion_tag'] = stored
    assert bootstrap.minion_tag() == expected


def test_windows_salt_root_dir_follows_programdata(bootstrap, monkeypatch):
    monkeypatch.setenv('ProgramData', r'D:\Data')
    assert bootstrap.windows_salt_root_dir() == Path(r'D:\Data') / 'Salt Project' / 'Salt'
    assert bootstrap.windows_salt_root_dir('2') == Path(r'D:\Data') / 'Salt Project' / 'Salt2'


@pytest.mark.parametrize('tag, expected', [
    ('', '/etc/salt/minion.d/00_bevy_boot.conf'),
    ('2', '/etc/salt2/minion.d/00_bevy_boot.conf'),
])
def test_config_file_path_on_linux(bootstrap, monkeypatch, tag, expected):
    monkeypatch.setattr(bootstrap.platform, 'system', lambda: 'Linux')
    bootstrap.my_settings['additional_minion_tag'] = tag
    assert bootstrap.my_salt_config_file_path() == Path(expected)


def test_config_file_path_on_windows(bootstrap, monkeypatch):
    monkeypatch.setattr(bootstrap.platform, 'system', lambda: 'Windows')
    monkeypatch.setenv('ProgramData', r'C:\ProgramData')
    assert bootstrap.my_salt_config_file_path() == \
        Path(r'C:\ProgramData') / 'Salt Project' / 'Salt' / 'conf' / 'minion.d' / '00_bevy_boot.conf'


# ---- additional file_roots / pillar_roots ----

def test_roots_keep_previous_settings_by_default(bootstrap):
    bootstrap.my_settings['projects_root'] = '/projects'
    bootstrap.settings['file_roots'] = ['/old/salt']
    bootstrap.get_additional_roots('file_roots')
    assert bootstrap.settings['file_roots'] == ['/old/salt']


def test_roots_take_new_values_from_the_command_line(bootstrap, monkeypatch):
    bootstrap.my_settings['projects_root'] = '/projects'
    monkeypatch.setattr(bootstrap, 'argv', ['x', r'--file_roots=[C:\one,{path}two]'])
    bootstrap.get_additional_roots('file_roots')
    assert bootstrap.settings['file_roots'] == ['C:/one', '{path}two']


def test_roots_erase_clears_the_named_setting(bootstrap):
    # regression: "erase both" used to set a literal "tag" key instead
    bootstrap.my_settings['projects_root'] = '/projects'
    bootstrap.settings['pillar_roots'] = []
    bootstrap.get_additional_roots('pillar_roots')
    assert bootstrap.settings['pillar_roots'] == []
    assert 'tag' not in bootstrap.settings


def test_format_additional_roots_expands_path(bootstrap, tmp_path):
    bootstrap.my_settings['projects_root'] = str(tmp_path)
    settings = {'file_roots': ['{path}/proj/salt', '{path}other'], 'pillar_roots': '{path}proj/pillar'}
    roots, pillars = bootstrap.format_additional_roots(settings, virtual=False)
    assert roots == [(tmp_path / 'proj' / 'salt').resolve().as_posix(), (tmp_path / 'other').resolve().as_posix()]
    assert pillars == [(tmp_path / 'proj' / 'pillar').resolve().as_posix()]


def test_format_additional_roots_for_a_vm_uses_the_vagrant_share(bootstrap):
    # regression: on a Windows host, Path.resolve() used to add a drive letter (C:/projects/...)
    settings = {'file_roots': ['{path}proj/salt', '/srv/extra'], 'pillar_roots': ['{path}/proj/pillar']}
    roots, pillars = bootstrap.format_additional_roots(settings, virtual=True)
    assert roots == ['/projects/proj/salt', '/srv/extra']
    assert pillars == ['/projects/proj/pillar']


# ---- the minion configuration file ----

def write_config(bootstrap, tmp_path, **kwargs):
    path = tmp_path / 'minion.d' / '00_bevy_boot.conf'
    bootstrap.write_config_file(path, **kwargs)
    return path, yaml.safe_load(path.read_text())


def test_config_for_a_master(bootstrap, tmp_path):
    bootstrap.my_settings.update(id='bevymaster', projects_root='none')
    path, conf = write_config(bootstrap, tmp_path, is_master=True, virtual=False, platform='Linux')
    assert conf['master'] == 'localhost'
    assert conf['id'] == 'bevymaster'
    assert conf['file_client'] == 'local'
    assert conf['file_roots']['base'] == ['/srv/salt', 'bevy_srv/salt']
    assert conf['pillar_roots']['base'] == ['/srv/pillar', 'bevy_srv/pillar']


def test_config_for_a_minion(bootstrap, tmp_path):
    bootstrap.settings['master_external_ip'] = 'salt.example.com'
    bootstrap.my_settings.update(id='node1', projects_root=str(tmp_path))
    path, conf = write_config(bootstrap, tmp_path, is_master=False, virtual=False, platform=platform.system())
    assert conf['master'] == 'salt.example.com'
    assert conf['id'] == 'node1'
    assert 'file_client' not in conf
    repo = BOOTSTRAP.parent.parent
    assert conf['file_roots']['base'][-1] == (repo / 'bevy_srv' / 'salt').as_posix()


def test_config_for_a_minion_hosting_the_master_vm(bootstrap, tmp_path):
    bootstrap.settings.update(master_vagrant_ip='192.168.2.2', master_external_ip='salt.example.com')
    bootstrap.my_settings.update(id='node1', projects_root='none')
    _, conf = write_config(bootstrap, tmp_path, is_master=False, virtual=False, platform='Linux',
                           master_host=True)
    assert conf['master'] == '192.168.2.2'


def test_config_for_a_vm_guest(bootstrap, tmp_path):
    bootstrap.my_settings.update(id='node1', projects_root='/somewhere')
    _, conf = write_config(bootstrap, tmp_path, is_master=False, virtual=True, platform='Linux')
    assert 'id' not in conf  # Vagrant names the guest
    assert conf['file_roots']['base'][-1] == '/vagrant/bevy_srv/salt'


def test_config_second_minion_id_wins(bootstrap, tmp_path):
    bootstrap.my_settings.update(id='node1', second_minion_id='other-id', projects_root='none')
    _, conf = write_config(bootstrap, tmp_path, is_master=False, virtual=False, platform='Linux')
    assert conf['id'] == 'other-id'


def test_config_for_windows_has_crlf_line_endings(bootstrap, tmp_path):
    bootstrap.my_settings.update(id='win1', projects_root='none')
    path, _ = write_config(bootstrap, tmp_path, is_master=False, virtual=False, platform='Windows')
    raw = path.read_bytes()
    assert b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n', b'')


# ---- the bevy settings files ----

@pytest.fixture
def settings_files(bootstrap, tmp_path, monkeypatch):
    shared = tmp_path / 'srv' / 'pillar' / '01_bevy_settings.sls'
    unique = tmp_path / 'etc' / 'salt-bevy' / 'my_settings.conf'
    monkeypatch.setattr(bootstrap, 'BEVY_SETTINGS_FILE_NAME', str(shared))
    monkeypatch.setattr(bootstrap, 'MY_SETTINGS_FILE_NAME', str(unique))
    return shared, unique


def test_settings_files_round_trip(bootstrap, settings_files):
    shared = {'bevy': 'bevy01', 'my_linux_user': 'vernon', 'file_roots': ['/a', '{path}b'],
              'force_linux_user_password': True, 'my_linux_uid': 3001, 'vagrant_network': '192.168.56.0/21'}
    unique = {'id': 'node1', 'master': False, 'master_host': False, 'additional_minion_tag': ''}
    bootstrap.settings = dict(shared, OLD_VAGRANT_SETTING='dropped')
    bootstrap.my_settings = dict(unique)
    bootstrap.write_bevy_settings_files()

    bootstrap.settings, bootstrap.my_settings = {}, {}
    bevy, changed = bootstrap.read_bevy_settings_files({'bevy': 'bevy01'})
    assert (bevy, changed) == ('bevy01', False)
    assert {k: v for k, v in bootstrap.settings.items() if not k.isupper()} == shared
    assert bootstrap.settings['GUEST_MINION_CONFIG_FILE'] == bootstrap.GUEST_MINION_CONFIG_FILE
    assert bootstrap.my_settings == unique


def test_settings_files_keep_a_value_with_an_apostrophe(bootstrap, settings_files):
    # regression: strings were written in single quotes without escaping
    bootstrap.settings = {'bevy': 'bevy01', 'my_windows_password': "it's"}
    bootstrap.my_settings = {}
    bootstrap.write_bevy_settings_files()
    bootstrap.settings = {}
    bootstrap.read_bevy_settings_files({'bevy': 'bevy01'})
    assert bootstrap.settings['my_windows_password'] == "it's"


def test_archived_bevys_are_listed(bootstrap, settings_files, capsys):
    bootstrap.settings, bootstrap.my_settings = {'bevy': 'second'}, {'id': 'n'}
    bootstrap.write_bevy_settings_files(bevy_extension='second')
    assert Path(bootstrap.BEVY_SETTINGS_FILE_NAME + '.second').is_file()
    capsys.readouterr()
    bootstrap.print_names_of_other_bevy_files()
    assert "['second']" in capsys.readouterr().out


# ---- the SSH public key ----

ED25519 = 'ssh-ed25519 ' + 'A' * 68 + ' vernon@example'
RSA = 'ssh-rsa ' + 'B' * 372 + ' vernon@example'


@pytest.fixture
def ssh_home(bootstrap, tmp_path, monkeypatch):
    home = tmp_path / 'home' / 'alice'
    (home / '.ssh').mkdir(parents=True)
    key_dir = tmp_path / 'ssh_keys'
    real_expanduser = os.path.expanduser
    monkeypatch.setattr(bootstrap.os.path, 'expanduser',
                        lambda p: str(home) if p == '~alice' else real_expanduser(p))
    monkeypatch.setattr(bootstrap, 'user_ssh_key_file_directory', key_dir)
    bootstrap.user_name = 'alice'  # the operator; the elevated run's own home would be root's
    return home, key_dir


def test_ssh_key_comes_from_the_operators_home_preferring_ed25519(bootstrap, ssh_home):
    home, key_dir = ssh_home
    (home / '.ssh' / 'id_rsa.pub').write_text(RSA)
    (home / '.ssh' / 'id_ed25519.pub').write_text(ED25519)
    bootstrap.write_ssh_key_file('vernon')
    assert (key_dir / 'vernon.pub').read_text() == ED25519


def test_ssh_key_falls_back_to_rsa(bootstrap, ssh_home):
    home, key_dir = ssh_home
    (home / '.ssh' / 'id_rsa.pub').write_text(RSA)
    bootstrap.write_ssh_key_file('vernon')
    assert (key_dir / 'vernon.pub').read_text() == RSA


def test_ssh_key_already_in_the_tree_is_left_alone(bootstrap, ssh_home):
    home, key_dir = ssh_home
    key_dir.mkdir()
    (key_dir / 'vernon.pub').write_text(RSA)
    (home / '.ssh' / 'id_ed25519.pub').write_text(ED25519)
    bootstrap.write_ssh_key_file('vernon')
    assert (key_dir / 'vernon.pub').read_text() == RSA

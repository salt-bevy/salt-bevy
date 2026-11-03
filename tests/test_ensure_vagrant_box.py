"""
Tests for configure_machine/helpers/ensure_vagrant_box.py, with "vagrant"
and the box build faked, plus a check that its machine table matches the
Vagrantfile (its own comment says to keep the two in sync by hand).
"""
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

from conftest import REPO_ROOT
from helpers import ensure_vagrant_box as evb

BOX_LIST = """\
salt-bevy/ubuntu-26.04 (hyperv, 0)
salt-bevy/ubuntu-24.04 (virtualbox, 0)
bento/ubuntu-22.04     (hyperv, 202401.01.0)
"""


def test_registered_boxes_for_parses_vagrant_box_list(monkeypatch):
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout=BOX_LIST))
    assert evb.registered_boxes_for('hyperv') == {'salt-bevy/ubuntu-26.04', 'bento/ubuntu-22.04'}
    assert evb.registered_boxes_for('vmware_desktop') == set()


def test_registered_boxes_for_without_vagrant(monkeypatch):
    def missing(*a, **kw):
        raise FileNotFoundError('vagrant')
    monkeypatch.setattr(subprocess, 'run', missing)
    assert evb.registered_boxes_for('hyperv') is None


@pytest.fixture
def builds(monkeypatch):
    """Fake environment: no boxes registered; records any build that would run."""
    monkeypatch.delenv('VAGRANT_DEFAULT_PROVIDER', raising=False)
    monkeypatch.delenv('NODE_BOX', raising=False)
    monkeypatch.setattr(evb, 'registered_boxes_for', lambda provider: set())
    calls = []
    monkeypatch.setattr(subprocess, 'run', lambda cmd, **kw: calls.append(cmd))
    return calls


def build_args(version, provider):
    return [sys.executable, str(evb.BUILD_BOXES), '--versions', version, '--providers', provider]


@pytest.mark.parametrize('argv', [
    [],
    ['status'],
    ['ssh', 'quail1'],
    ['up', 'win10'],          # not one of our self-built boxes
    ['reload', 'quail1'],     # no provider known for anything but "up"
])
def test_nothing_to_build(builds, argv):
    evb.main(argv)
    assert builds == []


def test_bare_up_builds_the_default_box_for_hyperv(builds):
    evb.main(['up'])
    assert builds == [build_args(evb.SELF_BUILT_MACHINE_VERSIONS[''], 'hyperv')]


def test_provider_comes_from_the_environment(builds, monkeypatch):
    monkeypatch.setenv('VAGRANT_DEFAULT_PROVIDER', 'virtualbox')
    evb.main(['reload', 'quail24'])
    assert builds == [build_args('24.04', 'virtualbox')]


def test_generic_uses_the_default_box_unless_node_box_is_set(builds, monkeypatch):
    evb.main(['up', 'generic', 'node9'])
    assert builds == [build_args(evb.SELF_BUILT_MACHINE_VERSIONS[''], 'hyperv')]
    builds.clear()
    monkeypatch.setenv('NODE_BOX', 'bento/ubuntu-22.04')
    evb.main(['up', 'generic', 'node9'])
    assert builds == []


def test_no_build_when_the_box_is_registered(builds, monkeypatch):
    monkeypatch.setattr(evb, 'registered_boxes_for', lambda provider: {'salt-bevy/ubuntu-26.04'})
    evb.main(['up', 'quail1'])
    assert builds == []


def test_no_build_when_vagrant_cannot_be_asked(builds, monkeypatch):
    monkeypatch.setattr(evb, 'registered_boxes_for', lambda provider: None)
    evb.main(['up', 'quail1'])
    assert builds == []


# ---- kept in sync with the Vagrantfile ----

def vagrantfile_boxes():
    """{machine name: box} for each quoted "config.vm.define" in the Vagrantfile."""
    lines = [line for line in (REPO_ROOT / 'Vagrantfile').read_text().splitlines()
             if not line.lstrip().startswith('#')]
    text = '\n'.join(lines)
    default_box = re.search(r'^DEFAULT_BOX\s*=\s*"([^"]+)"', text, re.M).group(1)
    defines = list(re.finditer(r'config\.vm\.define\s+"([^"]+)"', text))
    boxes = {}
    for i, define in enumerate(defines):
        end = defines[i + 1].start() if i + 1 < len(defines) else len(text)
        box = re.search(r'\.vm\.box\s*=\s*(DEFAULT_BOX|"([^"]+)")', text[define.end():end])
        if box:
            boxes[define.group(1)] = default_box if box.group(1) == 'DEFAULT_BOX' else box.group(2)
    return default_box, boxes


def test_machine_table_matches_the_vagrantfile():
    default_box, boxes = vagrantfile_boxes()
    self_built = {name: box.rsplit('-', 1)[1] for name, box in boxes.items()
                  if box.startswith('salt-bevy/ubuntu-')}
    table = dict(evb.SELF_BUILT_MACHINE_VERSIONS)
    assert table.pop('') == default_box.rsplit('-', 1)[1]
    assert table == self_built

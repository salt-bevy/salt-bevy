"""
Shared setup for salt-bevy's tests.

bootstrap_bevy_member_here.py is a script, not a package module: it does
"from helpers import ...", so configure_machine/ must be on sys.path, and it
is loaded from its file path rather than imported by name.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIGURE_MACHINE = REPO_ROOT / 'configure_machine'
BOOTSTRAP = CONFIGURE_MACHINE / 'bootstrap_bevy_member_here.py'

if str(CONFIGURE_MACHINE) not in sys.path:
    sys.path.insert(0, str(CONFIGURE_MACHINE))


def load_script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bootstrap(monkeypatch):
    """A fresh copy of the bootstrap script, with its prompts turned off."""
    for prerequisite in ('yaml', 'ifaddr', 'windows_sudo', 'passlib'):
        pytest.importorskip(prerequisite)  # the script exits without them
    monkeypatch.setattr(sys, 'argv', ['bootstrap_bevy_member_here.py'])
    module = load_script(BOOTSTRAP, 'bootstrap_bevy_member_here')
    module.interactive = False  # normally set by the script's main section
    module.settings = {}
    module.my_settings = {}
    module.user_name = ''
    return module

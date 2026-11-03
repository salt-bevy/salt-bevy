"""
Every YAML and Salt .sls file without Jinja in it should parse as YAML.
(Files with Jinja need Salt to render them first, so they're skipped.)
"""
import pytest

from conftest import REPO_ROOT

yaml = pytest.importorskip('yaml')

SKIP_DIRS = {'.git', '.venv', 'venv', '.bento', 'node_modules', '.idea'}
JINJA = ('{%', '{{', '{#')


def plain_yaml_files():
    for path in sorted(REPO_ROOT.rglob('*')):
        if path.suffix not in ('.sls', '.yaml', '.yml') or not path.is_file():
            continue
        if SKIP_DIRS.intersection(path.relative_to(REPO_ROOT).parts):
            continue
        if any(marker in path.read_text(encoding='utf-8') for marker in JINJA):
            continue
        yield path


@pytest.mark.parametrize('path', list(plain_yaml_files()),
                         ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_parses_as_yaml(path):
    yaml.safe_load(path.read_text(encoding='utf-8'))

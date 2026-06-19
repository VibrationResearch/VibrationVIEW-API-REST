"""
Guard against bare ``import config`` which leads to config.X AttributeError bugs (issue #9).

The config module and Config class share a name.  Using ``import config``
and then ``config.EXE_NAME`` silently refers to the *module*, not the class,
causing AttributeError at runtime.  All project code must use
``from config import Config`` (or ``TestingConfig``) instead.
"""

import ast
import os

import pytest

# Project source directories to scan (relative to repo root)
_SOURCE_DIRS = ["routes", "utils"]

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _python_files(dirs):
    """Yield (relative_path, absolute_path) for .py files in dirs."""
    for d in dirs:
        abs_dir = os.path.join(_REPO_ROOT, d)
        for root, _, files in os.walk(abs_dir):
            for f in files:
                if f.endswith(".py"):
                    abs_path = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_path, _REPO_ROOT)
                    yield rel_path, abs_path


def _has_bare_import_config(filepath):
    """Return True if the file contains ``import config`` (not ``from config import ...``)."""
    with open(filepath, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=filepath)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "config":
                    return True
    return False


@pytest.mark.parametrize(
    "rel_path,abs_path",
    list(_python_files(_SOURCE_DIRS)),
    ids=[rp for rp, _ in _python_files(_SOURCE_DIRS)],
)
def test_no_bare_import_config(rel_path, abs_path):
    """``import config`` must not appear — use ``from config import Config`` instead."""
    assert not _has_bare_import_config(abs_path), (
        f"{rel_path}: uses bare `import config`. "
        "Change to `from config import Config` to avoid config.X AttributeError bugs."
    )

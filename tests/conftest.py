import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = REPO_ROOT / "core"

sys.path.insert(0, str(CORE_DIR))

@pytest.fixture
def fake_ssh_dir(tmp_path, monkeypatch):
    import core.app as app_module
    import core.key_pair_gen

    monkeypatch.setattr(core.key_pair_gen, "ssh_directory", str(tmp_path))
    monkeypatch.setattr(app_module, "ssh_directory", str(tmp_path))

    return tmp_path


def load_ssh_connection_test_module():
    path = REPO_ROOT / "ssh" / "ssh-connection-test.py"
    spec = importlib.util.spec_from_file_location("ssh_connection_test_module_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ssh_connection_test_module():
    return load_ssh_connection_test_module()
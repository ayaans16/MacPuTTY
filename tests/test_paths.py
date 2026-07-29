from pathlib import Path


def test_resource_path_dev_mode_resolves_relative_to_repo_root():
    import core.paths 

    result = core.paths .resource_path("config.conf")

    expected_repo_root = Path(core.paths .__file__).resolve().parent.parent
    assert result == expected_repo_root / "config.conf"


def test_resource_path_frozen_mode_resolves_relative_to_meipass(tmp_path, monkeypatch):
    import sys
    import core.paths 

    fake_bundle_root = tmp_path / "bundle"
    fake_bundle_root.mkdir()

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(fake_bundle_root), raising=False)

    result = core.paths .resource_path("config.conf")

    assert result == fake_bundle_root / "config.conf"


def test_resource_path_joins_multiple_parts():
    import core.paths 

    result = core.paths .resource_path("ssh", "ssh-connection-test.py")

    expected_repo_root = Path(core.paths .__file__).resolve().parent.parent
    assert result == expected_repo_root / "ssh" / "ssh-connection-test.py"
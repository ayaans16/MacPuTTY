def test_no_config_file(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    result = get_ssh_config_usage(str(tmp_path))

    assert result["config_exists"] is False
    assert result["hosts"] == []


def test_basic_host_with_existing_key(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "id_ed25519").touch()
    (tmp_path / "config").write_text(
        "Host github.com\n"
        "    HostName github.com\n"
        "    User git\n"
        f"    IdentityFile {tmp_path}/id_ed25519\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert result["config_exists"] is True
    assert len(result["hosts"]) == 1
    host = result["hosts"][0]
    assert host["host"] == "github.com"
    assert host["hostname"] == "github.com"
    assert host["user"] == "git"
    assert host["identity_files"] == [{"path": f"{tmp_path}/id_ed25519", "exists": True}]


def test_missing_identity_file(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "config").write_text(
        "Host prod-server\n"
        "    HostName 10.0.1.5\n"
        f"    IdentityFile {tmp_path}/does_not_exist\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert result["hosts"][0]["identity_files"] == [
        {"path": f"{tmp_path}/does_not_exist", "exists": False}
    ]


def test_relative_identity_file_resolved_against_ssh_directory(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "id_rsa_relative").touch()
    (tmp_path / "config").write_text(
        "Host staging\n"
        "    HostName staging.example.com\n"
        "    IdentityFile id_rsa_relative\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert result["hosts"][0]["identity_files"] == [
        {"path": "id_rsa_relative", "exists": True}
    ]


def test_absolute_path_falls_back_to_matching_filename_in_ssh_directory(tmp_path):
    # Regression test: an IdentityFile written as an absolute path for a
    # DIFFERENT environment (e.g. a host-side macOS path like
    # /Users/you/.ssh/key, while this code runs inside a Docker container
    # that only has ssh_directory bind-mounted at a different absolute
    # path) should still resolve, as long as a same-named file exists in
    # our own ssh_directory.
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "skyblock_boba").touch()
    (tmp_path / "config").write_text(
        "Host sb-www\n"
        "    HostName 40.160.2.212\n"
        "    IdentityFile /Users/someone/.ssh/skyblock_boba\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert result["hosts"][0]["identity_files"] == [
        {"path": "/Users/someone/.ssh/skyblock_boba", "exists": True}
    ]


def test_absolute_path_genuinely_missing_is_not_a_false_positive(tmp_path):
    # Guards against the fallback above being too permissive: if no
    # same-named file exists in ssh_directory either, it must stay "missing".
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "config").write_text(
        "Host really-missing\n"
        "    HostName 1.2.3.4\n"
        "    IdentityFile /Users/someone/.ssh/genuinely_does_not_exist\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert result["hosts"][0]["identity_files"] == [
        {"path": "/Users/someone/.ssh/genuinely_does_not_exist", "exists": False}
    ]


def test_wildcard_host_excluded_from_results(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "config").write_text(
        "Host github.com\n"
        "    HostName github.com\n"
        "\n"
        "Host *\n"
        "    ServerAliveInterval 60\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    hosts = [h["host"] for h in result["hosts"]]
    assert "*" not in hosts
    assert hosts == ["github.com"]


def test_wildcard_defaults_merge_into_named_hosts(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "config").write_text(
        "Host *\n"
        "    User default-user\n"
        "\n"
        "Host github.com\n"
        "    HostName github.com\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert result["hosts"][0]["user"] == "default-user"


def test_host_with_no_identity_file_configured(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "config").write_text(
        "Host no-key-host\n"
        "    HostName no-key.example.com\n"
        "    User nobody\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert result["hosts"][0]["identity_files"] == []


def test_multiple_identity_files_for_one_host(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "key_one").touch()
    (tmp_path / "config").write_text(
        "Host multi-key\n"
        "    HostName multi.example.com\n"
        f"    IdentityFile {tmp_path}/key_one\n"
        f"    IdentityFile {tmp_path}/key_two\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    paths = [f["path"] for f in result["hosts"][0]["identity_files"]]
    assert paths == [f"{tmp_path}/key_one", f"{tmp_path}/key_two"]


def test_hosts_sorted_alphabetically(tmp_path):
    from core.ssh_config_visualizer import get_ssh_config_usage

    (tmp_path / "config").write_text(
        "Host zebra\n"
        "    HostName zebra.example.com\n"
        "\n"
        "Host apple\n"
        "    HostName apple.example.com\n"
    )

    result = get_ssh_config_usage(str(tmp_path))

    assert [h["host"] for h in result["hosts"]] == ["apple", "zebra"]
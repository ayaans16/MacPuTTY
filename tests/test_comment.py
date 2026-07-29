def test_add_comment_to_file_appends_comment(tmp_path):
    from core.comment import add_comment_to_file

    pubkey_file = tmp_path / "id_ed25519.pub"
    pubkey_file.write_text("ssh-ed25519 AAAAABBBBB\n")

    add_comment_to_file(pubkey_file, "ayaan@macbook")

    assert pubkey_file.read_text() == "ssh-ed25519 AAAAABBBBB ayaan@macbook\n"


def test_add_comment_to_file_strips_trailing_newlines_before_appending(tmp_path):
    from core.comment import add_comment_to_file

    pubkey_file = tmp_path / "id_ed25519.pub"
    pubkey_file.write_text("ssh-ed25519 AAAAABBBBB\n\n\n")

    add_comment_to_file(pubkey_file, "ayaan@macbook")

    content = pubkey_file.read_text()
    assert content == "ssh-ed25519 AAAAABBBBB ayaan@macbook\n"
    assert "\n\n" not in content


def test_add_comment_to_file_on_key_with_existing_comment(tmp_path):
    from core.comment import add_comment_to_file

    pubkey_file = tmp_path / "id_ed25519.pub"
    pubkey_file.write_text("ssh-ed25519 AAAAABBBBB old-comment\n")

    add_comment_to_file(pubkey_file, "new-comment")

    # Documents current behavior: the new core.comment is appended after the old
    # one rather than replacing it. If that's not the intended behavior,
    # this test is the place to change it.
    assert pubkey_file.read_text() == "ssh-ed25519 AAAAABBBBB old-core.comment new-comment\n"


def test_add_comment_to_file_expands_user_path(tmp_path, monkeypatch):
    from core.comment import add_comment_to_file

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    pubkey_file = fake_home / "id_ed25519.pub"
    pubkey_file.write_text("ssh-ed25519 AAAAABBBBB\n")

    monkeypatch.setenv("HOME", str(fake_home))

    add_comment_to_file("~/id_ed25519.pub", "ayaan@macbook")

    assert pubkey_file.read_text() == "ssh-ed25519 AAAAABBBBB ayaan@macbook\n"
from pathlib import Path

from cryptography.hazmat.primitives import serialization


def test_generate_rsa_key_pair_writes_expected_files(fake_ssh_dir):
    import core.key_pair_gen

    core.key_pair_gen.generate_rsa_key_pair()

    assert (fake_ssh_dir / "id_rsa").is_file()
    assert (fake_ssh_dir / "id_rsa.pub").is_file()


def test_generate_rsa_key_pair_uses_configured_bit_size(fake_ssh_dir, monkeypatch):
    import core.key_pair_gen

    monkeypatch.setattr(core.key_pair_gen, "rsa_key_bits", 2048)
    core.key_pair_gen.generate_rsa_key_pair()

    private_bytes = (fake_ssh_dir / "id_rsa").read_bytes()
    private_key = serialization.load_ssh_private_key(private_bytes, password=None)

    assert private_key.key_size == 2048


def test_generate_rsa_key_pair_default_bit_size_is_4096(fake_ssh_dir):
    import core.key_pair_gen

    assert core.key_pair_gen.rsa_key_bits == 4096

    core.key_pair_gen.generate_rsa_key_pair()
    private_bytes = (fake_ssh_dir / "id_rsa").read_bytes()
    private_key = serialization.load_ssh_private_key(private_bytes, password=None)

    assert private_key.key_size == 4096


def test_generate_ecdsa_key_pair_writes_expected_files(fake_ssh_dir):
    import core.key_pair_gen

    core.key_pair_gen.generate_ecdsa_key_pair()

    assert (fake_ssh_dir / "id_ecdsa").is_file()
    assert (fake_ssh_dir / "id_ecdsa.pub").is_file()


def test_generate_ed25519_key_pair_writes_expected_files(fake_ssh_dir):
    import core.key_pair_gen

    core.key_pair_gen.generate_ed25519_key_pair()

    assert (fake_ssh_dir / "id_ed25519").is_file()
    assert (fake_ssh_dir / "id_ed25519.pub").is_file()


def test_private_key_file_permissions_are_owner_only(fake_ssh_dir):
    import core.key_pair_gen

    core.key_pair_gen.generate_ed25519_key_pair()

    private_key_mode = (fake_ssh_dir / "id_ed25519").stat().st_mode & 0o777
    public_key_mode = (fake_ssh_dir / "id_ed25519.pub").stat().st_mode & 0o777

    assert private_key_mode == 0o600
    assert public_key_mode != 0o600  # public key isn't meant to be locked down


def test_generate_creates_ssh_directory_if_missing(tmp_path, monkeypatch):
    import core.key_pair_gen

    nested_dir = tmp_path / "does" / "not" / "exist" / "yet"
    monkeypatch.setattr(core.key_pair_gen, "ssh_directory", str(nested_dir))

    core.key_pair_gen.generate_ed25519_key_pair()

    assert (nested_dir / "id_ed25519").is_file()
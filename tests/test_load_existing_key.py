import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519


def _rsa_private_bytes(password=None):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    encryption = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=encryption,
    )


def _ecdsa_private_bytes(password=None):
    key = ec.generate_private_key(ec.SECP256K1())
    encryption = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    # Matches key_pair_gen.generate_ecdsa_key_pair()'s own encoding choice:
    # PKCS8/PEM, not OpenSSH format.
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )


def _ed25519_private_bytes(password=None):
    key = ed25519.Ed25519PrivateKey.generate()
    encryption = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=encryption,
    )


def test_get_key_type_rsa():
    from core.load_existing_key import get_key_type

    assert get_key_type(_rsa_private_bytes()) == "RSA"


def test_get_key_type_ecdsa():
    from core.load_existing_key import get_key_type

    assert get_key_type(_ecdsa_private_bytes()) == "ECDSA"


def test_get_key_type_ed25519():
    from core.load_existing_key import get_key_type

    assert get_key_type(_ed25519_private_bytes()) == "ED25519"


def test_get_key_type_encrypted_key_with_correct_password():
    from core.load_existing_key import get_key_type

    key_bytes = _ed25519_private_bytes(password=b"correct horse")
    assert get_key_type(key_bytes, password=b"correct horse") == "ED25519"


def test_get_key_type_encrypted_key_without_password_raises():
    from core.load_existing_key import get_key_type

    key_bytes = _ed25519_private_bytes(password=b"correct horse")
    with pytest.raises(TypeError):
        get_key_type(key_bytes)


def test_get_key_type_encrypted_key_wrong_password_raises():
    from core.load_existing_key import get_key_type

    key_bytes = _ed25519_private_bytes(password=b"correct horse")
    with pytest.raises(ValueError):
        get_key_type(key_bytes, password=b"wrong password")


def test_get_key_type_garbage_input_raises():
    from core.load_existing_key import get_key_type

    with pytest.raises(ValueError):
        get_key_type(b"this is not a key at all")


def test_pubkey_generation_rsa_is_openssh_format():
    from core.load_existing_key import pubkey_generation

    pubkey = pubkey_generation(_rsa_private_bytes())
    assert pubkey.startswith("ssh-rsa ")


def test_pubkey_generation_ed25519_is_openssh_format():
    from core.load_existing_key import pubkey_generation

    pubkey = pubkey_generation(_ed25519_private_bytes())
    assert pubkey.startswith("ssh-ed25519 ")


def test_pubkey_generation_ecdsa_is_pem_format():
    from core.load_existing_key import pubkey_generation

    pubkey = pubkey_generation(_ecdsa_private_bytes())
    assert pubkey.startswith("-----BEGIN PUBLIC KEY-----")
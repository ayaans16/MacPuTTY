from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_ssh_private_key, Encoding, PublicFormat
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519


def get_key_type(key_bytes: bytes, password: bytes = None) -> str:
    try:
        key = load_ssh_private_key(data=key_bytes, password=password)
    except ValueError:
        key = load_pem_private_key(data=key_bytes, password=password)

    if isinstance(key, rsa.RSAPrivateKey):
        return "RSA"
    if isinstance(key, ec.EllipticCurvePrivateKey):
        return "ECDSA"
    if isinstance(key, ed25519.Ed25519PrivateKey):
        return "ED25519"
    return "unknown"


def pubkey_generation(key_bytes: bytes, password: bytes = None) -> str:
    key_type = get_key_type(key_bytes, password)

    if key_type not in ("RSA", "ED25519", "ECDSA"):
        raise ValueError(f"RSA, ED25519 or ECDSA key expected, got {key_type}")

    if key_type == "ECDSA":
        priv_key = load_pem_private_key(data=key_bytes, password=password)
        public_key = priv_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )
    else:
        priv_key = load_ssh_private_key(data=key_bytes, password=password)
        public_key = priv_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

    return public_pem.decode()
"""
This file is meant to take in existing private keys so you can:
- modify the format (rsa <-> ed25519, ecdsa <-> ed25519, rsa <-> ecdsa)
- edit the comment associated with it
- generate its public key
"""

from pathlib import Path
from pyhocon import ConfigFactory

# imports for key detection
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_ssh_private_key
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

# rsa imports
from cryptography.hazmat.primitives.asymmetric import rsa

# ecdsa imports
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

# ed25519 import
from cryptography.hazmat.primitives.asymmetric import ed25519

# hocon config info
config = ConfigFactory.parse_file('config.conf')
ssh_directory = config.get('directory.path')

"""
for reference: -> str means the function return type should be a string
"""
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

"""
usage example:
ssh_directory = Path("~/test_ssh/id_ed25519").expanduser()
key_bytes = ssh_directory.read_bytes()
key_type = get_key_type(key_bytes)
print(key_type)
"""

def pubkey_generation(key_bytes: bytes, password: bytes = None) -> str:
    key_type = get_key_type(key_bytes, password)

    if key_type != "RSA" and key_type != "ED25519" and key_type != "ECDSA":
        raise ValueError(f"RSA, ED25519 or ECDSA key expected, did not receive this")

    if key_type == "ECDSA":
        priv_key = load_pem_private_key(data=key_bytes, password=password)
        public_key = priv_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )

    if key_type == "RSA" or key_type == "ED25519":
        priv_key = load_ssh_private_key(data=key_bytes, password=password)
        public_key = priv_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

    print(public_pem.decode())
    return public_pem.decode()

"""
example usage:
pubkey_generation(key_bytes)
"""

def add_comment_to_file(pubkey_filepath, comment: str) -> None:
    pubkey_filepath = Path(pubkey_filepath).expanduser()
    content = pubkey_filepath.read_text().rstrip("\n")
    updated = f"{content} {comment}\n"
    pubkey_filepath.write_text(updated)

"""
add_comment_to_file("~/test_ssh/id_ed25519.pub", "ayaan@macbook")
"""
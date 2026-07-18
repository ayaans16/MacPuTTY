"""
This file is meant to take in existing private keys so you can:
- modify the format (rsa <-> ed25519, ecdsa <-> ed25519, rsa <-> ecdsa)
- edit the comment associated with it
- generate its public key
"""

from pathlib import Path

# imports for key detection
from cryptography.hazmat.primitives.serialization import load_ssh_private_key
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

"""
for reference: -> str means the function return type should be a string
"""
def get_key_type(key_bytes: bytes, password: bytes = None) -> str:
    key = load_ssh_private_key(data=key_bytes, password=password)

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

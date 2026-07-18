"""
This file will be used to generate a public & private key file pair.
Types include: RSA, ECDSA, ED25519, SSH-1 (RSA)
"""
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

# rsa imports
from cryptography.hazmat.primitives.asymmetric import rsa

# ecdsa imports
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

# ed25519 import
from cryptography.hazmat.primitives.asymmetric import ed25519

def generate_rsa_key_pair():
    # generate keys
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    public_key = private_key.public_key()


    # file and directory info
    ssh_directory = Path("~/test_ssh").expanduser()
    ssh_directory.mkdir(parents=True, exist_ok=True)

    private_rsa_key_filename = "id_rsa"
    public_rsa_key_filename = "id_rsa.pub"

    private_key_filepath = ssh_directory / private_rsa_key_filename
    public_key_filepath = ssh_directory / public_rsa_key_filename

    # pem
    """
    for self knowledge: pem (privacy-enhanced mail) is the standard
    file format to store and transmit crypto keys & SSL/TLS certs
    """
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )

    # create id_rsa and id_rsa.pub
    private_key_filepath.write_bytes(private_pem)
    public_key_filepath.write_bytes(public_pem)

    # set up permissions
    private_key_filepath.chmod(0o600)

def generate_ecdsa_key_pair():
    # using SECP256k1 curve
    private_key = ec.generate_private_key(ec.SECP256K1())

    public_key = private_key.public_key()

    # pem
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    )

    # file and directory info
    ssh_directory = Path("~/test_ssh").expanduser()
    ssh_directory.mkdir(parents=True, exist_ok=True)

    private_ecdsa_key_filename = "id_ecdsa"
    public_ecdsa_key_filename = "id_ecdsa.pub"

    private_key_filepath = ssh_directory / private_ecdsa_key_filename
    public_key_filepath = ssh_directory / public_ecdsa_key_filename

    # create id_rsa and id_rsa.pub
    private_key_filepath.write_bytes(private_pem)
    public_key_filepath.write_bytes(public_pem)

    # set up permissions
    private_key_filepath.chmod(0o600)

def generate_ed25519_key_pair():
    # key gen
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # pem
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )

    # file and directory info
    ssh_directory = Path("~/test_ssh").expanduser()
    ssh_directory.mkdir(parents=True, exist_ok=True)

    private_ed25519_key_filename = "id_ed25519"
    public_ed25519_key_filename = "id_ed25519.pub"

    private_key_filepath = ssh_directory / private_ed25519_key_filename
    public_key_filepath = ssh_directory / public_ed25519_key_filename

    # create id_rsa and id_rsa.pub
    private_key_filepath.write_bytes(private_pem)
    public_key_filepath.write_bytes(public_pem)

    # set up permissions
    private_key_filepath.chmod(0o600)

if __name__ == "__main__":
    generate_ed25519_key_pair()
"""Encryption of contributors' private contact details.

If config/public_key.pem exists, private details are encrypted with it
(RSA-OAEP-SHA256 wrapping a random AES-256-GCM key), so only the holder of the
matching private key - the data-collection team - can read them. Generate the
key pair with tools/generate_keys.py.
"""

import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import PUBLIC_KEY_FILE

ALGORITHM = "RSA-OAEP-SHA256+AES-256-GCM"


def _oaep():
    return padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(), label=None)


def encryption_available() -> bool:
    return PUBLIC_KEY_FILE.is_file()


def encrypt_json(payload: dict, public_key_path: Path = PUBLIC_KEY_FILE) -> dict:
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    aes_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, json.dumps(payload).encode("utf-8"), None)
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return {"algorithm": ALGORITHM, "key": b64(public_key.encrypt(aes_key, _oaep())),
            "nonce": b64(nonce), "ciphertext": b64(ciphertext)}


def decrypt_json(envelope: dict, private_key_path: Path, password: bytes | None = None) -> dict:
    private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password)
    unb64 = base64.b64decode
    aes_key = private_key.decrypt(unb64(envelope["key"]), _oaep())
    plain = AESGCM(aes_key).decrypt(unb64(envelope["nonce"]), unb64(envelope["ciphertext"]), None)
    return json.loads(plain)

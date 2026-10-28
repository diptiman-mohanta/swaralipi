"""Create the key pair that protects contributors' contact details.

Run ONCE, on the data-collection team's computer:

    .venv\\Scripts\\python tools\\generate_keys.py

* config/public_key.pem  -> ship this with the app (safe to share).
* keys/private_key.pem   -> keep SECRET and backed up. Never put it in the repo
                            or send it to contributors. Without it the contact
                            details in submissions cannot be read.
"""

import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "config" / "public_key.pem"
PRIVATE = ROOT / "keys" / "private_key.pem"


def main() -> int:
    if PUBLIC.exists() or PRIVATE.exists():
        print("Keys already exist - refusing to overwrite.\n"
              f"  {PUBLIC}\n  {PRIVATE}\n"
              "Delete them yourself if you really want new keys (old submissions will then "
              "only open with the old private key).")
        return 1
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    PRIVATE.parent.mkdir(exist_ok=True)
    PRIVATE.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                          serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    PUBLIC.write_bytes(key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    print(f"Public key  (ship with the app): {PUBLIC}")
    print(f"Private key (KEEP SECRET):       {PRIVATE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

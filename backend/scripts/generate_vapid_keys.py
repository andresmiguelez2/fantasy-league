"""Generate VAPID keys for Web Push.

Usage:
    python scripts/generate_vapid_keys.py

Copy the printed values into your environment (e.g. secrets/db.env):
    VAPID_PUBLIC_KEY=...
    VAPID_PRIVATE_KEY=...
"""
import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1, generate_private_key
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def main() -> None:
    private_key = generate_private_key(SECP256R1())
    public_bytes = private_key.public_key().public_bytes(
        Encoding.X962, PublicFormat.UncompressedPoint
    )
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")

    print(f"VAPID_PUBLIC_KEY={_b64url(public_bytes)}")
    print(f"VAPID_PRIVATE_KEY={_b64url(private_bytes)}")


if __name__ == "__main__":
    main()

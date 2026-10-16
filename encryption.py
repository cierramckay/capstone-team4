import json
import os
from pathlib import Path
from typing import Dict, Mapping, Optional

from cryptography.fernet import Fernet


KEY_FILE = Path(__file__).resolve().with_name("secret.key")


def load_or_create_key() -> bytes:
    configured_key = os.environ.get("INVENTORY_ENCRYPTION_KEY")
    if configured_key:
        return configured_key.encode("ascii")

    try:
        key = KEY_FILE.read_bytes()
    except FileNotFoundError:
        key = Fernet.generate_key()
        try:
            descriptor = os.open(
                KEY_FILE,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            key = KEY_FILE.read_bytes()
        else:
            with os.fdopen(descriptor, "wb") as key_file:
                key_file.write(key)
            return key

    KEY_FILE.chmod(0o600)
    return key


cipher = Fernet(load_or_create_key())


def encrypt_metadata(metadata: Mapping[str, str]) -> Optional[bytes]:
    if not metadata:
        return None
    payload = json.dumps(dict(metadata), separators=(",", ":")).encode("utf-8")
    return cipher.encrypt(payload)


def decrypt_metadata(token: Optional[bytes]) -> Optional[Dict[str, str]]:
    if token is None:
        return None
    return json.loads(cipher.decrypt(token).decode("utf-8"))

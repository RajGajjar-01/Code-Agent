from __future__ import annotations

import logging
from functools import lru_cache

from cryptography.fernet import Fernet, MultiFernet

from app.core.config import settings

logger = logging.getLogger(__name__)


def _parse_fernet_keys(raw: str) -> list[bytes]:
    keys: list[bytes] = []
    for part in (raw or "").split(","):
        p = part.strip()
        if not p:
            continue
        keys.append(p.encode("utf-8"))
    return keys


@lru_cache(maxsize=8)
def _get_fernet(raw: str) -> MultiFernet:
    keys = _parse_fernet_keys(raw)

    if not keys:
        raise RuntimeError(
            "WP_CONNECTOR_FERNET_KEYS is required to encrypt/decrypt stored WordPress site passwords. "
            "Set it in backend/.env (comma-separated Fernet keys; first key is used for new encryptions)."
        )

    fernets = [Fernet(k) for k in keys]
    return MultiFernet(fernets)


def encrypt_secret(plaintext: str) -> str:
    if plaintext is None:
        raise ValueError("plaintext is required")
    raw = (getattr(settings, "WP_CONNECTOR_FERNET_KEYS", "") or "").strip()
    token = _get_fernet(raw).encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(token: str) -> str:
    if token is None:
        raise ValueError("token is required")
    raw = (getattr(settings, "WP_CONNECTOR_FERNET_KEYS", "") or "").strip()
    plaintext = _get_fernet(raw).decrypt(token.encode("utf-8"))
    return plaintext.decode("utf-8")


def maybe_decrypt_secret(value: str) -> str:
    if value is None:
        raise ValueError("value is required")
    raw = (getattr(settings, "WP_CONNECTOR_FERNET_KEYS", "") or "").strip()
    if not raw:
        return value
    try:
        return decrypt_secret(value)
    except Exception:
        return value

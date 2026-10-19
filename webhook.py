"""HMAC validation for Adyen standard webhooks.

Adyen signs each NotificationRequestItem with HMAC-SHA256 over a colon-joined string of
eight fields, using the hex-encoded HMAC key from Customer Area. The signature arrives
base64-encoded in additionalData.hmacSignature.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
from typing import Any


SIGNED_FIELDS = (
    "pspReference",
    "originalReference",
    "merchantAccountCode",
    "merchantReference",
    "amount.value",
    "amount.currency",
    "eventCode",
    "success",
)


def _field(item: dict[str, Any], path: str) -> str:
    cur: Any = item
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return ""
        cur = cur[part]
    if cur is None:
        return ""
    return str(cur)


def signing_string(item: dict[str, Any]) -> str:
    """The exact string Adyen signs. Backslashes and colons in values are escaped."""
    values = []
    for path in SIGNED_FIELDS:
        v = _field(item, path)
        v = v.replace("\\", "\\\\").replace(":", "\\:")
        values.append(v)
    return ":".join(values)


def compute_signature(item: dict[str, Any], hmac_key_hex: str) -> str:
    try:
        key = binascii.unhexlify(hmac_key_hex)
    except (binascii.Error, ValueError) as e:
        raise ValueError("ADYEN_HMAC_KEY must be the hex string from Customer Area") from e
    digest = hmac.new(key, signing_string(item).encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def is_valid(item: dict[str, Any], hmac_key_hex: str) -> bool:
    provided = (item.get("additionalData") or {}).get("hmacSignature", "")
    if not provided:
        return False
    expected = compute_signature(item, hmac_key_hex)
    return hmac.compare_digest(expected, provided)

"""Thin wrapper around the two Checkout API calls this app makes.

Everything here is plain `requests` so the request and response shapes stay visible.
The official `Adyen` Python library is fine too; it was left out on purpose so the
friction log reflects what a developer reading the docs actually has to send.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import requests


class AdyenConfigError(RuntimeError):
    pass


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise AdyenConfigError(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


def build_session_request(
    *,
    amount_minor: int,
    currency: str,
    country_code: str,
    merchant_account: str,
    return_url: str,
    reference: str | None = None,
) -> dict[str, Any]:
    """Build the body for POST /sessions.

    `amount.value` is in minor units: 1000 EUR cents = EUR 10.00.
    `reference` is your order id. Adyen echoes it back on the webhook as merchantReference.
    """
    if amount_minor <= 0:
        raise ValueError("amount_minor must be a positive integer in minor units")
    return {
        "amount": {"value": amount_minor, "currency": currency},
        "reference": reference or f"test-{uuid.uuid4().hex[:12]}",
        "returnUrl": return_url,
        "merchantAccount": merchant_account,
        "countryCode": country_code,
    }


def create_session(body: dict[str, Any]) -> dict[str, Any]:
    """POST /sessions and return Adyen's response as a dict.

    Raises requests.HTTPError with Adyen's error body attached so the caller can show it.
    """
    api_key = _required("ADYEN_API_KEY")
    base = os.environ.get("ADYEN_CHECKOUT_URL", "https://checkout-test.adyen.com/v71").rstrip("/")
    resp = requests.post(
        f"{base}/sessions",
        json=body,
        headers={"x-API-key": api_key, "content-type": "application/json"},
        timeout=15,
    )
    if resp.status_code >= 400:
        # Adyen returns {"status":403,"errorCode":"901","message":"Invalid Merchant Account",...}
        raise requests.HTTPError(f"{resp.status_code} from /sessions: {resp.text}", response=resp)
    return resp.json()

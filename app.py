"""Test Integration with Adyen.

A minimal, end-to-end Adyen Checkout integration using the Sessions flow and Drop-in v6:

    browser  --POST /api/sessions-->  this server  --POST /v71/sessions-->  Adyen
    browser  <-- session id + data --  this server
    Drop-in renders, shopper pays, Adyen posts a webhook to /api/webhooks/notifications

Run:  cp .env.example .env  (fill it in)  then  python app.py
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

import adyen_client
import webhook

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("adyen-test")

app = Flask(__name__, static_folder="static", template_folder="templates")

# Every webhook that passes HMAC lands here so you can see it at /api/webhooks/received.
RECEIVED: list[dict] = []


@app.get("/")
def index():
    return render_template(
        "index.html",
        client_key=os.environ.get("ADYEN_CLIENT_KEY", ""),
        environment="test",
    )


@app.get("/redirect")
def redirect_landing():
    """Adyen sends the shopper back here after a redirect payment method (iDEAL, 3DS, etc.).

    Query params: sessionId, redirectResult. The page hands redirectResult to Drop-in,
    which calls Adyen to finish the payment. Nothing is verified server-side here; the
    webhook is the source of truth.
    """
    return render_template(
        "redirect.html",
        client_key=os.environ.get("ADYEN_CLIENT_KEY", ""),
        environment="test",
        session_id=request.args.get("sessionId", ""),
        redirect_result=request.args.get("redirectResult", ""),
    )


@app.post("/api/sessions")
def create_session():
    """Create a Checkout session for Drop-in. Body (all optional):
    {"amount": 1000, "currency": "EUR", "countryCode": "NL"}
    """
    data = request.get_json(silent=True) or {}
    try:
        body = adyen_client.build_session_request(
            amount_minor=int(data.get("amount", 1000)),
            currency=str(data.get("currency", "EUR")),
            country_code=str(data.get("countryCode", "NL")),
            merchant_account=os.environ.get("ADYEN_MERCHANT_ACCOUNT", ""),
            return_url=os.environ.get("RETURN_URL", "http://localhost:8080/redirect"),
            reference=data.get("reference"),
        )
        if not body["merchantAccount"]:
            raise adyen_client.AdyenConfigError("ADYEN_MERCHANT_ACCOUNT is not set")
        log.info("POST /sessions reference=%s amount=%s %s", body["reference"], body["amount"]["value"], body["amount"]["currency"])
        session = adyen_client.create_session(body)
    except adyen_client.AdyenConfigError as e:
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # requests.HTTPError carries Adyen's error body in the message
        log.error("session creation failed: %s", e)
        return jsonify({"error": str(e)}), 502

    # Drop-in needs only id and sessionData; the rest is for your logs.
    return jsonify({"id": session["id"], "sessionData": session["sessionData"], "reference": body["reference"]})


@app.post("/api/webhooks/notifications")
def notifications():
    """Adyen standard webhook receiver.

    Adyen expects HTTP 200 within 10 seconds; anything else and it retries with backoff.
    Each notificationItem is HMAC-checked individually. Items that fail are logged and
    dropped; the request is still acknowledged so Adyen stops retrying a tampered item.
    """
    key = os.environ.get("ADYEN_HMAC_KEY", "")
    if not key:
        log.error("ADYEN_HMAC_KEY not set; refusing to accept webhooks")
        return jsonify({"error": "HMAC key not configured"}), 500

    payload = request.get_json(silent=True) or {}
    items = payload.get("notificationItems", [])
    accepted = 0
    for wrapper in items:
        item = wrapper.get("NotificationRequestItem", {})
        if not webhook.is_valid(item, key):
            log.warning("HMAC failed for pspReference=%s; dropped", item.get("pspReference"))
            continue
        accepted += 1
        record = {
            "receivedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "eventCode": item.get("eventCode"),
            "success": item.get("success"),
            "pspReference": item.get("pspReference"),
            "merchantReference": item.get("merchantReference"),
            "amount": item.get("amount"),
            "reason": item.get("reason"),
        }
        RECEIVED.append(record)
        log.info("webhook %s", json.dumps(record))

    # "[accepted]" is the legacy body; HTTP 200 is what Adyen checks today. Send both.
    return "[accepted]", 200, {"Content-Type": "text/plain"}


@app.get("/api/webhooks/received")
def received():
    """What this server has accepted so far (in-memory; resets on restart)."""
    return jsonify(RECEIVED)


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)

import pytest

import app as flask_app
import webhook
from tests.test_hmac import DOC_ITEM, DOC_KEY


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ADYEN_HMAC_KEY", DOC_KEY)
    flask_app.RECEIVED.clear()
    flask_app.app.config["TESTING"] = True
    return flask_app.app.test_client()


def _envelope(item):
    return {"live": "false", "notificationItems": [{"NotificationRequestItem": item}]}


def test_valid_webhook_is_accepted_and_recorded(client):
    res = client.post("/api/webhooks/notifications", json=_envelope(DOC_ITEM))
    assert res.status_code == 200
    assert res.data == b"[accepted]"
    got = client.get("/api/webhooks/received").get_json()
    assert len(got) == 1 and got[0]["pspReference"] == "7914073381342284" and got[0]["eventCode"] == "AUTHORISATION"


def test_tampered_webhook_is_dropped_but_still_200(client):
    bad = {**DOC_ITEM, "amount": {"value": 999999, "currency": "EUR"}}
    res = client.post("/api/webhooks/notifications", json=_envelope(bad))
    assert res.status_code == 200
    assert client.get("/api/webhooks/received").get_json() == []


def test_missing_hmac_key_is_a_server_error(client, monkeypatch):
    monkeypatch.delenv("ADYEN_HMAC_KEY")
    res = client.post("/api/webhooks/notifications", json=_envelope(DOC_ITEM))
    assert res.status_code == 500


def test_sessions_endpoint_reports_missing_config(client, monkeypatch):
    monkeypatch.delenv("ADYEN_MERCHANT_ACCOUNT", raising=False)
    res = client.post("/api/sessions", json={"amount": 1000})
    assert res.status_code == 500 and "ADYEN_MERCHANT_ACCOUNT" in res.get_json()["error"]

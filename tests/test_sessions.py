import pytest

import adyen_client


def test_build_session_request_shape():
    body = adyen_client.build_session_request(
        amount_minor=1000, currency="EUR", country_code="NL",
        merchant_account="TestMerchant", return_url="http://localhost:8080/redirect", reference="order-1",
    )
    assert body == {
        "amount": {"value": 1000, "currency": "EUR"},
        "reference": "order-1",
        "returnUrl": "http://localhost:8080/redirect",
        "merchantAccount": "TestMerchant",
        "countryCode": "NL",
    }


def test_reference_generated_when_missing():
    body = adyen_client.build_session_request(
        amount_minor=5, currency="USD", country_code="US", merchant_account="M", return_url="http://x/r",
    )
    assert body["reference"].startswith("test-") and len(body["reference"]) > 10


def test_rejects_non_positive_amount():
    with pytest.raises(ValueError):
        adyen_client.build_session_request(
            amount_minor=0, currency="EUR", country_code="NL", merchant_account="M", return_url="http://x/r",
        )


def test_create_session_requires_api_key(monkeypatch):
    monkeypatch.delenv("ADYEN_API_KEY", raising=False)
    with pytest.raises(adyen_client.AdyenConfigError):
        adyen_client.create_session({"amount": {"value": 1, "currency": "EUR"}})

import base64
import hashlib
import hmac
import binascii

import pytest

import webhook

# The worked example from Adyen's "Verify HMAC signatures" page (standard webhooks).
DOC_KEY = "44782DEF547AAA06C910C43932B1EB0C71FC68D9D0C057550C48EC2ACF6BA056"
DOC_ITEM = {
    "pspReference": "7914073381342284",
    "originalReference": "",
    "merchantAccountCode": "TestMerchant",
    "merchantReference": "TestPayment-1407325143704",
    "amount": {"value": 1130, "currency": "EUR"},
    "eventCode": "AUTHORISATION",
    "success": "true",
    "additionalData": {"hmacSignature": "coqCmt/IZ4E3CzPvMY8zTjQVL5hYJUiBRg8UU+iCWo0="},
}


def test_signing_string_order_and_blank_original_reference():
    s = webhook.signing_string(DOC_ITEM)
    assert s == "7914073381342284::TestMerchant:TestPayment-1407325143704:1130:EUR:AUTHORISATION:true"


def test_doc_vector_matches():
    assert webhook.compute_signature(DOC_ITEM, DOC_KEY) == DOC_ITEM["additionalData"]["hmacSignature"]
    assert webhook.is_valid(DOC_ITEM, DOC_KEY)


def test_independent_implementation_agrees():
    # Recompute with the stdlib directly so the module is checked, not trusted.
    key = binascii.unhexlify(DOC_KEY)
    msg = webhook.signing_string(DOC_ITEM).encode()
    expected = base64.b64encode(hmac.new(key, msg, hashlib.sha256).digest()).decode()
    assert webhook.compute_signature(DOC_ITEM, DOC_KEY) == expected


def test_tampered_amount_fails():
    item = {**DOC_ITEM, "amount": {"value": 1131, "currency": "EUR"}}
    assert not webhook.is_valid(item, DOC_KEY)


def test_missing_signature_fails():
    item = {**DOC_ITEM, "additionalData": {}}
    assert not webhook.is_valid(item, DOC_KEY)


def test_colons_in_values_are_escaped():
    item = {**DOC_ITEM, "merchantReference": "order:42"}
    assert "order\\:42" in webhook.signing_string(item)


def test_bad_key_raises():
    with pytest.raises(ValueError):
        webhook.compute_signature(DOC_ITEM, "not-hex")

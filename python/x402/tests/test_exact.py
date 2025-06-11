import pytest
import time
from web3 import Web3
from x402.exact import (
    create_nonce,
    prepare_payment_header,
    sign_payment_header,
    encode_payment,
    decode_payment,
)
from x402.types import PaymentRequirements, UnsupportedSchemeException


@pytest.fixture
def web3():
    w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
    account = w3.eth.account.create()
    w3.eth.default_account = account
    return w3, account


@pytest.fixture
def payment_requirements():
    return PaymentRequirements(
        scheme="exact",
        network="base-sepolia",
        asset="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        pay_to="0x0000000000000000000000000000000000000000",
        max_amount_required="10000",
        resource="https://example.com",
        description="test",
        max_timeout_seconds=1000,
        mime_type="text/plain",
        output_schema=None,
    )


def test_create_nonce():
    nonce1 = create_nonce()
    nonce2 = create_nonce()

    # Test nonce length
    assert len(nonce1) == 32

    # Test nonces are random
    assert nonce1 != nonce2


def test_prepare_payment_header(web3, payment_requirements):
    w3, account = web3
    x402_version = 1
    header = prepare_payment_header(account.address, x402_version, payment_requirements)

    assert header["sender"] == account.address
    assert header["x402_version"] == x402_version
    assert header["payment_requirements"] == payment_requirements.model_dump()


def test_sign_payment_header(web3, payment_requirements):
    w3, account = web3
    unsigned_header = prepare_payment_header(account.address, 1, payment_requirements)

    signed_message = sign_payment_header(w3, payment_requirements, unsigned_header)

    # Test signature properties
    assert "payload" in signed_message
    assert "signature" in signed_message["payload"]
    assert isinstance(signed_message["payload"]["signature"], str)
    assert len(signed_message["payload"]["signature"]) > 0


def test_sign_payment_header_unsupported_scheme(web3, payment_requirements):
    w3, account = web3
    payment_requirements.scheme = "unsupported"
    unsigned_header = prepare_payment_header(account.address, 1, payment_requirements)

    with pytest.raises(UnsupportedSchemeException):
        sign_payment_header(w3, payment_requirements, unsigned_header)


def test_encode_decode_payment(web3, payment_requirements):
    w3, account = web3
    # Create and sign a payment header
    unsigned_header = prepare_payment_header(account.address, 1, payment_requirements)
    signed_message = sign_payment_header(w3, payment_requirements, unsigned_header)

    # Test encoding
    encoded = encode_payment(signed_message)
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    # Test decoding
    decoded = decode_payment(encoded)
    assert isinstance(decoded, dict)
    assert "payload" in decoded
    assert "signature" in decoded["payload"]
    assert "authorization" in decoded["payload"]
    assert "from" in decoded["payload"]["authorization"]
    assert "to" in decoded["payload"]["authorization"]
    assert "value" in decoded["payload"]["authorization"]
    assert "validAfter" in decoded["payload"]["authorization"]
    assert "validBefore" in decoded["payload"]["authorization"]
    assert "nonce" in decoded["payload"]["authorization"]

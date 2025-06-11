import pytest
from web3 import Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder
from x402.clients.base import (
    x402Client,
    PaymentAmountExceededError,
    UnsupportedSchemeException,
)
from x402.types import PaymentRequirements, x402PaymentRequiredResponse


@pytest.fixture
def web3():
    w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
    account = w3.eth.account.create()
    w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(account), layer=0)
    w3.eth.default_account = account
    return w3, account


@pytest.fixture
def client(web3):
    w3, _ = web3
    return x402Client(w3)


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


def test_select_payment_requirements(client, payment_requirements):
    # Test selecting from single requirement
    selected = client.select_payment_requirements([payment_requirements])
    assert selected == payment_requirements

    # Test selecting with network filter
    selected = client.select_payment_requirements(
        [payment_requirements], network="base-sepolia"
    )
    assert selected == payment_requirements

    # Test selecting with scheme filter
    selected = client.select_payment_requirements(
        [payment_requirements], scheme="exact"
    )
    assert selected == payment_requirements

    # Test no matching requirements
    with pytest.raises(ValueError):
        client.select_payment_requirements([payment_requirements], network="ethereum")


def test_select_payment_requirements_amount_exceeded(client, payment_requirements):
    # Set max_value lower than required amount
    client.max_value = 1000

    with pytest.raises(PaymentAmountExceededError):
        client.select_payment_requirements([payment_requirements])


def test_create_payment_header(client, payment_requirements):
    header = client.create_payment_header(1, payment_requirements)

    # Test header is a non-empty string
    assert isinstance(header, str)
    assert len(header) > 0


def test_create_payment_header_unsupported_scheme(client, payment_requirements):
    payment_requirements.scheme = "unsupported"

    with pytest.raises(UnsupportedSchemeException):
        client.create_payment_header(1, payment_requirements)


def test_payment_requirements_sorting(client):
    base_req = PaymentRequirements(
        scheme="exact",
        network="base",
        asset="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        pay_to="0x0000000000000000000000000000000000000000",
        max_amount_required="10000",
        resource="https://example.com",
        description="test",
        max_timeout_seconds=1000,
        mime_type="text/plain",
        output_schema=None,
    )

    other_req = PaymentRequirements(
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

    # Test base network is preferred
    selected = client.select_payment_requirements([other_req, base_req])
    assert selected.network == "base"


# def test_signed_exact_evm_payment_payload(web3):
#     client = x402Client(web3)
#     signed_message = client._signed_exact_evm_payment_payload(
#         PaymentRequirements(
#             scheme="exact",
#             network="base-sepolia",
#             asset="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
#             pay_to="0x0000000000000000000000000000000000000000",
#             max_amount_required="10000",
#             resource="https://example.com",
#             description="test",
#             max_timeout_seconds=1000,
#             mime_type="text/plain",
#             output_schema=None,
#         )
#     )

#     recovered_address = web3.geth.personal.ecRecover(signed_message)
#     assert recovered_address == web3.eth.account.address

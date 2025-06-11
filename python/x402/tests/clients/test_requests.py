import pytest
import json
import base64
from unittest.mock import MagicMock, patch
from requests import Response
from web3 import Web3
from x402.clients.requests import RequestsSession, with_payment_interceptor
from x402.clients.base import (
    PaymentError,
    MissingRequestConfigError,
)
from x402.types import PaymentRequirements, x402PaymentRequiredResponse


@pytest.fixture
def web3():
    w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
    account = w3.eth.account.create()
    w3.eth.default_account = account
    return w3, account


@pytest.fixture
def session(web3):
    w3, _ = web3
    return with_payment_interceptor(w3)


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
        extra={
            "name": "USD Coin",
            "version": "2",
        },
    )


def test_request_success(session):
    # Test successful request (200)
    mock_response = Response()
    mock_response.status_code = 200
    mock_response._content = b"success"

    with patch.object(session, "send", return_value=mock_response) as mock_send:
        response = session.request("GET", "https://example.com")
        assert response.status_code == 200
        assert response.content == b"success"
        mock_send.assert_called_once()


def test_request_non_402(session):
    # Test non-402 response
    mock_response = Response()
    mock_response.status_code = 404
    mock_response._content = b"not found"

    with patch.object(session, "send", return_value=mock_response) as mock_send:
        response = session.request("GET", "https://example.com")
        assert response.status_code == 404
        assert response.content == b"not found"
        mock_send.assert_called_once()


def test_request_retry(session):
    # Test retry request
    session._is_retry = True
    mock_response = Response()
    mock_response.status_code = 402
    mock_response._content = b"payment required"

    with patch.object(session, "send", return_value=mock_response) as mock_send:
        response = session.request("GET", "https://example.com")
        assert response.status_code == 402
        assert response.content == b"payment required"
        mock_send.assert_called_once()


def test_request_missing_config(session):
    # Test missing request configuration
    mock_response = Response()
    mock_response.status_code = 402
    mock_response._content = b"payment required"

    with patch.object(session, "send", return_value=mock_response) as mock_send:
        with pytest.raises(
            MissingRequestConfigError, match="Missing request configuration"
        ):
            session.request("GET", "https://example.com")


def test_request_payment_flow(session, payment_requirements):
    # Mock the payment required response
    payment_response = x402PaymentRequiredResponse(
        x402_version=1,
        accepts=[payment_requirements],
        error="Payment Required",
    )

    # Create initial 402 response
    initial_response = Response()
    initial_response.status_code = 402
    initial_response._content = json.dumps(payment_response.model_dump()).encode()

    # Mock the retry response with payment response header
    payment_result = {
        "success": True,
        "transaction": "0x1234",
        "network": "base-sepolia",
        "payer": "0x5678",
    }
    retry_response = Response()
    retry_response.status_code = 200
    retry_response.headers = {
        "X-Payment-Response": base64.b64encode(
            json.dumps(payment_result).encode()
        ).decode()
    }

    # Mock both required methods
    session.client.select_payment_requirements = MagicMock(
        return_value=payment_requirements
    )
    mock_header = "mock_payment_header"
    session.client.create_payment_header = MagicMock(return_value=mock_header)

    # Mock the send method to return different responses
    def mock_send(request, **kwargs):
        if session._is_retry:
            return retry_response
        return initial_response

    with patch.object(session, "send", side_effect=mock_send) as mock_send:
        response = session.request("GET", "https://example.com", headers={})

        # Verify the result
        assert response.status_code == 200
        assert "X-Payment-Response" in response.headers

        # Verify the mocked methods were called with correct arguments
        session.client.select_payment_requirements.assert_called_once_with(
            [payment_requirements]
        )
        session.client.create_payment_header.assert_called_once_with(
            1, payment_requirements
        )

        # Verify the retry request was made with correct headers
        assert mock_send.call_count == 2
        retry_request = mock_send.call_args[0][0]
        assert retry_request.headers["X-Payment"] == mock_header
        assert (
            retry_request.headers["Access-Control-Expose-Headers"]
            == "X-Payment-Response"
        )


def test_request_payment_error(session, payment_requirements):
    # Mock the payment required response with unsupported scheme
    payment_requirements.scheme = "unsupported"
    payment_response = x402PaymentRequiredResponse(
        x402_version=1,
        accepts=[payment_requirements],
        error="Payment Required",
    )

    # Create initial 402 response
    initial_response = Response()
    initial_response.status_code = 402
    initial_response._content = json.dumps(payment_response.model_dump()).encode()

    with patch.object(session, "send", return_value=initial_response) as mock_send:
        with pytest.raises(PaymentError):
            session.request("GET", "https://example.com", headers={})

        # Verify retry flag is reset
        assert not session._is_retry


def test_request_general_error(session):
    # Create initial 402 response with invalid JSON
    initial_response = Response()
    initial_response.status_code = 402
    initial_response._content = b"invalid json"

    with patch.object(session, "send", return_value=initial_response) as mock_send:
        with pytest.raises(PaymentError):
            session.request("GET", "https://example.com", headers={})

        # Verify retry flag is reset
        assert not session._is_retry


def test_with_payment_interceptor(web3):
    w3, _ = web3

    # Test basic interceptor creation
    session = with_payment_interceptor(w3)
    assert isinstance(session, RequestsSession)
    assert session.client.web3 == w3
    assert session.client.max_value is None

    # Test interceptor with max_value
    session = with_payment_interceptor(w3, max_value=1000)
    assert session.client.max_value == 1000

    # Test interceptor with custom selector
    def custom_selector(accepts, network_filter=None, scheme_filter=None):
        return accepts[0]

    session = with_payment_interceptor(
        w3, payment_requirements_selector=custom_selector
    )
    assert (
        session.client.select_payment_requirements
        != session.client.__class__.select_payment_requirements
    )

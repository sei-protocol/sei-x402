import time
from typing import Optional, Callable, Dict, Any
from eth_account import Account
from x402.exact import sign_payment_header
from x402.types import (
    PaymentRequirements,
    UnsupportedSchemeException,
)
import secrets
from x402.encoding import safe_base64_decode
import json


def decode_x_payment_response(header: str) -> Dict[str, Any]:
    """Decode the X-PAYMENT-RESPONSE header.

    Args:
        header: The X-PAYMENT-RESPONSE header to decode

    Returns:
        The decoded payment response containing:
        - success: bool
        - transaction: str (hex)
        - network: str
        - payer: str (address)
    """
    decoded = safe_base64_decode(header)
    result = json.loads(decoded)
    return result


class PaymentError(Exception):
    """Base class for payment-related errors."""

    pass


class PaymentAmountExceededError(PaymentError):
    """Raised when payment amount exceeds maximum allowed value."""

    pass


class MissingRequestConfigError(PaymentError):
    """Raised when request configuration is missing."""

    pass


class PaymentAlreadyAttemptedError(PaymentError):
    """Raised when payment has already been attempted."""

    pass


class x402Client:
    """Base client for handling x402 payments."""

    def __init__(
        self,
        account: Account,
        max_value: Optional[int] = None,
        payment_requirements_selector: Optional[Callable] = None,
    ):
        """Initialize the x402 client.

        Args:
            account: eth_account.Account instance for signing payments
            max_value: Optional maximum allowed payment amount in base units
            payment_requirements_selector: Optional custom selector for payment requirements
        """
        self.account = account
        self.max_value = max_value
        if payment_requirements_selector:
            self.select_payment_requirements = payment_requirements_selector

    def select_payment_requirements(
        self,
        accepts: list,
        network_filter: Optional[str] = None,
        scheme_filter: Optional[str] = None,
    ) -> PaymentRequirements:
        """Select payment requirements from the list of accepted requirements.

        Args:
            accepts: List of accepted payment requirements
            network_filter: Optional network to filter by
            scheme_filter: Optional scheme to filter by

        Returns:
            Selected payment requirements

        Raises:
            UnsupportedSchemeException: If no supported scheme is found
            PaymentAmountExceededError: If payment amount exceeds max_value
        """
        for req in accepts:
            # If it's a dict, use key access; if it's a model, use attribute
            scheme = req["scheme"] if isinstance(req, dict) else req.scheme
            network = req["network"] if isinstance(req, dict) else req.network

            # Check scheme filter
            if scheme_filter and scheme != scheme_filter:
                continue

            # Check network filter
            if network_filter and network != network_filter:
                continue

            if scheme == "exact":
                # If it's already a PaymentRequirements, return it; else, construct it
                result = (
                    req
                    if isinstance(req, PaymentRequirements)
                    else PaymentRequirements(**req)
                )

                # Check max value if set
                if self.max_value is not None:
                    max_amount = int(result.max_amount_required)
                    if max_amount > self.max_value:
                        raise PaymentAmountExceededError(
                            f"Payment amount {max_amount} exceeds maximum allowed value {self.max_value}"
                        )

                return result

        raise UnsupportedSchemeException("No supported payment scheme found")

    def create_payment_header(
        self, x402_version: int, payment_requirements: PaymentRequirements
    ) -> str:
        """Create a payment header for the given requirements.

        Args:
            x402_version: x402 protocol version
            payment_requirements: Selected payment requirements

        Returns:
            Signed payment header
        """

        unsigned_header = {
            "x402Version": x402_version,
            "scheme": payment_requirements.scheme,
            "network": payment_requirements.network,
            "payload": {
                "signature": None,
                "authorization": {
                    "from": self.account.address,
                    "to": payment_requirements.pay_to,
                    "value": payment_requirements.max_amount_required,
                    "validAfter": str(int(time.time()) - 60),  # 60 seconds before
                    "validBefore": str(
                        int(time.time()) + payment_requirements.max_timeout_seconds
                    ),
                    "nonce": self.generate_nonce(),
                },
            },
        }

        signed_header = sign_payment_header(
            self.account,
            payment_requirements,
            unsigned_header,
        )
        return signed_header

    def generate_nonce(self):
        # Generate a random nonce (32 bytes = 64 hex chars)
        nonce = secrets.token_hex(32)
        return nonce

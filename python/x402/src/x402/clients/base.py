import time
import logging
from typing import Optional, List, Callable, Dict, Any
from web3 import Web3
from x402.chains import get_chain_id, get_token_name, get_token_version
from x402.exact import prepare_payment_header, sign_payment_header, encode_payment
from x402.types import (
    PaymentRequirements,
    UnsupportedSchemeException,
    x402PaymentRequiredResponse,
    ExactPaymentPayload,
    EIP3009Authorization,
)
import secrets
from x402.encoding import safe_base64_decode
import json

logger = logging.getLogger(__name__)


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
    logger.debug(f"Decoding payment response header: {header}")
    decoded = safe_base64_decode(header)
    result = json.loads(decoded)
    logger.debug(f"Decoded payment response: {result}")
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
        web3: Web3,
        max_value: Optional[int] = None,
        payment_requirements_selector: Optional[Callable] = None,
    ):
        """Initialize the x402 client.

        Args:
            web3: Web3 instance for signing payments
            max_value: Optional maximum allowed payment amount in base units
            payment_requirements_selector: Optional custom selector for payment requirements
        """
        self.web3 = web3
        self.max_value = max_value
        if payment_requirements_selector:
            self.select_payment_requirements = payment_requirements_selector
        logger.info(f"Initialized x402Client with max_value={max_value}")

    def select_payment_requirements(self, accepts: list) -> PaymentRequirements:
        """Select payment requirements from the list of accepted requirements.

        Args:
            accepts: List of accepted payment requirements

        Returns:
            Selected payment requirements

        Raises:
            UnsupportedSchemeException: If no supported scheme is found
        """
        logger.debug(f"Selecting payment requirements from: {accepts}")
        for req in accepts:
            # If it's a dict, use key access; if it's a model, use attribute
            scheme = req["scheme"] if isinstance(req, dict) else req.scheme
            logger.debug(f"Checking scheme: {scheme}")
            if scheme == "exact":
                # If it's already a PaymentRequirements, return it; else, construct it
                result = (
                    req
                    if isinstance(req, PaymentRequirements)
                    else PaymentRequirements(**req)
                )
                logger.info(f"Selected payment requirements: {result}")
                return result
        logger.error("No supported payment scheme found")
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
        logger.debug(
            f"Creating payment header for version {x402_version} with requirements: {payment_requirements}"
        )

        # Prepare unsigned header matching TypeScript structure
        unsigned_header = {
            "x402Version": x402_version,
            "scheme": payment_requirements.scheme,
            "network": payment_requirements.network,
            "payload": {
                "signature": None,
                "authorization": {
                    "from": self.web3.eth.default_account.address,
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
        logger.debug(f"Prepared unsigned header: {unsigned_header}")

        # Sign the header
        signed_header = sign_payment_header(
            self.web3,
            payment_requirements,
            unsigned_header,
        )
        logger.info("Successfully created signed payment header")
        return signed_header

    def generate_nonce(self):
        # Generate a random nonce (32 bytes = 64 hex chars)
        nonce = secrets.token_hex(32)
        logger.debug(f"Generated nonce: {nonce}")
        return nonce

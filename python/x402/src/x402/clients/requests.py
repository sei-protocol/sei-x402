from typing import Optional, Callable
import requests
from web3 import Web3
from x402.clients.base import (
    x402Client,
    MissingRequestConfigError,
    PaymentAlreadyAttemptedError,
    PaymentError,
)
from x402.types import x402PaymentRequiredResponse


class RequestsSession(requests.Session):
    def __init__(self, client: x402Client):
        super().__init__()
        self.client = client
        self._is_retry = False

    def request(self, method, url, **kwargs):
        """Override request to handle 402 responses."""
        if self._is_retry:
            return super().request(method, url, **kwargs)

        response = super().request(method, url, **kwargs)

        if response.status_code != 402:
            return response

        try:
            if not kwargs:
                raise MissingRequestConfigError("Missing request configuration")

            # Parse the 402 response
            data = response.json()
            payment_response = x402PaymentRequiredResponse(**data)

            # Select payment requirements
            selected_requirements = self.client.select_payment_requirements(
                payment_response.accepts
            )

            # Create payment header
            payment_header = self.client.create_payment_header(
                payment_response.x402_version, selected_requirements
            )

            # Mark as retry and add payment header
            self._is_retry = True
            headers = kwargs.get("headers", {})
            headers["X-PAYMENT"] = payment_header
            headers["Access-Control-Expose-Headers"] = "X-PAYMENT-RESPONSE"
            kwargs["headers"] = headers

            # Retry the request
            retry_response = super().request(method, url, **kwargs)

            # Store the payment response header for access
            if "X-PAYMENT-RESPONSE" in retry_response.headers:
                retry_response._payment_response = retry_response.headers[
                    "X-PAYMENT-RESPONSE"
                ]

            return retry_response

        except PaymentError as e:
            # Reset retry flag and re-raise payment errors
            self._is_retry = False
            raise e
        except Exception as e:
            # Reset retry flag and wrap other errors
            self._is_retry = False
            raise PaymentError(f"Failed to handle payment: {str(e)}") from e


def with_payment_interceptor(
    web3: Web3,
    max_value: Optional[int] = None,
    payment_requirements_selector: Optional[Callable] = None,
) -> RequestsSession:
    """Create a requests session that handles 402 Payment Required responses.

    Args:
        web3: Web3 instance for signing payments
        max_value: Optional maximum allowed payment amount in base units
        payment_requirements_selector: Optional custom selector for payment requirements

    Returns:
        RequestsSession instance that can be used for making requests
    """
    client = x402Client(web3, max_value=max_value)
    if payment_requirements_selector:
        client.select_payment_requirements = payment_requirements_selector
    return RequestsSession(client)

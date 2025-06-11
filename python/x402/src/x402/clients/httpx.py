from typing import Optional, Callable, Any
import logging
import json
from httpx import Request, Response, AsyncClient
from web3 import Web3
from x402.clients.base import (
    x402Client,
    MissingRequestConfigError,
    PaymentAlreadyAttemptedError,
    PaymentError,
    decode_x_payment_response,
)
from x402.types import x402PaymentRequiredResponse
from x402.encoding import safe_base64_encode


class HttpxHooks:
    def __init__(self, client: x402Client):
        self.client = client
        self._is_retry = False

    async def on_request(self, request: Request):
        """Handle request before it is sent."""
        pass

    async def on_response(self, response: Response) -> Response:
        """Handle response after it is received."""

        # If this is a successful response with a payment response header, store it and return
        if response.status_code == 200:
            return response

        # If this is not a 402, just return the response
        if response.status_code != 402:
            return response

        # If this is a retry response, just return it
        if self._is_retry:
            return response

        try:
            if not response.request:
                raise MissingRequestConfigError("Missing request configuration")

            # Read the response content before parsing
            content = await response.aread()

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
            request = response.request

            # Use the payment header directly - it's already base64 encoded from exact.py
            request.headers["X-Payment"] = payment_header
            request.headers["Access-Control-Expose-Headers"] = "X-Payment-Response"

            # Retry the request
            async with AsyncClient() as client:
                retry_response = await client.send(request)

                # Store the payment response header for access
                if "X-Payment-Response" in retry_response.headers:
                    payment_response = retry_response.headers["X-Payment-Response"]
                    retry_response._payment_response = decode_x_payment_response(
                        payment_response
                    )

                # Copy the retry response data to the original response
                response.status_code = retry_response.status_code
                response.headers = retry_response.headers
                response._content = retry_response._content
                response._payment_response = retry_response._payment_response
                return response

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
) -> HttpxHooks:
    """Create httpx hooks that handle 402 Payment Required responses.

    Args:
        web3: Web3 instance for signing payments
        max_value: Optional maximum allowed payment amount in base units
        payment_requirements_selector: Optional custom selector for payment requirements

    Returns:
        HttpxHooks instance that can be used with httpx clients
    """
    client = x402Client(web3, max_value=max_value)
    if payment_requirements_selector:
        client.select_payment_requirements = payment_requirements_selector
    return HttpxHooks(client)

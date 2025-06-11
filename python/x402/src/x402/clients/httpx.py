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

logger = logging.getLogger(__name__)


class HttpxHooks:
    def __init__(self, client: x402Client):
        self.client = client
        self._is_retry = False
        logger.debug("Initialized HttpxHooks")

    async def on_request(self, request: Request):
        """Handle request before it is sent."""
        logger.debug(f"Processing request to {request.url}")
        pass

    async def on_response(self, response: Response) -> Response:
        """Handle response after it is received."""
        logger.debug(f"Processing response with status code: {response.status_code}")

        # If this is a successful response with a payment response header, store it and return
        if response.status_code == 200 and "X-Payment-Response" in response.headers:
            payment_response = response.headers["X-Payment-Response"]
            response._payment_response = decode_x_payment_response(payment_response)
            logger.info(f"Decoded payment response: {response._payment_response}")
            return response

        # If this is not a 402, just return the response
        if response.status_code != 402:
            logger.debug("Skipping payment handling - not a 402")
            return response

        # If this is a retry response, just return it
        if self._is_retry:
            logger.debug("Skipping payment handling - this is a retry response")
            return response

        try:
            if not response.request:
                logger.error("Missing request configuration")
                raise MissingRequestConfigError("Missing request configuration")

            # Read the response content before parsing
            content = await response.aread()
            logger.debug(f"Response content: {content.decode()}")

            data = response.json()
            logger.debug(f"Parsed JSON data: {data}")

            payment_response = x402PaymentRequiredResponse(**data)
            logger.info(f"Parsed payment response: {payment_response}")

            # Select payment requirements
            selected_requirements = self.client.select_payment_requirements(
                payment_response.accepts
            )
            logger.info(f"Selected payment requirements: {selected_requirements}")

            # Create payment header
            payment_header = self.client.create_payment_header(
                payment_response.x402_version, selected_requirements
            )
            logger.debug(f"Created payment header: {payment_header}")

            # Mark as retry and add payment header
            self._is_retry = True
            request = response.request

            # Use the payment header directly - it's already base64 encoded from exact.py
            request.headers["X-Payment"] = payment_header
            request.headers["Access-Control-Expose-Headers"] = "X-Payment-Response"
            logger.info("Added payment headers and preparing to retry request")
            logger.debug(f"Request headers: {dict(request.headers)}")

            # Retry the request
            async with AsyncClient() as client:
                logger.info("Sending retry request with payment header")
                retry_response = await client.send(request)
                logger.info(
                    f"Received retry response with status: {retry_response.status_code}"
                )
                logger.debug(f"Retry response headers: {dict(retry_response.headers)}")

                # Store the payment response header for access
                if "X-Payment-Response" in retry_response.headers:
                    payment_response = retry_response.headers["X-Payment-Response"]
                    retry_response._payment_response = decode_x_payment_response(
                        payment_response
                    )
                    logger.info(
                        f"Decoded payment response: {retry_response._payment_response}"
                    )
                else:
                    logger.warning("No payment response header in retry response")
                    logger.debug(
                        f"Retry response content: {await retry_response.aread()}"
                    )

                return retry_response

        except PaymentError as e:
            # Reset retry flag and re-raise payment errors
            self._is_retry = False
            logger.error(f"Payment error occurred: {str(e)}", exc_info=True)
            raise e
        except Exception as e:
            # Reset retry flag and wrap other errors
            self._is_retry = False
            logger.error(
                f"Unexpected error during payment handling: {str(e)}", exc_info=True
            )
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

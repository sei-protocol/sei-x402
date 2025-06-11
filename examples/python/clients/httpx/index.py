import os
import asyncio
import logging
from dotenv import load_dotenv
from web3 import Web3
from x402.clients.httpx import with_payment_interceptor
from x402.clients.base import decode_x_payment_response
import httpx

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
private_key = os.getenv("PRIVATE_KEY")
base_url = os.getenv("RESOURCE_SERVER_URL")
endpoint_path = os.getenv("ENDPOINT_PATH")

if not all([private_key, base_url, endpoint_path]):
    logger.error("Missing required environment variables")
    exit(1)

# Create Web3 account from private key
web3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
account = web3.eth.account.from_key(private_key)
web3.eth.default_account = account
logger.info(f"Initialized Web3 with account: {account.address}")


async def main():
    # Create httpx client
    async with httpx.AsyncClient(base_url=base_url) as client:
        # Add payment interceptor hooks
        hooks = with_payment_interceptor(web3)
        client.event_hooks = {
            "request": [hooks.on_request],
            "response": [hooks.on_response],
        }
        logger.info(f"Initialized httpx client with payment interceptor")

        # Make request
        try:
            logger.info(f"Making request to {endpoint_path}")
            response = await client.get(endpoint_path)

            # Read the response content
            content = await response.aread()
            logger.info(f"Received response with status code: {response.status_code}")
            logger.debug(f"Response content: {content.decode()}")

            # Check for payment response
            if hasattr(response, "_payment_response"):
                logger.info(
                    f"Payment successful! Transaction: {response._payment_response['transaction']}"
                )
                logger.info(f"Network: {response._payment_response['network']}")
                logger.info(f"Payer: {response._payment_response['payer']}")
            else:
                logger.warning("No payment response found")

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

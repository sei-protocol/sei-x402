import os
from dotenv import load_dotenv
from web3 import Web3
from x402.clients.requests import with_payment_interceptor
from x402.clients.base import decode_x_payment_response
import requests

# Load environment variables
load_dotenv()

# Get environment variables
private_key = os.getenv("PRIVATE_KEY")
base_url = os.getenv("RESOURCE_SERVER_URL")
endpoint_path = os.getenv("ENDPOINT_PATH")

if not all([private_key, base_url, endpoint_path]):
    print("Error: Missing required environment variables")
    exit(1)

# Create Web3 account from private key
web3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
account = web3.eth.account.from_key(private_key)
web3.eth.default_account = account
print(f"Initialized Web3 with account: {account.address}")


def main():
    # Create requests session with payment interceptor
    session = with_payment_interceptor(web3)

    # Make request
    try:
        print(f"Making request to {endpoint_path}")
        response = session.get(f"{base_url}{endpoint_path}")

        # Read the response content
        content = response.content
        print(f"Response: {content.decode()}")

        # Check for payment response header
        if "X-Payment-Response" in response.headers:
            payment_response = decode_x_payment_response(
                response.headers["X-Payment-Response"]
            )
            print(
                f"Payment response transaction hash: {payment_response['transaction']}"
            )
        else:
            print("Warning: No payment response header found")

    except Exception as e:
        print(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    main()

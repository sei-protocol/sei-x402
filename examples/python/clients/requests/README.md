# x402 Requests Client Example

This example demonstrates how to use the x402 package with requests to make requests to 402-protected endpoints.

## Setup and Usage

1. Install dependencies and run the example:
```bash
uv sync
uv run python index.py
```

## How it Works

The example:
1. Initializes a Web3 instance with a Base Sepolia provider
2. Creates a new account for testing
3. Initializes the x402 client with requests
4. Makes a request to a protected endpoint
5. Handles the 402 Payment Required response automatically
6. Prints the final response

## Notes

- This example uses Base Sepolia testnet. For production, use the appropriate network.
- The example creates a new account for testing. In production, you should use a proper wallet.
- Make sure your API endpoint is properly configured to handle 402 responses. 
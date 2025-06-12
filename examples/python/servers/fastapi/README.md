# x402-fastapi Example Server

This is an example FastAPI server that demonstrates how to use the `x402-fastapi` middleware to implement paywall functionality in your API endpoints.

## Prerequisites

- Python 3.10+ (install via [pyenv](https://github.com/pyenv/pyenv))
- A valid Ethereum address for receiving payments

## Setup

1. Copy `.env-local` to `.env` and add your Ethereum address to receive payments:

```bash
cp .env-local .env
```

2. Install dependencies:
```bash
pip install -e .
```

3. Run the server:
```bash
python main.py
```

The server will start on http://localhost:4021

## Testing the Server

You can test the server using one of the example clients:

### Using the Python Requests Client
```bash
cd ../clients/requests
# Ensure .env is setup
pip install -e .
python main.py
```

These clients will demonstrate how to:
1. Make an initial request to get payment requirements
2. Process the payment requirements
3. Make a second request with the payment token

## Example Endpoints

The server includes two example endpoints:

1. `/weather` - Requires a payment of $0.001 to access
2. `/premium/content` - Requires a payment of 100000 units of the specified asset

## Response Format

### Payment Required (402)
```json
{
  "error": "No X-PAYMENT header provided",
  "paymentRequirements": {
    "scheme": "exact",
    "network": "base-sepolia",
    "maxAmountRequired": "1000",
    "resource": "http://localhost:4021/weather",
    "description": "",
    "mimeType": "",
    "payTo": "0xYourAddress",
    "maxTimeoutSeconds": 60,
    "asset": "0x...",
    "outputSchema": null,
    "extra": null
  }
}
```

### Successful Response
```json
{
  "report": {
    "weather": "sunny",
    "temperature": 70
  }
}
```

## Extending the Example

To add more paid endpoints, follow this pattern:

```python
# First, configure the payment middleware with your routes
app.middleware("http")(
    require_payment(
        amount="$0.10",
        pay_to_address=ADDRESS,
        path="/your-endpoint",
        network_id=NETWORK,
        facilitator_url=FACILITATOR_URL,
    )
)

# Then define your routes as normal
@app.get("/your-endpoint")
async def your_endpoint():
    return {
        # Your response data
    }
```

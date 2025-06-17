import os
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from x402.fastapi.middleware import require_payment

# Load environment variables
load_dotenv()

# Get configuration from environment
NETWORK = os.getenv("NETWORK", "base-sepolia")
ADDRESS = os.getenv("ADDRESS")

if not ADDRESS:
    raise ValueError("Missing required environment variables")

app = FastAPI()

# Apply payment middleware to specific routes
app.middleware("http")(
    require_payment(
        amount="$0.001",
        pay_to_address=ADDRESS,
        path="/weather",
        network_id=NETWORK,
    )
)

# Apply payment middleware to premium routes
app.middleware("http")(
    require_payment(
        amount="$0.01",
        pay_to_address=ADDRESS,
        path="/premium/*",
        network_id=NETWORK,
    )
)


@app.get("/weather")
async def get_weather() -> Dict[str, Any]:
    return {
        "report": {
            "weather": "sunny",
            "temperature": 70,
        }
    }


@app.get("/premium/content")
async def get_premium_content() -> Dict[str, Any]:
    return {
        "content": "This is premium content",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4021)

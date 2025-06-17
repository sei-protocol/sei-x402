from typing import Callable, Optional, Dict
import httpx
from pydantic import BaseModel, ConfigDict
from x402.types import (
    PaymentPayload,
    PaymentRequirements,
    VerifyResponse,
    SettleResponse,
)


class FacilitatorConfig(BaseModel):
    url: str
    create_headers: Optional[Callable[[], Dict[str, Dict[str, str]]]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(
        self,
        url: str,
        create_headers: Optional[Callable[[], Dict[str, Dict[str, str]]]] = None,
    ):
        if url.startswith("http://") or url.startswith("https://"):
            if url.endswith("/"):
                url = url[:-1]
        else:
            raise ValueError(f"Invalid URL {url}, must start with http:// or https://")
        super().__init__(url=url, create_headers=create_headers)


class FacilitatorClient:
    def __init__(self, config: Optional[FacilitatorConfig] = None):
        if config is None:
            config = FacilitatorConfig(url="https://x402.org/facilitator")
        self.config = config

    async def verify(
        self, payment: PaymentPayload, payment_requirements: PaymentRequirements
    ) -> VerifyResponse:
        """Verify a payment header is valid and a request should be processed"""
        headers = {"Content-Type": "application/json"}

        if self.config.create_headers:
            custom_headers = await self.config.create_headers()
            headers.update(custom_headers.get("verify", {}))

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.url}/verify",
                json={
                    "paymentPayload": payment.model_dump(),
                    "paymentRequirements": payment_requirements.model_dump(),
                },
                headers=headers,
                follow_redirects=True,
            )

            data = response.json()
            return VerifyResponse(**data)

    async def settle(
        self, payment: PaymentPayload, payment_requirements: PaymentRequirements
    ) -> SettleResponse:
        headers = {"Content-Type": "application/json"}

        if self.config.create_headers:
            custom_headers = await self.config.create_headers()
            headers.update(custom_headers.get("settle", {}))

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.url}/settle",
                json={
                    "paymentPayload": payment.model_dump(),
                    "paymentRequirements": payment_requirements.model_dump(),
                },
                headers=headers,
                follow_redirects=True,
            )
            data = response.json()
            return SettleResponse(**data)

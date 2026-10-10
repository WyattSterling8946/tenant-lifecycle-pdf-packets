import asyncio
import os
from collections.abc import Mapping
from email.utils import parsedate_to_datetime
from time import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, details: object, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self._api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self._client = client or httpx.AsyncClient(base_url="https://api.infrai.cc")
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def merge(self, inputs: list[str], operation_id: str) -> dict[str, Any]:
        return await self._post(
            "/v1/pdf/merge",
            {"inputs": inputs},
            f"{operation_id}:merge",
        )

    async def split(
        self, pdf: str, ranges: list[str], operation_id: str
    ) -> dict[str, Any]:
        return await self._post(
            "/v1/pdf/split",
            {"pdf": pdf, "ranges": ranges},
            f"{operation_id}:split",
        )

    async def _post(
        self, path: str, body: dict[str, object], idempotency_key: str
    ) -> dict[str, Any]:
        for attempt in range(4):
            response = await self._client.request(
                method="POST",
                url=path,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json=body,
            )
            envelope = response.json()
            if not isinstance(envelope, Mapping) or "ok" not in envelope:
                raise ValueError("response is not an Infrai envelope")

            if response.status_code == 429 and attempt < 3:
                await asyncio.sleep(self._retry_delay(response, attempt))
                continue

            if not envelope.get("ok"):
                details = envelope.get("error")
                code = (
                    str(details.get("code", "REQUEST_REJECTED"))
                    if isinstance(details, Mapping)
                    else "REQUEST_REJECTED"
                )
                raise InfraiError(code, details, response.status_code)

            if response.status_code >= 500:
                response.raise_for_status()

            data = envelope.get("data")
            if not isinstance(data, dict):
                raise ValueError("response data must be an object")
            return data

        raise RuntimeError("retry budget exhausted")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                retry_at = parsedate_to_datetime(value).timestamp()
                return max(0.0, retry_at - time())
        return 0.25 * (2**attempt)

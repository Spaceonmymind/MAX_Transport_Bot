import logging

import httpx

logger = logging.getLogger(__name__)


class MaxApiError(RuntimeError):
    pass


class MaxApi:
    def __init__(self, token: str, base_url: str, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=10.0)
        self._owns_client = client is None
        self._headers = {"Authorization": token}

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def send_message(self, recipient: dict[str, int], text: str, attachments: list[dict]) -> None:
        await self._request("POST", "/messages", params=recipient, json={"text": text, "attachments": attachments})

    async def answer_callback(self, callback_id: str, text: str, attachments: list[dict]) -> None:
        await self._request("POST", "/answers", params={"callback_id": callback_id}, json={"message": {"text": text, "attachments": attachments}})

    async def create_subscription(self, url: str, secret: str) -> None:
        await self._request("POST", "/subscriptions", json={"url": url, "update_types": ["bot_started", "message_created", "message_callback"], "secret": secret})

    async def _request(self, method: str, path: str, **kwargs: object) -> dict:
        try:
            response = await self._client.request(method, path, headers=self._headers, **kwargs)
            response.raise_for_status()
            data = response.json()
            if data.get("success") is False:
                raise MaxApiError(data.get("message", "MAX API returned success=false"))
            return data
        except (httpx.HTTPError, ValueError, MaxApiError) as exc:
            logger.error("max_api_request_failed", extra={"path": path, "error": str(exc)})
            raise MaxApiError("MAX API request failed") from exc


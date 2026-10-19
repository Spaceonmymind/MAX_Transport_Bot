import httpx
import pytest

from app.max_api import MaxApi, MaxApiError


@pytest.mark.asyncio
async def test_api_error_is_wrapped_without_exposing_token():
    async def responder(request):
        assert request.headers["Authorization"] == "secret-token"
        return httpx.Response(500, json={"message": "failure"})

    client = httpx.AsyncClient(base_url="https://example.test", transport=httpx.MockTransport(responder))
    api = MaxApi("secret-token", "https://example.test", client)
    with pytest.raises(MaxApiError):
        await api.send_message({"user_id": 1}, "text", [])
    await client.aclose()

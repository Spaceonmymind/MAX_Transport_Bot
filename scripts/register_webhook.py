"""Register a MAX webhook once; it is intentionally not invoked by application startup."""
import asyncio

from app.config import get_settings
from app.max_api import MaxApi


async def main() -> None:
    settings = get_settings()
    if not settings.public_base_url.startswith("https://"):
        raise SystemExit("PUBLIC_BASE_URL must start with https://")
    api = MaxApi(settings.max_bot_token, str(settings.max_api_base_url))
    try:
        await api.create_subscription(settings.public_base_url.rstrip("/") + settings.webhook_path, settings.max_webhook_secret)
    finally:
        await api.close()
    print("Webhook subscription created.")


if __name__ == "__main__":
    asyncio.run(main())


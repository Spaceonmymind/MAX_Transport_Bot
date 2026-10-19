import asyncio
import hmac
import logging
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from app.config import get_settings
from app.handlers import UpdateHandler
from app.logging_config import configure_logging
from app.max_api import MaxApi, MaxApiError
from app.menu import load_menu

logger = logging.getLogger(__name__)


class SeenUpdates:
    def __init__(self, limit: int = 2000):
        self.values: set[str] = set()
        self.order: deque[str] = deque(maxlen=limit)

    def add_if_new(self, update: dict[str, Any]) -> bool:
        key = str(update.get("update_id") or f"{update.get('update_type')}:{update.get('timestamp')}:{(update.get('callback') or {}).get('callback_id', '')}")
        if key in self.values:
            return False
        if len(self.order) == self.order.maxlen:
            self.values.discard(self.order[0])
        self.order.append(key)
        self.values.add(key)
        return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    menu = load_menu(Path(__file__).resolve().parent.parent / "data" / "menu.json")
    api = MaxApi(settings.max_bot_token, str(settings.max_api_base_url))
    app.state.settings = settings
    app.state.handler = UpdateHandler(menu, api)
    app.state.seen = SeenUpdates()
    logger.info("application_started")
    yield
    await api.close()
    logger.info("application_stopped")


app = FastAPI(title="MAX Transport Bot", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/{webhook_path:path}")
async def webhook(webhook_path: str, request: Request) -> dict[str, bool]:
    settings = request.app.state.settings
    if f"/{webhook_path}" != settings.webhook_path:
        raise HTTPException(status_code=404, detail="not found")
    provided = request.headers.get("X-Max-Bot-Api-Secret", "")
    if not hmac.compare_digest(provided, settings.max_webhook_secret):
        raise HTTPException(status_code=401, detail="invalid webhook secret")
    try:
        update: dict[str, Any] = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc
    if not request.app.state.seen.add_if_new(update):
        return {"ok": True}
    try:
        await request.app.state.handler.handle(update)
    except MaxApiError:
        # A non-200 response asks MAX to retry delivery. It is intentional for transient API errors.
        raise HTTPException(status_code=503, detail="temporary processing failure")
    except Exception:
        logger.exception("webhook_processing_failed")
        raise HTTPException(status_code=500, detail="processing failure")
    return {"ok": True}

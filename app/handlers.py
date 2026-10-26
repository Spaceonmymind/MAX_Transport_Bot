import logging
from typing import Any

from app.keyboards import BACK_ID, MAIN_ID, keyboard_for, start_keyboard
from app.max_api import MaxApi, MaxApiError
from app.menu import MenuTree

logger = logging.getLogger(__name__)


class UpdateHandler:
    def __init__(self, menu: MenuTree, api: MaxApi):
        self.menu = menu
        self.api = api

    async def handle(self, update: dict[str, Any]) -> None:
        kind = update.get("update_type")
        if kind == "bot_started":
            recipient = self._recipient(update)
            if recipient:
                await self._show_welcome(recipient)
        elif kind == "message_created":
            recipient = self._recipient(update)
            text = self._message_text(update)
            if recipient:
                if text in {"/start", "/menu"}:
                    if text == "/start":
                        await self._show_welcome(recipient)
                    else:
                        await self._show("main", recipient)
                else:
                    await self.api.send_message(recipient, self.menu.document.unknown_message, keyboard_for(self.menu.document.main, self.menu))
        elif kind == "message_callback":
            await self._handle_callback(update)
        else:
            logger.info("ignored_update", extra={"update_type": kind})

    async def _handle_callback(self, update: dict[str, Any]) -> None:
        callback = update.get("callback") or {}
        callback_id = callback.get("callback_id")
        payload = callback.get("payload")
        if not isinstance(callback_id, str) or not isinstance(payload, str):
            logger.warning("malformed_callback")
            return
        item_id = self._resolve_callback(payload)
        if not item_id:
            logger.warning("unknown_callback", extra={"payload": payload})
            await self.api.answer_callback(callback_id, self.menu.document.stale_callback_message, keyboard_for(self.menu.document.main, self.menu))
            return
        item = self.menu.get(item_id)
        assert item is not None
        await self.api.answer_callback(callback_id, item.text or item.title, keyboard_for(item, self.menu))

    def _resolve_callback(self, payload: str) -> str | None:
        if payload == MAIN_ID:
            return "main"
        if payload.startswith(BACK_ID) and self.menu.get(payload[len(BACK_ID):]):
            return payload[len(BACK_ID):]
        if payload.startswith("go:") and self.menu.get(payload[3:]):
            return payload[3:]
        return None

    async def _show(self, item_id: str, recipient: dict[str, int], welcome: bool = False) -> None:
        item = self.menu.get(item_id)
        assert item is not None
        text = self.menu.document.welcome if welcome else (item.text or item.title)
        await self.api.send_message(recipient, text, keyboard_for(item, self.menu))

    async def _show_welcome(self, recipient: dict[str, int]) -> None:
        await self.api.send_message(recipient, self.menu.document.welcome, start_keyboard(self.menu))

    @staticmethod
    def _message_text(update: dict[str, Any]) -> str:
        message = update.get("message") or {}
        body = message.get("body") or message
        return body.get("text", "") if isinstance(body, dict) else ""

    @staticmethod
    def _recipient(update: dict[str, Any]) -> dict[str, int] | None:
        message = update.get("message") or {}
        sender = message.get("sender") or {}
        user = update.get("user") or {}

        if isinstance(sender.get("user_id"), int):
            return {"user_id": sender["user_id"]}

        if isinstance(user.get("user_id"), int):
            return {"user_id": user["user_id"]}

        if isinstance(message.get("recipient"), dict):
            chat_id = message["recipient"].get("chat_id")
            if isinstance(chat_id, int):
                return {"chat_id": chat_id}

        if isinstance(update.get("chat_id"), int):
            return {"chat_id": update["chat_id"]}

        return None


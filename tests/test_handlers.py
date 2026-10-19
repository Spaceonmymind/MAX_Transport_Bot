from pathlib import Path

import pytest

from app.handlers import UpdateHandler
from app.menu import load_menu


class FakeApi:
    def __init__(self):
        self.messages = []
        self.answers = []

    async def send_message(self, recipient, text, attachments):
        self.messages.append((recipient, text, attachments))

    async def answer_callback(self, callback_id, text, attachments):
        self.answers.append((callback_id, text, attachments))


@pytest.fixture
def handler():
    return UpdateHandler(load_menu(Path("data/menu.json")), FakeApi())


@pytest.mark.asyncio
@pytest.mark.parametrize("command", ["/start", "/menu"])
async def test_commands_show_main_menu(handler, command):
    await handler.handle({"update_type": "message_created", "user": {"user_id": 7}, "message": {"body": {"text": command}}})
    assert handler.api.messages[-1][0] == {"user_id": 7}
    assert "Расписание" in handler.api.messages[-1][2][0]["payload"]["buttons"][0][0]["text"]


@pytest.mark.asyncio
async def test_unknown_message_shows_menu(handler):
    await handler.handle({"update_type": "message_created", "user": {"user_id": 7}, "message": {"body": {"text": "hello"}}})
    assert handler.api.messages[-1][1] == handler.menu.document.unknown_message


@pytest.mark.asyncio
async def test_callback_and_navigation(handler):
    await handler.handle({"update_type": "message_callback", "callback": {"callback_id": "one", "payload": "go:benefits"}})
    assert handler.api.answers[-1][1] == "Льготы на транспорте"
    await handler.handle({"update_type": "message_callback", "callback": {"callback_id": "two", "payload": "go:benefits_city"}})
    assert "городской общественный транспорт" in handler.api.answers[-1][1]
    await handler.handle({"update_type": "message_callback", "callback": {"callback_id": "three", "payload": "nav:back:benefits"}})
    assert handler.api.answers[-1][1] == "Льготы на транспорте"


@pytest.mark.asyncio
async def test_unknown_callback_returns_main_menu(handler):
    await handler.handle({"update_type": "message_callback", "callback": {"callback_id": "old", "payload": "go:gone"}})
    assert handler.api.answers[-1][1] == handler.menu.document.stale_callback_message


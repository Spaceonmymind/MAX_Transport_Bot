import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("MAX_BOT_TOKEN", "test-token")
os.environ.setdefault("MAX_WEBHOOK_SECRET", "test_secret")

from app.main import app


def test_health_and_webhook_authentication():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.post("/webhook/max", json={}).status_code == 401


def test_duplicate_event_is_ignored(monkeypatch):
    with TestClient(app) as client:
        calls = []

        async def handled(update):
            calls.append(update)

        monkeypatch.setattr(client.app.state.handler, "handle", handled)
        payload = {"update_id": "same", "update_type": "ignored"}
        headers = {"X-Max-Bot-Api-Secret": "test_secret"}
        assert client.post("/webhook/max", headers=headers, json=payload).status_code == 200
        assert client.post("/webhook/max", headers=headers, json=payload).status_code == 200
        assert len(calls) == 1

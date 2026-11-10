import json
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_reminder_service import parse_natural_language, parse_with_provider

client = TestClient(app)


def test_ai_parser_extracts_relative_time_for_reminder_creation():
    result = parse_natural_language("Remind me to submit my assignment in 30 minutes.", timezone_name="Europe/London")

    assert result.intent == "create"
    assert "submit my assignment" in result.title.lower()
    assert result.remind_at is not None
    assert result.remind_at.tzinfo is not None


def test_ai_parser_rejects_non_reminder_questions():
    result = parse_natural_language("What is the weather like today?", timezone_name="Europe/London")

    assert result.intent == "unknown"
    assert result.requires_clarification is True


def test_ai_reminder_endpoint_creates_a_reminder_from_natural_language():
    response = client.post(
        "/api/ai/reminders",
        json={
            "text": "Remind me to call John tomorrow at 9 AM.",
            "timezone": "Europe/London",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["intent"] == "create"
    assert payload["created"] is True
    assert "call john" in payload["reminder"]["title"].lower()
    assert payload["reminder"]["remind_at"] is not None


def test_ai_reminder_endpoint_requires_date_when_missing():
    response = client.post(
        "/api/ai/reminders",
        json={
            "text": "Remind me to review the proposal.",
            "timezone": "Europe/London",
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["requires_clarification"] is True


def test_parse_with_provider_uses_ollama_when_configured(monkeypatch):
    calls = {"count": 0}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return json.dumps({
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "intent": "create",
                        "title": "call John",
                        "remind_at": "2026-11-10T09:00:00+00:00",
                        "requires_clarification": False,
                        "clarification": None,
                    })
                }
            }).encode("utf-8")

    def fake_urlopen(request_obj, timeout=20):
        calls["count"] += 1
        payload = json.loads(request_obj.data.decode("utf-8"))
        assert payload["model"] == "qwen3:8b"
        assert payload["messages"][0]["role"] == "system"
        return FakeResponse()

    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    monkeypatch.setattr("app.services.ai_reminder_service.request.urlopen", fake_urlopen)

    result = parse_with_provider("Remind me to call John tomorrow at 9 AM.", "Europe/London")

    assert calls["count"] == 1
    assert result.intent == "create"
    assert result.title == "call John"
    assert result.remind_at is not None

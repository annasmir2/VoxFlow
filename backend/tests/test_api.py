from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services.reminder_service import reminder_status

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_task_crud_flow():
    create_response = client.post(
        "/api/tasks",
        json={
            "title": "Draft sprint recap",
            "description": "Summarize blockers and wins.",
            "priority": "high",
            "status": "pending",
            "due_date": "2026-11-20T09:00:00",
        },
    )
    assert create_response.status_code == 201
    task = create_response.json()
    assert task["title"] == "Draft sprint recap"

    list_response = client.get("/api/tasks")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
    assert len(list_response.json()) >= 1

    single_response = client.get(f"/api/tasks/{task['id']}")
    assert single_response.status_code == 200
    assert single_response.json()["id"] == task["id"]

    patch_response = client.patch(
        f"/api/tasks/{task['id']}",
        json={"status": "completed", "priority": "medium"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "completed"

    delete_response = client.delete(f"/api/tasks/{task['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_task = client.get("/api/tasks/999999")
    assert missing_task.status_code == 404


def test_reminder_crud_flow():
    create_response = client.post(
        "/api/reminders",
        json={
            "title": "Design review",
            "remind_at": "2026-11-08T10:30:00",
        },
    )
    assert create_response.status_code == 201
    reminder = create_response.json()
    assert reminder["title"] == "Design review"

    list_response = client.get("/api/reminders")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
    assert len(list_response.json()) >= 1

    patch_response = client.patch(
        f"/api/reminders/{reminder['id']}",
        json={"title": "Design review updated", "is_completed": True},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["is_completed"] is True

    delete_response = client.delete(f"/api/reminders/{reminder['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    missing_reminder = client.get("/api/reminders/999999")
    assert missing_reminder.status_code == 404


def test_invalid_input_and_not_found():
    invalid_task = client.post(
        "/api/tasks",
        json={"title": "", "priority": "urgent"},
    )
    assert invalid_task.status_code == 422

    invalid_reminder = client.post(
        "/api/reminders",
        json={"title": "", "remind_at": "not-a-date"},
    )
    assert invalid_reminder.status_code == 422

    bad_update = client.patch("/api/tasks/999999", json={"status": "completed"})
    assert bad_update.status_code == 404

    bad_reminder_update = client.patch("/api/reminders/999999", json={"is_completed": True})
    assert bad_reminder_update.status_code == 404


def test_reminder_status_logic_and_notification_tracking():
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    create_response = client.post(
        "/api/reminders",
        json={
            "title": "Follow up with design",
            "remind_at": future_time,
        },
    )
    assert create_response.status_code == 201
    reminder = create_response.json()
    assert reminder_status(type("StubReminder", (), {"is_completed": False, "remind_at": reminder["remind_at"], "notification_sent_at": None})()) == "UPCOMING"

    past_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    overdue_response = client.post(
        "/api/reminders",
        json={
            "title": "Overdue billing reminder",
            "remind_at": past_time,
        },
    )
    assert overdue_response.status_code == 201
    overdue_reminder = overdue_response.json()
    assert overdue_reminder["is_completed"] is False

    patched_response = client.patch(
        f"/api/reminders/{overdue_reminder['id']}",
        json={"notification_sent_at": datetime.now(timezone.utc).isoformat()},
    )
    assert patched_response.status_code == 200
    assert patched_response.json()["notification_sent_at"] is not None

    assert client.delete(f"/api/reminders/{reminder['id']}").status_code == 200
    assert client.delete(f"/api/reminders/{overdue_reminder['id']}").status_code == 200

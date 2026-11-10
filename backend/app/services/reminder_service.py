from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union

from sqlalchemy.orm import Session

from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderUpdate


def _normalize_datetime(value: Optional[Union[datetime, str]]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def reminder_status(reminder: Reminder) -> str:
    if reminder.is_completed:
        return "COMPLETED"

    now = datetime.now(timezone.utc)
    due_at = _normalize_datetime(reminder.remind_at)
    if due_at is None:
        return "UPCOMING"

    if due_at > now:
        return "UPCOMING"

    if reminder.notification_sent_at is not None:
        return "OVERDUE"

    return "DUE"


def list_reminders(db: Session) -> list[Reminder]:
    return db.query(Reminder).order_by(Reminder.created_at.desc()).all()


def get_reminder(db: Session, reminder_id: int) -> Optional[Reminder]:
    return db.query(Reminder).filter(Reminder.id == reminder_id).first()


def create_reminder(db: Session, reminder_data: ReminderCreate) -> Reminder:
    db_reminder = Reminder(**reminder_data.model_dump())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


def update_reminder(db: Session, reminder_id: int, reminder_data: ReminderUpdate) -> Optional[Reminder]:
    db_reminder = get_reminder(db, reminder_id)
    if db_reminder is None:
        return None

    update_data = reminder_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reminder, field, value)

    db.commit()
    db.refresh(db_reminder)
    return db_reminder


def delete_reminder(db: Session, reminder_id: int) -> bool:
    db_reminder = get_reminder(db, reminder_id)
    if db_reminder is None:
        return False
    db.delete(db_reminder)
    db.commit()
    return True

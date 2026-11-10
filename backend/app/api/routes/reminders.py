from typing import Dict, Union

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reminder import ReminderCreate, ReminderRead, ReminderUpdate
from app.services import reminder_service

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderRead])
def list_reminders(db: Session = Depends(get_db)) -> list[ReminderRead]:
    return reminder_service.list_reminders(db)


@router.get("/{reminder_id}", response_model=ReminderRead)
def get_reminder(reminder_id: int, db: Session = Depends(get_db)) -> ReminderRead:
    reminder = reminder_service.get_reminder(db, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    return reminder


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db)) -> ReminderRead:
    return reminder_service.create_reminder(db, reminder)


@router.patch("/{reminder_id}", response_model=ReminderRead)
def update_reminder(reminder_id: int, reminder_data: ReminderUpdate, db: Session = Depends(get_db)) -> ReminderRead:
    reminder = reminder_service.update_reminder(db, reminder_id, reminder_data)
    if reminder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    return reminder


@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)) -> Dict[str, Union[bool, int]]:
    deleted = reminder_service.delete_reminder(db, reminder_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")
    return {"deleted": True, "reminder_id": reminder_id}

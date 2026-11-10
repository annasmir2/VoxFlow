from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reminder import ReminderCreate, ReminderRead
from app.services import reminder_service
from app.services.ai_reminder_service import parse_with_provider

router = APIRouter(prefix="/ai", tags=["ai"])


class AiReminderRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    timezone: str = "Europe/London"


class AiReminderResponse(BaseModel):
    intent: str
    created: bool = False
    requires_clarification: bool = False
    clarification: Optional[str] = None
    confirmation: Optional[str] = None
    reminder: Optional[ReminderRead] = None


@router.post("/reminders", response_model=AiReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder_from_natural_language(payload: AiReminderRequest, db: Session = Depends(get_db)) -> AiReminderResponse:
    parsed = parse_with_provider(payload.text, payload.timezone)

    if parsed.intent != "create" or parsed.requires_clarification or not parsed.title or not parsed.remind_at:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "intent": parsed.intent,
                "requires_clarification": True,
                "clarification": parsed.clarification or "I need a clearer reminder instruction before I can create it.",
            },
        )

    reminder = reminder_service.create_reminder(
        db,
        ReminderCreate(
            title=parsed.title,
            remind_at=parsed.remind_at,
            is_completed=False,
        ),
    )

    return AiReminderResponse(
        intent="create",
        created=True,
        requires_clarification=False,
        clarification=None,
        confirmation=f"I\'ve scheduled your {parsed.title} reminder for {parsed.remind_at.isoformat(timespec='minutes')}",
        reminder=ReminderRead.model_validate(reminder),
    )

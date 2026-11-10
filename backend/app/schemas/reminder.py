from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReminderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    remind_at: datetime
    is_completed: bool = False
    notification_sent_at: Optional[datetime] = None


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    remind_at: Optional[datetime] = None
    is_completed: Optional[bool] = None
    notification_sent_at: Optional[datetime] = None


class ReminderRead(ReminderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

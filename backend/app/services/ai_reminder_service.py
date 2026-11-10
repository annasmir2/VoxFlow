from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Literal, Optional
from urllib import error, request
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

DAY_NAMES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class AiReminderParseResult(BaseModel):
    intent: Literal["create", "update", "delete", "retrieve", "unknown"] = "unknown"
    title: Optional[str] = None
    remind_at: Optional[datetime] = None
    requires_clarification: bool = False
    clarification: Optional[str] = None
    raw_text: str = ""


def _normalise_spacing(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clean_title(raw_title: str) -> str:
    cleaned = raw_title.strip(" \t\r\n.,;:!?-_/[](){}")
    cleaned = re.sub(r"^(?:remind me to|remind me|please remind me|create a reminder to|create reminder to|schedule a reminder for|schedule a reminder to|schedule reminder for|set a reminder for|set reminder for|set reminder to|make a reminder to|add a reminder to|reminder to)\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:on|at|for|in|my|the|a|an)\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:on|at|for|in)\s+", " ", cleaned, flags=re.IGNORECASE)
    cleaned = _normalise_spacing(cleaned)
    return cleaned.strip(" -,:;!?.")


def _resolve_timezone(timezone_name: Optional[str]) -> ZoneInfo:
    candidate = timezone_name or "Europe/London"
    try:
        return ZoneInfo(candidate)
    except Exception:
        return ZoneInfo("Europe/London")


def _extract_time_value(text: str) -> Optional[tuple[int, int]]:
    time_match = re.search(r"\b(?:(\d{1,2})(?::(\d{2}))?\s*(am|pm)|((\d{1,2}):(\d{2})))\b", text, flags=re.IGNORECASE)
    if not time_match:
        return None

    if time_match.group(1):
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or "0")
        meridiem = time_match.group(3).lower()
        if meridiem == "pm" and hour < 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
    else:
        hour = int(time_match.group(4))
        minute = int(time_match.group(5))

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour, minute


def _extract_relative_delta(text: str) -> Optional[timedelta]:
    relative_match = re.search(r"\bin\s+(\d+)\s*(minute|minutes|hour|hours|day|days|week|weeks)\b", text, flags=re.IGNORECASE)
    if not relative_match:
        return None

    value = int(relative_match.group(1))
    unit = relative_match.group(2).lower()
    if unit.startswith("minute"):
        return timedelta(minutes=value)
    if unit.startswith("hour"):
        return timedelta(hours=value)
    if unit.startswith("day"):
        return timedelta(days=value)
    if unit.startswith("week"):
        return timedelta(weeks=value)
    return None


def _find_next_weekday(day_name: str, now: datetime) -> datetime:
    target_index = DAY_NAMES[day_name.lower()]
    current_index = now.weekday()
    days_until = (target_index - current_index) % 7
    if days_until == 0:
        days_until = 7
    target_date = now.date() + timedelta(days=days_until)
    return datetime.combine(target_date, datetime.min.time())


def _extract_datetime_from_text(text: str, now: datetime) -> tuple[Optional[datetime], Optional[str]]:
    if not text:
        return None, None

    relative_delta = _extract_relative_delta(text)
    if relative_delta is not None:
        return now + relative_delta, re.search(r"\bin\s+\d+\s*(?:minute|minutes|hour|hours|day|days|week|weeks)\b", text, flags=re.IGNORECASE).group(0)

    day_match = re.search(r"\b(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", text, flags=re.IGNORECASE)
    if day_match:
        day_phrase = day_match.group(0).lower()
        time_value = _extract_time_value(text)
        if time_value is None:
            return None, day_match.group(0)

        hour, minute = time_value
        if "tomorrow" in day_phrase:
            base_date = (now + timedelta(days=1)).date()
        elif "today" in day_phrase:
            base_date = now.date()
        elif "next" in day_phrase:
            target_day = day_phrase.split()[-1]
            base_date = _find_next_weekday(target_day, now).date()
        else:
            target_day = day_phrase
            base_date = _find_next_weekday(target_day, now).date()

        candidate = datetime.combine(base_date, datetime.min.time()).replace(
            hour=hour,
            minute=minute,
            tzinfo=now.tzinfo,
        )
        if candidate < now and "today" not in day_phrase and "tomorrow" not in day_phrase and "next" not in day_phrase:
            candidate += timedelta(days=7)
        return candidate, day_match.group(0)

    time_value = _extract_time_value(text)
    if time_value is not None:
        hour, minute = time_value
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate < now:
            candidate += timedelta(days=1)
        return candidate, re.search(r"\b(?:(?:\d{1,2}(?::\d{2})?\s*(?:am|pm))|(?:\d{1,2}:\d{2}))\b", text, flags=re.IGNORECASE).group(0)

    return None, None


def _extract_title(text: str, matched_text: Optional[str]) -> str:
    working_text = text
    if matched_text:
        working_text = working_text.replace(matched_text, " ")

    working_text = re.sub(r"\b(?:remind me to|remind me|please remind me|please|create a reminder to|create reminder to|schedule a reminder for|schedule a reminder to|schedule reminder for|schedule reminder to|set a reminder for|set reminder for|set reminder to|make a reminder to|add a reminder to|reminder to)\b", " ", working_text, flags=re.IGNORECASE)
    working_text = re.sub(r"\b(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", " ", working_text, flags=re.IGNORECASE)
    working_text = re.sub(r"\b(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", " ", working_text, flags=re.IGNORECASE)
    working_text = re.sub(r"\b(?:at\s+)?\d{1,2}:\d{2}\b", " ", working_text, flags=re.IGNORECASE)
    working_text = re.sub(r"\b(?:for|on|at|in|the|a|an)\b", " ", working_text, flags=re.IGNORECASE)
    working_text = working_text.strip(" \t\r\n.,;:!?-/[](){}")
    return _clean_title(working_text)


def _contains_reminder_intent(text: str) -> bool:
    normalized = text.lower()
    if re.search(r"\b(?:remind|reminder|schedule|scheduled|create a reminder|create reminder|set a reminder|set reminder|add a reminder|reminder to)\b", normalized):
        return True
    return False


def _extract_json_object(content: str) -> str:
    cleaned = (content or "").strip()
    if not cleaned:
        return "{}"
    if cleaned.startswith("```"):
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
        if fenced_match:
            return fenced_match.group(1)
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned
    candidate = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if candidate:
        return candidate.group(0)
    return "{}"


def _extract_provider_content(response_json: dict) -> str:
    message = response_json.get("message") or {}
    if isinstance(message, dict):
        content = message.get("content")
        if content:
            return str(content)

    choices = response_json.get("choices") or []
    if choices and isinstance(choices[0], dict):
        message = choices[0].get("message") or {}
        content = message.get("content") if isinstance(message, dict) else None
        if content:
            return str(content)

    return ""


def parse_natural_language(text: str, timezone_name: str = "Europe/London") -> AiReminderParseResult:
    normalized = _normalise_spacing(text or "")
    if not normalized:
        return AiReminderParseResult(
            intent="unknown",
            requires_clarification=True,
            clarification="I need a reminder instruction before I can create anything.",
            raw_text=text or "",
        )

    lower_text = normalized.lower()
    if "update" in lower_text or "edit" in lower_text:
        return AiReminderParseResult(intent="update", requires_clarification=True, clarification="I can create a new reminder from natural language, but editing an existing reminder still needs the manual workflow.", raw_text=normalized)
    if "delete" in lower_text or "remove" in lower_text:
        return AiReminderParseResult(intent="delete", requires_clarification=True, clarification="I can help create a reminder, but I do not handle deletion from natural language in this version.", raw_text=normalized)
    if "show" in lower_text or "list" in lower_text or "what reminders" in lower_text:
        return AiReminderParseResult(intent="retrieve", requires_clarification=True, clarification="I can help create new reminders, but retrieval is still handled from the dashboard.", raw_text=normalized)

    if not _contains_reminder_intent(normalized):
        return AiReminderParseResult(
            intent="unknown",
            requires_clarification=True,
            clarification="I can create a reminder from your message, but I need a reminder instruction like 'remind me to call John tomorrow at 9 AM'.",
            raw_text=normalized,
        )

    timezone = _resolve_timezone(timezone_name)
    now = datetime.now(timezone)
    remind_at, matched_text = _extract_datetime_from_text(normalized, now)
    if remind_at is None:
        return AiReminderParseResult(
            intent="create",
            title=None,
            requires_clarification=True,
            clarification="I need a clear date and time for the reminder, such as 'tomorrow at 10 AM' or 'in 30 minutes'.",
            raw_text=normalized,
        )

    title = _extract_title(normalized, matched_text)
    if not title:
        return AiReminderParseResult(
            intent="create",
            remind_at=remind_at,
            requires_clarification=True,
            clarification="I need a clear reminder title, for example: 'submit the application' or 'call John'.",
            raw_text=normalized,
        )

    return AiReminderParseResult(
        intent="create",
        title=title,
        remind_at=remind_at,
        requires_clarification=False,
        clarification=None,
        raw_text=normalized,
    )


def parse_with_provider(text: str, timezone_name: str = "Europe/London") -> AiReminderParseResult:
    provider = (os.getenv("AI_PROVIDER") or "ollama").strip().lower()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()

    if provider == "ollama":
        base_url = (os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL") or "qwen3:8b"
        payload = {
            "model": model,
            "stream": False,
            "options": {"temperature": 0},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a reminder parser. Return valid JSON only with keys: intent, title, "
                        "remind_at, requires_clarification, clarification. Use Europe/London timezone. "
                        "intent must be one of create, update, delete, retrieve, unknown. "
                        "When no valid reminder can be extracted, set intent to 'unknown' and requires_clarification to true. "
                        "Use ISO 8601 datetime strings for remind_at when available."
                    ),
                },
                {"role": "user", "content": text},
            ],
        }

        request_body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{base_url}/api/chat",
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=60) as response:
                response_json = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, ValueError):
            return parse_natural_language(text, timezone_name)

        try:
            content = _extract_provider_content(response_json)
            data = json.loads(_extract_json_object(content))
            parsed = AiReminderParseResult.model_validate(data)
            if parsed.remind_at is not None and not isinstance(parsed.remind_at, datetime):
                parsed.remind_at = datetime.fromisoformat(str(parsed.remind_at))
            return parsed
        except Exception:
            return parse_natural_language(text, timezone_name)

    if provider == "openai" and api_key:
        payload = {
            "model": os.getenv("OPENAI_MODEL") or "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Return JSON only with keys: intent, title, remind_at, requires_clarification, clarification. The intent must be one of create, update, delete, retrieve, unknown. Use ISO 8601 datetime strings for remind_at when available. If the user request is not a reminder instruction, set intent to 'unknown' and requires_clarification to true.",
                },
                {"role": "user", "content": text},
            ],
            "response_format": {"type": "json_object"},
        }

        request_body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=20) as response:
                response_json = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, ValueError):
            return parse_natural_language(text, timezone_name)

        try:
            choice = response_json["choices"][0]["message"]["content"]
            data = json.loads(choice)
            return AiReminderParseResult.model_validate(data)
        except Exception:
            return parse_natural_language(text, timezone_name)

    return parse_natural_language(text, timezone_name)

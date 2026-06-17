"""UTC timestamp parsing and formatting."""

from __future__ import annotations

from datetime import UTC, datetime


def parse_utc(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and require/normalize UTC."""

    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(f"timestamp must include UTC offset: {value}")
    return dt.astimezone(UTC)


def utcnow() -> datetime:
    return datetime.now(UTC)


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

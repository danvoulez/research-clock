"""Configuration loading for the checked-in material YAML specs.

The repository intentionally has no runtime dependencies, so this module parses
only the simple YAML subset used by specs/rate_law.yaml: nested mappings,
scalars, and scalar lists.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RateLawConfig:
    tick_seconds: int
    base_cpm: float
    amplitude_cpm: float
    min_cpm: float
    max_cpm: float
    period_seconds: int
    phase_utc: str
    daily_call_ceiling: int
    minute_peak_ceiling: int


def _scalar(raw: str) -> Any:
    raw = raw.strip()
    if raw in {"true", "false"}:
        return raw == "true"
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Parse the small YAML subset used by repository material specs."""

    root: dict[str, Any] = {}
    current_map: dict[str, Any] = root
    current_indent = 0
    current_list_key: str | None = None

    for line_no, original in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not original.strip() or original.lstrip().startswith("#"):
            continue
        indent = len(original) - len(original.lstrip(" "))
        text = original.strip()

        if indent == 0:
            current_map = root
            current_indent = 0
            current_list_key = None
        elif indent == 2 and current_indent == 0:
            current_indent = 2
        elif indent < current_indent:
            current_map = root
            current_indent = indent
            current_list_key = None

        if text.startswith("- "):
            if current_list_key is None:
                raise ValueError(f"list item without list key at {path}:{line_no}")
            current_map.setdefault(current_list_key, []).append(_scalar(text[2:]))
            continue

        key, sep, value = text.partition(":")
        if not sep:
            raise ValueError(f"invalid YAML subset at {path}:{line_no}: {text}")
        key = key.strip()
        value = value.strip()
        if indent == 0:
            if value:
                root[key] = _scalar(value)
                current_list_key = None
            else:
                root[key] = {}
                current_map = root[key]
                current_indent = 2
                current_list_key = None
        else:
            if value:
                current_map[key] = _scalar(value)
                current_list_key = None
            else:
                current_map[key] = []
                current_list_key = key
    return root

def load_rate_law(path: str | Path) -> RateLawConfig:
    data = load_simple_yaml(path)
    law = data["law"]
    budget = data["budget"]
    return RateLawConfig(
        tick_seconds=int(data["tick_seconds"]),
        base_cpm=float(law["base_cpm"]),
        amplitude_cpm=float(law["amplitude_cpm"]),
        min_cpm=float(law["min_cpm"]),
        max_cpm=float(law["max_cpm"]),
        period_seconds=int(law["period_seconds"]),
        phase_utc=str(law["phase_utc"]),
        daily_call_ceiling=int(budget["daily_call_ceiling"]),
        minute_peak_ceiling=int(budget["minute_peak_ceiling"]),
    )

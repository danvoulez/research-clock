"""Canonical material hashing utilities for Research Clock records."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Return deterministic, compact JSON for content addressing.

    This is intentionally a narrow JCS-compatible subset for the material
    records produced by this package: UTF-8 JSON, sorted object keys, compact
    separators, and no NaN/Infinity values.
    """

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_hex(value: Any) -> str:
    """Hash a JSON-like value or raw string/bytes with SHA-256."""

    if isinstance(value, bytes):
        data = value
    elif isinstance(value, str):
        data = value.encode("utf-8")
    else:
        data = canonical_json(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

"""Ghost candidate builders for material clock failures."""

from __future__ import annotations

from .canonical import sha256_hex
from .timeutil import iso_utc, utcnow


def ghost_candidate(reason: str, payload: dict) -> dict:
    body = {
        "kind": "clock.ghost_candidate.v0",
        "reason": reason,
        "observed_at": iso_utc(utcnow()),
        "payload": payload,
        "semantic_status": "candidate_only_not_admitted",
    }
    body["ghost_candidate_hash"] = sha256_hex(body)
    return body

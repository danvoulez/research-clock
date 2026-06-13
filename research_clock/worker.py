"""Research Clock worker-once implementation.

Workers are the only component here that can call inference, and they do so only
through the declared single inference boundary URL supplied by the envelope/run
configuration. Worker output remains material evidence/candidate/ghost only.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .canonical import sha256_hex
from .ghosts import ghost_candidate
from .store import MaterialStore
from .timeutil import iso_utc, utcnow

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|authorization|bearer|token|secret|password)\s*[:=]\s*(?:bearer\s+)?[^\s,;]+"),
]
FORBIDDEN_AUTHORITY_WORDS = {"receipt", "done", "admitted", "closed.receipt"}


@dataclass(frozen=True)
class Boundary:
    ref: str
    url: str
    model_ref: str

    def assert_allowed(self, actual_url: str) -> None:
        declared = urlparse(self.url)
        actual = urlparse(actual_url)
        if (actual.scheme, actual.netloc, actual.path) != (declared.scheme, declared.netloc, declared.path):
            raise BoundaryViolation(f"worker refused non-declared inference URL: {actual_url}")
        host = actual.hostname or ""
        if "lab512" in host.lower() and "LAB_8GB" in self.ref:
            raise BoundaryViolation("worker refused direct LAB512 URL for LAB_8GB boundary")


class BoundaryViolation(RuntimeError):
    pass


def redact(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: match.group(1) + "=<redacted>", redacted)
    return redacted


def score_response(text: str) -> tuple[str, dict]:
    lowered = text.lower()
    if any(word in lowered for word in FORBIDDEN_AUTHORITY_WORDS):
        return "fail", {"reason": "forbidden_authority_word"}
    if not text.strip():
        return "no_candidate", {"reason": "empty_response"}
    parsed_json = False
    try:
        json.loads(text)
        parsed_json = True
    except json.JSONDecodeError:
        parsed_json = False
    return "pass", {"schema_valid": parsed_json, "forbidden_authority_words": 0}


def call_inference(boundary: Boundary, prompt: str, timeout_seconds: int) -> tuple[str, dict]:
    boundary.assert_allowed(boundary.url)
    payload = json.dumps({"model": boundary.model_ref, "prompt": prompt, "stream": False}).encode("utf-8")
    request = Request(
        boundary.url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8", errors="replace")
    text = body
    metadata = {"http_response_hash": sha256_hex(body)}
    try:
        data = json.loads(body)
        text = str(data.get("response") or data.get("text") or data.get("content") or body)
    except json.JSONDecodeError:
        pass
    return text, metadata


def worker_once(
    *,
    store: MaterialStore,
    worker_ref: str,
    boundary: Boundary,
    prompt_ref: str,
    prompt_text: str,
    scorecard_ref: str,
    timeout_seconds: int = 30,
    variable_ref: str | None = None,
    variable_value: str | None = None,
) -> dict:
    lease_id = str(uuid.uuid4())
    beat = store.lease_next(worker_ref, lease_id)
    if beat is None:
        return {"kind": "clock.worker_report.v0", "result": "no_due_beat"}

    attempt = store.next_attempt(beat["beat_id"]) - 1
    leased_at = iso_utc(utcnow())
    variable_as_of = iso_utc(utcnow()) if variable_value is not None else None
    full_prompt = prompt_text if variable_value is None else f"{prompt_text}\n\nVARIABLE:\n{variable_value}"
    request_material = {
        "boundary_ref": boundary.ref,
        "url": boundary.url,
        "model_ref": boundary.model_ref,
        "prompt_hash": sha256_hex(prompt_text),
        "variable_hash": sha256_hex(variable_value) if variable_value is not None else None,
    }
    request_hash = sha256_hex(request_material)
    called_at = iso_utc(utcnow())

    response_text = ""
    response_hash = None
    error_code = None
    ghost_hash = None
    try:
        response_text, metadata = call_inference(boundary, full_prompt, timeout_seconds)
        response_hash = metadata["http_response_hash"]
        score_result, score = score_response(response_text)
    except BoundaryViolation:
        raise
    except Exception as exc:  # inference boundary operational failure becomes material Ghost candidate
        error_code = exc.__class__.__name__
        ghost = ghost_candidate(
            "inference_boundary_unreachable",
            {"beat_id": beat["beat_id"], "boundary_ref": boundary.ref, "error_code": error_code},
        )
        ghost_hash = ghost["ghost_candidate_hash"]
        score_result = "ghost_candidate"
        score = {"reason": "inference_boundary_unreachable", "error_code": error_code}

    closed_at = iso_utc(utcnow())
    redacted_response = redact(response_text)
    score_hash = sha256_hex(score)
    candidate_hash = None
    if score_result == "pass":
        candidate_hash = sha256_hex(
            {
                "kind": "clock.result_candidate.v0",
                "beat_id": beat["beat_id"],
                "response_hash": response_hash,
                "score_hash": score_hash,
                "semantic_status": "candidate_only_not_admitted",
            }
        )

    record = {
        "beat_id": beat["beat_id"],
        "attempt": attempt,
        "worker_ref": worker_ref,
        "due_at": beat["due_at"],
        "dispatched_at": beat["emitted_at"],
        "leased_at": leased_at,
        "called_at": called_at,
        "closed_at": closed_at,
        "prompt_ref": prompt_ref,
        "prompt_hash": sha256_hex(prompt_text),
        "variable_ref": variable_ref,
        "variable_hash": sha256_hex(variable_value) if variable_value is not None else None,
        "variable_as_of": variable_as_of,
        "model_ref": boundary.model_ref,
        "inference_boundary_ref": boundary.ref,
        "request_hash": request_hash,
        "response_hash": response_hash,
        "scorecard_ref": scorecard_ref,
        "score_hash": score_hash,
        "score_result": score_result,
        "candidate_hash": candidate_hash,
        "ghost_candidate_hash": ghost_hash,
        "error_code": error_code,
        "redaction_status": "redacted",
    }
    call_record_hash = store.insert_call_record(record)
    terminal = "honored" if score_result in {"pass", "no_candidate"} else "ghosted"
    store.append_event(
        beat["beat_id"],
        terminal,
        worker_ref=worker_ref,
        lease_id=lease_id,
        attempt=attempt,
        payload={
            "call_record_hash": call_record_hash,
            "score_result": score_result,
            "candidate_hash": candidate_hash,
            "ghost_candidate_hash": ghost_hash,
            "redacted_response_hash": sha256_hex(redacted_response),
        },
    )
    return {
        "kind": "clock.worker_report.v0",
        "beat_id": beat["beat_id"],
        "attempt": attempt,
        "score_result": score_result,
        "call_record_hash": call_record_hash,
        "candidate_hash": candidate_hash,
        "ghost_candidate_hash": ghost_hash,
    }

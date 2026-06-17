"""SQLite material store for Research Clock operations.

SQLite is used for a local production-grade material queue: durable writes,
unique beat identity, append-only events, leases, and content-addressed call
records. It is operational material only, never semantic truth.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .canonical import sha256_hex
from .rate_law import EmittedBeat
from .timeutil import iso_utc, utcnow

SCHEMA = """
pragma journal_mode = wal;
pragma foreign_keys = on;

create table if not exists beats (
  beat_id text primary key,
  plan_ref text not null,
  experiment_ref text not null,
  due_at text not null,
  sequence_index integer not null,
  prompt_ref text not null,
  variable_selector_ref text not null,
  target_calls_per_minute real not null,
  emitted_at text not null,
  dispatcher_ref text not null,
  material_hash text not null,
  unique(plan_ref, due_at, sequence_index)
);

create table if not exists beat_events (
  event_id integer primary key autoincrement,
  beat_id text not null references beats(beat_id),
  event_kind text not null,
  observed_at text not null,
  worker_ref text,
  lease_id text,
  attempt integer,
  event_payload text not null default '{}',
  material_hash text not null
);

create table if not exists call_records (
  call_record_hash text primary key,
  beat_id text not null references beats(beat_id),
  attempt integer not null,
  worker_ref text not null,
  due_at text not null,
  dispatched_at text not null,
  leased_at text not null,
  called_at text not null,
  closed_at text not null,
  prompt_ref text not null,
  prompt_hash text not null,
  variable_ref text,
  variable_hash text,
  variable_as_of text,
  model_ref text not null,
  inference_boundary_ref text not null,
  request_hash text not null,
  response_hash text,
  scorecard_ref text not null,
  score_hash text not null,
  score_result text not null,
  candidate_hash text,
  ghost_candidate_hash text,
  error_code text,
  redaction_status text not null,
  unique(beat_id, attempt)
);

create view if not exists pending_beats as
select b.*
from beats b
where not exists (
  select 1 from beat_events e
  where e.beat_id = b.beat_id
    and e.event_kind in ('honored', 'missed_sla', 'ghosted')
);

create view if not exists minute_metrics as
select substr(b.due_at, 1, 16) || ':00Z' as minute,
       b.plan_ref,
       count(*) as emitted,
       sum(case when exists (select 1 from beat_events e where e.beat_id = b.beat_id and e.event_kind = 'honored') then 1 else 0 end) as honored,
       sum(case when exists (select 1 from beat_events e where e.beat_id = b.beat_id and e.event_kind in ('missed_sla','ghosted')) then 1 else 0 end) as missed_or_ghosted
from beats b
group by 1, 2;
"""


class MaterialStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def insert_beats(self, beats: Iterable[EmittedBeat], dispatcher_ref: str) -> int:
        inserted = 0
        now = iso_utc(utcnow())
        with self.conn:
            for beat in beats:
                material = {
                    "beat_id": beat.beat_id,
                    "plan_ref": beat.plan_ref,
                    "experiment_ref": beat.experiment_ref,
                    "due_at": beat.due_at,
                    "sequence_index": beat.sequence_index,
                    "prompt_ref": beat.prompt_ref,
                    "variable_selector_ref": beat.variable_selector_ref,
                    "target_calls_per_minute": beat.target_calls_per_minute,
                    "emitted_at": now,
                    "dispatcher_ref": dispatcher_ref,
                }
                material_hash = sha256_hex(material)
                cur = self.conn.execute(
                    """
                    insert or ignore into beats
                    (beat_id, plan_ref, experiment_ref, due_at, sequence_index, prompt_ref,
                     variable_selector_ref, target_calls_per_minute, emitted_at, dispatcher_ref, material_hash)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        beat.beat_id,
                        beat.plan_ref,
                        beat.experiment_ref,
                        beat.due_at,
                        beat.sequence_index,
                        beat.prompt_ref,
                        beat.variable_selector_ref,
                        beat.target_calls_per_minute,
                        now,
                        dispatcher_ref,
                        material_hash,
                    ),
                )
                inserted += cur.rowcount
        return inserted

    def append_event(
        self,
        beat_id: str,
        event_kind: str,
        *,
        worker_ref: str | None = None,
        lease_id: str | None = None,
        attempt: int | None = None,
        payload: dict | None = None,
    ) -> str:
        observed_at = iso_utc(utcnow())
        event_payload = payload or {}
        material = {
            "beat_id": beat_id,
            "event_kind": event_kind,
            "observed_at": observed_at,
            "worker_ref": worker_ref,
            "lease_id": lease_id,
            "attempt": attempt,
            "event_payload": event_payload,
        }
        material_hash = sha256_hex(material)
        with self.conn:
            self.conn.execute(
                """
                insert into beat_events
                (beat_id, event_kind, observed_at, worker_ref, lease_id, attempt, event_payload, material_hash)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (beat_id, event_kind, observed_at, worker_ref, lease_id, attempt, json.dumps(event_payload), material_hash),
            )
        return material_hash

    def lease_next(self, worker_ref: str, lease_id: str) -> sqlite3.Row | None:
        row = self.conn.execute(
            """
            select * from pending_beats
            where due_at <= ?
            order by due_at, sequence_index
            limit 1
            """,
            (iso_utc(utcnow()),),
        ).fetchone()
        if row is None:
            return None
        attempt = self.next_attempt(row["beat_id"])
        self.append_event(row["beat_id"], "leased", worker_ref=worker_ref, lease_id=lease_id, attempt=attempt)
        return row

    def next_attempt(self, beat_id: str) -> int:
        value = self.conn.execute(
            "select coalesce(max(attempt), 0) + 1 from beat_events where beat_id = ?",
            (beat_id,),
        ).fetchone()[0]
        return int(value)

    def insert_call_record(self, record: dict) -> str:
        call_record_hash = sha256_hex(record)
        record = {**record, "call_record_hash": call_record_hash}
        with self.conn:
            self.conn.execute(
                """
                insert into call_records
                (call_record_hash, beat_id, attempt, worker_ref, due_at, dispatched_at, leased_at,
                 called_at, closed_at, prompt_ref, prompt_hash, variable_ref, variable_hash,
                 variable_as_of, model_ref, inference_boundary_ref, request_hash, response_hash,
                 scorecard_ref, score_hash, score_result, candidate_hash, ghost_candidate_hash,
                 error_code, redaction_status)
                values
                (:call_record_hash, :beat_id, :attempt, :worker_ref, :due_at, :dispatched_at, :leased_at,
                 :called_at, :closed_at, :prompt_ref, :prompt_hash, :variable_ref, :variable_hash,
                 :variable_as_of, :model_ref, :inference_boundary_ref, :request_hash, :response_hash,
                 :scorecard_ref, :score_hash, :score_result, :candidate_hash, :ghost_candidate_hash,
                 :error_code, :redaction_status)
                """,
                record,
            )
        return call_record_hash

    def metrics(self) -> list[dict]:
        rows = self.conn.execute("select * from minute_metrics order by minute, plan_ref").fetchall()
        return [dict(row) for row in rows]

-- clock_material_schema.sql
-- Status: proposed material schema, not semantic ledger.
-- Purpose: high-frequency Research Clock accounting under admitted experiment envelopes.
-- Law: tables here are operational material. They are not truth.

create schema if not exists clock;

create table if not exists clock.beats (
  beat_id text primary key,
  plan_ref text not null,
  experiment_ref text not null,
  due_at timestamptz not null,
  sequence_index integer not null,
  prompt_ref text not null,
  variable_selector_ref text not null,
  emitted_at timestamptz not null default now(),
  dispatcher_ref text not null,
  material_hash text,
  unique(plan_ref, due_at, sequence_index)
);

create table if not exists clock.beat_events (
  event_id bigserial primary key,
  beat_id text not null references clock.beats(beat_id),
  event_kind text not null,
  observed_at timestamptz not null default now(),
  worker_ref text,
  lease_id text,
  attempt integer,
  event_payload jsonb not null default '{}'::jsonb,
  material_hash text
);

create table if not exists clock.call_records (
  call_record_hash text primary key,
  beat_id text not null references clock.beats(beat_id),
  attempt integer not null,
  worker_ref text not null,
  due_at timestamptz not null,
  dispatched_at timestamptz,
  leased_at timestamptz,
  called_at timestamptz not null,
  closed_at timestamptz not null,
  prompt_ref text not null,
  prompt_hash text,
  variable_ref text,
  variable_hash text,
  variable_as_of timestamptz,
  model_ref text not null,
  inference_boundary_ref text not null,
  request_hash text not null,
  response_hash text,
  scorecard_ref text not null,
  score_hash text,
  score_result text not null,
  candidate_hash text,
  ghost_candidate_hash text,
  error_code text,
  redaction_status text not null default 'redacted'
);

create or replace view clock.pending_beats as
select b.*
from clock.beats b
where not exists (
  select 1 from clock.beat_events e
  where e.beat_id = b.beat_id
    and e.event_kind in ('honored','missed_sla','cancelled','budget_stopped')
);

create or replace view clock.minute_metrics as
select
  date_trunc('minute', b.due_at) as minute,
  b.plan_ref,
  count(*) as emitted,
  count(*) filter (where exists (
    select 1 from clock.beat_events e where e.beat_id = b.beat_id and e.event_kind = 'honored'
  )) as honored,
  count(*) filter (where exists (
    select 1 from clock.beat_events e where e.beat_id = b.beat_id and e.event_kind = 'missed_sla'
  )) as missed_sla
from clock.beats b
group by 1, 2;

comment on schema clock is
  'Research Clock material schema. Operational material only; admitted Acts remain semantic truth.';

comment on table clock.beats is
  'Deterministic due beats emitted under an admitted envelope. Not semantic truth.';

comment on table clock.beat_events is
  'Append-only material events about beat handling. Not semantic truth.';

comment on table clock.call_records is
  'Content-addressed material records for inference calls. Not semantic truth.';

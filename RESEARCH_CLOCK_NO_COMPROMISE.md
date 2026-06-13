# The Research Clock v0 -- No-Compromise Specification

Status: stone draft, 2026-06-13.
Scope: Santo Andre Laboratory, ActGraph, Track A high-frequency local inference.
Authority status: material proposal until registered/admitted by Act.

## 0. Thesis

The Research Clock is not a worker.
The Research Clock is not a scheduler that secretly executes.
The Research Clock is not a second gate.
The Research Clock is the Lab's time-enforcement organ for one bounded research envelope.

It exists to make one claim testable:

```text
small local models
+ strict grammars
+ many cheap calls
+ scorecards
+ ledger memory
+ time
= accumulated institutional signal
```

The Clock does not prove the thesis. It creates the conditions to measure it.

## 1. Non-negotiable laws

RCLK-001. The Gate is the only semantic minter.

RCLK-002. The metronome observes time. It does not call models, judge results, write Acts, close receipts, or execute consequences.

RCLK-003. The dispatcher emits material beat jobs. It does not call models and it does not write truth.

RCLK-004. Workers drain material beat jobs and call inference only through the declared single inference boundary.

RCLK-005. No worker may call LAB512, Mistral.rs, or any local model endpoint directly if that bypasses the declared inference door.

RCLK-006. The wave controls call rate only. It never precomputes model output.

RCLK-007. Tomorrow's emission curve may be precomputed. Tomorrow's answers may not.

RCLK-008. High frequency produces signal. It does not produce authority.

RCLK-009. Per-call accounting is mandatory. Per-call sovereign Acts are not mandatory and should not be the default.

RCLK-010. Every call must have a content-addressed material record. Consequential outputs return to Gate as candidates, ghosts, receipts, or findings according to policy.

RCLK-011. A missed beat does not stall the clock. It becomes material backlog and, past SLA, a Ghost candidate or batched Ghost candidate.

RCLK-012. The Clock may claim due, dispatched, called, scored, submitted, missed, or ghosted. It may not claim done.

RCLK-013. A result is not a Receipt. A report is not a Receipt. A green metric is not a Receipt.

RCLK-014. pg_cron, launchd, systemd, or any metronome mechanism may witness time. None may mint Acts.

RCLK-015. Material tables, queues, files, and views are operational material. They are not semantic truth.

RCLK-016. Budget breach stops emission and opens a Ghost candidate. It does not silently overrun.

RCLK-017. Rate law and emission plan are deterministic and rebuildable.

RCLK-018. All timestamps are recorded honestly. No component may release a stale value as fresh.

RCLK-019. Every autonomous clock agent must have passport, T-class visa, scope, budget, expiry, and superior contract reference.

RCLK-020. T3 consequence is impossible for this stone. The Clock is T1/T2 at most until a later admitted policy says otherwise.

## 2. Separation of organs

```text
TIME WITNESS / METRONOME
  Observes that time passed.
  Writes no semantic truth.
  Performs no inference.
  Produces beat observations or triggers dispatcher ticks.

DISPATCHER
  Reads admitted experiment envelope and deterministic rate law.
  Emits material beat jobs according to the wave.
  Returns before next tick.
  Performs no inference.

MATERIAL QUEUE
  Stores due beats, leases, call attempts, score outputs, and accounting events.
  Is rebuildable or explainable from admitted plan + material event log.
  Is not semantic authority.

WORKERS
  Lease beat jobs.
  Call Mistral.rs only through the single inference boundary.
  Record call material.
  Run grammar/scorecard.
  Submit consequential candidates or Ghost candidates to Gate.

GATE
  Admits, rejects, ghosts, or escalates semantic consequences.
  Is the only minter.

PROJECTIONS
  Produce calendar, backlog, metrics, capacity, and Track A views.
  Are rebuildable and disposable.
```

## 3. The rate law

The wave is a deterministic function over UTC time.

Let:

```text
lambda(t) = clamp(min_cpm, max_cpm, base_cpm + amp_cpm * sin(2*pi*(t - phase)/period))
```

where:

```text
lambda(t) = target calls per minute at time t
min_cpm   = minimum calls per minute
max_cpm   = hard peak cap from visa/budget
base_cpm  = center rate
amp_cpm   = wave amplitude
phase     = UTC phase timestamp
period    = wave period, e.g. 24h or 6h
```

Emission is computed by integrating the rate over tick buckets with deterministic fractional carry:

```text
ideal_calls(bucket_i) = integral(lambda(t)/60 dt over [t_i, t_{i+1}))
carry_i               = fractional remainder from previous bucket
emit_i                = floor(ideal_calls(bucket_i) + carry_i)
carry_{i+1}           = ideal_calls(bucket_i) + carry_i - emit_i
```

This prevents random jitter and makes precompute equal live dispatch.

## 4. Precompute vs execution

Allowed before `when`:

```text
- compute tomorrow's emission plan;
- validate rate law;
- validate prompt references;
- validate variable selector references;
- verify scorecard exists;
- verify inference boundary health;
- estimate budget;
- prepare cache;
- reserve workers;
- detect impossible capacity;
- open readiness Ghost candidates if needed.
```

Forbidden before `when`:

```text
- model call;
- score result;
- result qualifier;
- result receipt;
- claiming completion;
- writing a real run result;
- treating capacity forecast as promise.
```

Formula:

```text
Precompute the wave.
Never precompute the answer.
```

## 5. Experiment envelope

The Clock runs only inside an admitted experimental envelope.

The envelope must declare:

```text
experiment_ref
superior_rule_refs
inference_boundary_ref
clock_agent_ref
visa_ref
rate_law_ref
prompt_ref
variable_selector_ref
scorecard_ref
budget
SLA
start_at
end_at
allowed_outputs
forbidden_outputs
review_path
```

The envelope admits the research boundary, not the results.

## 6. Material accounting model

High frequency cannot mean 10,000 sovereign Acts per day by default.
It means 10,000 honest material records per day under one admitted envelope.

Per-call accounting is a material record with content identity:

```text
beat_id
plan_ref
due_at
dispatched_at
leased_at
called_at
closed_at
prompt_ref
prompt_hash
variable_ref
variable_hash
variable_as_of
model_ref
inference_boundary_ref
request_hash
response_hash
scorecard_ref
score_hash
score_result
candidate_hash optional
ghost_candidate_hash optional
error_code optional
worker_ref
lease_id
attempt
retry_of optional
```

A material call record becomes semantically relevant only when an admitted Act references it.

Examples:

```text
reported.clock_minute_metrics
opened.clock_missed_beat_ghost
reported.track_a_batch_result
proposed.research_finding
proposed.policy_candidate
```

## 7. Material schema doctrine

Use material tables for performance, not authority.

Recommended schema split:

```text
clock.beats
  one deterministic due beat per due call

clock.beat_events
  append-only material events about leases, calls, scores, retries, misses

clock.call_records
  content-addressed material request/response/score records

clock.views_*
  rebuildable operational views: pending queue, backlog, metrics, capacity
```

The queue is a projection:

```text
pending = emitted beats - terminal honored/missed events
```

No semantic rule may depend on a material queue without an admitted Act or policy giving it role and scope.

## 8. Beat identity and idempotency

A beat id is deterministic:

```text
beat_id = sha256(JCS({
  kind: "clock.beat.v0",
  plan_ref,
  due_at,
  sequence_index,
  prompt_ref,
  variable_selector_ref
}))
```

Properties:

```text
same plan + same due_at + same sequence_index => same beat_id
re-dispatching the same tick is idempotent
worker retry creates new attempt, not new beat
only one terminal honor is accepted per beat_id
extra terminal attempts are duplicate material, not truth
```

## 9. Timestamp law

Every call must expose timing honestly:

```text
due_at         deterministic contract time
dispatched_at  time witness / dispatcher emission time
leased_at      worker lease time
called_at      actual hit to inference boundary
closed_at      response received and scorecard completed
submitted_at   candidate/ghost submission to Gate, if any
admitted_at    Gate admission time, if admitted
```

No component may use due_at as if it were called_at.
No component may use called_at as if it were admitted_at.
No component may use closed_at as if it were reviewed_at.

## 10. Variable law

The prompt can be pinned. The variable can be pinned or live.

Every call records the class:

```text
prompt:
  class: pinned
  prompt_ref
  prompt_hash

variable:
  class: pinned | live
  variable_ref
  variable_hash optional
  as_of timestamp
  selector_ref optional

model:
  class: live
  model_ref
  inference_boundary_ref
```

Live variable means honestly live at `as_of`, not timeless.

## 11. Worker law

A worker may:

```text
- lease one or more due beats;
- call the single inference door;
- record request/response/score material;
- run grammar and scorecard;
- submit candidate/ghost to Gate when consequential;
- mark material beat event as honored or failed;
- report metrics.
```

A worker may not:

```text
- write admitted Acts directly;
- call LAB512 directly if the inference boundary is LAB_8GB;
- bypass grammar/scorecard;
- exceed visa budget;
- claim done;
- close receipt;
- mutate the rate law;
- change prompt, variable selector, or scorecard outside the envelope;
- leak secrets in material logs;
- treat its own output as truth.
```

## 12. Ghost policy

A Ghost candidate is required when:

```text
- beat is unhonored past SLA;
- inference boundary is unreachable;
- scorecard cannot run;
- budget is breached;
- stale variable would be released as fresh;
- worker cannot prove it used the declared boundary;
- clock skew exceeds threshold;
- repeated retries make the call non-idempotent;
- material store corruption is detected.
```

For high volume, Ghosts may be batched if the Act identifies:

```text
range_start
range_end
beat_count
beat_merkle_root or beat_id list hash
reason
SLA
observed timestamps
recovery path
```

A batched Ghost is not a cover-up. It is the only sane way to preserve absence at high frequency without flooding the semantic ledger.

## 13. Metrics

Minimum Track A metrics:

```text
target_calls_per_minute
emitted_calls_per_minute
honored_calls_per_minute
missed_calls_per_minute
backlog_depth
backlog_age_p95
due_to_dispatch_ms_p50
due_to_dispatch_ms_p95
dispatch_to_call_ms_p50
dispatch_to_call_ms_p95
call_latency_ms_p50
call_latency_ms_p95
tokens_per_second_prompt
tokens_per_second_generation
schema_valid_rate
scorecard_pass_rate
no_candidate_rate
ghost_candidate_rate
candidate_submission_rate
candidate_admission_rate
useful_signal_rate
cost_per_call
cost_per_useful_candidate
cost_per_admitted_consequence
worker_error_rate
single_door_violation_count
budget_breach_count
```

Metrics are projections. They can support findings. They are not findings by themselves.

## 14. Projections

Allowed projections:

```text
lab_clock_calendar
lab_clock_emission_plan
lab_clock_due_queue
lab_clock_backlog
lab_clock_worker_leases
lab_clock_minute_metrics
lab_clock_day_metrics
lab_clock_missed_sla
lab_track_a_signal_funnel
```

Every projection must declare source set:

```text
source_set = admitted envelope Acts + admitted rate law Acts + material clock tables + referenced material records
```

Projection rebuild must be tested.

## 15. Contract hierarchy

The Clock stone requires, in order:

```text
1. superior inference boundary Act
2. clock agent contract rule Act
3. registered clock agent passport Act
4. issued clock agent visa Act
5. registered rate law / emission plan Act
6. registered experiment envelope Act
7. material schema migration
8. dispatcher dry-run proof
9. worker dry-run proof
10. pilot metrics Act / Ghost
```

No worker runs before the envelope exists.
No high-frequency loop runs before visa + budget + expiry exist.

## 16. Authorization vocabulary

Use T-classes for authority.
Use dry-run/propose-only as operational modes, not as authorization classes.

```text
T0 = projection only
T1 = observation, material accounting, ghost/candidate proposal
T2 = internal policy/grammar/projection change proposal under gate
T3 = external consequence; never automatic; Dan signs
```

The first clock visa should be:

```text
class: T1
mode: resident_dry_run_then_propose_only
scope: lab.clock.track_a.<experiment>
```

Forbidden:

```text
class: apply
broad IDE write key
unscoped resident worker
no expiry
no daily ceiling
```

## 17. Build order

S0 -- register this spec as material, not law.

S1 -- admit clock agent contract rule candidate.

S2 -- enroll the first clock agent with passport and narrow T1 visa.

S3 -- add material schema migration for clock.beats, clock.beat_events, and clock.call_records.

S4 -- implement deterministic rate law library and unit tests.

S5 -- implement emission-plan generator: no model calls, no gate calls.

S6 -- implement dispatcher dry-run: print due calls per minute and prove shape.

S7 -- enable dispatcher material writes under cap: still no model calls.

S8 -- implement one worker with single-door enforcement: one beat, one call, one score, no admit by default.

S9 -- allow explicit `--admit` only for scorecard-passing candidate or Ghost candidate.

S10 -- run 24h pilot at low cap. Admit one metrics/ghost summary, not 10,000 Acts.

S11 -- ramp wave only after missed-SLA and budget-breach behavior is proven.

## 18. Command surface

Suggested commands:

```bash
actgraph clock plan-wave \
  --experiment act:<hash> \
  --date 2026-06-14 \
  --out material/clock/emission-plan.json

actgraph clock dry-run-dispatch \
  --plan material/clock/emission-plan.json \
  --from 2026-06-14T00:00:00Z \
  --to 2026-06-14T01:00:00Z

actgraph clock dispatch-once \
  --plan act:<hash> \
  --material-db $CLOCK_DB \
  --no-model

actgraph clock worker-once \
  --inference-boundary act:<hash> \
  --scorecard act:<hash> \
  --no-admit

actgraph clock worker-once \
  --inference-boundary act:<hash> \
  --scorecard act:<hash> \
  --admit

actgraph clock metrics \
  --from 2026-06-14T00:00:00Z \
  --to 2026-06-15T00:00:00Z \
  --as-candidate
```

## 19. Acceptance tests

The implementation is not acceptable until these tests exist:

```text
1. rate law precompute equals live dispatch for same interval
2. dispatcher cannot import or call inference client
3. worker refuses non-declared inference URL
4. worker refuses direct LAB512 URL if boundary says LAB_8GB door
5. material beat record includes due/dispatched/called/closed timestamps
6. missed SLA creates Ghost candidate or batched Ghost candidate
7. budget cap stops emission before overrun
8. crash/restart re-emits no duplicate beats
9. repeated worker attempts preserve one beat id and multiple attempts
10. scorecard failure never calls Gate as accepted candidate
11. no `done` or Receipt emitted by worker
12. projection rebuild matches live metrics
13. no secrets appear in material call record
14. timezone and DST do not affect UTC wave shape
15. no semantic Act is written by pg_cron, launchd, or dispatcher
```

## 20. Rollback

Rollback is safe because material state is not semantic truth.

Allowed rollback:

```text
- stop dispatcher;
- stop workers;
- drop clock material views;
- archive clock.beats / beat_events / call_records as material;
- supersede the clock contract rule;
- supersede the experiment envelope;
- admit a Ghost explaining abandoned or invalid pilot.
```

Forbidden rollback:

```text
- delete admitted Acts;
- rewrite admitted schedule history;
- hide missed beats;
- reinterpret material metrics as if no pilot happened;
- silently change rate law after the fact.
```

## 21. No-compromise final form

The Clock is not impressive because it is fast.
It is important because it is relentless, bounded, honest, and replayable.

It turns time into a research instrument:

```text
wave due
  -> material beat
  -> single-door inference
  -> grammar/scorecard
  -> candidate | ghost | no_candidate
  -> gate only if consequential
  -> projection
  -> Track A measurement
```

The Clock does not make the Lab true.
It makes the Lab impossible to fool cheaply.

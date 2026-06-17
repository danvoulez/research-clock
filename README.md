# Research Clock No-Compromise Pack

Status: material draft pack, not admitted law.
Date: 2026-06-13.
Scope: Relogio v0 / Track A high-frequency local inference.

This pack materializes a no-compromise Research Clock stone:

- wave-shaped call rate;
- deterministic emission plans;
- material per-call accounting;
- workers through the single inference door;
- scorecards before gate;
- gate as the only semantic minter;
- no pg_cron worker logic;
- no direct LAB512 bypass;
- no claim of done without review;
- no projection as truth.

Main file:

- RESEARCH_CLOCK_NO_COMPROMISE.md

Supporting material:

- contracts/*.candidate.act.json
- migrations/clock_material_schema.sql
- specs/rate_law.yaml
- specs/beat_record.schema.json
- scorecards/track_a_metrics.yaml
- ACCEPTANCE_TESTS.md
- CODEX_TASK_RESEARCH_CLOCK.md

Admission note:

Do not admit candidate Acts as-is if they contain TODO placeholders. Fill exact passport, superior Act hashes, budget, inference boundary, and schedule data first.

## Production material runtime added in this branch

This repository now includes a runnable `research-clock` Python package for the
v0 material engine. It implements the production separation required by the
spec while keeping all outputs material-only unless a later Gate path admits
them:

- `research-clock plan` precomputes deterministic UTC beat IDs from the clamped
  sine rate law.
- `research-clock dispatch-dry-run` replays dispatcher output without DB writes
  and without any inference imports.
- `research-clock dispatch-write` writes idempotent material beats to a durable
  SQLite material store.
- `research-clock worker-once` leases one due beat and calls only the declared
  inference boundary URL, then records request/response/score hashes and the
  four required timestamps.
- `research-clock ghost-missed` creates a batched Ghost candidate for beats past
  SLA.
- `research-clock metrics` rebuilds minute metrics from material tables.

Example dry run:

```bash
research-clock dispatch-dry-run \
  --plan-ref lab.clock.track_a.wave_plan.v0 \
  --experiment-ref lab.track_a.high_frequency_local_inference.wave_clock.v0 \
  --prompt-ref TODO_PROMPT_ACT_OR_MATERIAL_REF \
  --variable-selector-ref TODO_SELECTOR_ACT_OR_MATERIAL_REF \
  --start 2026-06-14T00:00:00Z \
  --end 2026-06-14T00:10:00Z
```

Example material write:

```bash
research-clock dispatch-write \
  --store .local/research-clock.sqlite \
  --dispatcher-ref dispatcher:local:v0 \
  --plan-ref lab.clock.track_a.wave_plan.v0 \
  --experiment-ref lab.track_a.high_frequency_local_inference.wave_clock.v0 \
  --prompt-ref TODO_PROMPT_ACT_OR_MATERIAL_REF \
  --variable-selector-ref TODO_SELECTOR_ACT_OR_MATERIAL_REF \
  --start 2026-06-14T00:00:00Z \
  --end 2026-06-14T00:10:00Z
```

The runtime still does not admit Acts, close Receipts, claim done, call direct
LAB512 bypasses for a `LAB_8GB` boundary, or let the dispatcher call models.

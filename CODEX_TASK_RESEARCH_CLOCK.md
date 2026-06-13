# Codex Task -- Research Clock v0, No-Compromise Stone

You are working in the real ActGraph / LogLine / Santo Andre Laboratory repo.

Goal: implement the Research Clock v0 in small stones. Do not implement autonomous 24/7 operation first.

Read first:

1. pinned canon and conformance files;
2. Formal Foundations;
3. Lab Operating Method;
4. Ecosystem Rules;
5. current inference boundary rule;
6. current Grammar Engine / scorecard code;
7. this Research Clock spec.

Hard restrictions:

- no canon changes;
- no second ledger;
- no pg_cron minting;
- no direct LAB512 bypass;
- no model calls from metronome or dispatcher;
- no worker receipt closure;
- no done claims;
- no high-frequency admission of every microcall by default;
- no autonomous run before passport, visa, envelope, budget, and expiry exist.

Small stones:

S1. Add docs only.
S2. Add candidate Acts for contract, rate law, and experiment envelope.
S3. Add material migration for clock.beats, clock.beat_events, clock.call_records.
S4. Add pure rate-law module + tests.
S5. Add emission plan generator + tests.
S6. Add dispatcher dry-run command, no DB writes.
S7. Add material dispatcher write behind explicit flag.
S8. Add worker-once command through single inference door, no admit.
S9. Add explicit --admit path for scorecard-passing candidate or Ghost candidate only.
S10. Add metrics candidate generator.

Required final report:

- files created/modified;
- commands run;
- tests passed/failed/not available;
- what is still material only;
- what candidate Acts were produced;
- what was not implemented;
- next stone.

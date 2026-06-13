# Research Clock Acceptance Tests

Status: required before autonomous 24/7 operation.

## A. Rate and schedule

1. Precompute equality
   - Given a rate law and UTC interval,
   - when the emission plan is precomputed and the live dispatcher is replayed,
   - then minute-level emitted beat counts must match exactly.

2. UTC only
   - Given a local DST boundary,
   - when planning emissions,
   - then UTC wave shape remains unchanged.

3. Budget cap
   - Given a rate law peak above visa cap,
   - then the dispatcher clamps or refuses before emission and produces a budget Ghost candidate.

## B. Separation

4. Metronome no inference
   - The metronome binary/module must not link or import inference client code.

5. Dispatcher no inference
   - The dispatcher must not call the inference door, Mistral.rs, LAB512, or model APIs.

6. Worker single door
   - The worker must refuse any URL not matching the declared inference boundary.

7. No pg minting
   - pg_cron or SQL functions may create material beat observations only; they may not mint or admit Acts.

## C. Provenance

8. Four timestamps minimum
   - Every call record must contain due_at, dispatched_at, called_at, closed_at.

9. As-of honesty
   - Live variables must include as_of and source hash/pointer if available.

10. No stale freshness
   - A stale variable cannot be released as live; it must be recorded as stale or ghosted.

## D. Idempotency

11. Beat id deterministic
   - Re-running emission for the same plan/due_at/sequence produces the same beat_id.

12. Retry preserves beat
   - Worker retry creates another attempt for same beat_id, not another due beat.

13. Duplicate terminal refusal
   - Only one terminal honor may count in projections; duplicates remain material attempts.

## E. Gate boundary

14. Scorecard fail no admission
   - Scorecard failure cannot submit a positive candidate to Gate.

15. Ghost allowed
   - Scorecard failure may produce a Ghost candidate if policy says the failure is consequential.

16. Worker no receipt
   - Worker cannot emit Receipt or done. It can emit report/evidence/candidate/ghost.

17. Projection rebuild
   - Dropping clock metric views and rebuilding from material records and admitted envelope must produce same normalized metrics.

## F. Safety

18. Secret redaction
   - Request records may not contain raw API keys, tokens, or secrets.

19. Backlog ghost
   - Beats unhonored past SLA must be ghosted or batched into a Ghost candidate with count/range/root.

20. Stop behavior
   - On budget breach, boundary violation, material corruption, or clock skew breach, emission stops and a Ghost candidate is produced.

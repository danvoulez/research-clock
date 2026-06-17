# Validation Report

- JSON OK: contracts/declared_clock_agent_contract.candidate.act.json
- JSON OK: contracts/registered_track_a_experiment_envelope.candidate.act.json
- JSON OK: contracts/registered_wave_emission_plan.candidate.act.json
- YAML OK: scorecards/track_a_metrics.yaml
- JSON OK: specs/beat_record.schema.json
- YAML OK: specs/rate_law.yaml
- Runtime package added: research_clock
- CLI added: research-clock / python -m research_clock.cli
- Tests added: tests/test_rate_law.py, tests/test_material_store.py, tests/test_worker.py, tests/test_separation.py
- Runtime changes: material-only engine for deterministic planning, dry-run dispatch, SQLite material writes, worker-once through declared inference boundary, Ghost candidate generation, and metrics projection
- Canon changes: 0
- Semantic admissions: 0

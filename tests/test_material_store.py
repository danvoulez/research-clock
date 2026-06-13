from research_clock.config import load_rate_law
from research_clock.rate_law import emission_plan
from research_clock.store import MaterialStore
from research_clock.timeutil import parse_utc


def test_dispatch_write_is_idempotent_and_metrics_rebuild(tmp_path):
    cfg = load_rate_law("specs/rate_law.yaml")
    beats = emission_plan(
        cfg,
        plan_ref="plan:test",
        experiment_ref="exp:test",
        prompt_ref="prompt:test",
        variable_selector_ref="selector:test",
        start=parse_utc("2026-06-14T00:00:00Z"),
        end=parse_utc("2026-06-14T00:02:00Z"),
    )
    store = MaterialStore(tmp_path / "clock.sqlite")
    assert store.insert_beats(beats, "dispatcher:test") == len(beats)
    assert store.insert_beats(beats, "dispatcher:test") == 0
    metrics = store.metrics()
    assert sum(row["emitted"] for row in metrics) == len(beats)
    store.close()

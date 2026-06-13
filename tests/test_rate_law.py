import pytest

from research_clock.config import RateLawConfig, load_rate_law
from research_clock.rate_law import BudgetBreach, beat_id, emission_plan
from research_clock.timeutil import parse_utc


def test_precompute_equals_live_replay_for_same_interval():
    cfg = load_rate_law("specs/rate_law.yaml")
    kwargs = dict(
        plan_ref="plan:test",
        experiment_ref="exp:test",
        prompt_ref="prompt:test",
        variable_selector_ref="selector:test",
        start=parse_utc("2026-06-14T00:00:00Z"),
        end=parse_utc("2026-06-14T03:00:00Z"),
    )
    precomputed = emission_plan(cfg, **kwargs)
    live_replay = emission_plan(cfg, **kwargs)

    assert [b.beat_id for b in precomputed] == [b.beat_id for b in live_replay]


def test_beat_id_is_deterministic():
    one = beat_id("plan", "2026-06-14T00:00:00Z", 0, "prompt", "selector")
    two = beat_id("plan", "2026-06-14T00:00:00Z", 0, "prompt", "selector")
    three = beat_id("plan", "2026-06-14T00:00:00Z", 1, "prompt", "selector")
    assert one == two
    assert one != three


def test_budget_peak_breach_stops_emission():
    cfg = RateLawConfig(
        tick_seconds=60,
        base_cpm=10,
        amplitude_cpm=0,
        min_cpm=10,
        max_cpm=10,
        period_seconds=86400,
        phase_utc="2026-06-14T00:00:00Z",
        daily_call_ceiling=100,
        minute_peak_ceiling=8,
    )
    with pytest.raises(BudgetBreach):
        emission_plan(
            cfg,
            plan_ref="plan",
            experiment_ref="exp",
            prompt_ref="prompt",
            variable_selector_ref="selector",
            start=parse_utc("2026-06-14T00:00:00Z"),
            end=parse_utc("2026-06-14T00:01:00Z"),
        )

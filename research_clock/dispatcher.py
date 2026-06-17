"""Dispatcher functions that emit material beat jobs only.

This module intentionally has no model-call code or network client imports.
"""

from __future__ import annotations

from .config import RateLawConfig
from .rate_law import EmittedBeat, emission_plan
from .store import MaterialStore
from datetime import datetime


def dry_run_plan(
    config: RateLawConfig,
    *,
    plan_ref: str,
    experiment_ref: str,
    prompt_ref: str,
    variable_selector_ref: str,
    start: datetime,
    end: datetime,
) -> list[EmittedBeat]:
    return emission_plan(
        config,
        plan_ref=plan_ref,
        experiment_ref=experiment_ref,
        prompt_ref=prompt_ref,
        variable_selector_ref=variable_selector_ref,
        start=start,
        end=end,
    )


def write_material_beats(beats: list[EmittedBeat], *, store: MaterialStore, dispatcher_ref: str) -> int:
    return store.insert_beats(beats, dispatcher_ref)

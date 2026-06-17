"""Deterministic wave rate law and beat planning."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from .canonical import sha256_hex
from .config import RateLawConfig
from .timeutil import iso_utc, parse_utc

TAU = 2.0 * math.pi


@dataclass(frozen=True)
class EmittedBeat:
    beat_id: str
    plan_ref: str
    experiment_ref: str
    due_at: str
    sequence_index: int
    prompt_ref: str
    variable_selector_ref: str
    target_calls_per_minute: float


def _seconds_from_phase(dt: datetime, phase: datetime) -> float:
    return (dt - phase).total_seconds()


def target_cpm(config: RateLawConfig, when: datetime) -> float:
    phase = parse_utc(config.phase_utc)
    theta = TAU * _seconds_from_phase(when, phase) / config.period_seconds
    raw = config.base_cpm + config.amplitude_cpm * math.sin(theta)
    return min(config.max_cpm, max(config.min_cpm, raw))


def _raw_integral_cpm_seconds(config: RateLawConfig, start_s: float, end_s: float) -> float:
    omega = TAU / config.period_seconds
    return (
        config.base_cpm * (end_s - start_s)
        + config.amplitude_cpm * (-math.cos(omega * end_s) + math.cos(omega * start_s)) / omega
    )


def _crossings_for_threshold(config: RateLawConfig, start_s: float, end_s: float, threshold: float) -> list[float]:
    if config.amplitude_cpm == 0:
        return []
    ratio = (threshold - config.base_cpm) / config.amplitude_cpm
    if ratio <= -1.0 or ratio >= 1.0:
        return []
    alpha = math.asin(ratio)
    period = config.period_seconds
    seeds = [alpha, math.pi - alpha]
    out: list[float] = []
    k_min = math.floor((TAU * start_s / period - max(seeds)) / TAU) - 1
    k_max = math.ceil((TAU * end_s / period - min(seeds)) / TAU) + 1
    for k in range(k_min, k_max + 1):
        for theta in seeds:
            second = (theta + TAU * k) * period / TAU
            if start_s < second < end_s:
                out.append(second)
    return sorted(set(round(x, 12) for x in out))


def integral_calls(config: RateLawConfig, start: datetime, end: datetime) -> float:
    """Integrate the clamped sine law over [start, end) and return calls."""

    if end <= start:
        return 0.0
    phase = parse_utc(config.phase_utc)
    start_s = _seconds_from_phase(start, phase)
    end_s = _seconds_from_phase(end, phase)
    points = [start_s, end_s]
    points.extend(_crossings_for_threshold(config, start_s, end_s, config.min_cpm))
    points.extend(_crossings_for_threshold(config, start_s, end_s, config.max_cpm))
    points = sorted(set(points))

    cpm_seconds = 0.0
    for left, right in zip(points, points[1:]):
        mid = config.base_cpm + config.amplitude_cpm * math.sin(TAU * ((left + right) / 2.0) / config.period_seconds)
        if mid < config.min_cpm:
            cpm_seconds += config.min_cpm * (right - left)
        elif mid > config.max_cpm:
            cpm_seconds += config.max_cpm * (right - left)
        else:
            cpm_seconds += _raw_integral_cpm_seconds(config, left, right)
    return cpm_seconds / 60.0


def beat_id(plan_ref: str, due_at: str, sequence_index: int, prompt_ref: str, variable_selector_ref: str) -> str:
    return sha256_hex(
        {
            "kind": "clock.beat.v0",
            "plan_ref": plan_ref,
            "due_at": due_at,
            "sequence_index": sequence_index,
            "prompt_ref": prompt_ref,
            "variable_selector_ref": variable_selector_ref,
        }
    )


def emission_plan(
    config: RateLawConfig,
    *,
    plan_ref: str,
    experiment_ref: str,
    prompt_ref: str,
    variable_selector_ref: str,
    start: datetime,
    end: datetime,
) -> list[EmittedBeat]:
    """Build deterministic beat plan with fractional carry.

    This function performs no inference, no scoring, and no semantic admission.
    """

    if config.max_cpm > config.minute_peak_ceiling:
        raise BudgetBreach(
            f"rate max_cpm {config.max_cpm:g} exceeds minute_peak_ceiling {config.minute_peak_ceiling:g}"
        )
    if end <= start:
        return []

    tick = timedelta(seconds=config.tick_seconds)
    cursor = start
    carry = 0.0
    emitted: list[EmittedBeat] = []
    total = 0
    while cursor < end:
        bucket_end = min(cursor + tick, end)
        ideal = integral_calls(config, cursor, bucket_end)
        count = math.floor(ideal + carry + 1e-12)
        carry = ideal + carry - count
        due_at = iso_utc(cursor)
        target = target_cpm(config, cursor)
        for seq in range(count):
            total += 1
            if total > config.daily_call_ceiling:
                raise BudgetBreach(
                    f"emission would exceed daily_call_ceiling {config.daily_call_ceiling}"
                )
            emitted.append(
                EmittedBeat(
                    beat_id=beat_id(plan_ref, due_at, seq, prompt_ref, variable_selector_ref),
                    plan_ref=plan_ref,
                    experiment_ref=experiment_ref,
                    due_at=due_at,
                    sequence_index=seq,
                    prompt_ref=prompt_ref,
                    variable_selector_ref=variable_selector_ref,
                    target_calls_per_minute=target,
                )
            )
        cursor = bucket_end
    return emitted


class BudgetBreach(RuntimeError):
    """Emission must stop and a Ghost candidate should be opened."""

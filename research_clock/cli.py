"""Command line entry points for the material Research Clock runtime."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

from .config import load_rate_law
from .ghosts import ghost_candidate
from .rate_law import BudgetBreach, emission_plan
from .store import MaterialStore
from .timeutil import parse_utc, utcnow
from .worker import Boundary, BoundaryViolation, worker_once


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def add_common_plan_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--rate-law", default="specs/rate_law.yaml")
    parser.add_argument("--plan-ref", required=True)
    parser.add_argument("--experiment-ref", required=True)
    parser.add_argument("--prompt-ref", required=True)
    parser.add_argument("--variable-selector-ref", required=True)
    parser.add_argument("--start", required=True, help="UTC ISO timestamp")
    parser.add_argument("--end", required=True, help="UTC ISO timestamp")


def build_plan(args: argparse.Namespace):
    config = load_rate_law(args.rate_law)
    return emission_plan(
        config,
        plan_ref=args.plan_ref,
        experiment_ref=args.experiment_ref,
        prompt_ref=args.prompt_ref,
        variable_selector_ref=args.variable_selector_ref,
        start=parse_utc(args.start),
        end=parse_utc(args.end),
    )


def cmd_plan(args: argparse.Namespace) -> int:
    try:
        beats = build_plan(args)
    except BudgetBreach as exc:
        _print_json(ghost_candidate("budget_breach", {"error": str(exc), "plan_ref": args.plan_ref}))
        return 2
    _print_json([beat.__dict__ for beat in beats])
    return 0


def cmd_dispatch_dry_run(args: argparse.Namespace) -> int:
    try:
        beats = build_plan(args)
    except BudgetBreach as exc:
        _print_json(ghost_candidate("budget_breach", {"error": str(exc), "plan_ref": args.plan_ref}))
        return 2
    _print_json(
        {
            "kind": "clock.dispatcher_dry_run.v0",
            "count": len(beats),
            "first_due_at": beats[0].due_at if beats else None,
            "last_due_at": beats[-1].due_at if beats else None,
            "beats": [beat.__dict__ for beat in beats] if args.include_beats else [],
            "semantic_status": "material_only_not_admitted",
        }
    )
    return 0


def cmd_dispatch_write(args: argparse.Namespace) -> int:
    try:
        beats = build_plan(args)
    except BudgetBreach as exc:
        _print_json(ghost_candidate("budget_breach", {"error": str(exc), "plan_ref": args.plan_ref}))
        return 2
    store = MaterialStore(args.store)
    inserted = store.insert_beats(beats, args.dispatcher_ref)
    store.close()
    _print_json(
        {
            "kind": "clock.dispatcher_material_write.v0",
            "planned": len(beats),
            "inserted": inserted,
            "idempotent_duplicates": len(beats) - inserted,
            "store": args.store,
            "semantic_status": "material_only_not_admitted",
        }
    )
    return 0


def cmd_worker_once(args: argparse.Namespace) -> int:
    store = MaterialStore(args.store)
    prompt_text = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else args.prompt_text
    variable_value = Path(args.variable_file).read_text(encoding="utf-8") if args.variable_file else args.variable_value
    try:
        report = worker_once(
            store=store,
            worker_ref=args.worker_ref,
            boundary=Boundary(args.boundary_ref, args.boundary_url, args.model_ref),
            prompt_ref=args.prompt_ref,
            prompt_text=prompt_text,
            scorecard_ref=args.scorecard_ref,
            timeout_seconds=args.timeout_seconds,
            variable_ref=args.variable_ref,
            variable_value=variable_value,
        )
    except BoundaryViolation as exc:
        _print_json(ghost_candidate("single_door_violation", {"error": str(exc), "boundary_ref": args.boundary_ref}))
        return 2
    finally:
        store.close()
    _print_json(report)
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    store = MaterialStore(args.store)
    try:
        rows = store.metrics()
    finally:
        store.close()
    _print_json(
        {
            "kind": "clock.minute_metrics_report.v0",
            "metrics": rows,
            "semantic_status": "projection_material_not_admitted",
        }
    )
    return 0


def cmd_ghost_missed(args: argparse.Namespace) -> int:
    store = MaterialStore(args.store)
    cutoff = utcnow() - timedelta(seconds=args.sla_seconds)
    rows = store.conn.execute(
        "select * from pending_beats where due_at < ? order by due_at, sequence_index",
        (cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z"),),
    ).fetchall()
    beat_ids = [row["beat_id"] for row in rows]
    ghost = ghost_candidate(
        "missed_sla",
        {
            "beat_count": len(beat_ids),
            "range_start": rows[0]["due_at"] if rows else None,
            "range_end": rows[-1]["due_at"] if rows else None,
            "beat_list_hash": None if not beat_ids else __import__("hashlib").sha256("\n".join(beat_ids).encode()).hexdigest(),
            "SLA_seconds": args.sla_seconds,
        },
    )
    if args.mark and beat_ids:
        for beat_id in beat_ids:
            store.append_event(beat_id, "missed_sla", payload={"batched_ghost_candidate_hash": ghost["ghost_candidate_hash"]})
    store.close()
    _print_json(ghost)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-clock")
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="precompute deterministic material beats; no inference")
    add_common_plan_args(plan)
    plan.set_defaults(func=cmd_plan)

    dry = sub.add_parser("dispatch-dry-run", help="dispatcher replay without DB writes or inference")
    add_common_plan_args(dry)
    dry.add_argument("--include-beats", action="store_true")
    dry.set_defaults(func=cmd_dispatch_dry_run)

    write = sub.add_parser("dispatch-write", help="material dispatcher write; explicit store required")
    add_common_plan_args(write)
    write.add_argument("--store", required=True)
    write.add_argument("--dispatcher-ref", required=True)
    write.set_defaults(func=cmd_dispatch_write)

    worker = sub.add_parser("worker-once", help="lease one due beat and call the declared inference boundary")
    worker.add_argument("--store", required=True)
    worker.add_argument("--worker-ref", required=True)
    worker.add_argument("--boundary-ref", required=True)
    worker.add_argument("--boundary-url", required=True)
    worker.add_argument("--model-ref", required=True)
    worker.add_argument("--prompt-ref", required=True)
    worker.add_argument("--prompt-text", default="")
    worker.add_argument("--prompt-file")
    worker.add_argument("--variable-ref")
    worker.add_argument("--variable-value")
    worker.add_argument("--variable-file")
    worker.add_argument("--scorecard-ref", required=True)
    worker.add_argument("--timeout-seconds", type=int, default=30)
    worker.set_defaults(func=cmd_worker_once)

    metrics = sub.add_parser("metrics", help="emit rebuildable material metrics projection")
    metrics.add_argument("--store", required=True)
    metrics.set_defaults(func=cmd_metrics)

    missed = sub.add_parser("ghost-missed", help="create batched Ghost candidate for SLA-missed pending beats")
    missed.add_argument("--store", required=True)
    missed.add_argument("--sla-seconds", type=int, required=True)
    missed.add_argument("--mark", action="store_true")
    missed.set_defaults(func=cmd_ghost_missed)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

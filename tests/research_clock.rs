use research_clock::{
    config::RateLawDocument,
    dispatcher::{build_emission_plan, deterministic_beat_id, PlanRequest},
    rate_law::RateLaw,
    time::UtcInstant,
    worker::enforce_single_inference_boundary,
};

fn dt(value: &str) -> UtcInstant {
    UtcInstant::parse(value).unwrap()
}

fn request(start_at: UtcInstant, end_at: UtcInstant) -> PlanRequest {
    PlanRequest {
        plan_ref: "plan:test".to_string(),
        experiment_ref: "experiment:test".to_string(),
        prompt_ref: "prompt:test".to_string(),
        variable_selector_ref: "vars:test".to_string(),
        dispatcher_ref: "dispatcher:test".to_string(),
        start_at,
        end_at,
        tick_seconds: 60,
        daily_call_ceiling: 10_000,
    }
}

#[test]
fn bundled_rate_law_is_valid_utc_and_budget_safe() {
    let document = RateLawDocument::from_path("specs/rate_law.yaml").unwrap();
    document.validate().unwrap();
    assert_eq!(document.timezone, "UTC");
    assert_eq!(document.tick_seconds, 60);
}

#[test]
fn precompute_and_dispatch_replay_are_equal() {
    let law = RateLaw::new(4.0, 3.0, 1.0, 8.0, 86_400, dt("2026-06-14T03:00:00Z")).unwrap();
    let req = request(dt("2026-06-14T00:00:00Z"), dt("2026-06-14T02:00:00Z"));
    let precomputed = build_emission_plan(&law, &req).unwrap();
    let replayed = build_emission_plan(&law, &req).unwrap();
    assert_eq!(precomputed.beats, replayed.beats);
    assert_eq!(precomputed.emitted_count, replayed.emitted_count);
}

#[test]
fn beat_id_is_deterministic_for_plan_due_and_sequence() {
    let due = dt("2026-06-14T00:01:00Z");
    assert_eq!(
        deterministic_beat_id("plan:test", due, 42),
        deterministic_beat_id("plan:test", due, 42)
    );
    assert_ne!(
        deterministic_beat_id("plan:test", due, 42),
        deterministic_beat_id("plan:test", due, 43)
    );
}

#[test]
fn budget_ceiling_stops_emission() {
    let law = RateLaw::new(8.0, 0.0, 1.0, 8.0, 86_400, dt("2026-06-14T03:00:00Z")).unwrap();
    let mut req = request(dt("2026-06-14T00:00:00Z"), dt("2026-06-14T03:00:00Z"));
    req.daily_call_ceiling = 2;
    let err = build_emission_plan(&law, &req).unwrap_err().to_string();
    assert!(err.contains("daily_call_ceiling 2 breached"));
}

#[test]
fn worker_refuses_urls_outside_single_inference_boundary() {
    let base = "http://127.0.0.1:8080/v1/";
    let allowed = "http://127.0.0.1:8080/v1/chat/completions";
    let blocked_host = "http://127.0.0.1:8081/v1/chat/completions";
    let blocked_path = "http://127.0.0.1:8080/admin";
    enforce_single_inference_boundary(base, allowed).unwrap();
    assert!(enforce_single_inference_boundary(base, blocked_host).is_err());
    assert!(enforce_single_inference_boundary(base, blocked_path).is_err());
}

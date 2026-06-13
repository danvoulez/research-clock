use crate::{
    config::RateLawDocument,
    dispatcher::{build_emission_plan, PlanRequest},
    time::UtcInstant,
    worker::enforce_single_inference_boundary,
};
use std::{
    env, fs,
    io::{self, Write},
};

pub fn run() -> crate::Result<()> {
    let mut args = env::args().skip(1).collect::<Vec<_>>();
    if args.is_empty() {
        usage();
        return Err("missing command".into());
    }
    let command = args.remove(0);
    match command.as_str() {
        "plan" | "dispatch-dry-run" => run_plan(&args),
        "check-boundary" => run_check_boundary(&args),
        _ => {
            usage();
            Err(format!("unknown command {command}").into())
        }
    }
}

fn run_plan(args: &[String]) -> crate::Result<()> {
    let config = value(args, "--config").unwrap_or_else(|| "specs/rate_law.yaml".to_string());
    let plan_ref = required(args, "--plan-ref")?;
    let experiment_ref = required(args, "--experiment-ref")?;
    let prompt_ref = required(args, "--prompt-ref")?;
    let variable_selector_ref = required(args, "--variable-selector-ref")?;
    let dispatcher_ref = required(args, "--dispatcher-ref")?;
    let start_at = UtcInstant::parse(&required(args, "--start-at")?)?;
    let end_at = UtcInstant::parse(&required(args, "--end-at")?)?;
    let jsonl = args.iter().any(|a| a == "--jsonl");
    let output = value(args, "--output");

    let document = RateLawDocument::from_path(config)?;
    document.validate()?;
    let plan = build_emission_plan(
        &document.rate_law()?,
        &PlanRequest {
            plan_ref,
            experiment_ref,
            prompt_ref,
            variable_selector_ref,
            dispatcher_ref,
            start_at,
            end_at,
            tick_seconds: document.tick_seconds,
            daily_call_ceiling: document.daily_call_ceiling,
        },
    )?;
    let rendered = if jsonl {
        plan.to_jsonl()
    } else {
        format!("{}\n", plan.to_json())
    };
    if let Some(path) = output {
        fs::write(path, rendered)?;
    } else {
        io::stdout().write_all(rendered.as_bytes())?;
    }
    Ok(())
}

fn run_check_boundary(args: &[String]) -> crate::Result<()> {
    enforce_single_inference_boundary(
        &required(args, "--boundary-base-url")?,
        &required(args, "--endpoint-url")?,
    )?;
    println!("ok");
    Ok(())
}

fn value(args: &[String], flag: &str) -> Option<String> {
    args.windows(2).find(|w| w[0] == flag).map(|w| w[1].clone())
}
fn required(args: &[String], flag: &str) -> crate::Result<String> {
    value(args, flag).ok_or_else(|| format!("missing {flag}").into())
}
fn usage() {
    eprintln!("usage: research-clock plan|dispatch-dry-run --plan-ref REF --experiment-ref REF --prompt-ref REF --variable-selector-ref REF --dispatcher-ref REF --start-at UTC --end-at UTC [--config PATH] [--jsonl] [--output PATH]\n       research-clock check-boundary --boundary-base-url URL --endpoint-url URL");
}

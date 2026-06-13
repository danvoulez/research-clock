use crate::{
    hash::{escape_json, fnv1a64_hex},
    rate_law::RateLaw,
    time::UtcInstant,
};

#[derive(Debug, Clone)]
pub struct PlanRequest {
    pub plan_ref: String,
    pub experiment_ref: String,
    pub prompt_ref: String,
    pub variable_selector_ref: String,
    pub dispatcher_ref: String,
    pub start_at: UtcInstant,
    pub end_at: UtcInstant,
    pub tick_seconds: u32,
    pub daily_call_ceiling: u64,
}

#[derive(Debug, Clone, PartialEq)]
pub struct PlannedBeat {
    pub beat_id: String,
    pub plan_ref: String,
    pub experiment_ref: String,
    pub due_at: UtcInstant,
    pub sequence_index: u64,
    pub prompt_ref: String,
    pub variable_selector_ref: String,
    pub target_calls_per_minute: f64,
    pub dispatcher_ref: String,
    pub material_hash: String,
}

#[derive(Debug, Clone)]
pub struct EmissionPlan {
    pub plan_ref: String,
    pub start_at: UtcInstant,
    pub end_at: UtcInstant,
    pub tick_seconds: u32,
    pub emitted_count: u64,
    pub final_fractional_carry: f64,
    pub beats: Vec<PlannedBeat>,
}

pub fn build_emission_plan(law: &RateLaw, request: &PlanRequest) -> crate::Result<EmissionPlan> {
    if request.end_at < request.start_at {
        return Err("end_at must not be before start_at".into());
    }
    if request.tick_seconds == 0 {
        return Err("tick_seconds must be positive".into());
    }
    let mut beats = Vec::new();
    let mut carry = 0.0_f64;
    let mut due = request.start_at;
    let mut sequence_index = 0_u64;
    while due < request.end_at {
        let next = due
            .add_seconds(request.tick_seconds as i64)
            .min(request.end_at);
        let total = law.ideal_calls_between(due, next) + carry;
        let emit = total.floor() as u64;
        carry = total - emit as f64;
        for _ in 0..emit {
            sequence_index += 1;
            if sequence_index > request.daily_call_ceiling {
                return Err(format!(
                    "daily_call_ceiling {} breached at {} for plan {}",
                    request.daily_call_ceiling, due, request.plan_ref
                )
                .into());
            }
            let beat_id = deterministic_beat_id(&request.plan_ref, due, sequence_index);
            let target = law.lambda_cpm_at(due);
            let mut beat = PlannedBeat {
                beat_id,
                plan_ref: request.plan_ref.clone(),
                experiment_ref: request.experiment_ref.clone(),
                due_at: due,
                sequence_index,
                prompt_ref: request.prompt_ref.clone(),
                variable_selector_ref: request.variable_selector_ref.clone(),
                target_calls_per_minute: target,
                dispatcher_ref: request.dispatcher_ref.clone(),
                material_hash: String::new(),
            };
            beat.material_hash = material_hash(&beat);
            beats.push(beat);
        }
        due = next;
    }
    Ok(EmissionPlan {
        plan_ref: request.plan_ref.clone(),
        start_at: request.start_at,
        end_at: request.end_at,
        tick_seconds: request.tick_seconds,
        emitted_count: beats.len() as u64,
        final_fractional_carry: carry,
        beats,
    })
}

pub fn deterministic_beat_id(plan_ref: &str, due_at: UtcInstant, sequence_index: u64) -> String {
    format!(
        "rclk_{}",
        fnv1a64_hex(&[
            "research-clock:v0:beat",
            plan_ref,
            &due_at.to_string(),
            &sequence_index.to_string()
        ])
        .replace("fnv1a64:", "")
    )
}

pub fn material_hash(beat: &PlannedBeat) -> String {
    fnv1a64_hex(&[
        &beat.beat_id,
        &beat.plan_ref,
        &beat.experiment_ref,
        &beat.due_at.to_string(),
        &beat.sequence_index.to_string(),
        &beat.prompt_ref,
        &beat.variable_selector_ref,
        &format!("{:.9}", beat.target_calls_per_minute),
        &beat.dispatcher_ref,
    ])
}

impl PlannedBeat {
    pub fn to_json(&self) -> String {
        format!("{{\"beat_id\":\"{}\",\"plan_ref\":\"{}\",\"experiment_ref\":\"{}\",\"due_at\":\"{}\",\"sequence_index\":{},\"prompt_ref\":\"{}\",\"variable_selector_ref\":\"{}\",\"target_calls_per_minute\":{},\"dispatcher_ref\":\"{}\",\"material_hash\":\"{}\"}}",
            escape_json(&self.beat_id), escape_json(&self.plan_ref), escape_json(&self.experiment_ref), self.due_at, self.sequence_index, escape_json(&self.prompt_ref), escape_json(&self.variable_selector_ref), self.target_calls_per_minute, escape_json(&self.dispatcher_ref), escape_json(&self.material_hash))
    }
}

impl EmissionPlan {
    pub fn to_json(&self) -> String {
        let beats = self
            .beats
            .iter()
            .map(|b| b.to_json())
            .collect::<Vec<_>>()
            .join(",");
        format!("{{\"plan_ref\":\"{}\",\"start_at\":\"{}\",\"end_at\":\"{}\",\"tick_seconds\":{},\"emitted_count\":{},\"final_fractional_carry\":{},\"beats\":[{}]}}", escape_json(&self.plan_ref), self.start_at, self.end_at, self.tick_seconds, self.emitted_count, self.final_fractional_carry, beats)
    }
    pub fn to_jsonl(&self) -> String {
        self.beats
            .iter()
            .map(|b| format!("{}\n", b.to_json()))
            .collect()
    }
}

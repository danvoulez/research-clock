use crate::{rate_law::RateLaw, time::UtcInstant};
use std::{fs, path::Path};

#[derive(Debug, Clone)]
pub struct RateLawDocument {
    pub timezone: String,
    pub tick_seconds: u32,
    pub base_cpm: f64,
    pub amplitude_cpm: f64,
    pub min_cpm: f64,
    pub max_cpm: f64,
    pub period_seconds: u64,
    pub phase_utc: UtcInstant,
    pub daily_call_ceiling: u64,
    pub minute_peak_ceiling: f64,
}

impl RateLawDocument {
    pub fn from_path(path: impl AsRef<Path>) -> crate::Result<Self> {
        Self::from_yaml(&fs::read_to_string(path)?)
    }
    pub fn from_yaml(input: &str) -> crate::Result<Self> {
        Ok(Self {
            timezone: scalar(input, "timezone").unwrap_or_else(|| "UTC".to_string()),
            tick_seconds: scalar(input, "tick_seconds")
                .ok_or("missing tick_seconds")?
                .parse()?,
            base_cpm: scalar(input, "base_cpm")
                .ok_or("missing base_cpm")?
                .parse()?,
            amplitude_cpm: scalar(input, "amplitude_cpm")
                .ok_or("missing amplitude_cpm")?
                .parse()?,
            min_cpm: scalar(input, "min_cpm").ok_or("missing min_cpm")?.parse()?,
            max_cpm: scalar(input, "max_cpm").ok_or("missing max_cpm")?.parse()?,
            period_seconds: scalar(input, "period_seconds")
                .ok_or("missing period_seconds")?
                .parse()?,
            phase_utc: scalar(input, "phase_utc")
                .ok_or("missing phase_utc")?
                .trim_matches('\'')
                .parse()?,
            daily_call_ceiling: scalar(input, "daily_call_ceiling")
                .ok_or("missing daily_call_ceiling")?
                .parse()?,
            minute_peak_ceiling: scalar(input, "minute_peak_ceiling")
                .ok_or("missing minute_peak_ceiling")?
                .parse()?,
        })
    }
    pub fn validate(&self) -> crate::Result<()> {
        if self.timezone != "UTC" {
            return Err(format!("rate law requires UTC timezone, got {}", self.timezone).into());
        }
        if self.tick_seconds == 0 || self.tick_seconds > 3600 {
            return Err("tick_seconds must be in 1..=3600".into());
        }
        if self.max_cpm > self.minute_peak_ceiling {
            return Err("rate-law max_cpm exceeds budget minute_peak_ceiling".into());
        }
        self.rate_law()?.validate()
    }
    pub fn rate_law(&self) -> crate::Result<RateLaw> {
        RateLaw::new(
            self.base_cpm,
            self.amplitude_cpm,
            self.min_cpm,
            self.max_cpm,
            self.period_seconds,
            self.phase_utc,
        )
    }
}

fn scalar(input: &str, key: &str) -> Option<String> {
    for line in input.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('#') {
            continue;
        }
        if let Some(rest) = trimmed.strip_prefix(&format!("{key}:")) {
            return Some(rest.trim().trim_matches('"').to_string());
        }
    }
    None
}

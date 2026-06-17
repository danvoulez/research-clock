use crate::time::UtcInstant;

#[derive(Debug, Clone, Copy)]
pub struct RateLaw {
    pub base_cpm: f64,
    pub amplitude_cpm: f64,
    pub min_cpm: f64,
    pub max_cpm: f64,
    pub period_seconds: u64,
    pub phase_utc: UtcInstant,
}

impl RateLaw {
    pub fn new(
        base_cpm: f64,
        amplitude_cpm: f64,
        min_cpm: f64,
        max_cpm: f64,
        period_seconds: u64,
        phase_utc: UtcInstant,
    ) -> crate::Result<Self> {
        let law = Self {
            base_cpm,
            amplitude_cpm,
            min_cpm,
            max_cpm,
            period_seconds,
            phase_utc,
        };
        law.validate()?;
        Ok(law)
    }
    pub fn validate(&self) -> crate::Result<()> {
        if self.period_seconds == 0 {
            return Err("period_seconds must be positive".into());
        }
        for rate in [
            self.base_cpm,
            self.amplitude_cpm,
            self.min_cpm,
            self.max_cpm,
        ] {
            if !rate.is_finite() || rate < 0.0 {
                return Err("rates must be finite non-negative numbers".into());
            }
        }
        if self.min_cpm > self.max_cpm {
            return Err("min_cpm must be <= max_cpm".into());
        }
        Ok(())
    }
    pub fn lambda_cpm_at(&self, at: UtcInstant) -> f64 {
        let elapsed = (at.epoch_seconds - self.phase_utc.epoch_seconds) as f64;
        let theta = 2.0 * std::f64::consts::PI * elapsed / self.period_seconds as f64;
        (self.base_cpm + self.amplitude_cpm * theta.sin()).clamp(self.min_cpm, self.max_cpm)
    }
    pub fn ideal_calls_between(&self, start: UtcInstant, end: UtcInstant) -> f64 {
        assert!(end >= start, "end must be >= start");
        let total = end.epoch_seconds - start.epoch_seconds;
        let mut calls = 0.0;
        for offset in 0..total {
            calls += self.lambda_cpm_at(start.add_seconds(offset)) / 60.0;
        }
        calls
    }
}

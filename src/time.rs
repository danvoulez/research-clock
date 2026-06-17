use std::{fmt, str::FromStr};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct UtcInstant {
    pub epoch_seconds: i64,
}

impl UtcInstant {
    pub fn parse(value: &str) -> crate::Result<Self> {
        value.parse()
    }
    pub fn add_seconds(self, seconds: i64) -> Self {
        Self {
            epoch_seconds: self.epoch_seconds + seconds,
        }
    }
    pub fn min(self, other: Self) -> Self {
        if self <= other {
            self
        } else {
            other
        }
    }
    pub fn to_rfc3339(self) -> String {
        let (y, m, d, hh, mm, ss) = civil_from_epoch(self.epoch_seconds);
        format!("{y:04}-{m:02}-{d:02}T{hh:02}:{mm:02}:{ss:02}Z")
    }
}

impl fmt::Display for UtcInstant {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.to_rfc3339())
    }
}

impl FromStr for UtcInstant {
    type Err = Box<dyn std::error::Error + Send + Sync>;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if !s.ends_with('Z') {
            return Err("UTC instant must end with Z".into());
        }
        let s = &s[..s.len() - 1];
        let (date, time) = s.split_once('T').ok_or("UTC instant must contain T")?;
        let mut d = date.split('-');
        let y: i32 = d.next().ok_or("missing year")?.parse()?;
        let m: u32 = d.next().ok_or("missing month")?.parse()?;
        let day: u32 = d.next().ok_or("missing day")?.parse()?;
        let mut t = time.split(':');
        let hh: u32 = t.next().ok_or("missing hour")?.parse()?;
        let mm: u32 = t.next().ok_or("missing minute")?.parse()?;
        let ss: u32 = t.next().ok_or("missing second")?.parse()?;
        if !(1..=12).contains(&m) || !(1..=31).contains(&day) || hh > 23 || mm > 59 || ss > 60 {
            return Err("invalid UTC instant fields".into());
        }
        Ok(Self {
            epoch_seconds: epoch_from_civil(y, m, day, hh, mm, ss),
        })
    }
}

fn epoch_from_civil(y: i32, m: u32, d: u32, hh: u32, mm: u32, ss: u32) -> i64 {
    let y = y as i64 - (m <= 2) as i64;
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = y - era * 400;
    let mp = m as i64 + if m > 2 { -3 } else { 9 };
    let doy = (153 * mp + 2) / 5 + d as i64 - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    let days = era * 146097 + doe - 719468;
    days * 86400 + hh as i64 * 3600 + mm as i64 * 60 + ss as i64
}

fn civil_from_epoch(epoch: i64) -> (i32, u32, u32, u32, u32, u32) {
    let days = epoch.div_euclid(86400);
    let sod = epoch.rem_euclid(86400);
    let z = days + 719468;
    let era = if z >= 0 { z } else { z - 146096 } / 146097;
    let doe = z - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = mp + if mp < 10 { 3 } else { -9 };
    let y = y + (m <= 2) as i64;
    (
        (y as i32),
        m as u32,
        d as u32,
        (sod / 3600) as u32,
        ((sod % 3600) / 60) as u32,
        (sod % 60) as u32,
    )
}

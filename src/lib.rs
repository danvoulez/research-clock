//! Research Clock v0 production engine with no runtime dependency on model code in planner/dispatcher.

pub mod cli;
pub mod config;
pub mod dispatcher;
pub mod hash;
pub mod rate_law;
pub mod time;
pub mod worker;

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;

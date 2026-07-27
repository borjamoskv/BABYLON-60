#![no_std]

mod contract;
mod error;
mod events;
mod storage;
mod types;

pub use contract::TokenContract;
pub use error::TokenError;

#[cfg(test)]
mod test;

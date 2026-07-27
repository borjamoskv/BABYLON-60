// C5-REAL EXERGY CERTIFIED
//! Host backend implementations for offline and online proof generation.

mod offline;
pub use offline::OfflineHostBackend;

mod online;
pub use online::OnlineHostBackend;

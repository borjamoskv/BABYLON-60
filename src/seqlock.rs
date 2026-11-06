//! Compatibility functions over the shared atomic protocol.
use crate::manifest::SharedManifest;
/// Publish through the shared bounded writer protocol.
pub fn publish(m: &SharedManifest, epoch: u64, hash: &[u64; 4]) -> bool {
    m.publish(epoch, hash).is_ok()
}
/// Historical forensic reader; poison alone does not deny snapshot access.
#[must_use]
pub fn read(m: &SharedManifest) -> Option<(u64, [u64; 4])> {
    m.read_snapshot()
}

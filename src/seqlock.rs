// SPDX-License-Identifier: LicenseRef-Babylon60-Enterprise
// SPDX-FileCopyrightText: 2025-2026 Borja Fernández Angulo (borjamoskv)
//
// IP PROVENANCE & LINEAGE NOTICE:
// The author attributes the coherent snapshot protocol to work on SeqlockCell
// in `borjamoskv/axiom-0`. These wrappers call BABYLON-60's SharedManifest.
// See contracts/IP_PROVENANCE.md#seqlock-y-axiom-0 for the Git history.
// Sole copyright and full commercial relicensing rights are held 100% by Borja Fernández Angulo
// under `contracts/ENTERPRISE_LICENSE.md` with zero third-party license encumbrances.

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

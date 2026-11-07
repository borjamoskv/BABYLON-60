//! Export the real BABYLON confinement profile for the isolated FL-PKG-01 lab.
//! No runtime authority, biometric receipt, or broker mediation is fabricated.

use babylon60::omega_mediation::MacOsAgentConfinement;
use std::{env, fs, path::PathBuf};

#[test]
#[ignore = "explicit FL-PKG synthetic lab required; exports a profile, not a containment verdict"]
fn export_fl_pkg_profile() {
    let root = env::var_os("FL_PKG_LAB_ROOT").expect("FL_PKG_LAB_ROOT is required");
    if !cfg!(target_os = "macos") {
        panic!("FL-PKG-01 requires real macOS");
    }
    let root = PathBuf::from(root);
    assert!(root.is_absolute());
    assert!(root.join("FL_PKG_SYNTHETIC_LAB").is_file());
    let protected = root.join("protected");
    fs::create_dir_all(&protected).unwrap();
    let profile = MacOsAgentConfinement::new(&[&protected], None).to_seatbelt_profile();
    fs::write(root.join("babylon-current.sb"), profile).unwrap();
}

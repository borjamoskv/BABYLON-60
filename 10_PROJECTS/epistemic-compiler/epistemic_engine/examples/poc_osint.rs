use epistemic_engine::{epistemic, Inference, Transition};
use std::fs;
use std::path::PathBuf;

epistemic! {
    graph osint_investigation {
        SocialMediaScrape -> IdentityResolution [0.85];
        IdentityResolution -> MetadataCorrelation [0.95];
        MetadataCorrelation -> GeolocationPinpoint [0.90];
        GeolocationPinpoint -> PhysicalVerification [0.80];
        PhysicalVerification -> TargetAcquired [1.0];
    }
}

fn main() {
    println!("[OSINT] Initializing Target Resolution...");
    let evidence = Inference::<states::SocialMediaScrape>::new("Extracted EXIF data from public image".to_string(), 1.0);
    
    let step1: Inference<states::IdentityResolution> = evidence.apply();
    let step2: Inference<states::MetadataCorrelation> = step1.apply();
    let step3: Inference<states::GeolocationPinpoint> = step2.apply();
    let step4: Inference<states::PhysicalVerification> = step3.apply();
    let final_node: Inference<states::TargetAcquired> = step4.apply();
    
    println!("Final OSINT Target Confidence: {:.2}", final_node.confidence);

    let dot = states::CORTEX_SANEDRIN_DOT;
    let mut path = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".to_string()));
    path.push("target");
    let _ = fs::create_dir_all(&path);
    path.push("poc_osint.dot");
    fs::write(&path, dot).unwrap();
    println!("[OSINT] Emitido: {}", path.display());
}

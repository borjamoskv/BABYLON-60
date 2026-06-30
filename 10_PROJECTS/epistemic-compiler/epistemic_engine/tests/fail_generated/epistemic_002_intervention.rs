use epistemic_engine::epistemic;

epistemic! {
    graph invalid_intervention {
        Intervention FormatDrive -> Evidence DiskImage [1.0];
    }
}

fn main() {}

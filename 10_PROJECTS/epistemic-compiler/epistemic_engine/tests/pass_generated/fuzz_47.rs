use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_47 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N0;
    }
}

fn main() {}

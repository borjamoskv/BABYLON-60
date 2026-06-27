use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_40 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N1;
N5 -> N2;
N6 -> N4;
    }
}

fn main() {}

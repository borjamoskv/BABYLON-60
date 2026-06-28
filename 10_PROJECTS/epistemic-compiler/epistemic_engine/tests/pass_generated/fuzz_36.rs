use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_36 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N1;
N5 -> N2;
N6 -> N4;
N7 -> N2;
    }
}

fn main() {}

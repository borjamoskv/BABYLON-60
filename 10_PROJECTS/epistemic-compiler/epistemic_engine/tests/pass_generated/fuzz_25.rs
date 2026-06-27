use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_25 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N0;
N6 -> N2;
N7 -> N2;
N8 -> N5;
N9 -> N0;
    }
}

fn main() {}

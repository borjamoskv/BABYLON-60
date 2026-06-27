use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_12 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N0;
N5 -> N4;
N6 -> N0;
N7 -> N6;
N8 -> N5;
N9 -> N4;
    }
}

fn main() {}

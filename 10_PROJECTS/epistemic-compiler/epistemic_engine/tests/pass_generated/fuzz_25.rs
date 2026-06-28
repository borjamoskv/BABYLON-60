use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_25 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N4;
N6 -> N3;
N7 -> N4;
N8 -> N0;
N9 -> N8;
N10 -> N5;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_16 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N3;
N5 -> N1;
N6 -> N5;
N7 -> N6;
N8 -> N1;
N9 -> N6;
N10 -> N9;
N11 -> N1;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_17 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N2;
N5 -> N4;
N6 -> N2;
N7 -> N4;
N8 -> N7;
N9 -> N3;
N10 -> N3;
N11 -> N2;
    }
}

fn main() {}

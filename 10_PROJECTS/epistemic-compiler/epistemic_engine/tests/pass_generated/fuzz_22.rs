use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_22 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N3;
N5 -> N3;
N6 -> N3;
N7 -> N6;
N8 -> N0;
N9 -> N6;
N10 -> N8;
N11 -> N2;
    }
}

fn main() {}

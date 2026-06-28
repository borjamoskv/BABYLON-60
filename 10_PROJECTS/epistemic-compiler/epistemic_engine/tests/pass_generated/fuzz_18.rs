use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_18 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N1;
N6 -> N0;
N7 -> N2;
N8 -> N1;
N9 -> N3;
N10 -> N8;
N11 -> N4;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_16 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N1;
N5 -> N1;
N6 -> N1;
N7 -> N6;
N8 -> N2;
N9 -> N5;
N10 -> N8;
N11 -> N2;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_8 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N1;
N6 -> N2;
N7 -> N4;
N8 -> N2;
N9 -> N2;
N10 -> N2;
N11 -> N7;
    }
}

fn main() {}

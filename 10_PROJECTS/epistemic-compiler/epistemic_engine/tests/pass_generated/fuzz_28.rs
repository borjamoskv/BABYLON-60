use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_28 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N3;
N5 -> N4;
N6 -> N1;
N7 -> N4;
N8 -> N1;
N9 -> N7;
N10 -> N4;
N11 -> N4;
N12 -> N1;
N13 -> N7;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_23 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N3;
N5 -> N3;
N6 -> N3;
N7 -> N4;
N8 -> N1;
N9 -> N1;
N10 -> N4;
N11 -> N2;
N12 -> N5;
N13 -> N7;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_34 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N1;
N5 -> N4;
N6 -> N1;
N7 -> N0;
N8 -> N2;
N9 -> N1;
N10 -> N9;
N11 -> N7;
N12 -> N6;
N13 -> N9;
N14 -> N4;
    }
}

fn main() {}

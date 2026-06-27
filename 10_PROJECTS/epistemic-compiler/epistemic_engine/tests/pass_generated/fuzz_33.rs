use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_33 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N2;
N5 -> N0;
N6 -> N2;
N7 -> N1;
N8 -> N1;
N9 -> N4;
N10 -> N5;
N11 -> N9;
N12 -> N3;
N13 -> N7;
    }
}

fn main() {}

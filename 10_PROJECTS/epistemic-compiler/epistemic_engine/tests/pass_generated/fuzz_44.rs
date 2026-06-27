use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_44 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N2;
N5 -> N0;
N6 -> N1;
N7 -> N6;
N8 -> N1;
N9 -> N4;
N10 -> N3;
N11 -> N5;
N12 -> N3;
N13 -> N7;
N14 -> N12;
    }
}

fn main() {}

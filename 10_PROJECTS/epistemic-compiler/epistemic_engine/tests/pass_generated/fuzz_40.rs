use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_40 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N1;
N5 -> N2;
N6 -> N0;
N7 -> N4;
N8 -> N5;
N9 -> N8;
N10 -> N0;
N11 -> N2;
N12 -> N7;
N13 -> N10;
N14 -> N6;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_28 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N4;
N6 -> N0;
N7 -> N3;
N8 -> N7;
N9 -> N5;
N10 -> N9;
N11 -> N4;
N12 -> N10;
    }
}

fn main() {}

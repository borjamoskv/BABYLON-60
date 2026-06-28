use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_23 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N4;
N6 -> N0;
N7 -> N1;
N8 -> N4;
N9 -> N5;
N10 -> N8;
N11 -> N3;
N12 -> N10;
    }
}

fn main() {}

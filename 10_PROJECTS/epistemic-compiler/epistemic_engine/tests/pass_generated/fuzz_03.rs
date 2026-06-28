use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_3 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N1;
N5 -> N4;
N6 -> N1;
N7 -> N3;
N8 -> N4;
N9 -> N1;
N10 -> N8;
N11 -> N9;
N12 -> N11;
    }
}

fn main() {}

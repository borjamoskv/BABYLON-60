use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_5 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N2;
N5 -> N2;
N6 -> N5;
N7 -> N1;
N8 -> N7;
N9 -> N5;
N10 -> N1;
N11 -> N0;
N12 -> N8;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_41 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N2;
N5 -> N1;
N6 -> N1;
N7 -> N1;
N8 -> N7;
N9 -> N6;
N10 -> N0;
N11 -> N1;
N12 -> N8;
N13 -> N12;
    }
}

fn main() {}

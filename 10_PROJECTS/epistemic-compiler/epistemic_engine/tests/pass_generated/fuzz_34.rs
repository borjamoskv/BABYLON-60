use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_34 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N0;
N5 -> N4;
N6 -> N4;
N7 -> N3;
N8 -> N7;
N9 -> N3;
N10 -> N2;
N11 -> N1;
N12 -> N2;
    }
}

fn main() {}

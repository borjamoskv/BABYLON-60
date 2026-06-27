use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_38 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N4;
N6 -> N3;
N7 -> N0;
N8 -> N3;
N9 -> N5;
N10 -> N7;
N11 -> N6;
N12 -> N11;
    }
}

fn main() {}

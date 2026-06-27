use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_24 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N0;
N5 -> N4;
N6 -> N5;
N7 -> N2;
N8 -> N0;
N9 -> N5;
N10 -> N6;
N11 -> N7;
N12 -> N8;
    }
}

fn main() {}

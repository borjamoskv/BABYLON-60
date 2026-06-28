use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_24 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N3;
N6 -> N4;
N7 -> N1;
N8 -> N0;
N9 -> N0;
N10 -> N7;
N11 -> N9;
N12 -> N3;
N13 -> N2;
    }
}

fn main() {}

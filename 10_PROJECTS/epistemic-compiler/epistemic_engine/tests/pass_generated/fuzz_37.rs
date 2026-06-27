use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_37 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N3;
N5 -> N4;
N6 -> N1;
N7 -> N2;
N8 -> N7;
N9 -> N3;
N10 -> N2;
N11 -> N7;
N12 -> N10;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_18 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N0;
N6 -> N2;
N7 -> N2;
N8 -> N2;
N9 -> N5;
N10 -> N3;
N11 -> N2;
N12 -> N0;
    }
}

fn main() {}

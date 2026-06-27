use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_22 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N1;
N6 -> N1;
N7 -> N2;
N8 -> N4;
N9 -> N2;
N10 -> N1;
N11 -> N1;
N12 -> N6;
N13 -> N1;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_15 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N1;
N6 -> N1;
N7 -> N5;
N8 -> N4;
N9 -> N1;
N10 -> N5;
N11 -> N0;
N12 -> N5;
N13 -> N8;
    }
}

fn main() {}

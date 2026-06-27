use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_6 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N1;
N5 -> N2;
N6 -> N0;
N7 -> N5;
N8 -> N2;
N9 -> N4;
N10 -> N8;
N11 -> N8;
    }
}

fn main() {}

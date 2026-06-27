use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_32 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N0;
N5 -> N1;
N6 -> N4;
N7 -> N6;
N8 -> N0;
N9 -> N6;
N10 -> N1;
N11 -> N8;
    }
}

fn main() {}

use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_46 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N2;
N5 -> N1;
N6 -> N5;
N7 -> N1;
N8 -> N6;
N9 -> N2;
N10 -> N3;
    }
}

fn main() {}

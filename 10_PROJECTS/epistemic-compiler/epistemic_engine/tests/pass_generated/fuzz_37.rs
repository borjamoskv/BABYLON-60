use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_37 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N1;
N6 -> N3;
N7 -> N0;
N8 -> N4;
N9 -> N3;
N10 -> N1;
    }
}

fn main() {}

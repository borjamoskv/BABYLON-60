use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_30 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N0;
N5 -> N4;
N6 -> N0;
N7 -> N4;
N8 -> N3;
N9 -> N5;
N10 -> N9;
N11 -> N0;
N12 -> N1;
N13 -> N2;
    }
}

fn main() {}

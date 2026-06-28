use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_5 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N0;
N6 -> N5;
N7 -> N3;
N8 -> N5;
N9 -> N0;
N10 -> N1;
N11 -> N2;
N12 -> N1;
N13 -> N1;
    }
}

fn main() {}

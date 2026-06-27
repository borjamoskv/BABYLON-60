use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_20 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N1;
N6 -> N3;
N7 -> N6;
N8 -> N2;
N9 -> N2;
N10 -> N6;
N11 -> N5;
N12 -> N5;
N13 -> N5;
    }
}

fn main() {}

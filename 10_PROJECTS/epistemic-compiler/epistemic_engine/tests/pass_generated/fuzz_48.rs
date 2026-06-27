use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_48 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N3;
N5 -> N4;
N6 -> N0;
N7 -> N4;
N8 -> N6;
N9 -> N3;
N10 -> N5;
N11 -> N2;
N12 -> N3;
N13 -> N5;
    }
}

fn main() {}

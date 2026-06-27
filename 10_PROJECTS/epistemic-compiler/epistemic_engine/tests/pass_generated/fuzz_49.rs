use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_49 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N2;
N5 -> N1;
N6 -> N4;
N7 -> N5;
N8 -> N5;
N9 -> N4;
N10 -> N5;
N11 -> N10;
N12 -> N5;
N13 -> N1;
    }
}

fn main() {}

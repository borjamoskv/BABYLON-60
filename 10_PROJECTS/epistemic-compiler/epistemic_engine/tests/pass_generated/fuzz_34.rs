use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_34 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N3;
N5 -> N3;
N6 -> N0;
N7 -> N6;
N8 -> N7;
N9 -> N0;
N10 -> N1;
N11 -> N1;
N12 -> N2;
N13 -> N10;
    }
}

fn main() {}

from cortex.compiled_theorem import synthesized_theorem_0

def test_synthesized_theorem_0() -> None:
    res = synthesized_theorem_0(2)
    assert res == 4
    res_zero = synthesized_theorem_0(0)
    assert res_zero == 0

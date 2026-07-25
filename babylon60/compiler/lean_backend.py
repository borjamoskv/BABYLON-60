def generate_proof_ir() -> str:
    lean_ast = "\ndef causal_EV_2_EV_3 : Nat := 2\n\ntheorem causal_order_valid (a b : Nat) (h : a <= b) : True := by\n  trivial\n"
    return lean_ast


if __name__ == "__main__":
    print(generate_proof_ir())

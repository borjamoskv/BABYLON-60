from z3 import *

def verify_unstoppable_invariant():
    print("--- [C5-REAL] Formal Verification: DVDEFI Unstoppable ---")
    
    # State variables
    pool_balance = Int('pool_balance')
    actual_token_balance = Int('actual_token_balance')
    
    # Invariant: The internal accounting must match the actual balance
    invariant = (pool_balance == actual_token_balance)
    
    # Pre-condition: System starts in a valid state
    s = Solver()
    s.add(pool_balance >= 0)
    s.add(actual_token_balance >= 0)
    s.add(invariant)
    
    # Action: Direct Transfer (External influence not tracked by internal state)
    transfer_amount = Int('transfer_amount')
    s.add(transfer_amount > 0)
    
    # New state after direct transfer
    pool_balance_new = pool_balance
    actual_token_balance_new = actual_token_balance + transfer_amount
    
    # Question: Is the invariant broken?
    invariant_broken = (pool_balance_new != actual_token_balance_new)
    
    # Check if a state exists where the invariant is broken
    s.push()
    s.add(invariant_broken)
    
    if s.check() == sat:
        m = s.model()
        print("[!] INVARIANT BROKEN DETECTED")
        print(f"    Initial Pool Balance: {m[pool_balance]}")
        print(f"    Initial Actual Balance: {m[actual_token_balance]}")
        print(f"    Direct Transfer Amount: {m[transfer_amount]}")
        print(f"    Resulting Pool Balance: {m.evaluate(pool_balance_new)}")
        print(f"    Resulting Actual Balance: {m.evaluate(actual_token_balance_new)}")
        print("--- VERIFICATION: FAIL (Vulnerability Confirmed) ---")
    else:
        print("[+] INVARIANT HOLDS")
        print("--- VERIFICATION: PASS ---")
    
    s.pop()

if __name__ == "__main__":
    try:
        verify_unstoppable_invariant()
    except ImportError:
        print("Error: z3-solver not found. Run 'pip install z3-solver'")

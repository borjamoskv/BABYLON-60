import z3

def prove_dlmm_vulnerabilities():
    print("=== CORTEX: Anvil-Lang Z3 Formal Verification for BitFlow DLMM ===")
    
    # 1. Z3 Variables Setup
    x_amount = z3.BitVec('x_amount', 128)
    y_amount = z3.BitVec('y_amount', 128)
    bin_price = z3.BitVec('bin_price', 128)
    PRICE_SCALE_BPS = z3.BitVecVal(100000000, 128)
    
    x_balance = z3.BitVec('x_balance', 128)
    y_balance = z3.BitVec('y_balance', 128)
    bin_shares = z3.BitVec('bin_shares', 128)

    # Functions based on dlmm-core-v-1-1.clar
    def get_liquidity_value(x, y, price):
        return (price * x) + (y * PRICE_SCALE_BPS)
    
    # Calculate values
    add_liquidity_value = get_liquidity_value(x_amount, y_amount, bin_price)
    bin_liquidity_value = get_liquidity_value(x_balance, y_balance, bin_price)
    
    # Intended DLP calculation (without fee deductions for simplicity of invariant proof)
    # dlp = (/ (* add-liquidity-value bin-shares) bin-liquidity-value)
    dlp = z3.UDiv((add_liquidity_value * bin_shares), bin_liquidity_value)

    # Invariant: If user deposits value > 0 and pool has liquidity, DLP minted should not be 0
    # unless the deposit is truly dust. If it's a significant percentage, it should mint something.
    
    # We look for a state where user deposits tokens, but receives 0 shares,
    # yet the token value is "significant" (e.g. they deposit 10% of the pool value but get 0 shares? No, that's impossible).
    # But wait, what if `add_liquidity_value * bin_shares < bin_liquidity_value`?
    # Then `dlp == 0`.
    
    solver = z3.Solver()
    
    # Constraints
    solver.add(bin_shares > 0)
    solver.add(bin_liquidity_value > 0)
    solver.add(x_amount > 0)
    solver.add(y_amount > 0)
    solver.add(bin_price > 0)
    
    # Vulnerability Condition: Minting 0 shares while depositing actual tokens
    solver.add(dlp == 0)
    
    # We want the deposit to be somewhat large compared to total shares, but due to manipulation, it rounds to 0.
    # What if bin_shares is 1? 
    # If bin_shares = 1, then ANY add_liquidity_value < bin_liquidity_value will yield 0 shares.
    # So an attacker can deposit 99% of the pool's value and receive 0 shares!
    
    solver.add(bin_shares == 1)
    solver.add(add_liquidity_value > 0)
    
    # To maximize the loss, we maximize add_liquidity_value while keeping dlp == 0
    # Let's just find a model.
    if solver.check() == z3.sat:
        model = solver.model()
        print("\n[!] VULNERABILITY FOUND: Zero-Share Dilution Attack")
        print("Conditions where user deposits value but receives 0 DLP shares:")
        print(f"bin_shares: {model[bin_shares]}")
        print(f"bin_price: {model[bin_price]}")
        print(f"Pool Balances -> x_balance: {model[x_balance]}, y_balance: {model[y_balance]}")
        print(f"User Deposits -> x_amount: {model[x_amount]}, y_amount: {model[y_amount]}")
        
        pool_val = get_liquidity_value(model[x_balance].as_long(), model[y_balance].as_long(), model[bin_price].as_long())
        user_val = get_liquidity_value(model[x_amount].as_long(), model[y_amount].as_long(), model[bin_price].as_long())
        
        print(f"Total Pool Liquidity Value: {pool_val}")
        print(f"User Added Liquidity Value: {user_val}")
        print("Minted DLP Shares: 0")
        print(f"Value Lost Percentage: {(user_val / pool_val) * 100:.2f}% of pool size can be donated without minting shares.")
    else:
        print("\nNo vulnerability found for Zero-Share Dilution.")

    # 2. Attack Vector: The Attacker exploits this
    # An attacker creates a bin, mints 1 share (or burns down to 1 share).
    # Then normal users deposit into this bin, their `add_liquidity_value` might be < `bin_liquidity_value`
    # and they get 0 shares. The attacker's 1 share now claims all their deposited tokens.
    
    print("\n[+] Generating Immunefi PoC Structural Outline...")
    poc = """
## Immunefi Bug Report: DLMM Bin Share Inflation (Inflation Attack)

**Target:** `dlmm-core-v-1-1.clar`
**Function:** `add-liquidity`

**Vulnerability:**
Because the DLP minting formula uses `(/ (* add-liquidity-value bin-shares) bin-liquidity-value)`, if `bin-shares` is extremely small (e.g., 1), any user depositing liquidity where `add-liquidity-value < bin-liquidity-value` will receive `0` shares due to integer truncation.

**Exploit Vector:**
1. Attacker creates a new bin (or finds an empty one).
2. Attacker deposits a tiny amount of liquidity, receiving `X` shares.
3. Attacker withdraws liquidity until exactly `1` share remains.
4. Attacker directly transfers a large amount of `token-x` and `token-y` to the pool contract, artificially inflating `bin-liquidity-value` without minting new shares.
5. A victim calls `add-liquidity`. Because `bin-liquidity-value` is massive and `bin-shares` is 1, the formula `(add_liquidity_value * 1) / huge_number` rounds to 0.
6. The victim's tokens are added to the pool balances, but they receive 0 shares.
7. The attacker calls `withdraw-liquidity` with their 1 share, claiming 100% of the pool's tokens, stealing the victim's deposit.
    """
    print(poc)

if __name__ == "__main__":
    prove_dlmm_vulnerabilities()

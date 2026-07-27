import math
from decimal import getcontext

# Set precision for decimal math to mirror Solidity/Clarity uint behavior
getcontext().prec = 60

PRICE_SCALE_BPS = 100000000
FEE_SCALE_BPS = 10000

def get_liquidity_value(x_amount, y_amount, bin_price):
    """
    (ok (+ (* bin-price x-amount) (* y-amount PRICE_SCALE_BPS)))
    """
    return (bin_price * x_amount) + (y_amount * PRICE_SCALE_BPS)

def sqrti(n):
    """Clarity sqrti implementation (integer square root)"""
    if n == 0: return 0
    return int(math.isqrt(n))

def calculate_dlp(add_liquidity_value, bin_shares, bin_liquidity_value):
    """
    (dlp (if (or (is-eq bin-shares u0) (is-eq bin-liquidity-value u0))
						 (sqrti add-liquidity-value)
						 (/ (* add-liquidity-value bin-shares) bin-liquidity-value)))
    """
    if bin_shares == 0 or bin_liquidity_value == 0:
        return sqrti(add_liquidity_value)
    else:
        return (add_liquidity_value * bin_shares) // bin_liquidity_value

def calculate_withdraw(amount_to_burn, balance, bin_shares):
    """
    (x-amount (/ (* amount x-balance) bin-shares))
    (y-amount (/ (* amount y-balance) bin-shares))
    """
    return (amount_to_burn * balance) // bin_shares

def audit_rounding_asymmetry():
    print("--- Auditing Rounding Asymmetry ---")
    
    # Case 1: Minimal Liquidity Addition
    bin_price = 50000000 # 0.5 ratio
    x_add = 1000
    y_add = 0
    
    val = get_liquidity_value(x_add, y_add, bin_price)
    shares = calculate_dlp(val, 0, 0)
    
    print(f"Initial: x={x_add}, y={y_add}, price={bin_price}")
    print(f"Liquidity Value: {val}")
    print(f"Shares Minted: {shares}")
    
    # Case 2: Immediate Withdrawal
    x_out = calculate_withdraw(shares, x_add, shares)
    y_out = calculate_withdraw(shares, y_add, shares)
    
    print(f"Withdraw: x={x_out}, y={y_out}")
    
    if x_out < x_add or y_out < y_add:
        print(f"LOSS DETECTED: x_loss={x_add - x_out}, y_loss={y_add - y_out}")
    else:
        print("No immediate loss.")

    # Case 3: Precision Loss in Multi-step
    # Small deposits in empty bin
    x_dep = 1
    val_dep = get_liquidity_value(x_dep, 0, bin_price)
    shares_dep = calculate_dlp(val_dep, 0, 0)
    print(f"\nSmall Deposit x={x_dep} -> Shares={shares_dep}")
    
    # If shares_dep is 0, user loses everything.
    # val_dep = 50000000 * 1 = 50,000,000
    # sqrt(50,000,000) = 7071
    
    # Case 4: Rounding Down in Withdraw
    # Deposit 1,000,001. Shares minted.
    # Another user deposits.
    # Total shares increases.
    # Withdraw 1 share.
    
    x_pool = 1000000
    y_pool = 1000000
    total_shares = calculate_dlp(get_liquidity_value(x_pool, y_pool, bin_price), 0, 0)
    
    # User withdraws 1 share
    x_withdraw_1 = calculate_withdraw(1, x_pool, total_shares)
    y_withdraw_1 = calculate_withdraw(1, y_pool, total_shares)
    
    print(f"\nPool: x={x_pool}, y={y_pool}, Total Shares={total_shares}")
    print(f"Withdraw 1 share -> x={x_withdraw_1}, y={y_withdraw_1}")
    
    if x_withdraw_1 == 0 and y_withdraw_1 == 0:
        print("Invariance Violation: User burned 1 share for 0 assets.")

if __name__ == "__main__":
    audit_rounding_asymmetry()

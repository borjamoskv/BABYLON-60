import math

PRICE_SCALE_BPS = 100000000
FEE_SCALE_BPS = 10000

def get_liquidity_value(x_amount, y_amount, bin_price):
    return (bin_price * x_amount) + (y_amount * PRICE_SCALE_BPS)

def sqrti(n):
    if n == 0: return 0
    return int(math.isqrt(n))

def audit_fees():
    print("--- Auditing Fee Logic ---")
    
    # Active bin fee logic
    x_balance = 10**12 # 1M tokens with 6 decimals
    y_balance = 10**12
    bin_shares = 10**12
    bin_price = 10**8 # 1:1 price
    
    x_add = 10**6
    y_add = 0
    
    # Fees in BPS
    protocol_fee = 500 # 5%
    provider_fee = 500 # 5%
    variable_fee = 0
    total_fee_bps = protocol_fee + provider_fee + variable_fee
    
    # Step 1: Calculate dlp without fees
    val_add = get_liquidity_value(x_add, y_add, bin_price)
    val_bin = get_liquidity_value(x_balance, y_balance, bin_price)
    
    dlp = (val_add * bin_shares) // val_bin
    
    print(f"Adding x={x_add}, y={y_add} to pool x={x_balance}, y={y_balance}")
    print(f"Calculated dlp (no fees): {dlp}")
    
    # Step 2: Calculate withdrawable amounts
    # (x-amount-withdrawable (/ (* dlp (+ x-balance x-amount)) (+ bin-shares dlp)))
    x_withdrawable = (dlp * (x_balance + x_add)) // (bin_shares + dlp)
    y_withdrawable = (dlp * (y_balance + y_add)) // (bin_shares + dlp)
    
    print(f"x_withdrawable: {x_withdrawable}")
    print(f"y_withdrawable: {y_withdrawable}")
    
    # max-x-amount-fees-liquidity (if (and (> y-amount-withdrawable y-amount) (> x-amount x-amount-withdrawable))
    #                                (/ (* (- x-amount x-amount-withdrawable) x-liquidity-fee) FEE_SCALE_BPS)
    #                                u0)
    
    x_fee = 0
    y_fee = 0
    
    if y_withdrawable > y_add and x_add > x_withdrawable:
        x_fee = ((x_add - x_withdrawable) * total_fee_bps) // FEE_SCALE_BPS
        print(f"X Fee triggered: {x_fee}")
    
    if x_withdrawable > x_add and y_add > y_withdrawable:
        y_fee = ((y_add - y_withdrawable) * total_fee_bps) // FEE_SCALE_BPS
        print(f"Y Fee triggered: {y_fee}")

    print(f"Final Fees: x={x_fee}, y={y_fee}")

if __name__ == "__main__":
    audit_fees()

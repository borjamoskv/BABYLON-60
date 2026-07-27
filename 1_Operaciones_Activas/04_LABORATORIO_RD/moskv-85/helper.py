# MOSKV-85 Developer Helper Utility
# Creator: Borja Moskv
# Reality Level: C5-REAL

import sys

ALPHABET = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstu"

def encode_b85(val, width=5):
    # Handle negative numbers by converting to unsigned representation
    if val < 0:
        if width == 5:
            val += 0x100000000
        else:
            val += 0x10000000000000000
            
    chars = []
    for _ in range(width):
        chars.append(ALPHABET[val % 85])
        val //= 85
    return "".join(reversed(chars))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python helper.py <integer> [width=5]")
        sys.exit(1)
    try:
        val = int(sys.argv[1])
        width = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        encoded = encode_b85(val, width)
        prefix = "#" if width == 5 else "$"
        print(f"Decimal: {val}")
        print(f"Base-85 representation: {encoded}")
        print(f"MOSKV-85 code snippet: {prefix}{encoded}")
    except ValueError:
        print("Error: Input must be an integer.")

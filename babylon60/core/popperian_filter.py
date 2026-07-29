import sys
import math
import re
import argparse

# C4-SIM Corporate Buzzwords (Syntactic Holograms)
HYPE_PATTERNS = [
    r"game(\s|-)changer",
    r"100x",
    r"10x",
    r"passive income",
    r"synergy",
    r"disrupt(ive|ing)?",
    r"revolutionary",
    r"next(-|\s)?generation",
    r"paradigm shift",
    r"unpacking",
    r"delve",
]

HYPE_REGEX = re.compile(r'\b(' + '|'.join(HYPE_PATTERNS) + r')\b', re.IGNORECASE)

# Physical Anchors (URL, SHA256, hex hashes)
ANCHOR_REGEX = re.compile(r'(https?://[^\s]+|[a-f0-9]{64}|0x[a-f0-9]{40})', re.IGNORECASE)

def shannon_entropy(data: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not data:
        return 0.0
    
    entropy = 0.0
    length = len(data)
    
    # Calculate frequency of each character
    frequencies = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1
        
    # Calculate entropy
    for count in frequencies.values():
        prob = count / length
        entropy -= prob * math.log2(prob)
        
    return entropy

def evaluate_payload(text: str) -> bool:
    """
    Evaluates text against the Popperian Thermodynamic Filter.
    Returns True if passed (Exergy), False if rejected (Entropy).
    """
    # 1. Shannon Entropy Check
    entropy = shannon_entropy(text)
    if entropy < 2.0 or entropy > 6.0:
        print(f"[REJECTED] Shannon Entropy Out of Bounds: {entropy:.2f} (Allowed: 2.0 - 6.0)", file=sys.stderr)
        return False
        
    # 2. Hype Pattern Masking
    hype_matches = HYPE_REGEX.findall(text)
    if hype_matches:
        print(f"[REJECTED] Hype Patterns Detected (1-WL Failure): {hype_matches}", file=sys.stderr)
        return False
        
    # 3. Physical Anchor Requirement
    if len(text) > 120:
        if not ANCHOR_REGEX.search(text):
            print("[REJECTED] Missing Physical Anchor in long text (No URL or SHA256 found)", file=sys.stderr)
            return False
            
    print(f"[PASSED] Entropy: {entropy:.2f}. No hype detected. Anchors validated.", file=sys.stderr)
    return True

def main():
    parser = argparse.ArgumentParser(description="Popperian Falsification Filter (C5-REAL)")
    parser.add_argument("file", nargs="?", help="File to evaluate (reads from stdin if not provided)")
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"[ERROR] Could not read file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        content = sys.stdin.read()
        
    if not content.strip():
        print("[ERROR] Empty payload.", file=sys.stderr)
        sys.exit(1)
        
    passed = evaluate_payload(content)
    
    # Emit sanitized content to stdout if passed, otherwise return error code
    if passed:
        print(content)
        sys.exit(0)
    else:
        sys.exit(2) # Fallo epistemológico

if __name__ == "__main__":
    main()

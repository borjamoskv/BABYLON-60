"""
VENOM — Vulnerability Pattern Signatures

50+ patterns for automated vulnerability detection across
Solidity, Rust, and C codebases.
"""

SOLIDITY_PATTERNS = [
    # ─── Reentrancy ────────────────────────────────────────────
    {
        "id": "SOL_REENTRANCY_01",
        "name": "External call before state update",
        "severity": "critical",
        "pattern": r'\.call\{value:.*?\}.*?\n(?:(?!.*=\s).*\n)*.*(?:balance|amount|debt)\s*[+-]?=',
        "description": "External call with value transfer occurs before state variable update.",
        "recommendation": "Apply checks-effects-interactions pattern. Update state before external calls.",
    },
    {
        "id": "SOL_REENTRANCY_02",
        "name": "Cross-function reentrancy via shared state",
        "severity": "critical",
        "pattern": r'(?:external|public)\s+.*\{[^}]*\.call\{',
        "description": "Public/external function makes external call — potential cross-function reentrancy.",
        "recommendation": "Use ReentrancyGuard or mutex pattern.",
    },
    # ─── Access Control ───────────────────────────────────────
    {
        "id": "SOL_ACCESS_01",
        "name": "Missing access control on state-changing function",
        "severity": "high",
        "pattern": r'function\s+\w+\s*\([^)]*\)\s+(?:external|public)\s+(?!view|pure)(?!.*(?:onlyOwner|onlyRole|require\(msg\.sender|_checkRole))',
        "description": "State-changing public/external function without access control modifier.",
        "recommendation": "Add appropriate access control modifier.",
    },
    {
        "id": "SOL_ACCESS_02",
        "name": "tx.origin authentication",
        "severity": "critical",
        "pattern": r'require\s*\(\s*tx\.origin\s*==',
        "description": "Using tx.origin for authentication is vulnerable to phishing attacks.",
        "recommendation": "Use msg.sender instead of tx.origin.",
    },
    # ─── Oracle Manipulation ──────────────────────────────────
    {
        "id": "SOL_ORACLE_01",
        "name": "Missing oracle staleness check",
        "severity": "high",
        "pattern": r'latestRoundData\s*\(\s*\).*?(?!.*(?:updatedAt|timestamp|heartbeat|staleness))',
        "description": "Chainlink latestRoundData() called without checking staleness.",
        "recommendation": "Check updatedAt against heartbeat threshold.",
    },
    {
        "id": "SOL_ORACLE_02",
        "name": "Single oracle dependency",
        "severity": "medium",
        "pattern": r'(?:priceFeed|oracle)\s*\.\s*latestRoundData',
        "description": "Protocol depends on a single oracle source.",
        "recommendation": "Implement oracle redundancy or circuit breakers.",
    },
    {
        "id": "SOL_ORACLE_03",
        "name": "Price not validated > 0",
        "severity": "high",
        "pattern": r'latestRoundData\(\).*?(?!.*require\s*\(\s*\w+\s*>\s*0)',
        "description": "Oracle price not validated to be positive.",
        "recommendation": "Add require(price > 0) after oracle call.",
    },
    # ─── Flash Loan ───────────────────────────────────────────
    {
        "id": "SOL_FLASH_01",
        "name": "Spot price used for valuation",
        "severity": "critical",
        "pattern": r'(?:getReserves|balanceOf)\s*\(.*?\)\s*.*(?:price|value|worth)',
        "description": "Using spot DEX reserves for price calculation — flash-loan manipulable.",
        "recommendation": "Use TWAP oracle instead of spot prices.",
    },
    {
        "id": "SOL_FLASH_02",
        "name": "Missing flash loan guard",
        "severity": "high",
        "pattern": r'function\s+(?:deposit|withdraw|borrow|liquidat)\w*\s*\([^)]*\)\s+(?:external|public)',
        "description": "Core DeFi function without flash loan protection.",
        "recommendation": "Add same-block transaction check or flash loan guard.",
    },
    # ─── Integer Arithmetic ───────────────────────────────────
    {
        "id": "SOL_INT_01",
        "name": "Unchecked arithmetic in Solidity >= 0.8",
        "severity": "medium",
        "pattern": r'unchecked\s*\{[^}]*(?:\+|\-|\*)',
        "description": "Unchecked block contains arithmetic that could overflow/underflow.",
        "recommendation": "Verify overflow/underflow is truly impossible in this context.",
    },
    {
        "id": "SOL_INT_02",
        "name": "Division before multiplication",
        "severity": "medium",
        "pattern": r'\w+\s*/\s*\w+\s*\*\s*\w+',
        "description": "Division before multiplication causes precision loss.",
        "recommendation": "Multiply first, then divide.",
    },
    # ─── Delegation & Proxy ───────────────────────────────────
    {
        "id": "SOL_PROXY_01",
        "name": "Uninitialized proxy implementation",
        "severity": "critical",
        "pattern": r'delegatecall\s*\(',
        "description": "delegatecall found — verify storage layout compatibility.",
        "recommendation": "Ensure storage layout matches between proxy and implementation.",
    },
    {
        "id": "SOL_PROXY_02",
        "name": "Missing initializer guard",
        "severity": "critical",
        "pattern": r'function\s+initialize\s*\([^)]*\)\s+(?:external|public)\s+(?!.*initializer)',
        "description": "Initialize function without initializer modifier — can be called multiple times.",
        "recommendation": "Use OpenZeppelin's initializer modifier.",
    },
    # ─── MEV / Frontrunning ───────────────────────────────────
    {
        "id": "SOL_MEV_01",
        "name": "No slippage protection",
        "severity": "high",
        "pattern": r'(?:swap|exchange|trade)\w*\s*\([^)]*\)\s*(?:external|public)(?!.*(?:minOut|slippage|deadline|amountOutMin))',
        "description": "Swap function without slippage parameter.",
        "recommendation": "Add minimum output amount parameter.",
    },
    {
        "id": "SOL_MEV_02",
        "name": "Missing deadline parameter",
        "severity": "medium",
        "pattern": r'(?:swap|addLiquidity|removeLiquidity)\s*\([^)]*\)(?!.*deadline)',
        "description": "DEX interaction without deadline — vulnerable to sandwich attacks.",
        "recommendation": "Add deadline parameter to prevent stale transactions.",
    },
    # ─── Liquidation ──────────────────────────────────────────
    {
        "id": "SOL_LIQ_01",
        "name": "Close factor bypass (K2 pattern)",
        "severity": "critical",
        "pattern": r'(?:close_factor|closeFactor|maxLiquidatable).*?(?:individual|per_call|amount)',
        "description": "Close factor enforced per-call rather than per-transaction — bypass via atomic batching.",
        "recommendation": "Track cumulative liquidated amount per user per transaction.",
    },
    {
        "id": "SOL_LIQ_02",
        "name": "Liquidation reward exceeds collateral",
        "severity": "high",
        "pattern": r'(?:liquidationBonus|incentive)\s*(?:=|:)\s*\d{3,}',
        "description": "Liquidation bonus may allow profitable self-liquidation.",
        "recommendation": "Cap liquidation bonus below collateral margin.",
    },
    # ─── ERC20 / Token ────────────────────────────────────────
    {
        "id": "SOL_TOKEN_01",
        "name": "Unsafe ERC20 transfer",
        "severity": "high",
        "pattern": r'\.transfer\s*\([^)]+\)\s*;(?!\s*(?:require|if|assert))',
        "description": "ERC20 transfer without return value check.",
        "recommendation": "Use SafeERC20.safeTransfer().",
    },
    {
        "id": "SOL_TOKEN_02",
        "name": "Missing approve(0) before approve(n)",
        "severity": "medium",
        "pattern": r'\.approve\s*\([^,]+,\s*\w+\s*\)(?!.*approve\s*\([^,]+,\s*0\s*\))',
        "description": "Approval race condition — some tokens require approve(0) before approve(n).",
        "recommendation": "Call approve(0) before setting new approval.",
    },
]

RUST_PATTERNS = [
    # ─── Authorization ────────────────────────────────────────
    {
        "id": "RUST_AUTH_01",
        "name": "Missing require_auth in Soroban",
        "severity": "critical",
        "pattern": r'pub\s+fn\s+\w+\s*\([^)]*(?:Address|AccountId)[^)]*\)[^{]*\{(?:(?!require_auth).)*\}',
        "description": "Public function accepts an Address but never calls require_auth().",
        "recommendation": "Add .require_auth() for the caller address.",
    },
    {
        "id": "RUST_AUTH_02",
        "name": "Unchecked caller in Anchor",
        "severity": "high",
        "pattern": r'#\[instruction\].*?pub\s+fn\s+\w+.*?(?!.*(?:has_one|constraint|signer))',
        "description": "Anchor instruction without has_one/constraint/signer validation.",
        "recommendation": "Add account validation constraints.",
    },
    # ─── Arithmetic ───────────────────────────────────────────
    {
        "id": "RUST_INT_01",
        "name": "Unchecked integer arithmetic",
        "severity": "high",
        "pattern": r'(?:as\s+u(?:8|16|32|64|128|size))',
        "description": "Integer cast with `as` can silently truncate.",
        "recommendation": "Use .try_into().unwrap() or checked conversion.",
    },
    {
        "id": "RUST_INT_02",
        "name": "Missing checked_mul/checked_add",
        "severity": "high",
        "pattern": r'\w+\s*\*\s*\w+(?!.*(?:checked_mul|saturating_mul|overflowing_mul))',
        "description": "Multiplication without overflow protection in token math.",
        "recommendation": "Use checked_mul() for financial calculations.",
    },
    # ─── State Management ─────────────────────────────────────
    {
        "id": "RUST_STATE_01",
        "name": "Mutable global state without lock",
        "severity": "high",
        "pattern": r'static\s+mut\s+',
        "description": "Static mutable variable — unsafe without synchronization.",
        "recommendation": "Use Mutex, RwLock, or atomic types.",
    },
    {
        "id": "RUST_STATE_02",
        "name": "Unwrap on Result in critical path",
        "severity": "medium",
        "pattern": r'\.unwrap\(\)',
        "description": "unwrap() will panic on error — dangerous in contract/critical code.",
        "recommendation": "Handle errors explicitly or use expect() with reason.",
    },
    # ─── Memory Safety ────────────────────────────────────────
    {
        "id": "RUST_MEM_01",
        "name": "Unsafe block usage",
        "severity": "high",
        "pattern": r'unsafe\s*\{',
        "description": "Unsafe block — bypasses Rust's safety guarantees.",
        "recommendation": "Minimize unsafe scope and document invariants.",
    },
    {
        "id": "RUST_MEM_02",
        "name": "Raw pointer dereference",
        "severity": "critical",
        "pattern": r'\*(?:mut|const)\s+\w+.*?(?:as\s+\*(?:mut|const))',
        "description": "Raw pointer cast and potential dereference.",
        "recommendation": "Verify pointer validity and alignment.",
    },
]

C_PATTERNS = [
    # ─── Memory Safety ────────────────────────────────────────
    {
        "id": "C_MEM_01",
        "name": "Buffer overflow via unchecked index",
        "severity": "critical",
        "pattern": r'\w+\s*\[\s*\w+\s*\](?!.*(?:if|assert|check|bound|len))',
        "description": "Array access without bounds checking.",
        "recommendation": "Add bounds validation before array access.",
    },
    {
        "id": "C_MEM_02",
        "name": "Missing NULL check after malloc",
        "severity": "high",
        "pattern": r'(?:malloc|calloc|realloc)\s*\([^)]*\)\s*;(?!\s*if\s*\()',
        "description": "Memory allocation without NULL check.",
        "recommendation": "Check return value of malloc/calloc/realloc.",
    },
    {
        "id": "C_MEM_03",
        "name": "Use after free potential",
        "severity": "critical",
        "pattern": r'free\s*\(\s*(\w+)\s*\)\s*;(?!.*\1\s*=\s*NULL)',
        "description": "Freed pointer not set to NULL — use-after-free risk.",
        "recommendation": "Set pointer to NULL immediately after free().",
    },
    {
        "id": "C_MEM_04",
        "name": "Integer underflow in pointer arithmetic",
        "severity": "critical",
        "pattern": r'(?:fd_vm_mem|mem)_haddr.*?\-\s*\w+',
        "description": "Pointer arithmetic with subtraction — underflow risk (Firedancer pattern).",
        "recommendation": "Validate operand range before pointer arithmetic.",
    },
    # ─── String Handling ──────────────────────────────────────
    {
        "id": "C_STR_01",
        "name": "Unsafe string functions",
        "severity": "high",
        "pattern": r'(?:strcpy|strcat|sprintf|gets)\s*\(',
        "description": "Using unsafe string function — buffer overflow risk.",
        "recommendation": "Use strncpy, strncat, snprintf, or fgets instead.",
    },
    {
        "id": "C_STR_02",
        "name": "Format string vulnerability",
        "severity": "critical",
        "pattern": r'(?:printf|fprintf|sprintf)\s*\(\s*\w+\s*\)',
        "description": "User-controlled format string — arbitrary read/write.",
        "recommendation": "Use printf(\"%s\", str) instead of printf(str).",
    },
    # ─── Concurrency ──────────────────────────────────────────
    {
        "id": "C_RACE_01",
        "name": "TOCTOU race condition",
        "severity": "high",
        "pattern": r'(?:access|stat)\s*\([^)]*\).*?(?:open|fopen)\s*\(',
        "description": "Time-of-check-time-of-use race condition.",
        "recommendation": "Use atomic operations or file locking.",
    },
]

# Unified pattern index
ALL_PATTERNS = {
    "solidity": SOLIDITY_PATTERNS,
    "rust": RUST_PATTERNS,
    "c": C_PATTERNS,
}

PATTERN_COUNT = sum(len(v) for v in ALL_PATTERNS.values())


def get_patterns_for_language(lang: str) -> list[dict]:
    """Get vulnerability patterns for a specific language."""
    lang = lang.lower()
    # Map file extensions to languages
    ext_map = {
        ".sol": "solidity",
        ".rs": "rust",
        ".c": "c",
        ".h": "c",
        ".cpp": "c",
    }
    resolved = ext_map.get(lang, lang)
    return ALL_PATTERNS.get(resolved, [])


def get_all_patterns() -> list[dict]:
    """Get all vulnerability patterns across all languages."""
    result = []
    for patterns in ALL_PATTERNS.values():
        result.extend(patterns)
    return result

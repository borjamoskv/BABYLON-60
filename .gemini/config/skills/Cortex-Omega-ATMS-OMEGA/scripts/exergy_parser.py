#!/usr/bin/env python3
import sys
import yaml
import re
import os
import json

# Session history file for stack-based contextual resolution (AX-III)
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_history.json")
MAX_HISTORY_DEPTH = 10

# Thermodynamic Stopwords (Anergy) - Precompiled for speed (Single-Pass execution)
ANERGY_REGEX = re.compile(
    r"\b(?:por favor|gracias|hola|creo que|me gustaría|podrías|si no te importa|quizás|tal vez|no sé|a lo mejor|te importa si|bueno|pues|oye)\b",
    re.IGNORECASE
)

# Precompiled stochastic markers
STOCHASTIC_REGEX = re.compile(
    r"\b(?:quizás|tal vez|no sé|a lo mejor|depende)\b",
    re.IGNORECASE
)

# Splitting clauses: match commas, semicolons, coordinating conjunctions, or periods that are NOT followed by letters/numbers
CLAUSE_SPLIT_REGEX = re.compile(
    r'(?:\s+y\s+|\s+o\s+|\s+pero\s+|[;,]|\.(?!\w))',
    re.IGNORECASE
)

# Rules to route actions to specific Swarm Daemons based on keywords
DAEMON_ROUTING_RULES = [
    (re.compile(r'\b(?:db|postgres|redis|sqlite|sql|mysql|mongo|database)\b', re.I), "Database Daemon"),
    (re.compile(r'\b(?:docker|colima|puerto|port|servidor|server|nginx|host)\b', re.I), "GHOST-1"),
    (re.compile(r'\b(?:git|commit|push|pull|branch|pr|github)\b', re.I), "Jules-Secretario"),
    (re.compile(r'\b(?:purge|anergy|dead code|cleanup|clean|delete|rm)\b', re.I), "LEA-Ω"),
    (re.compile(r'\b(?:test|pytest|vitest|eslint|lint|verify|audit)\b', re.I), "CORTEX-Guard"),
]

# Dynamic validation rules mapping action keywords to specific verification procedures
VALIDATION_ROUTING_RULES = [
    (re.compile(r'\b(?:db|postgres|redis|sqlite|sql|mysql|mongo|database)\b', re.I), "Verify query execution return (SELECT 1) or port bind verification"),
    (re.compile(r'\b(?:puerto|port)\b', re.I), "Verify port bound using `lsof -i :<port>` or socket connection probe"),
    (re.compile(r'\b(?:docker|colima|servidor|server|nginx|host)\b', re.I), "Verify system process runtime or container UP status"),
    (re.compile(r'\b(?:git|commit|push|pull|branch|pr|github)\b', re.I), "Verify git status clean / verify commit SHA on head"),
    (re.compile(r'\b(?:purge|anergy|dead code|cleanup|clean|delete|rm)\b', re.I), "Verify target files/variables purged or file deleted from filesystem"),
    (re.compile(r'\b(?:test|pytest|vitest|eslint|lint|verify|audit)\b', re.I), "Assert zero errors return code from linter/test runner"),
]

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data] # Upgrade old format
        except Exception:
            pass
    return []

def save_history(manifest: dict):
    try:
        history = load_history()
        history.append(manifest)
        # Prune to max depth
        if len(history) > MAX_HISTORY_DEPTH:
            history = history[-MAX_HISTORY_DEPTH:]
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def route_daemon(action: str) -> str:
    for pattern, daemon_name in DAEMON_ROUTING_RULES:
        if pattern.search(action):
            return daemon_name
    return "Swarm Agent"

def route_validation(action: str) -> str:
    for pattern, validation_desc in VALIDATION_ROUTING_RULES:
        if pattern.search(action):
            return validation_desc
    return "Cryptographic Hash or Hardware status verification"

def calculate_exergy(raw_text: str, cleaned_text: str) -> float:
    raw_tokens = len(raw_text.split())
    if raw_tokens == 0:
        return 0.0
    clean_tokens = len(cleaned_text.split())
    return round((clean_tokens / raw_tokens), 2)

def purge_anergy(raw_text: str) -> str:
    cleaned = ANERGY_REGEX.sub("", raw_text)
    return " ".join(cleaned.split())

def detect_amputation(raw_text: str) -> bool:
    return bool(STOCHASTIC_REGEX.search(raw_text))

def extract_directives(cleaned_text: str) -> list:
    clauses = CLAUSE_SPLIT_REGEX.split(cleaned_text)
    return [c.strip() for c in clauses if len(c.strip()) > 3]

def resolve_context(raw_text: str) -> str:
    """Resolves referring expressions utilizing stack history."""
    history = load_history()
    if not history:
        return raw_text

    # Resolve "hace dos pasos" / "ante-penúltimo" (-2)
    two_steps_ago_pattern = re.compile(r"\b(?:lo de hace dos pasos|el anterior al anterior|hace 2 pasos)\b", re.IGNORECASE)
    if two_steps_ago_pattern.search(raw_text) and len(history) >= 2:
        prev_directives = " y ".join(history[-2]["Directives_Extracted"])
        raw_text = two_steps_ago_pattern.sub(prev_directives, raw_text)

    # Resolve "último" / "lo anterior" (-1)
    last_step_pattern = re.compile(r"\b(?:lo anterior|lo de antes|el ultimo|el último|el paso anterior)\b", re.IGNORECASE)
    if last_step_pattern.search(raw_text) and len(history) >= 1:
        prev_directives = " y ".join(history[-1]["Directives_Extracted"])
        raw_text = last_step_pattern.sub(prev_directives, raw_text)
        
    return raw_text

def parse_order(raw_text: str):
    # Contextual Resolution Phase
    raw_text = resolve_context(raw_text)
    
    if detect_amputation(raw_text):
        return {
            "Manifest": "C5-REAL_AMPUTATION",
            "Reason": "Stochastic Intent Detected - Amputated by AX-VII",
            "Required_Input": "[Binary Choice / Strict Path]"
        }
        
    cleaned_text = purge_anergy(raw_text)
    exergy_rating = calculate_exergy(raw_text, cleaned_text)
    directives = extract_directives(cleaned_text)
    
    if exergy_rating < 0.20:
        return {
            "Manifest": "C5-REAL_AMPUTATION",
            "Reason": f"Critical Thermodynamic Failure (Exergy={exergy_rating}). Too much narrative smoke.",
            "Required_Input": "[Rewrite order without conversational padding]"
        }

    manifest = {
        "Manifest": "ORDER_CONSOLIDATION",
        "Reality_Level": "C5-REAL",
        "Exergy_Rating": exergy_rating,
        "Intent": " ".join(directives[:1]).capitalize() if directives else "Unclear intent",
        "Target_State": "Deterministic execution based on parsed directives",
        "Directives_Extracted": directives,
        "Execution_Topology": {
            f"Phase_{i+1}": {
                "Daemon": route_daemon(d),
                "Action": d.capitalize(),
                "Validation": route_validation(d)
            } for i, d in enumerate(directives)
        }
    }
    
    # Save successful manifest to session history
    save_history(manifest)
    
    return manifest

def run_interactive_loop():
    """Runs a continuous parse loop reading from stdin to prevent python VM startup latency."""
    print("ORDER-CONSOLIDATOR-Ω Daemon Active. Enter raw orders (Ctrl+D to exit):", file=sys.stderr)
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            result = parse_order(line)
            print("---")
            print(yaml.dump(result, sort_keys=False, default_flow_style=False).strip())
            print("---")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--daemon", "-d", "--interactive", "-i"):
        run_interactive_loop()
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python3 exergy_parser.py '<raw_order_text>' or use --daemon / -d")
        sys.exit(1)
        
    raw_order = sys.argv[1]
    result = parse_order(raw_order)
    
    print("---")
    print(yaml.dump(result, sort_keys=False, default_flow_style=False).strip())
    print("---")

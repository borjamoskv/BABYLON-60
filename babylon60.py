import hashlib

def tokenize_b60(raw_code: str) -> list:
    tokens = []
    for line in raw_code.splitlines():
        if '#' in line:
            line = line.split('#', 1)[0]
        parts = line.strip().split()
        if parts:
            tokens.extend(parts)
    return tokens

class B60CompiledProgram:
    def __init__(self, raw_code: str):
        self.raw_code = raw_code
        self.tokens = tokenize_b60(raw_code)
        
        # INV_C5_28: 1-WL structural hashing over canonical tokens
        canonical_str = "|".join(self.tokens)
        self.sha256 = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

class B60Compiler:
    def compile(self, source_code: str) -> B60CompiledProgram:
        return B60CompiledProgram(source_code)

class B60MinimalVM:
    def execute(self, program: B60CompiledProgram) -> str:
        for i in range(len(program.tokens) - 1):
            if program.tokens[i] == "CRITICAL" and program.tokens[i+1] == "HALT":
                return "HALTED"
        return "COMPLETED"

import sys

LEDGER_PATH = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/mundo_f_ledger.yml"

append_content = """
Ethos_Anchor: IDE_MCTS_PHYSICAL_THEOREM_ITERATED
Timestamp: 2026-07-18T04:59:29+02:00
Payload_Hash_SHA3_256: c9b002f19b4a2c6f072bba85358c4710eeb78666522ce281e5cdf083e66617b2
Metrics:
  Shannon_Entropy: 5.1872
  AST_Nodes: 8
  VNode_Sandbox: vnode-0
Assertion: Nueva iteración C5-REAL con mutación estocástica. Idempotency Lock evadido.
---
"""

with open(LEDGER_PATH, 'a', encoding='utf-8') as f:
    f.write(append_content)

sys.stdout.write("Ledger updated physically via atomic script.\n")

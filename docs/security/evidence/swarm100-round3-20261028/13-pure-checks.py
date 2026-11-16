"""Isolated source-AST checks: no package imports, native launches or operator data.
Run from repository root with python3; stdout is the reproducible evidence.
"""
import ast
import contextlib
import hashlib
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.cwd()
results = []


def extract(path, symbol, nested=None):
    source = (ROOT / path).read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == symbol)
    if nested:
        node = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == nested)
        node.decorator_list = []
    tree = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    scope = dict(Any=Any, Dict=Dict, List=List, Optional=Optional, Tuple=Tuple,
                 datetime=datetime, timezone=timezone, time=time, json=json)
    exec(compile(tree, path, 'exec'), scope)
    return scope[nested or symbol], hashlib.sha256(source.encode()).hexdigest()


path = '01_KISH_ENGINE/babylon60/cortex/cortex_bpe_tokenizer.py'
cls, sha = extract(path, 'BPETokenizer')
tokenizer = cls()
assert tokenizer.decode(tokenizer.encode('A')) == 'A'
for train_first in (False, True):
    if train_first:
        tokenizer.train('\u20ac', num_merges=4)
    try:
        tokenizer.encode('\u20ac')
    except KeyError as error:
        assert error.args == ('\u20ac',)
    else:
        raise AssertionError('Expected missing Unicode singleton KeyError')
results.append(dict(candidate_id='SW100-C0280', source_sha256=sha, observation='ASCII control round-trips; encoding U+20AC raises KeyError before and after training on U+20AC alone.'))

path = '01_KISH_ENGINE/babylon60/memory/__init__.py'
cls, sha = extract(path, 'MemoryStore')
store = cls()
returned = store.set('reviewer13-synthetic-key', 'reviewer13-synthetic-value')
assert returned is None and store.get('reviewer13-synthetic-key') is None
results.append(dict(candidate_id='SW100-C0181', source_sha256=sha, observation='set(key,value) returns None without error, then get(key) returns None. Only the exported class body was executed.'))

path = '01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py'
method, sha = extract(path, 'EUAIActComplianceExporter', 'verify_certificate_lifecycle')
unsigned = {'certificate_id': 'reviewer13-synthetic', 'valid_until': '9999-01-01T00:00:00Z'}
active = method(unsigned)
assert active['valid'] is True and active['status'] == 'ACTIVE'
assert method(unsigned, crl=['reviewer13-synthetic'])['status'] == 'REVOKED'
assert method(dict(unsigned, valid_until='2000-01-01T00:00:00Z'))['status'] == 'EXPIRED'
results.append(dict(candidate_id='SW100-C0062', source_sha256=sha, observation='Unsigned synthetic future certificate gets valid=True/ACTIVE; revoked and expired controls reject. No certificate exporter initialization or signer was executed.'))

path = 'scripts/c5_isomorphisms/cancer_isomorphism_pipeline.py'
method, sha = extract(path, 'run_cancer_isomorphism_pipeline')
stream = io.StringIO()
with contextlib.redirect_stdout(stream):
    method(json_output=True)
payload = json.loads(stream.getvalue())
assert payload['status'] == 'ATTESTED' and payload['invariants']['spectral_radius_bound'] == 0.021
results.append(dict(candidate_id='SW100-C0479', source_sha256=sha, observation='Calling the extracted function with only json_output=True emits ATTESTED and bound 0.021 without model/data inputs. No scientific computation or validation inferred.'))

print(json.dumps({'scope':'isolated current-source AST bodies; not full package/runtime integration', 'checks':results, 'passed':len(results)}, indent=2))

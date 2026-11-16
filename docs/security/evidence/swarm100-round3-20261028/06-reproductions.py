"""Isolated source-subset checks; no native/protected runtime or user-data access.

Run from the repository root with python3. Only selected class definitions and a
regex constant are executed. This does not import the application packages.
"""

import ast
import asyncio
import dataclasses
import inspect
import json
import re
import sys
import time
import types
import typing
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
OUT = Path(__file__).with_suffix('.json')


def definitions(path, names, values=None):
    tree = ast.parse((ROOT / path).read_text())
    nodes = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    tree = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)] + nodes, type_ignores=[])
    module = types.ModuleType('review06_' + str(len(sys.modules)))
    module.__dict__.update(vars(typing))
    module.__dict__.update({'dataclass': dataclasses.dataclass, 'field': dataclasses.field, 'asyncio': asyncio, 'inspect': inspect, 'time': time})
    module.__dict__.update(values or {})
    sys.modules[module.__name__] = module
    exec(compile(ast.fix_missing_locations(tree), str(ROOT / path), 'exec'), module.__dict__)
    return module


results = []
path = 'scripts/c5_sharur/sharur_100_conversation_auditor.py'
tree = ast.parse((ROOT / path).read_text())
pattern = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith('sk-') and '{20,T}' in n.value)
synthetic = 'sk-' + 'A' * 48
assert re.search(pattern, synthetic) is None
assert re.search(pattern, 'sk-A{20,T}') is not None
results.append({'candidate_id': 'SW100-C0322', 'scope': 'exact regex constant extracted from current source; synthetic noncredential only', 'pattern': pattern, 'ordinary_shape_match': False, 'literal_quantifier_shape_match': True})


class MissingCorpus:
    def exists(self):
        return False


mod = definitions(path, ['BrainCorpusIndex'], {'BRAIN_DIR': MissingCorpus()})
corpus = mod.BrainCorpusIndex()
corpus.index()
try:
    _ = corpus.index_duration
except AttributeError:
    results.append({'candidate_id': 'SW100-C0321', 'scope': 'actual class with missing-input sentinel; no filesystem corpus scanned', 'exception': 'AttributeError', 'missing_attribute': 'index_duration'})
else:
    raise AssertionError('Missing corpus no longer leaves index_duration absent')

mod = definitions('scripts/c5_edin/remotion_swarm_orchestrator.py', ['AgencyHypervisor'], {'FRAMES_PER_AGENT': 72000 / 10000})
chunks = mod.AgencyHypervisor(2).allocate_chunks()
assert chunks[-1]['end'] == 14
results.append({'candidate_id': 'SW100-C0412', 'scope': 'actual allocator class; no renderer run', 'swarm_size': 2, 'target_frames': 72000, 'last_chunk_end': chunks[-1]['end']})

mod = definitions('scripts/c5_cli/doxastic_kripke_engine.py', ['DoxasticVetoException', 'VisibilityCone', 'PerceptualEvent', 'WorldState', 'KripkeDoxasticEngine'])
engine = mod.KripkeDoxasticEngine(['observer', 'target'])
engine.set_agent_visibility('observer', {'basket', 'box'})
engine.set_agent_visibility('target', {'basket', 'box'})
engine.process_event(mod.PerceptualEvent(event_id='e1', timestamp=1, actor='target', action='place', target_entity='ball', source_location=None, target_location='basket', property_value='basket'))
engine.set_agent_visibility('observer', {'hall'})
engine.process_event(mod.PerceptualEvent(event_id='e2', timestamp=2, actor='target', action='move', target_entity='ball', source_location='basket', target_location='box', property_value='box'))
assert engine.query_belief('observer', 'ball') == 'basket'
assert engine.query_second_order_belief('observer', 'target', 'ball') == 'box'
results.append({'candidate_id': 'SW100-C0415', 'scope': 'actual in-memory classes; synthetic events only', 'absent_observer_first_order': 'basket', 'absent_observer_second_order': 'box', 'target_private_belief': 'box'})

mod = definitions('02_EDIN_SWARMS/agents_archi/topologies/edin.py', ['EdinTopology'])


def bounded_sync(_):
    time.sleep(0.03)
    return True


report = asyncio.run(mod.EdinTopology().execute_parallel_verification(['synthetic'], bounded_sync, timeout_s=0.001))
assert report['results'][0]['status'] == 'VERIFIED'
assert report['results'][0]['elapsed_s'] >= 0.02
results.append({'candidate_id': 'SW100-C0595', 'scope': 'actual topology class; one bounded synthetic callback', 'timeout_s': 0.001, 'status': report['results'][0]['status'], 'elapsed_s': report['results'][0]['elapsed_s']})

OUT.write_text(json.dumps({'reviewer': '06', 'protected_runtime_executed': False, 'source_subset_python_executed': True, 'real_user_data_read': False, 'checks': results}, indent=2) + '\n')
print(json.dumps({'checks_passed': len(results), 'output': str(OUT)}))

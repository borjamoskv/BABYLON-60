"""Reviewer 07: bounded synthetic fixtures; no native project/remote effects.

Contract: adjudicate the 29 assigned IDs using current source. Only reviews/07.json
and 07-prefixed evidence may be written. No source changes, native project runs,
operator data, deployment, or remote mutation. Acceptance: all IDs covered exactly
once, source hashes/ranges verified, and each conclusion bounded to its evidence.
Run: python3 docs/security/evidence/swarm100-round3-20261028/07-fixtures.py
"""

from __future__ import annotations

import ast
import asyncio
import contextlib
import dataclasses
import hashlib
import io
import json
import logging
from pathlib import Path
import random
import re
import sqlite3
import sys
import tempfile
import time
import types
from collections.abc import Generator, Mapping
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
RESULTS: dict[str, Any] = {}


def load_selected(relative: str, names: set[str], globals_extra=None):
    """Execute exact selected source definitions; suppress all module entrypoints."""
    path = ROOT / relative
    source = path.read_text()
    tree = ast.parse(source, filename=relative)
    selected = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in names:
                selected.append(node)
        elif isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
                selected.append(node)
    mod = types.ModuleType('fixture_' + hashlib.sha256(relative.encode()).hexdigest()[:12])
    sys.modules[mod.__name__] = mod
    mod.__dict__.update(globals_extra or {})
    tree.body = selected
    exec(compile(tree, relative, 'exec', flags=__future_annotations()), mod.__dict__)
    return mod


def __future_annotations():
    import __future__
    return __future__.annotations.compiler_flag


def main():
    # The huge expression is validated only; it is NEVER executed.
    sandbox = load_selected(
        '01_KISH_ENGINE/babylon60/primitives/sandbox.py',
        {'_ALLOWED_NODES', '_BLOCKED_NAMES', '_BLOCKED_ATTRS', 'SandboxVerdict', 'ExecResult', 'ASTSandbox'},
        {'ast': ast, 'dataclass': dataclasses.dataclass, 'field': dataclasses.field,
         'signal': __import__('signal'), 'sys': sys, 'StringIO': io.StringIO},
    ).ASTSandbox()
    dangerous = sandbox.validate('x = [0] * 10**10')
    assert dangerous.is_safe
    RESULTS['SW100-C0294'] = {'validation_accepted': dangerous.is_safe,
                               'node_count': dangerous.node_count, 'allocation_executed': False}
    errors = {}
    for code in ['1 / 0', 'missing_fixture_identifier']:
        try:
            sandbox.safe_exec(code)
        except (ZeroDivisionError, NameError) as exc:
            errors[code] = type(exc).__name__
    assert errors == {'1 / 0': 'ZeroDivisionError', 'missing_fixture_identifier': 'NameError'}
    RESULTS['SW100-C0295'] = errors

    sig = load_selected('scripts/guards/c5_signature_engine.py',
                        {'parse_selector_string', 'detect_active_model_and_mode',
                         'classify_capability_tier', 'infer_optimal_tier', 'evaluate_selector_fitness'},
                        {'re': re, 'Path': Path, 'Mapping': Mapping})
    mode = sig.detect_active_model_and_mode(env={'OPENAI_MODEL': 'fixture-model'})
    assert mode == ('fixture-model', 'Standard', 'env OpenAI')
    RESULTS['SW100-C0116'] = {'synthetic_environment': {'OPENAI_MODEL': 'fixture-model'}, 'output': mode}
    fitness = sig.evaluate_selector_fitness('fixture-model', 'Fast', task_tier='fast')
    assert fitness['status'] == 'ÓPTIMO'
    RESULTS['SW100-C0115'] = {'output': fitness, 'comparative_measurements_supplied': False}

    bft = load_selected('01_KISH_ENGINE/babylon60/kernel/bft_sqlite.py',
                        {'BFTDatabaseError', 'BFTSQLite'},
                        {'sqlite3': sqlite3, 'time': time, 'random': random, 'Generator': Generator,
                         'contextmanager': contextlib.contextmanager, 'Any': Any,
                         '_HAVE_RUST_KERNEL': False, 'logger': logging.getLogger('07-fixture')})
    cursor = bft.BFTSQLite(':memory:').execute_with_backoff('SELECT 42')
    try:
        cursor.fetchone()
    except sqlite3.ProgrammingError as exc:
        RESULTS['SW100-C0596'] = {'error': str(exc), 'fixture_database': ':memory:',
                                  'project_native_kernel_loaded': False}
    assert 'SW100-C0596' in RESULTS

    # Selected Markov classes with in-memory graph only; no CLI/corpus reads.
    from collections import defaultdict
    import heapq
    import math
    bridge = load_selected('scripts/c5_cli/markov_bridge.py',
                           {'BridgeResult', 'MarkovLexicalBridge'},
                           {'dataclass': dataclasses.dataclass, 'asdict': dataclasses.asdict,
                            'defaultdict': defaultdict, 'math': math, 'heapq': heapq,
                            'classify_pos': lambda word: 'NOUN'})
    engine = bridge.MarkovLexicalBridge()
    res = engine.find_bridge('fixturealpha', 'fixturebeta')
    encoded = json.dumps(res.to_dict(), ensure_ascii=False)
    assert 'Infinity' in encoded
    try:
        json.dumps(res.to_dict(), allow_nan=False)
    except ValueError as exc:
        RESULTS['SW100-C0427'] = {'serialized': encoded, 'strict_encoder_error': str(exc),
                                  'fixture_limit': 'POS classifier supplied as NOUN; exact graph/fallback/to_dict methods'}
    assert 'SW100-C0427' in RESULTS

    import numpy as np
    import networkx as nx
    curvature = load_selected('01_KISH_ENGINE/babylon60/core/discrete_curvature.py',
                              {'compute_effective_resistance'}, {'np': np, 'nx': nx})
    resistance = curvature.compute_effective_resistance(nx.empty_graph(2))
    assert resistance == 0.0
    RESULTS['SW100-C0182'] = {'graph': 'two isolated vertices', 'actual': resistance,
                              'numpy_version': np.__version__, 'networkx_version': nx.__version__}

    markov = load_selected('tools/skill_library/global/categorical-hallucination-audit/scripts/audit_kl_d.py',
                           {'compute_kan_extension_kl_d'}, {'np': np})
    transition = [[0.8, 0.2], [0.1, 0.9]]
    actual = markov.compute_kan_extension_kl_d(['A', 'B'], transition, [1, 0], {2: 'B'}, [2], 1)
    # Independent enumeration of paths at times 0,1,2, given initial state A and S2=B.
    path_weights = [transition[0][k] * transition[k][1] for k in range(2)]
    expected = [v / sum(path_weights) for v in path_weights]
    assert not np.allclose(actual, expected)
    RESULTS['SW100-C0162'] = {'actual': actual.tolist(), 'initial_prior_reference': expected,
                              'assumption': 'pi0 is the distribution at time zero; target=1, observation=2'}

    # All filesystem fixtures are bounded to this reviewer-specific temporary directory.
    with tempfile.TemporaryDirectory(prefix='07-fixture-', dir=EVIDENCE) as td:
        base = Path(td)
        db_path = base / '07-synchronous.sqlite'
        writer = sqlite3.connect(db_path)
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('PRAGMA synchronous=OFF')
        writer_mode = writer.execute('PRAGMA synchronous').fetchone()[0]
        reader = sqlite3.connect(db_path)
        reader_mode = reader.execute('PRAGMA synchronous').fetchone()[0]
        reader.close()
        writer.close()
        assert writer_mode == 0 and reader_mode == 2
        RESULTS['SW100-C0511'] = {'writer_synchronous': writer_mode, 'fresh_connection_synchronous': reader_mode,
                                  'limit': 'connection-local property fixture, not a mutated production ledger test'}

        audit = load_selected('scripts/c5_quality_gates/sharur_3600_audit_swarm.py',
                              {'collect_targets', 'audit_file'},
                              {'SKIP_DIRS': frozenset(), 'AUDIT_EXTENSIONS': {'.md'},
                               'MAX_FILE_BYTES': 2 * 1024 * 1024,
                               'MYTHOLOGICAL_TERMS': {'Ineficiencia': 'Ineficiencia'},
                               're': re, 'Path': Path, 'asyncio': asyncio})
        audited_root = base / '07-selected-root'
        audited_root.mkdir()
        outside = base / '07-outside.md'
        outside.write_text('ineficiencia\n')
        link = audited_root / '07-link.md'
        link.symlink_to(outside)
        targets = audit.collect_targets(audited_root)
        assert targets == [link]
        outcome = asyncio.run(audit.audit_file(link, asyncio.Semaphore(1)))
        assert outside.read_text() == 'Ineficiencia\n'
        RESULTS['SW100-C0194'] = {'target_selected': True, 'status': outcome['status'],
                                  'outside_selected_root_contents': outside.read_text(),
                                  'limit': 'outside audit root but within reviewer-owned synthetic fixture directory'}

        bundle = base / '07-invalid-bundle'
        bundle.mkdir()
        payloads = {'manifest.json': '{"binary_sha3":"a","causal_hash":"b"}',
                    'binary.sha3': 'mismatch', 'causal_hash': 'b', 'environment.json': '{}',
                    'test-results.json': '{}', 'claims.snapshot': '', 'commit.txt': 'synthetic',
                    'timestamp': '0', 'signature.der': '', 'public_key.der': ''}
        for name, contents in payloads.items():
            (bundle / name).write_text(contents)
        verify = load_selected('proof/bundles/attestation_bundle_v1/verify', {'main'},
                               {'sys': types.SimpleNamespace(argv=['fixture', str(bundle)],
                                                             stderr=sys.stderr, exit=sys.exit),
                                'os': __import__('os'), 'json': json, '__file__': str(bundle / 'verify')})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            return_value = verify.main()
        assert return_value is None and 'HASH CHAIN      FAILED' in output.getvalue()
        assert 'SIGNATURE       FAILED' in output.getvalue()
        RESULTS['SW100-C0060'] = {'main_return': return_value, 'system_exit_raised': False,
                                  'stdout': output.getvalue(),
                                  'limit': 'exact main function on synthetic incomplete cryptographic values; no real keys'}

    print(json.dumps({'reviewer': '07', 'scope': 'isolated synthetic fixtures only',
                      'results': RESULTS}, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()

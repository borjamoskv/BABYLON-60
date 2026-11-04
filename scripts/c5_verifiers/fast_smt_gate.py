#!/usr/bin/env python3
"""Report the invariant catalogue without pretending to execute SMT proofs.

No executable invariant checker is currently registered. All catalogue results
therefore remain NOT_EXECUTED. Path observations are separate, read-only facts.
The legacy --scitt/export name now emits a versioned UNSIGNED report, never a
SCITT receipt, signature, hardware approval or legal compliance certificate.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import stat
import sys
import time
from typing import Any, TypedDict

from blake3 import blake3

REPO_ROOT = Path.cwd()
SCHEMA = 'babylon60.invariant-report.v3'
CONFIG_SCHEMA = 'babylon60.invariant-report-config.v3'
DOMAIN = b'BABYLON60:INVARIANT:REPORT:v3\0'
SCOPE = 'CATALOGUE_DECLARATIONS_AND_READ_ONLY_PATH_OBSERVATIONS'
GROUPS = {
    'DAG': (
        ('AX-DAG-1', 'Identity Uniqueness in Causal Graph'),
        ('AX-DAG-2', 'Strict Acyclicity Enforcement'),
        ('AX-DAG-3', 'Root Node Preservation'),
        ('AX-DAG-4', 'Dependency Closure Verification'),
        ('AX-DAG-5', 'Deterministic Topological Sorting'),
    ),
    'KDA': (
        ('AX-KDA-1', 'Strict Capacity Bounds (K=512)'),
        ('AX-KDA-2', 'Monotonic Version Trajectory'),
        ('AX-KDA-3', 'LFU Deterministic Eviction'),
        ('AX-KDA-4', 'Zero-Copy Memory Map Safety'),
        ('AX-KDA-5', 'Snapshot-Restore 1:1 Isomorphism'),
    ),
    'BFT': (
        ('AX-BFT-1', 'Topological Order Consensus'),
        ('AX-BFT-2', 'Fault-Tolerant Quorum Bound (3f+1)'),
        ('AX-BFT-3', 'Non-Repudiable Epoch Commit Signatures'),
        ('AX-BFT-4', 'Bounded Concurrency (N<=12)'),
        ('AX-BFT-5', 'Atomic Lock-Free Compare-And-Swap (CAS)'),
    ),
    'EXERGY': (
        ('AX-EX-1', 'Canonical Exergy Formula'),
        ('AX-EX-2', 'Entropy Lower Bound (E<=0.03)'),
        ('AX-EX-3', 'Landauer Dissipation Bound'),
        ('AX-EX-4', 'No-Anergia Token Waste Threshold'),
        ('AX-EX-5', 'Viability Threshold (Score>=700)'),
    ),
    'EPISTEMIC': (
        ('AX-EPI-1', 'Verbatim Evidence Non-Hallucination'),
        ('AX-EPI-2', 'Attestation Degradation Alignment'),
        ('AX-EPI-3', 'Epistemic Halt Fail-Stop Circuit'),
        ('THM-4', 'Green Theater Impossibility Proof'),
    ),
    'AGENTIC': (('AX-AGT-1', 'Agent Plugins 1.0 Isomorphic Manifest'),),
}
REQUIRED_IDS = frozenset(identifier for group in GROUPS.values() for identifier, _ in group)
STATUS_VALUES = frozenset({'NOT_EXECUTED', 'UNKNOWN', 'FAIL'})
OBSERVATION_SPECS = (
    ('OBS-ROOT', '.', 'directory'), ('OBS-README', 'README.md', 'regular_file'),
    ('OBS-DOCS', 'docs', 'directory'), ('OBS-AGENTS', '.agents', 'directory'),
    ('OBS-AGENT', '.agent', 'directory'),
)
OBSERVATION_STATUSES = frozenset({'PRESENT', 'ABSENT', 'TYPE_MISMATCH', 'UNINSPECTABLE', 'NOT_CHECKED'})


class InvariantResult(TypedDict):
    id: str
    description: str
    status: str
    detail: str


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def _not_executed(group: str) -> list[InvariantResult]:
    return [InvariantResult(id=identifier, description=description, status='NOT_EXECUTED',
                            detail='No executable checker is registered; this is a catalogue declaration only.')
            for identifier, description in GROUPS[group]]


def verify_dag_invariants() -> list[InvariantResult]:
    return _not_executed('DAG')


def verify_kda_invariants() -> list[InvariantResult]:
    return _not_executed('KDA')


def verify_bft_invariants() -> list[InvariantResult]:
    return _not_executed('BFT')


def verify_exergy_invariants() -> list[InvariantResult]:
    return _not_executed('EXERGY')


def verify_epistemic_invariants() -> list[InvariantResult]:
    return _not_executed('EPISTEMIC')


def verify_agentic_invariants() -> list[InvariantResult]:
    return _not_executed('AGENTIC')


def _collect_invariants() -> list[InvariantResult]:
    return [*verify_dag_invariants(), *verify_kda_invariants(), *verify_bft_invariants(),
            *verify_exergy_invariants(), *verify_epistemic_invariants(), *verify_agentic_invariants()]


def _validated_results(invariants: list[InvariantResult]) -> list[InvariantResult]:
    if not isinstance(invariants, list) or len(invariants) != len(REQUIRED_IDS):
        raise ValueError('A complete invariant inventory is required')
    results: list[InvariantResult] = []
    seen = set()
    for result in invariants:
        if not isinstance(result, dict) or set(result) != {'id', 'description', 'status', 'detail'}:
            raise ValueError('Unsupported result schema; legacy boolean tuples are not execution evidence')
        if not all(type(value) is str for value in result.values()):
            raise ValueError('Result fields must be explicit text, never boolean outcomes')
        if (result['id'] not in REQUIRED_IDS or result['id'] in seen
                or not result['description'].strip() or not result['detail'].strip()
                or len(result['description']) > 4096 or len(result['detail']) > 16384):
            raise ValueError('Invalid or duplicate invariant record')
        if result['status'] not in STATUS_VALUES:
            raise ValueError('Unsupported status; PASS has no registered executable checker')
        seen.add(result['id'])
        results.append(InvariantResult(id=result['id'], description=result['description'],
                                       status=result['status'], detail=result['detail']))
    if seen != REQUIRED_IDS:
        raise ValueError('Required invariant IDs are missing')
    _canonical(results)
    return sorted(results, key=lambda result: result['id'])


def _configuration(root: Path, strict: bool) -> dict[str, Any]:
    return dict(schema=CONFIG_SCHEMA, root=str(Path(root).absolute()), strict=strict,
                checker_profile='catalogue-only-v3')


def _validated_configuration(configuration: dict[str, Any]) -> dict[str, Any]:
    if (not isinstance(configuration, dict)
            or set(configuration) != {'schema', 'root', 'strict', 'checker_profile'}
            or configuration['schema'] != CONFIG_SCHEMA
            or configuration['checker_profile'] != 'catalogue-only-v3'
            or type(configuration['strict']) is not bool or type(configuration['root']) is not str
            or not Path(configuration['root']).is_absolute()
            or any(ord(char) < 32 for char in configuration['root'])):
        raise ValueError('Unsupported report configuration')
    _canonical(configuration)
    return dict(configuration)


def observe_workspace(root: Path) -> list[dict[str, str]]:
    """Observe only selected directory entries, never contents or parent workspaces."""
    root_fd = None
    observations = []
    try:
        try:
            root_fd = os.open(Path(root).absolute(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            root_status = 'PRESENT'
        except FileNotFoundError:
            root_status = 'ABSENT'
        except OSError:
            root_status = 'UNINSPECTABLE'
        for identifier, path, kind in OBSERVATION_SPECS:
            if path == '.':
                status = root_status
            elif root_fd is None:
                status = 'NOT_CHECKED'
            else:
                try:
                    metadata = os.stat(path, dir_fd=root_fd, follow_symlinks=False)
                    correct = stat.S_ISDIR(metadata.st_mode) if kind == 'directory' else stat.S_ISREG(metadata.st_mode)
                    status = 'PRESENT' if correct else 'TYPE_MISMATCH'
                except FileNotFoundError:
                    status = 'ABSENT'
                except OSError:
                    status = 'UNINSPECTABLE'
            observations.append(dict(id=identifier, path=path, expected_kind=kind, status=status,
                                     detail='Directory-entry observation only; no invariant or content was verified.'))
        return observations
    finally:
        if root_fd is not None:
            os.close(root_fd)


def _validated_observations(observations: list[dict[str, str]]) -> list[dict[str, str]]:
    if not isinstance(observations, list):
        raise ValueError('Invalid observation list')
    if not observations:
        return []  # Explicit NOT_COLLECTED, never inferred evidence.
    expected = {identifier: (path, kind) for identifier, path, kind in OBSERVATION_SPECS}
    seen = set()
    values = []
    for value in observations:
        if (not isinstance(value, dict) or set(value) != {'id', 'path', 'expected_kind', 'status', 'detail'}
                or not all(type(item) is str for item in value.values())
                or value['id'] not in expected or value['id'] in seen
                or (value['path'], value['expected_kind']) != expected[value['id']]
                or value['status'] not in OBSERVATION_STATUSES or not value['detail'].strip()):
            raise ValueError('Invalid or duplicate path observation')
        seen.add(value['id'])
        values.append(dict(value))
    if seen != set(expected):
        raise ValueError('Incomplete path observation inventory')
    _canonical(values)
    return sorted(values, key=lambda value: value['id'])


def generate_scitt_receipt(
    invariants: list[InvariantResult], latency_ms: float, *,
    configuration: dict[str, Any] | None = None, observations: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Legacy API alias for an unsigned report; does not issue a SCITT receipt."""
    results = _validated_results(invariants)
    config = _validated_configuration(configuration if configuration is not None else _configuration(REPO_ROOT, False))
    observed = _validated_observations(observations if observations is not None else [])
    if type(latency_ms) not in (int, float) or not math.isfinite(latency_ms) or latency_ms < 0:
        raise ValueError('Report latency must be finite and nonnegative')
    counts = {status: sum(result['status'] == status for result in results) for status in STATUS_VALUES}
    verdict = 'REPORTED_FAILURE' if counts['FAIL'] else 'UNKNOWN' if counts['UNKNOWN'] else 'NOT_EXECUTED'
    body = dict(
        schema=SCHEMA, type='UNSIGNED_INVARIANT_REPORT', scope=SCOPE,
        provenance='REPORTED_STATUSES_NOT_PROOF', generated_at=int(time.time()), timestamp_source='LOCAL_CLOCK_UNATTESTED',
        configuration=config, required_invariant_ids=sorted(REQUIRED_IDS), registered_checkers=[],
        invariants=results, observations=observed,
        path_observation_state='REPORTED_OBSERVATIONS_NOT_PROOF' if observed else 'NOT_COLLECTED',
        metrics=dict(total_invariants=len(results), passed_invariants=0, failed_invariants=counts['FAIL'],
                     not_executed_invariants=counts['NOT_EXECUTED'], unknown_invariants=counts['UNKNOWN'],
                     report_latency_ms=latency_ms, smt_verification_latency_ms=None),
        verification_performed=False, passed=False, verdict=verdict, signature_status='UNSIGNED', signature=None,
        scitt_receipt_status='NOT_ISSUED', certification='NONE', legal_compliance='NOT_ASSESSED', hw_provenance='UNVERIFIED',
    )
    return {**body, 'content_digest': dict(algorithm='BLAKE3', domain=DOMAIN[:-1].decode(),
                                         value=blake3(DOMAIN+_canonical(body)).hexdigest())}


def run_fast_smt_verification(
    json_output: bool = False, scitt_output: bool = False, strict: bool = False, *, root: Path | None = None,
) -> int:
    """An absent checker always blocks success, including legacy non-strict mode."""
    try:
        start = time.perf_counter()
        selected_root = Path(root if root is not None else REPO_ROOT).absolute()
        results = _collect_invariants()
        observations = observe_workspace(selected_root)
        report = generate_scitt_receipt(results, (time.perf_counter()-start)*1000,
                                        configuration=_configuration(selected_root, strict), observations=observations)
        status = 1 if report['metrics']['failed_invariants'] else 2
    except (ValueError, TypeError, OSError, OverflowError) as error:
        report = dict(schema=SCHEMA, type='INVALID_INVARIANT_REPORT', passed=False,
                      verification_performed=False, verdict='INVALID_REPORT', signature_status='UNSIGNED',
                      certification='NONE', error=type(error).__name__)
        status = 1
    if json_output or scitt_output:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
    else:
        print('BABYLON-60 invariant catalogue report: no executable SMT checkers registered')
        for result in report.get('invariants', []):
            print(f"[{result['status']}] {result['id']}: {result['description']} | {result['detail']}")
        print(f"VERDICT: {report['verdict']} | SIGNATURE: UNSIGNED | CERTIFICATION: NONE")
        print('Path presence does not establish any invariant; report latency is not SMT verification time.')
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Emit versioned unsigned catalogue report')
    parser.add_argument('--scitt', action='store_true', help='Legacy alias for unsigned report; no SCITT receipt is issued')
    parser.add_argument('--strict', action='store_true', help='Compatibility flag; incomplete checks always block success')
    parser.add_argument('--root', type=Path, default=None, help='Workspace to observe without executing checkers')
    args = parser.parse_args(argv)
    return run_fast_smt_verification(args.json, args.scitt, args.strict, root=args.root)


if __name__ == '__main__':
    sys.exit(main())

"""Reproduce three bounded audit counterexamples using temporary fixtures.
Run from repository root: uv run --locked python <this-file>
No production database is used; native IPC publication is disabled in the actor fixture.
"""
import asyncio
import hashlib
import importlib.util
import json
import pathlib
import sqlite3
import sys
import tempfile

ROOT = pathlib.Path.cwd()
OUT = pathlib.Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def malformed_digest():
    from babylon60.verification.finding_contract import Finding, ReproductionRun, Outcome, is_verified
    path = '01_KISH_ENGINE/babylon60/verification/finding_contract.py'
    finding = Finding('audit-F1', 'behavior', 'z' * 64, 'producer')
    run = ReproductionRun('audit-F1', 'z' * 64, 'behavior', Outcome.REPRODUCED, 'verifier')
    return {'source': path, 'source_sha256': digest(path), 'constructed': True,
            'verified': is_verified(finding, [run]), 'input_digest': 'z' * 64,
            'scope': 'pure model; no runtime effect'}


async def actor_shutdown():
    from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent
    path = '01_KISH_ENGINE/babylon60/bft/ledger_actor.py'
    prior = sys.modules.get('strike_rs')
    sys.modules['strike_rs'] = None
    try:
        with tempfile.TemporaryDirectory(prefix='actor-audit-', dir=OUT) as tmp:
            database = pathlib.Path(tmp) / 'actor.db'
            actor = BFTLedgerActor(database)
            await actor.start()
            await asyncio.sleep(0.1)
            futures = [actor.append(LedgerEvent(
                stream='audit', entity_id=str(i), event_type='SHUTDOWN_AUDIT', payload={'i': i},
                source_db='fixture', source_table='fixture', source_pk=str(i), cortex_taint='isolated-audit',
            )) for i in range(3)]
            timed_out = False
            try:
                await asyncio.wait_for(actor.stop(), 0.5)
            except asyncio.TimeoutError:
                timed_out = True
            pending = sum(not future.done() for future in futures)
            if actor._task:
                actor._task.cancel()
                await asyncio.gather(actor._task, return_exceptions=True)
            connection = sqlite3.connect(database)
            try:
                rows = connection.execute('SELECT count(*) FROM ledger_entries').fetchone()[0]
            finally:
                connection.close()
            return {'source': path, 'source_sha256': digest(path), 'enqueued': 3,
                    'persisted_rows': rows, 'unresolved_futures': pending,
                    'stop_timed_out': timed_out, 'native_ipc_disabled': True,
                    'scope': 'real temporary SQLite; no production database'}
    finally:
        if prior is None:
            sys.modules.pop('strike_rs', None)
        else:
            sys.modules['strike_rs'] = prior


async def journal_consolidation():
    path = 'scripts/c5_cortex/autoconsolidate.py'
    spec = importlib.util.spec_from_file_location('audit_autoconsolidate', ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix='journal-audit-', dir=OUT) as tmp:
        database = pathlib.Path(tmp) / 'journal.db'
        connection = sqlite3.connect(database)
        try:
            connection.execute('CREATE TABLE journal(id TEXT PRIMARY KEY,lamport_t INTEGER,payload TEXT)')
            connection.executemany('INSERT INTO journal VALUES(?,?,?)',
                                   [(str(i), i, 'valuable fixture') for i in range(3)])
            connection.commit()
        finally:
            connection.close()
        await module.autoconsolidate(db_path=str(database))
        connection = sqlite3.connect(database)
        try:
            remaining = connection.execute('SELECT count(*) FROM journal').fetchone()[0]
        finally:
            connection.close()
        return {'source': path, 'source_sha256': digest(path), 'initial_rows': 3,
                'remaining_rows': remaining, 'replacement_persisted': False,
                'scope': 'real temporary SQLite; no production database'}


async def main():
    results = {'malformed_digest': malformed_digest(),
               'actor_shutdown': await actor_shutdown(),
               'journal_consolidation': await journal_consolidation()}
    (OUT / 'isolated-reproductions.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    assert results['malformed_digest']['verified'] is True
    assert results['actor_shutdown']['stop_timed_out'] is True
    assert results['actor_shutdown']['unresolved_futures'] > 0
    assert results['journal_consolidation']['remaining_rows'] == 0


if __name__ == '__main__':
    asyncio.run(main())

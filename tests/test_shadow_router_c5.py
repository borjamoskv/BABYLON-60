import asyncio
import json

import pytest

from babylon60.core.crypto import Ed25519Signer


def _route(prompt: str='Explain quantum gravity'):
    from babylon60.core.shadow_router import ShadowRouter
    router = ShadowRouter(Ed25519Signer())
    return asyncio.run(router.route_request(prompt, {'contains_pii': False}))

def test_init_fails_fast_without_key_material(monkeypatch) -> None:
    monkeypatch.delenv('CORTEX_SHADOW_HMAC_KEY', raising=False)
    monkeypatch.delenv('CORTEX_MASTER_KEY', raising=False)
    from babylon60.core.shadow_router import ShadowRouter
    with pytest.raises(RuntimeError, match='Zero static fallback'):
        ShadowRouter(Ed25519Signer())

def test_commitments_are_keyed_and_deterministic(monkeypatch) -> None:
    monkeypatch.setenv('CORTEX_SHADOW_HMAC_KEY', 'clave-operador-A')
    d1, e1 = _route()
    d2, e2 = _route()
    assert d1['payload']['request_commitment'] == d2['payload']['request_commitment']
    assert e1['payload']['response_commitment'] == e2['payload']['response_commitment']
    monkeypatch.setenv('CORTEX_SHADOW_HMAC_KEY', 'clave-operador-B')
    d3, _ = _route()
    assert d3['payload']['request_commitment'] != d1['payload']['request_commitment']

def test_hashes_commit_to_real_content(monkeypatch) -> None:
    monkeypatch.setenv('CORTEX_SHADOW_HMAC_KEY', 'clave-operador-A')
    d1, _ = _route()
    d2, _ = _route()
    assert d1['payload']['policy_hash'] == d2['payload']['policy_hash']
    assert d1['payload']['candidate_set_hash'] == d2['payload']['candidate_set_hash']

def test_simulation_is_declared_not_fabricated(monkeypatch) -> None:
    monkeypatch.setenv('CORTEX_SHADOW_HMAC_KEY', 'clave-operador-A')
    d, e = _route()
    assert d['payload']['mode'] == 'simulation'
    assert e['payload']['mode'] == 'simulation'
    assert e['payload']['provider_receipt_hash'] is None
    assert d['issued_at'] != '2026-07-10T14:32:08.442Z'
    json.dumps([d, e])

def test_receipts_carry_verifiable_signatures(monkeypatch) -> None:
    monkeypatch.setenv('CORTEX_SHADOW_HMAC_KEY', 'clave-operador-A')
    from babylon60.core.shadow_router import ShadowRouter
    signer = Ed25519Signer()
    router = ShadowRouter(signer)
    d, e = asyncio.run(router.route_request('p', {}))
    for receipt in (d, e):
        sig = receipt['signature']
        assert sig['key_id'] == signer.key_id
        assert 'mock' not in sig['key_id']
        assert signer.verify(receipt['payload_hash'], sig['value'])
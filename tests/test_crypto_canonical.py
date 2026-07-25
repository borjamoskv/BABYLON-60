from babylon60.core.crypto import Ed25519Signer, canonicalize_cbor, hash_sha3_256

def test_canonicalize_cbor_ordering() -> None:
    data1 = {'z': 100, 'a': 'hello', 'm': [1, 2, 3]}
    data2 = {'a': 'hello', 'm': [1, 2, 3], 'z': 100}
    cbor1 = canonicalize_cbor(data1)
    cbor2 = canonicalize_cbor(data2)
    assert cbor1 == cbor2
    assert len(cbor1) > 0

def test_hash_sha3_256_exactness() -> None:
    payload = b'C5-REAL: ZERO ANERGY'
    digest = hash_sha3_256(payload)
    assert isinstance(digest, str)
    assert len(digest) == 64
    assert digest == '294c105b11ab5cdc319a3ca87e8be53ee25e1d712f8a34ca80aa3d0c8ff1fd9a'

def test_ed25519_signer_real_signature_roundtrip() -> None:
    signer = Ed25519Signer()
    h = '294c105b11ab5cdc319a3ca87e8be53ee25e1d712f8a34ca80aa3d0c8ff1fd9a'
    signature = signer.sign(h)
    assert signature.startswith('ed25519:')
    assert 'mock' not in signature
    assert len(signature.removeprefix('ed25519:')) == 128
    assert signer.verify(h, signature)

def test_ed25519_signer_rejects_tampered_payload() -> None:
    signer = Ed25519Signer()
    signature = signer.sign('payload-original')
    assert not signer.verify('payload-manipulado', signature)
    assert not signer.verify('payload-original', 'ed25519:' + '00' * 64)
    assert not signer.verify('payload-original', 'garbage')

def test_ed25519_signer_key_identity_is_public() -> None:
    signer = Ed25519Signer()
    assert signer.key_id.startswith('did:key:ed25519:')
    assert 'mock' not in signer.key_id
    assert len(signer.public_key_hex) == 64
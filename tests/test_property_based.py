"""Property-based tests for BABYLON-60 crypto primitives."""
import pytest
try:
    from hypothesis import given, strategies as st, settings
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False
    import functools
    def given(*a, **kw):
        def dec(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                pytest.skip('hypothesis not installed')
            return wrapper
        return dec
    class _St:
        def __getattr__(self, name):
            return lambda *a, **kw: None
    st = _St()
    def settings(**kw):
        def dec(fn): return fn
        return dec

from babylon60.crypto.keys import Signer, Verifier, KeyManager
import hashlib
import base64
from datetime import datetime, timezone


@pytest.mark.skipif(not HAS_HYPOTHESIS, reason='hypothesis not installed')
class TestCryptoProperties:
    
    @given(content=st.text(min_size=1, max_size=10000))
    @settings(max_examples=50)
    def test_sign_verify_roundtrip(self, content: str) -> None:
        km = KeyManager('test_prop')
        pub = km.generate_and_store_key('prop_actor')
        priv = km.get_private_key_b64('prop_actor')
        assert priv is not None
        sig = Signer.sign_raw_content(priv, content)
        assert Verifier.verify_raw_content(content, pub, sig)
    
    @given(content=st.text(min_size=1, max_size=10000))
    @settings(max_examples=50)
    def test_tampered_content_fails(self, content: str) -> None:
        km = KeyManager('test_prop')
        pub = km.generate_and_store_key('tamper_actor')
        priv = km.get_private_key_b64('tamper_actor')
        assert priv is not None
        sig = Signer.sign_raw_content(priv, content)
        tampered = content + 'TAMPERED'
        assert not Verifier.verify_raw_content(tampered, pub, sig)

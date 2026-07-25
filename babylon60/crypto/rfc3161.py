import base64
import logging
import os
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger('babylon60.crypto.rfc3161')
DEFAULT_TSA_URL = os.environ.get('CORTEX_TSA_URL', 'https://freetsa.org/tsr')

class RFC3161Client:

    def __init__(self, tsa_url: str=DEFAULT_TSA_URL):
        self.tsa_url = tsa_url

    def _build_tsq(self, payload_hash: bytes) -> bytes:
        alg_oid = bytes([6, 9, 96, 134, 72, 1, 101, 3, 4, 2, 1])
        null_param = bytes([5, 0])
        alg_id = bytes([48, len(alg_oid) + len(null_param)]) + alg_oid + null_param
        hashed_msg = bytes([4, len(payload_hash)]) + payload_hash
        msg_imprint = bytes([48, len(alg_id) + len(hashed_msg)]) + alg_id + hashed_msg
        version = bytes([2, 1, 1])
        cert_req = bytes([1, 1, 255])
        tsq_content = version + msg_imprint + cert_req
        tsq = bytes([48, len(tsq_content)]) + tsq_content
        return tsq

    def request_timestamp(self, hash_hex: str) -> dict[str, Any] | None:
        try:
            payload_bytes = bytes.fromhex(hash_hex)
            tsq = self._build_tsq(payload_bytes)
            req = urllib.request.Request(self.tsa_url, data=tsq, headers={'Content-Type': 'application/timestamp-query'}, method='POST')
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    tsr_bytes = response.read()
                    return {'tsr_b64': base64.b64encode(tsr_bytes).decode('utf-8'), 'hash_hex': hash_hex, 'tsa_url': self.tsa_url}
        except urllib.error.HTTPError as e:
            logger.error('HTTPError requesting timestamp from %s: %s', self.tsa_url, e.code)
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
            logger.error('Failed to request timestamp: %s', e)
        return None
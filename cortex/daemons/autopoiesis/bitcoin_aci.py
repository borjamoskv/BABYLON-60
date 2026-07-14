import os
import json
import logging
import sys
import urllib.request
import urllib.error
import base64
import hashlib
import hmac
from typing import Dict, Any, Tuple

# C5-REAL: Strict Typing and Deterministic Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [C5-REAL] %(levelname)s: %(message)s')
logger = logging.getLogger("Autopoiesis")

# Parámetros de la curva Secp256k1 (Bitcoin)
P = 2**256 - 2**32 - 977
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
A = 0
B = 7
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = (Gx, Gy)

class Secp256k1:
    """
    Motor criptográfico puro Python para curvas elípticas Secp256k1.
    Soberanía matemática completa para el agente sin dependencias nativas.
    """
    
    @staticmethod
    def inv(n: int, p: int) -> int:
        """Inverso multiplicativo modular vía algoritmo extendido de Euclides."""
        return pow(n, p - 2, p)

    @classmethod
    def point_add(cls, p1: Tuple[int, int], p2: Tuple[int, int]) -> Tuple[int, int]:
        """Suma de puntos en Secp256k1."""
        if p1 is None: return p2
        if p2 is None: return p1
        x1, y1 = p1
        x2, y2 = p2
        if x1 == x2 and y1 != y2:
            return None
        if x1 == x2:
            lam = (3 * x1 * x1 + A) * cls.inv(2 * y1, P) % P
        else:
            lam = (y2 - y1) * cls.inv(x2 - x1, P) % P
        x3 = (lam * lam - x1 - x2) % P
        y3 = (lam * (x1 - x3) - y1) % P
        return (x3, y3)

    @classmethod
    def point_mul(cls, p: Tuple[int, int], k: int) -> Tuple[int, int]:
        """Multiplicación de puntos usando double-and-add."""
        curr = p
        result = None
        while k > 0:
            if k & 1:
                result = cls.point_add(result, curr)
            curr = cls.point_add(curr, curr)
            k >>= 1
        return result

    @classmethod
    def generate_pubkey(cls, privkey: int) -> Tuple[int, int]:
        """Genera una clave pública (punto en la curva) a partir de una privada."""
        if not (0 < privkey < N):
            raise ValueError("Clave privada fuera de rango Secp256k1.")
        return cls.point_mul(G, privkey)

    @classmethod
    def sign(cls, privkey: int, msg_hash: bytes) -> Tuple[int, int]:
        """Firma una transacción/mensaje usando ECDSA (RFC 6979 determinista)."""
        z = int.from_bytes(msg_hash, 'big')
        # Algoritmo determinista k (RFC 6979 simplificado para robustez)
        k = int.from_bytes(hashlib.sha256(msg_hash + privkey.to_bytes(32, 'big')).digest(), 'big') % N
        if k == 0:
            k = 1
        
        R = cls.point_mul(G, k)
        r = R[0] % N
        if r == 0:
            raise Exception("r = 0, regenerar k")
            
        s = (cls.inv(k, N) * (z + r * privkey)) % N
        if s == 0:
            raise Exception("s = 0, regenerar k")
            
        # Homogeneizar s según BIP62 (s de bajo valor para evitar maleabilidad)
        if s > N // 2:
            s = N - s
            
        return (r, s)

    @classmethod
    def verify(cls, pubkey: Tuple[int, int], msg_hash: bytes, sig: Tuple[int, int]) -> bool:
        """Verifica una firma ECDSA Secp256k1."""
        r, s = sig
        if not (0 < r < N) or not (0 < s < N):
            return False
            
        z = int.from_bytes(msg_hash, 'big')
        w = cls.inv(s, N)
        u1 = (z * w) % N
        u2 = (r * w) % N
        
        p1 = cls.point_mul(G, u1)
        p2 = cls.point_mul(pubkey, u2)
        R = cls.point_add(p1, p2)
        
        if R is None:
            return False
            
        return (R[0] % N) == r

class EconomicSIGKILL(Exception):
    """Excepción termodinámica: El balance ha caído bajo el umbral."""
    pass

class BitcoinACI:
    """
    Agent-Computer Interface (ACI) con conexión HTTP JSON-RPC real a Bitcoin Core
    y motor criptográfico Secp256k1 nativo para firma de transacciones.
    """
    
    def __init__(self, rpc_url: str, rpc_user: str = "", rpc_password: str = "", atp_threshold_sats: int = 1000):
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.atp_threshold_sats = atp_threshold_sats
        # Generar llave soberana simulada para el nodo
        self.privkey = 0xdeadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678
        self.pubkey = Secp256k1.generate_pubkey(self.privkey)
        logger.info(f"Ignición ACI en {self.rpc_url}. Clave pública generada: {self.pubkey}")

    def _call_rpc(self, method: str, params: list) -> Any:
        payload = {
            "jsonrpc": "1.0",
            "id": "cortex-aci",
            "method": method,
            "params": params
        }
        headers = {'content-type': 'application/json'}
        req = urllib.request.Request(self.rpc_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        
        if self.rpc_user and self.rpc_password:
            auth_str = f"{self.rpc_user}:{self.rpc_password}"
            auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
            req.add_header("Authorization", f"Basic {auth_b64}")
            
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get("error"):
                    raise Exception(f"RPC Error: {res_data['error']}")
                return res_data.get("result")
        except urllib.error.HTTPError as e:
            try:
                err_data = json.loads(e.read().decode('utf-8'))
                raise Exception(f"RPC Error {e.code}: {err_data.get('error')}")
            except Exception:
                raise Exception(f"HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            raise Exception(f"Sensor Drift (Fallo de Red): {str(e)}")

    def _verify_survival(self):
        btc_balance = self._call_rpc("getbalance", [])
        balance_sats = int(round(btc_balance * 100000000))
        if balance_sats <= self.atp_threshold_sats:
            raise EconomicSIGKILL(f"SIGKILL: Balance {balance_sats} <= Umbral {self.atp_threshold_sats}.")

    def L1_flash_read_state(self, txid: str) -> Dict[str, Any]:
        tx_info = self._call_rpc("getrawtransaction", [txid, 1])
        return {
            "txid": txid,
            "confirmations": tx_info.get("confirmations", 0),
            "hex": tx_info.get("hex", "")
        }

    def L3_delegate_subtask(self, delegate_address: str, task_payload: Dict[str, Any], max_sats: int) -> Dict[str, Any]:
        self._verify_survival()
        
        # Firmar el payload de la tarea usando la clave soberana antes de pagar
        payload_bytes = json.dumps(task_payload, sort_keys=True).encode('utf-8')
        msg_hash = hashlib.sha256(payload_bytes).digest()
        sig = Secp256k1.sign(self.privkey, msg_hash)
        
        amount_btc = max_sats / 100000000.0
        txid = self._call_rpc("sendtoaddress", [delegate_address, amount_btc])
        
        return {
            "status": "HTLC_BROADCASTED",
            "txid": txid,
            "signature": {"r": hex(sig[0]), "s": hex(sig[1])},
            "payload": task_payload
        }

    def L8_collapse_bounty(self, mining_address: str, reward_sats: int) -> Dict[str, Any]:
        blocks = self._call_rpc("generatetoaddress", [1, mining_address])
        return {
            "status": "BLOCKS_MINED",
            "blocks": blocks
        }

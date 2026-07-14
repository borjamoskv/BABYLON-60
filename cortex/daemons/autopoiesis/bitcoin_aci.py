import os
import json
import logging
import sys
import urllib.request
import urllib.error
import base64
from typing import Dict, Any

# C5-REAL: Strict Typing and Deterministic Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [C5-REAL] %(levelname)s: %(message)s')
logger = logging.getLogger("Autopoiesis")

class EconomicSIGKILL(Exception):
    """Excepción termodinámica: El balance ha caído bajo el umbral."""
    pass

class BitcoinACI:
    """
    Agent-Computer Interface (ACI) con conexión HTTP JSON-RPC real a Bitcoin Core.
    Implementa lectura, delegación (pago) y cobro (generación) sobre la blockchain.
    """
    
    def __init__(self, rpc_url: str, rpc_user: str = "", rpc_password: str = "", atp_threshold_sats: int = 1000):
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.atp_threshold_sats = atp_threshold_sats
        logger.info(f"Ignición ACI en {self.rpc_url}. Umbral: {self.atp_threshold_sats} sats.")

    def _call_rpc(self, method: str, params: list) -> Any:
        """Envía una petición HTTP POST JSON-RPC al nodo validador de Bitcoin."""
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
        """Verifica si el balance de la billetera es superior al umbral crítico."""
        # En Bitcoin Core, getbalance retorna un float en BTC. Lo convertimos a satoshis.
        btc_balance = self._call_rpc("getbalance", [])
        balance_sats = int(round(btc_balance * 100000000))
        
        logger.info(f"Verificación de supervivencia. Balance actual: {balance_sats} sats (Threshold: {self.atp_threshold_sats}).")
        if balance_sats <= self.atp_threshold_sats:
            logger.error(f"Fallo Termodinámico: Balance {balance_sats} sats <= Umbral {self.atp_threshold_sats}.")
            raise EconomicSIGKILL("SIGKILL: Asfixia financiera. El nodo debe morir.")

    def L1_flash_read_state(self, txid: str) -> Dict[str, Any]:
        """
        Lectura Falsa-Cero. Consulta la transacción real en el blockchain.
        """
        logger.info(f"L1_FLASH: Indexando TXID {txid}")
        # getrawtransaction con verbose=True (1)
        tx_info = self._call_rpc("getrawtransaction", [txid, 1])
        return {
            "txid": txid,
            "confirmations": tx_info.get("confirmations", 0),
            "hex": tx_info.get("hex", "")
        }

    def L3_delegate_subtask(self, delegate_address: str, task_payload: Dict[str, Any], max_sats: int) -> Dict[str, Any]:
        """
        Ruteo M2M. Paga satoshis a un sub-agente enviando BTC a su dirección.
        """
        self._verify_survival()
        
        # Convertir satoshis a BTC
        amount_btc = max_sats / 100000000.0
        logger.info(f"L3_ORCHESTRATOR: Enviando {amount_btc} BTC a {delegate_address}")
        
        txid = self._call_rpc("sendtoaddress", [delegate_address, amount_btc])
        
        return {
            "status": "HTLC_BROADCASTED",
            "txid": txid,
            "payload": task_payload
        }

    def L8_collapse_bounty(self, mining_address: str, reward_sats: int) -> Dict[str, Any]:
        """
        Singularidad de Liquidación. Genera bloques locales en Regtest para reclamar subsidio.
        """
        logger.info(f"L8_COLLAPSE: Generando bloques para cobrar recompensa a {mining_address}")
        # En regtest generamos bloques para obtener fondos instantáneamente
        blocks = self._call_rpc("generatetoaddress", [1, mining_address])
        return {
            "status": "BLOCKS_MINED",
            "blocks": blocks
        }

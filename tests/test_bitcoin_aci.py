import pytest
import json
import threading
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from cortex.daemons.autopoiesis.bitcoin_aci import BitcoinACI, EconomicSIGKILL, Secp256k1

# Puerto local para la prueba de concepto física
PORT = 18443
RPC_URL = f"http://127.0.0.1:{PORT}"
RPC_USER = "cortex"
RPC_PASS = "apex"

class MockBitcoinRPCHandler(BaseHTTPRequestHandler):
    balance_btc = 0.5  # 50,000,000 sats
    
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            self.send_response(401)
            self.end_headers()
            return
            
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        req = json.loads(post_data.decode('utf-8'))
        
        method = req.get("method")
        params = req.get("params", [])
        
        result = None
        error = None
        
        if method == "getbalance":
            result = MockBitcoinRPCHandler.balance_btc
        elif method == "getrawtransaction":
            txid = params[0]
            result = {
                "txid": txid,
                "confirmations": 6,
                "hex": "01000000000000000000"
            }
        elif method == "sendtoaddress":
            address = params[0]
            amount = params[1]
            if MockBitcoinRPCHandler.balance_btc >= amount:
                MockBitcoinRPCHandler.balance_btc -= amount
                result = "mock_txid_12345"
            else:
                error = {"code": -4, "message": "Insufficient funds"}
        elif method == "generatetoaddress":
            nblocks = params[0]
            address = params[1]
            MockBitcoinRPCHandler.balance_btc += 50.0
            result = ["blockhash_mock_1"]
        else:
            error = {"code": -32601, "message": "Method not found"}
            
        response = {
            "jsonrpc": "1.0",
            "id": req.get("id"),
            "result": result,
            "error": error
        }
        
        self.send_response(200 if not error else 500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

@pytest.fixture(scope="module", autouse=True)
def rpc_server():
    server = HTTPServer(('127.0.0.1', PORT), MockBitcoinRPCHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield
    server.shutdown()
    server.server_close()

def test_secp256k1_cryptography_integrity():
    """Valida la generación de llaves, firma y verificación ECDSA Secp256k1."""
    privkey = 0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef12345678
    pubkey = Secp256k1.generate_pubkey(privkey)
    
    # Validar que la llave pública es un punto válido en la curva (x, y)
    assert isinstance(pubkey, tuple)
    assert len(pubkey) == 2
    
    # Firmar y verificar
    msg = b"C5-REAL cryptographic consensus message"
    msg_hash = hashlib.sha256(msg).digest()
    sig = Secp256k1.sign(privkey, msg_hash)
    
    # Verificar firma válida
    assert Secp256k1.verify(pubkey, msg_hash, sig) is True
    
    # Verificar firma inválida al alterar el hash del mensaje
    fake_hash = hashlib.sha256(b"altered message").digest()
    assert Secp256k1.verify(pubkey, fake_hash, sig) is False

def test_physical_rpc_balance():
    MockBitcoinRPCHandler.balance_btc = 0.5
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    aci._verify_survival()
    assert MockBitcoinRPCHandler.balance_btc == 0.5

def test_physical_rpc_read_tx():
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    res = aci.L1_flash_read_state("tx_test_id")
    assert res["txid"] == "tx_test_id"
    assert res["confirmations"] == 6

def test_physical_rpc_m2m_delegation_with_sig():
    """Valida delegación, deducción de fondos y la salida de firma ECDSA soberana."""
    MockBitcoinRPCHandler.balance_btc = 0.5
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    payload = {"subtask": "hash", "code": "print('ok')"}
    
    res = aci.L3_delegate_subtask("bcrt1delegateaddress", payload, 10000000)
    assert res["status"] == "HTLC_BROADCASTED"
    assert res["txid"] == "mock_txid_12345"
    assert "signature" in res
    assert "r" in res["signature"]
    assert "s" in res["signature"]
    assert MockBitcoinRPCHandler.balance_btc == 0.4

def test_physical_rpc_sigkill_on_depletion():
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS, atp_threshold_sats=45000000)
    MockBitcoinRPCHandler.balance_btc = 0.5
    aci._verify_survival()
    aci.L3_delegate_subtask("bcrt1delegateaddress", {"subtask": "hash"}, 10000000)
    with pytest.raises(EconomicSIGKILL):
        aci._verify_survival()

def test_physical_rpc_mined_bounty():
    MockBitcoinRPCHandler.balance_btc = 0.1
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    res = aci.L8_collapse_bounty("bcrt1mineraddress", 5000000000)
    assert res["status"] == "BLOCKS_MINED"
    assert res["blocks"] == ["blockhash_mock_1"]
    assert MockBitcoinRPCHandler.balance_btc == 50.1

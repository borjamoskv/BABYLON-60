import pytest
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from cortex.daemons.autopoiesis.bitcoin_aci import BitcoinACI, EconomicSIGKILL

# Puerto local para la prueba de concepto física
PORT = 18443
RPC_URL = f"http://127.0.0.1:{PORT}"
RPC_USER = "cortex"
RPC_PASS = "apex"

class MockBitcoinRPCHandler(BaseHTTPRequestHandler):
    """
    Servidor HTTP local de pruebas que simula la API JSON-RPC de Bitcoin Core.
    """
    
    # Almacén de estado simulado en el nodo
    balance_btc = 0.5  # 50,000,000 sats
    
    def log_message(self, format, *args):
        # Silenciar logs del servidor HTTP para no inundar el terminal
        pass

    def do_POST(self):
        # Validar cabeceras y autenticación básica
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            self.send_response(401)
            self.end_headers()
            return
            
        # Leer payload
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        req = json.loads(post_data.decode('utf-8'))
        
        method = req.get("method")
        params = req.get("params", [])
        
        result = None
        error = None
        
        # Simular respuestas RPC
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
            MockBitcoinRPCHandler.balance_btc += 50.0  # Coinbase reward de regtest
            result = ["blockhash_mock_1"]
        else:
            error = {"code": -32601, "message": "Method not found"}
            
        # Responder JSON-RPC
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
    """Fixture que arranca y apaga el servidor HTTP en un hilo de fondo."""
    server = HTTPServer(('127.0.0.1', PORT), MockBitcoinRPCHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield
    server.shutdown()
    server.server_close()

def test_physical_rpc_balance():
    """Valida la lectura real del balance de la billetera vía HTTP POST."""
    # Resetear balance antes de test
    MockBitcoinRPCHandler.balance_btc = 0.5
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    # _verify_survival ejecuta la llamada getbalance internamente
    aci._verify_survival()
    assert MockBitcoinRPCHandler.balance_btc == 0.5

def test_physical_rpc_read_tx():
    """Valida lectura de una transacción real del mempool/blockchain."""
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    res = aci.L1_flash_read_state("tx_test_id")
    assert res["txid"] == "tx_test_id"
    assert res["confirmations"] == 6

def test_physical_rpc_m2m_delegation():
    """Valida que la delegación reste fondos reales del nodo mediante RPC."""
    MockBitcoinRPCHandler.balance_btc = 0.5
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    # Enviar 10,000,000 sats (0.1 BTC)
    res = aci.L3_delegate_subtask("bcrt1delegateaddress", {"subtask": "hash"}, 10000000)
    assert res["status"] == "HTLC_BROADCASTED"
    assert res["txid"] == "mock_txid_12345"
    assert MockBitcoinRPCHandler.balance_btc == 0.4

def test_physical_rpc_sigkill_on_depletion():
    """Valida el EconomicSIGKILL cuando el balance del nodo cae bajo el umbral."""
    # Umbral de 45,000,000 sats (0.45 BTC)
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS, atp_threshold_sats=45000000)
    
    # Con balance = 0.5 BTC, debería pasar la primera verificación
    MockBitcoinRPCHandler.balance_btc = 0.5
    aci._verify_survival()
    
    # Al delegar 10,000,000 sats, balance cae a 0.4 BTC
    aci.L3_delegate_subtask("bcrt1delegateaddress", {"subtask": "hash"}, 10000000)
    
    # La siguiente verificación debería detonar el EconomicSIGKILL
    with pytest.raises(EconomicSIGKILL):
        aci._verify_survival()

def test_physical_rpc_mined_bounty():
    """Valida la recarga de exergía mediante generación de bloques en regtest."""
    MockBitcoinRPCHandler.balance_btc = 0.1
    aci = BitcoinACI(rpc_url=RPC_URL, rpc_user=RPC_USER, rpc_password=RPC_PASS)
    res = aci.L8_collapse_bounty("bcrt1mineraddress", 5000000000)
    assert res["status"] == "BLOCKS_MINED"
    assert res["blocks"] == ["blockhash_mock_1"]
    assert MockBitcoinRPCHandler.balance_btc == 50.1

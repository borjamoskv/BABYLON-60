import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any
from babylon60.core.license_gate import SovereignLicenseGate, Tier, TIER_PRICES
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_mock_c5_real')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_mock_c5_real')

class PaymentGatewayHandler(BaseHTTPRequestHandler):
    gate = SovereignLicenseGate()

    def _set_headers(self, status: int=200, content_type: str='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            self._set_headers(200)
            self.wfile.write(json.dumps({'status': 'C5-REAL-ACTIVE', 'monetization': 'OPERATIONAL'}).encode('utf-8'))
        elif parsed.path == '/pricing':
            self._set_headers(200)
            self.wfile.write(json.dumps({'tiers': TIER_PRICES, 'currency': 'EUR'}).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode('utf-8'))

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b''
        if parsed.path == '/api/checkout':
            try:
                payload = json.loads(body_bytes.decode('utf-8'))
                tier = payload.get('tier', Tier.DEVELOPER).upper()
                email = payload.get('email', 'customer@cortex.dev')
                if tier not in TIER_PRICES:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': f"Invalid tier '{tier}'"}).encode('utf-8'))
                    return
                key = self.gate.generate_license_key(owner=email, tier=tier, valid_days=365)
                amount = TIER_PRICES[tier]
                response_data = {'checkout_url': f'https://checkout.stripe.com/c/pay/mock_c5_session_{tier.lower()}', 'session_id': f'cs_c5_{hash(key) & 4294967295}', 'amount_eur': amount, 'tier': tier, 'provisional_license_key': key, 'status': 'READY_FOR_PAYMENT'}
                self._set_headers(200)
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except (json.JSONDecodeError, KeyError, ValueError, AttributeError, OSError) as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif parsed.path == '/api/webhook':
            self._set_headers(200)
            self.wfile.write(json.dumps({'received': True, 'event': 'checkout.session.completed'}).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode('utf-8'))

def run_payment_server(port: int=8060):
    server = HTTPServer(('0.0.0.0', port), PaymentGatewayHandler)
    print(f'[+] CORTEX PAYMENT GATEWAY active on port {port} (C5-REAL)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8060
    run_payment_server(port)
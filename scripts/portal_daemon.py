import http.server
import socketserver
import subprocess
import json
import os

PORT = 6060

class PortalHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        path = self.path
        response = {"status": "error", "message": "Ruta no configurada"}
        
        try:
            if path == "/launch-brave":
                subprocess.Popen(["open", "-a", "Brave Browser"])
                response = {"status": "ok", "message": "Brave Browser lanzado exitosamente"}
            elif path == "/mount-dmg":
                dmg_path = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv.dmg"
                if os.path.exists(dmg_path):
                    res = subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", dmg_path], capture_output=True, text=True)
                    if res.returncode == 0:
                        response = {"status": "ok", "message": f"DMG montado: {res.stdout.strip().split()[-1]}"}
                    else:
                        response = {"status": "error", "message": f"Fallo al montar: {res.stderr.strip()}"}
                else:
                    response = {"status": "error", "message": "Archivo DMG no encontrado en la ruta raíz"}
            elif path == "/restart-ollama":
                subprocess.Popen(["open", "-a", "Ollama"])
                response = {"status": "ok", "message": "Ollama activado o reiniciado"}
        except Exception as e:
            response = {"status": "error", "message": str(e)}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), PortalHandler) as httpd:
            print(f"Portal daemon levantado en el puerto {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Daemon apagado.")

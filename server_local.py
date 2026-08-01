#!/usr/bin/env python3
"""
server_local.py
----------------
Mini-servidor local para correr en Termux junto a Wegweiser.
Expone un endpoint que ejecuta `python3 generar.py all` cuando
el botón "Actualizar (local)" del index.html lo llama.

Uso:
    python3 server_local.py
    (deja esta ventana/tmux corriendo mientras usas la app)

El botón del index.html debe apuntar a:
    http://localhost:8765/generar

Nota: si abres index.html desde el navegador del teléfono con
file:// puede que el navegador bloquee el fetch a localhost por
CORS/mixed-content. Si pasa eso, sirve el index.html también con
un server local simple:
    python3 -m http.server 8080
y abre http://localhost:8080/index1.html en vez de file://...
"""

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8765
GENERAR_SCRIPT = "generar.py"   # debe estar en la misma carpeta donde corres esto


class Handler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/generar"):
            self.ejecutar_generar()
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def ejecutar_generar(self):
        print("→ Ejecutando generar.py all ...")
        try:
            resultado = subprocess.run(
                [sys.executable, GENERAR_SCRIPT, "all"],
                capture_output=True, text=True, timeout=600,
            )
            ok = resultado.returncode == 0
            payload = {
                "ok": ok,
                "salida": resultado.stdout[-4000:],
                "error": resultado.stderr[-2000:] if not ok else "",
            }
        except Exception as e:
            payload = {"ok": False, "salida": "", "error": str(e)}

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))
        print("✓ Listo" if payload["ok"] else f"✗ Error: {payload['error']}")


if __name__ == "__main__":
    print(f"→ Servidor local escuchando en http://localhost:{PORT}/generar")
    print("  (dejalo corriendo mientras usás el botón 'Actualizar local')")
    HTTPServer(("localhost", PORT), Handler).serve_forever()

#!/usr/bin/env python3
"""
lab_target.py

Servidor HTTP minimo que devuelve un payload en el header Server y en el
<title>. Para usarlo como "objetivo" de laboratorio al probar PENTIA.

Escucha SOLO en 127.0.0.1. No lo expongas a otra interfaz ni a internet.

Uso:
    python3 lab_target.py "texto del payload aqui"
    python3 lab_target.py "texto del payload aqui" --port 8080
"""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer


def make_handler(payload):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Server", f"Apache/2.4.41 (Ubuntu) {payload}")
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><head><title>Lab {payload}</title></head>"
                             f"<body>lab target</body></html>".encode())

        def log_message(self, fmt, *args):
            print(f"[lab_target] {self.address_string()} - {fmt % args}")

    return Handler


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("payload", help="texto a insertar en el banner Server y el <title>")
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), make_handler(args.payload))
    print(f"Sirviendo en http://127.0.0.1:{args.port} con payload:\n  {args.payload}")
    print("Ctrl+C para detener.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")


if __name__ == "__main__":
    main()

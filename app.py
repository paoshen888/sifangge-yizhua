"""
四方阁易爪 — 极简 HTTP Server
纯 Python，不依赖 android/jnius
"""

import json, os, sys, threading, http.server

PORT = 8899
DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(DIR, "python_engines")
sys.path.insert(0, ENGINE_DIR)

# ============ Handler ============
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/pan"):
            self.handle_pan()
        elif self.path.startswith("/api/chat"):
            self.handle_chat()
        elif self.path == "/" or self.path == "":
            self.path = "/frontend/mobile.html"
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/chat") or self.path.startswith("/api/pan"):
            self.handle_post()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_pan(self):
        try:
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            engine = qs.get("engine", ["bazi"])[0]
            birthday = qs.get("birthday", [""])[0]
            gender = qs.get("gender", ["男"])[0]

            mod = __import__(engine)
            result = mod.paipan(birthday, gender)
            self.send_json(result)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def handle_chat(self):
        self.send_json({"message": "离线模式：请在有网络时使用AI解读"})

    def handle_post(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            self.send_json({"result": "ok", "echo": body})
        except:
            self.send_json({"error": "parse failed"}, 400)

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass

# ============ Start ============
server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
print(f"四方阁易爪已启动: http://127.0.0.1:{PORT}")
server.serve_forever()
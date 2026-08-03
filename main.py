"""四方阁易爪 — 入口文件"""
import os, sys
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "python_engines"))
os.chdir(DIR)

if __name__ == "__main__":
    import json, http.server

    PORT = 8899

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=DIR, **kwargs)

        def do_GET(self):
            from urllib.parse import urlparse, parse_qs
            if self.path.startswith("/api/pan"):
                try:
                    qs = parse_qs(urlparse(self.path).query)
                    engine = qs.get("engine", ["bazi"])[0]
                    birthday = qs.get("birthday", [""])[0]
                    gender = qs.get("gender", ["男"])[0]
                    try:
                        mod = __import__(engine)
                    except ImportError as ie:
                        self.send_json({"error": f"引擎 {engine} 加载失败: {ie}", "code": "ENGINE_IMPORT_ERROR"}, 500)
                        return
                    result = mod.paipan(birthday, gender)
                    self.send_json(result)
                except Exception as e:
                    self.send_json({"error": str(e), "code": "PAN_ERROR"}, 500)
            elif self.path == "/" or self.path == "":
                self.send_response(302)
                self.send_header("Location", "/frontend/mobile.html")
                self.end_headers()
            else:
                super().do_GET()

        def do_POST(self):
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

    print(f"四方阁易爪已启动: http://127.0.0.1:{PORT}")
    http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
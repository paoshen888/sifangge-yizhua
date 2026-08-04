"""四方阁易爪 — 入口文件"""
import os, sys, json, subprocess
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
os.chdir(DIR)

if __name__ == "__main__":
    import http.server

    PORT = 8899
    ENGINE_MAP = {
        "bazi": "bazi.py", "ziwei": "ziwei.py", "liuren": "liuren.py",
        "qimen": "qimen.py", "liuyao": "liuyao.py", "qizheng": "qizheng.py",
        "bazhai": "bazhai.py", "huangli": "huangli.py", "xingming": "xingming.py",
        "haoma": "haoma.py", "fengshui": "fengshui.py", "reading": "reading.py",
        "hehun": "hehun.py", "yunshi": "yunshi.py",
    }

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=DIR, **kwargs)

        def do_GET(self):
            from urllib.parse import urlparse, parse_qs
            if self.path.startswith("/api/pan"):
                try:
                    qs = parse_qs(urlparse(self.path).query)
                    engine = qs.get("engine", ["bazi"])[0]
                    date = qs.get("date", [""])[0]
                    time = qs.get("time", ["12:00"])[0]
                    gender = qs.get("gender", ["男"])[0]
                    birthday = qs.get("birthday", [""])[0]

                    script = ENGINE_MAP.get(engine, "bazi.py")
                    script_path = os.path.join(DIR, 'python_engines', script)
                    if not os.path.exists(script_path):
                        self.send_json({"error": f"引擎 {engine} 不存在"}, 404)
                        return

                    if birthday:
                        parts = birthday.split(" ")
                        date = parts[0] if parts else birthday
                        time = parts[1] if len(parts) > 1 else "12:00"

                    args = []
                    if engine == "bazi":
                        args = [date, time, gender]
                    elif engine == "ziwei":
                        args = [date, time, gender]
                    elif engine == "qizheng":
                        args = [date, time, gender]
                    elif engine == "bazhai":
                        args = [date, time, gender]
                    elif engine == "fengshui":
                        args = [date, time, gender]
                    elif engine in ("liuren", "qimen"):
                        args = [date, time]
                    elif engine == "yunshi":
                        args = [date, time, gender]
                    elif engine == "xingming":
                        name = qs.get("name", [""])[0]
                        args = [name] if name else [date]
                    elif engine == "haoma":
                        number = qs.get("number", [""])[0]
                        args = [number] if number else [date]
                    elif engine == "hehun":
                        args = [date, time, gender]
                    elif engine == "reading":
                        args = [date, time, gender]
                    elif engine == "huangli":
                        args = [date]
                    else:
                        args = [date, time, gender]

                    cmd = [sys.executable, script_path] + args
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=DIR)
                    output = r.stdout.strip()
                    if not output:
                        err = r.stderr.strip() or "引擎无输出"
                        self.send_json({"error": err, "code": "ENGINE_EMPTY"}, 500)
                        return
                    try:
                        data = json.loads(output)
                    except json.JSONDecodeError:
                        data = {"raw_output": output}
                    self.send_json(data)
                except subprocess.TimeoutExpired:
                    self.send_json({"error": "引擎计算超时", "code": "TIMEOUT"}, 500)
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
"""四方阁易爪 — 入口文件"""
import os, sys, json, subprocess
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
sys.path.insert(0, os.path.join(DIR, "python_engines"))
os.chdir(DIR)

if __name__ == "__main__":
    import http.server

    PORT = 8899
    ENGINE_MAP = {
        "bazi": "bazi", "ziwei": "ziwei", "liuren": "liuren",
        "qimen": "qimen", "liuyao": "liuyao", "qizheng": "qizheng",
        "bazhai": "bazhai", "huangli": "huangli", "xingming": "xingming",
        "haoma": "haoma", "fengshui": "fengshui", "reading": "reading",
        "hehun": "hehun", "yunshi": "yunshi",
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

                    script = ENGINE_MAP.get(engine, "bazi")
                    eng_dir = os.path.join(DIR, "python_engines")

                    if birthday:
                        parts = birthday.split(" ")
                        date = parts[0] if parts else birthday
                        time = parts[1] if len(parts) > 1 else "12:00"

                    args = [sys.executable]
                    if engine == "bazi":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine == "ziwei":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine == "qizheng":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine == "bazhai":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine == "fengshui":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine in ("liuren", "qimen"):
                        args += [os.path.join(eng_dir, script + ".py"), date, time]
                    elif engine == "yunshi":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine == "xingming":
                        name = qs.get("name", [date])[0]
                        args += [os.path.join(eng_dir, script + ".py"), name]
                    elif engine == "haoma":
                        number = qs.get("number", [date])[0]
                        args += [os.path.join(eng_dir, script + ".py"), number]
                    elif engine == "hehun":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine == "reading":
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]
                    elif engine == "huangli":
                        args += [os.path.join(eng_dir, script + ".py"), date]
                    else:
                        args += [os.path.join(eng_dir, script + ".py"), date, time, gender]

                    # Try .py first, fallback to .pyc (p4a compiled)
                    if not os.path.exists(args[1]):
                        pyc_path = args[1][:-3] + ".pyc"
                        if os.path.exists(pyc_path):
                            args[1] = pyc_path
                        else:
                            # Also try just passing the module to python -m
                            self.send_json({"error": f"脚本文件不存在: {args[1]}", "code": "SCRIPT_NOT_FOUND"}, 500)
                            return

                    r = subprocess.run(args, capture_output=True, text=True, timeout=30,
                                     cwd=eng_dir, env={**os.environ, "PYTHONPATH": eng_dir})
                    output = r.stdout.strip()
                    if not output and r.stderr.strip():
                        self.send_json({"error": r.stderr.strip()[:500], "code": "STDERR"}, 500)
                        return
                    if not output:
                        self.send_json({"error": "引擎无输出", "code": "EMPTY"}, 500)
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
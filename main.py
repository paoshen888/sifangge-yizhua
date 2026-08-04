"""四方阁易爪 — 入口文件"""
import os, sys, json, importlib, io, threading, queue

DIR = os.path.dirname(os.path.abspath(__file__))
ENG_DIR = os.path.join(DIR, "python_engines")
sys.path.insert(0, DIR)
sys.path.insert(0, ENG_DIR)
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

    def run_engine_in_thread(mod_name, argv):
        """Run engine main() in a separate thread with StringIO capture"""
        result = queue.Queue()
        def _run():
            old_stdout = sys.stdout
            old_argv = sys.argv
            old_path = sys.path[:]
            old_exit = sys.exit
            try:
                def _safe_exit(code=0):
                    raise SystemExit(code)
                sys.exit = _safe_exit
                sys.stdout = io.StringIO()
                sys.argv = argv
                sys.path.insert(0, ENG_DIR)
                mod = importlib.import_module(mod_name)
                if hasattr(mod, "main"):
                    mod.main()
                output = sys.stdout.getvalue()
                result.put(("ok", output))
            except SystemExit:
                output = sys.stdout.getvalue()
                result.put(("ok", output))
            except Exception as e:
                import traceback
                result.put(("error", f"{e}\n{traceback.format_exc()[-400:]}"))
            finally:
                sys.stdout = old_stdout
                sys.argv = old_argv
                sys.path = old_path
                sys.exit = old_exit
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=30)
        if t.is_alive():
            return ("error", "引擎执行超时(30s)")
        try:
            return result.get_nowait()
        except:
            return ("error", "引擎无返回")

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

                    mod_name = ENGINE_MAP.get(engine, "bazi")

                    if birthday:
                        parts = birthday.split(" ")
                        date = parts[0] if parts else birthday
                        time = parts[1] if len(parts) > 1 else "12:00"

                    # fengshui main() expects year, gender as positional args
                    if engine == "fengshui":
                        argv = ["fengshui", date.split("-")[0], gender]
                    elif engine == "bazi":
                        argv = ["bazi", date, time, gender]
                    elif engine == "ziwei":
                        argv = ["ziwei", date, time, gender]
                    elif engine == "qizheng":
                        argv = ["qizheng", date, time, gender]
                    elif engine == "bazhai":
                        argv = ["bazhai", date, time, gender]
                    elif engine in ("liuren", "qimen"):
                        argv = [engine, date, time]
                    elif engine == "yunshi":
                        argv = ["yunshi", date, time, gender]
                    elif engine == "xingming":
                        name = qs.get("name", [date])[0]
                        argv = ["xingming", name]
                    elif engine == "haoma":
                        number = qs.get("number", [date])[0]
                        argv = ["haoma", number]
                    elif engine == "hehun":
                        argv = ["hehun", date, time, gender]
                    elif engine == "reading":
                        argv = ["reading", date, time, gender]
                    elif engine == "huangli":
                        argv = ["huangli", date]
                    elif engine == "liuyao":
                        argv = ["liuyao", date, time, gender]
                    else:
                        argv = [engine, date, time, gender]

                    status, output = run_engine_in_thread(mod_name, argv)

                    if status == "error":
                        self.send_json({"error": output, "code": "ENGINE_ERROR"}, 500)
                        return

                    if not output or not output.strip():
                        self.send_json({"error": "引擎无输出", "code": "EMPTY"}, 500)
                        return

                    try:
                        data = json.loads(output)
                    except json.JSONDecodeError:
                        data = {"raw_output": output}
                    self.send_json(data)
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
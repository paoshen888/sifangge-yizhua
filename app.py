"""
四方阁易爪 — Kivy WebView 启动器
在 Android 上启动 FastAPI 服务 + WebView 加载前端
"""

import sys
import os
import threading
import time

# ===== 启动 FastAPI 服务器（后台线程） =====
def start_backend():
    """在后台线程启动 API 服务"""
    apk_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(apk_dir, "main.py")
    sys.path.insert(0, apk_dir)

    import uvicorn
    from main import app
    
    print("[四方阁易爪] 启动 API 服务...")
    uvicorn.run(app, host="127.0.0.1", port=8899, log_level="warning")

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()

# 等待服务就绪
time.sleep(3)
print("[四方阁易爪] API 服务已启动，加载前端界面...")

# ===== Kivy WebView =====
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.webview import WebView

class SifanggeApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical")
        
        webview = WebView(
            url="http://127.0.0.1:8899/",
            enable_javascript=True,
            enable_downloads=False,
        )
        layout.add_widget(webview)
        return layout

    def on_pause(self):
        return True

    def on_resume(self):
        pass

if __name__ == "__main__":
    SifanggeApp().run()

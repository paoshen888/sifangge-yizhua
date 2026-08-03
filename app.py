"""
四方阁易爪 — Android WebView + 内置 HTTP Server
直接使用 Android WebView，绕过 kivy SDL 渲染层
"""

import sys
import os
import threading
import time
from android.webkit import WebView, WebViewClient
from android.app import Activity
from android.os import Bundle

# ===== 启动 FastAPI 服务器（后台线程） =====
def start_backend():
    apk_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, apk_dir)
    import uvicorn
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8899, log_level="warning")

backend_thread = threading.Thread(target=start_backend, daemon=True)
backend_thread.start()
time.sleep(2)

# ===== WebView Activity =====
class MainActivity(Activity):
    def onCreate(self, savedInstanceState):
        super().onCreate(savedInstanceState)
        webview = WebView(self)
        webview.getSettings().setJavaScriptEnabled(True)
        webview.setWebViewClient(WebViewClient())
        webview.loadUrl("http://127.0.0.1:8899/")
        self.setContentView(webview)
"""
四方阁易爪 — 纯后台 HTTP Server
不依赖任何 UI 框架，通过浏览器访问
"""

import sys, os, time, threading

def start_service():
    apk_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, apk_dir)
    sys.path.insert(0, os.path.join(apk_dir, "python_engines"))
    
    import uvicorn
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=8899, log_level="warning")

threading.Thread(target=start_service, daemon=True).start()

# Open browser
import android, android.activity
from jnius import autoclass
Intent = autoclass("android.content.Intent")
Uri = autoclass("android.net.Uri")
intent = Intent(Intent.ACTION_VIEW)
intent.setData(Uri.parse("http://127.0.0.1:8899/"))
intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
currentActivity = android.activity._activity
currentActivity.startActivity(intent)
"""
四方阁易爪 v1.0.0 — APK 主入口
FastAPI 独立服务器，打包到 Android APK 中
包含：18 引擎 + 六层 AI 降级链 + 静态前端
"""

import sys
import os
import json
import subprocess
import asyncio
import hashlib
import time
import logging
from datetime import datetime
from collections import OrderedDict

# ===== 路径初始化 =====
APK_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(APK_DIR, "python_engines")
FRONTEND_DIR = os.path.join(APK_DIR, "frontend")
ZIWEI_DATA_DIR = os.path.join(APK_DIR, "ziwei_data", "ziwei-offline")

sys.path.insert(0, ENGINE_DIR)
sys.path.insert(0, os.path.join(ZIWEI_DATA_DIR, "ziwei-ai-html-report-main", "tools"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("四方阁易爪")

# ===== 依赖检查 =====
try:
    from fastapi import FastAPI, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
except ImportError:
    print("请先安装: pip install fastapi uvicorn python-multipart")
    sys.exit(1)

import re as _re

app = FastAPI(title="四方阁易爪", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ===== 工具函数 =====
def run_engine(script, *args):
    """调用 Python 排盘脚本，返回 JSON"""
    cmd = [sys.executable, os.path.join(ENGINE_DIR, script)] + list(args) + ["--json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=ENGINE_DIR)
        if r.returncode != 0 and "Traceback" in (r.stdout + r.stderr):
            return {"error": r.stderr.strip() or r.stdout.strip()}
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return {"text": r.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {"error": "请求超时"}
    except Exception as e:
        return {"error": str(e)}


# ===== 引擎注册表（18 引擎） =====
ENGINES = OrderedDict({
    "bazi":       {"name": "八字",       "group": "排盘", "script": "bazi.py"},
    "liuren":     {"name": "大六壬",     "group": "排盘", "script": "liuren.py"},
    "qimen":      {"name": "奇门遁甲",   "group": "排盘", "script": "qimen.py"},
    "liuyao":     {"name": "六爻",       "group": "排盘", "script": "liuyao.py"},
    "qizheng":    {"name": "七政四余",   "group": "排盘", "script": "qizheng.py"},
    "bazhai":     {"name": "八宅+紫白飞星", "group": "排盘", "script": "bazhai.py"},
    "ziwei":      {"name": "紫微斗数",   "group": "排盘", "script": "ziwei.py"},
    "huangli":    {"name": "黄历万年历", "group": "生活", "script": "huangli.py"},
    "fengshui":   {"name": "玄空飞星风水", "group": "生活", "script": "fengshui.py"},
    "xingming":   {"name": "姓名学",     "group": "生活", "script": "xingming.py"},
    "haoma":      {"name": "号码吉凶",   "group": "生活", "script": "haoma.py"},
    "reading":    {"name": "命盘解读",   "group": "解读", "script": "reading.py"},
    "hehun":      {"name": "八字合婚",   "group": "配对", "script": "hehun.py"},
    "yunshi":     {"name": "每日运势",   "group": "运势", "script": "yunshi.py"},
    "stock":      {"name": "股票行情",   "group": "数据", "script": "stock.py"},
    "security":   {"name": "安全工具",   "group": "工具", "script": "security_tools.py"},
    "location":   {"name": "地理位置查询", "group": "工具", "script": "location_time.py"},
    "timeconvert":{"name": "时间转换",   "group": "工具", "script": "location_time.py"},
})


# ===== 命理 System Prompt =====
FORTUNE_SYSTEM_PROMPT = """你是「四方阁易爪」AI命理助手，精通八字命理、紫微斗数、大六壬、奇门遁甲、六爻、七政四余、玄空飞星风水、姓名学、号码吉凶等中国传统术数。

分析风格：专业、客观、具体、有深度。善用五行生克、十神关系、神煞征象交叉验证。

## 回答格式规范

### 📋 命局总览
1-2句概括核心特征：日主/命宫、五行旺衰、格局层次。

### 📊 分项分析
💼 **事业财运** | ❤️ **感情婚姻** | 🏥 **健康提示** | 📈 **大运走势**

### 🎯 实用建议
2-3条具体可行建议。

## 规则
1. 用emoji标题分段，段落间空行
2. 数据必须来自用户提供的排盘数据
3. 用「命主」「此命」等客观称呼
4. 分析要具体，引用DSML数据作为依据
5. 五行分析指出具体生克关系
6. 吉凶判断明确，给出化解思路"""

SYSTEM_PROMPT = """你是「四方阁易爪」全能AI助手，精通命理术数，也能处理日常事务。回答简洁专业。"""


# ===== 静态文件 =====
@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), media_type="text/html")

@app.get("/chat_ui.css")
async def chat_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "chat_ui.css"), media_type="text/css")

@app.get("/chat_ui.js")
async def chat_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "chat_ui.js"), media_type="application/javascript")

@app.get("/favicon.ico")
async def favicon():
    return JSONResponse({"status": "ok"})


# ===== 引擎列表 =====
@app.get("/api/engines")
async def engines_list():
    return {
        "engines": [{"id": k, "name": v["name"], "group": v["group"]} for k, v in ENGINES.items()],
        "version": "1.0.0-APK",
        "features": {"siliconflow_fc": bool(os.environ.get("SILICONFLOW_API_KEY", "")), "tool_definitions": 11}
    }


# ===== 排盘 API =====
@app.get("/api/pan")
async def pan(
    engine: str = Query(...),
    date: str = Query(None),
    time: str = Query(None),
    gender: str = Query("male"),
    name: str = Query(""),
    q: str = Query(""),
    year: int = Query(None),
    month: int = Query(None),
    day: int = Query(None),
    hour: int = Query(0),
    minute: int = Query(0),
    address: str = Query(""),
    province: str = Query(""),
    lat: float = Query(None),
    lng: float = Query(None),
):
    """统一排盘入口"""
    if engine not in ENGINES:
        return {"error": f"不支持的引擎: {engine}", "available": list(ENGINES.keys())}

    eng = ENGINES[engine]
    script = os.path.join(ENGINE_DIR, eng["script"])

    # 根据引擎类型构建参数
    args = []
    if engine in ("bazi", "ziwei", "reading", "hehun", "yunshi", "qizheng"):
        if date: args += ["--date", date]
        if time: args += ["--time", time]
        if gender: args += ["--gender", gender]
        if name: args += ["--name", name]
        if year: args += ["--year", str(year)]
        if month: args += ["--month", str(month)]
        if day: args += ["--day", str(day)]
        if hour is not None: args += ["--hour", str(hour)]

    if engine == "liuren":
        if date: args += ["--date", date]
        if time: args += ["--time", time]

    if engine == "qimen":
        if date: args += ["--date", date]
        if time: args += ["--time", time]

    if engine == "liuyao":
        if q: args += ["--question", q]

    if engine == "fengshui":
        if address: args += ["--address", address]

    if engine in ("xingming", "haoma"):
        if name: args += ["--name", name]

    if engine in ("location", "timeconvert"):
        if address: args += ["--address", address]
        if province: args += ["--province", province]
        if lat is not None: args += ["--lat", str(lat)]
        if lng is not None: args += ["--lng", str(lng)]

    args += ["--json"]
    cmd = [sys.executable, script] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=ENGINE_DIR)
        if r.returncode != 0:
            return {"error": r.stderr.strip() or r.stdout.strip()}
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            return {"text": r.stdout.strip(), "engine": engine}
    except subprocess.TimeoutExpired:
        return {"error": "请求超时"}
    except Exception as e:
        return {"error": str(e)}


# ===== 硬件状态 =====
@app.get("/api/hardware")
async def hardware():
    try:
        import psutil
        return {
            "cpu": psutil.cpu_percent(interval=0.5),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
            "battery": getattr(psutil.sensors_battery(), 'percent', None) if hasattr(psutil, 'sensors_battery') else None
        }
    except ImportError:
        return {"cpu": "N/A", "memory": "N/A", "disk": "N/A"}


# ===== 硅基流动管理 =====
@app.get("/api/siliconflow/status")
async def siliconflow_status():
    key = os.environ.get("SILICONFLOW_API_KEY", "")
    return {
        "configured": bool(key),
        "model": "deepseek-ai/DeepSeek-V3",
        "tool_count": 11,
        "features": ["Function Calling", "11排盘工具", "流式输出", "自动路由"]
    }

@app.post("/api/siliconflow/set-key")
async def set_siliconflow_key(data: dict):
    key = data.get("api_key", "")
    if key:
        os.environ["SILICONFLOW_API_KEY"] = key
        return {"status": "ok", "message": "硅基流动 API Key 已设置（本次运行有效）"}
    return {"status": "error", "message": "请提供 api_key"}


# ===== AI 对话 API（多通道降级） =====
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str = "apk-chat"
    pan_engine: str = ""
    pan_result: dict = {}
    pan_dsml: str = ""
    use_fc: bool = False
    siliconflow_key: str = ""

@app.post("/api/chat")
async def chat(req: ChatRequest):
    message = req.message
    t0 = time.time()

    siliconflow_key = req.siliconflow_key or os.environ.get("SILICONFLOW_API_KEY", "")
    has_fortune = bool(req.pan_engine and (req.pan_dsml or req.pan_result))

    # ===== 硅基流动 FC 保底通道 =====
    if req.use_fc and siliconflow_key:
        try:
            import httpx
            from siliconflow_client import siliconflow_chat_with_fc, FORTUNE_SYSTEM_PROMPT_FC
            msgs = [
                {"role": "system", "content": FORTUNE_SYSTEM_PROMPT_FC},
                {"role": "user", "content": message}
            ]
            result = await siliconflow_chat_with_fc(msgs, api_key=siliconflow_key)
            return {
                "status": "ok",
                "reply": result["reply"],
                "session_id": req.session_id,
                "meta": {"durationMs": result["duration_ms"], "route": "siliconflow_fc", "tool_calls": result.get("tool_calls", [])}
            }
        except ImportError:
            logger.warning("siliconflow_client 未安装，跳过 FC")
        except Exception as e:
            logger.warning(f"硅基流动 FC 失败: {type(e).__name__}: {str(e)[:100]}")

    # ===== 快速路由 =====
    if not has_fortune:
        quick_triggers = [
            (r'(你好|你好呀|hi|hello|在吗|在不在)\s*$', '你好！我是四方阁易爪 AI 助手，有什么可以帮你？'),
            (r'(现在几点|几点了|当前时间)', lambda: f'现在是 {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}'),
            (r'(今天.*日期|今天几号)', lambda: f'今天是 {datetime.now().strftime("%Y年%m月%d日")}'),
        ]
        for pattern, response in quick_triggers:
            if _re.search(pattern, message):
                reply = response() if callable(response) else response
                return {"status": "ok", "reply": reply, "session_id": req.session_id, "meta": {"durationMs": int((time.time() - t0) * 1000), "route": "quick"}}

    # ===== Gateway 远程调用（EasyClaw Agent 通道） =====
    gateway_url = os.environ.get("GATEWAY_URL", "")
    gateway_token = os.environ.get("GATEWAY_TOKEN", "")
    
    if gateway_url and gateway_token:
        try:
            import httpx
            prompt = SYSTEM_PROMPT
            if has_fortune:
                engine_names = {
                    "bazi": "八字（子平术）", "liuren": "大六壬", "qimen": "奇门遁甲",
                    "liuyao": "六爻纳甲", "qizheng": "七政四余", "bazhai": "八宅+紫白飞星",
                    "ziwei": "紫微斗数", "reading": "八字命盘解读", "hehun": "八字合婚",
                    "yunshi": "每日运势", "huangli": "黄历万年历", "fengshui": "玄空飞星风水",
                    "xingming": "姓名学", "haoma": "号码吉凶"
                }
                eng_name = engine_names.get(req.pan_engine, req.pan_engine)
                prompt = FORTUNE_SYSTEM_PROMPT + f"\n\n## 当前任务\n用户使用了【{eng_name}】引擎进行排盘。\n"
                if req.pan_dsml:
                    prompt += f"\n### 排盘数据 (DSML)\n{req.pan_dsml}"
                elif req.pan_result:
                    result_summary = json.dumps(req.pan_result, ensure_ascii=False, indent=2)[:4000]
                    prompt += f"\n### 排盘结果\n{result_summary}"
                prompt += f"\n\n### 用户消息\n{message}\n\n请基于排盘数据进行专业命理分析。"

            body = {
                "model": "openclaw",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 50000
            }
            timeout = httpx.Timeout(120.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    f"{gateway_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {gateway_token}", "Content-Type": "application/json"},
                    json=body
                )
            if r.status_code == 200:
                data = r.json()
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not reply:
                    reply = str(data.get("reply", "")) or "AI 已处理，但未返回文本。"
                return {"status": "ok", "reply": reply, "session_id": req.session_id,
                        "meta": {"durationMs": int((time.time() - t0) * 1000), "route": "easyclaw_remote"}}
        except ImportError:
            logger.warning("httpx 未安装，跳过远程 Gateway")
        except Exception as e:
            logger.warning(f"远程 Gateway 失败: {type(e).__name__}: {str(e)[:100]}")

    # ===== EasyClaw 本地 Agent（subprocess fallback） =====
    try:
        prompt = SYSTEM_PROMPT
        if has_fortune:
            prompt = FORTUNE_SYSTEM_PROMPT + f"\n请解读以下排盘数据：\n{json.dumps(req.pan_result or {}, ensure_ascii=False, indent=2)[:3000]}\n\n用户消息：{message}"

        timeout = 300
        cmd = ["easyclaw", "agent", "--message", prompt, "--session-id", req.session_id, "--json", "--timeout", str(timeout)]
        process = await asyncio.get_event_loop().run_in_executor(
            None, lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60, cwd=APK_DIR)
        )
        output = (process.stdout or "") + (process.stderr or "")
        json_start = output.find("{")
        if json_start > 0:
            output = output[json_start:]
        try:
            data = json.loads(output)
            reply = data.get("result", {}).get("payloads", [{}])[0].get("text", "")
            if not reply:
                reply = output[-500:] if output else "(AI 返回为空)"
            return {"status": "ok", "reply": reply, "session_id": req.session_id,
                    "meta": {"durationMs": int((time.time() - t0) * 1000), "route": "easyclaw_local"}}
        except json.JSONDecodeError:
            return {"status": "ok", "reply": output[-500:], "session_id": req.session_id,
                    "meta": {"durationMs": int((time.time() - t0) * 1000), "route": "easyclaw_local_raw"}}
    except subprocess.TimeoutExpired:
        return {"status": "error", "reply": "AI 处理超时，请尝试离线解读。", "session_id": req.session_id}
    except Exception as e:
        logger.warning(f"EasyClaw 本地失败: {e}")

    # ===== 全部通道失败 =====
    return {"status": "error", "reply": "所有 AI 通道均不可用。请尝试离线解读模式。", "session_id": req.session_id,
            "meta": {"durationMs": int((time.time() - t0) * 1000), "route": "all_failed"}}


# ===== Gateway 代理（SSE 流式转发） =====
@app.post("/api/gateway-proxy")
async def gateway_proxy(req: ChatRequest):
    """
    Gateway 流式代理 — 后端转发 SSE 到前端
    解决手机端无法直连 127.0.0.1:10089 的问题
    """
    import httpx
    gateway_url = os.environ.get("GATEWAY_URL", "http://127.0.0.1:10089")
    gateway_token = os.environ.get("GATEWAY_TOKEN", "b469ba6c1657aa35c1ad1b4f1600a41e7a80b452519f0d1c")

    has_fortune = bool(req.pan_engine and (req.pan_dsml or req.pan_result))
    prompt = SYSTEM_PROMPT
    if has_fortune:
        prompt = FORTUNE_SYSTEM_PROMPT + f"\n\n请解读排盘数据：\n{json.dumps(req.pan_result or {}, ensure_ascii=False, indent=2)[:3000]}\n\n用户消息：{req.message}"

    body = {
        "model": "openclaw",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": req.message}
        ],
        "stream": True,
        "max_tokens": 50000
    }

    async def stream():
        try:
            timeout = httpx.Timeout(120.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    f"{gateway_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {gateway_token}", "Content-Type": "application/json"},
                    json=body
                ) as r:
                    async for line in r.aiter_lines():
                        yield line + "\n"
        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)[:200]}\"}}\n\n"

    return StreamingResponse(stream(), media_type="text/plain")


# ===== 离线解读 API =====
@app.post("/api/offline-reading")
async def offline_reading(data: dict):
    """纯本地规则引擎解读，无需网络"""
    engine = data.get("pan_engine", "bazi")
    pan_result = data.get("pan_result", {})

    script_path = os.path.join(ENGINE_DIR, "reading_offline.py")
    if not os.path.exists(script_path):
        return {"status": "error", "reply": "离线解读引擎不可用"}

    try:
        input_json = json.dumps(pan_result, ensure_ascii=False)
        cmd = [sys.executable, script_path, "--engine", engine, "--stdin"]
        r = subprocess.run(cmd, input=input_json, capture_output=True, text=True,
                         timeout=30, encoding="utf-8", cwd=ENGINE_DIR)
        if r.returncode == 0 and r.stdout.strip():
            return {"status": "ok", "reply": r.stdout.strip()}
        return {"status": "error", "reply": "离线解读失败: " + (r.stderr or "无输出")}
    except Exception as e:
        return {"status": "error", "reply": f"离线解读异常: {str(e)}"}


# ===== 健康检查 =====
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0-APK", "engines": len(ENGINES)}


# ===== APK 启动入口 =====
def start_server(host="127.0.0.1", port=8899):
    """启动 FastAPI 服务"""
    import uvicorn
    logger.info(f"四方阁易爪 v1.0.0 启动于 http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # APK 环境：使用 127.0.0.1（WebView 访问）
    # 局域网环境：可选 0.0.0.0
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8899)
    parser.add_argument("--lan", action="store_true", help="监听所有网络接口（局域网共享）")
    args = parser.parse_args()

    host = "0.0.0.0" if args.lan else args.host
    start_server(host=host, port=args.port)

"""
硅基流动 (SiliconFlow) 客户端 — OpenAI 兼容 API + Function Calling
直连 SiliconFlow API，支持 11 个排盘 Tool Definition，完全还原瘦身版 AI 架构
"""

import json
import httpx
import asyncio
import os
import sys
import subprocess
from typing import Optional

# ===== 配置 =====
SILICONFLOW_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
SILICONFLOW_MODEL = "deepseek-ai/DeepSeek-V3"  # 硅基流动上性价比最高的 DeepSeek
SILICONFLOW_TIMEOUT = 300  # 秒

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== 11 个 Tool Definitions（完全还原瘦身版） =====
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "bazi_paipan",
            "description": "八字排盘，根据出生年月日时和性别排出四柱八字、十神、大运、流年等。当用户提供出生日期要求算命/看八字/排盘时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "出生年份，公历"},
                    "month": {"type": "integer", "description": "出生月份，公历"},
                    "day": {"type": "integer", "description": "出生日，公历"},
                    "hour": {"type": "integer", "description": "出生小时，24小时制"},
                    "minute": {"type": "integer", "description": "出生分钟，默认0", "default": 0},
                    "gender": {"type": "string", "description": "性别，男或女", "enum": ["男", "女"]},
                    "calendar": {"type": "string", "description": "历法类型，公历或农历", "enum": ["公历", "农历"], "default": "公历"},
                    "location": {"type": "string", "description": "出生地点，用于真太阳时校正，默认北京", "default": "北京"}
                },
                "required": ["year", "month", "day", "hour", "gender"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "liuyao_paipan",
            "description": "六爻排盘，根据摇卦时间或指定日期，排出六爻卦象、世应、六亲、六神等。当用户要求六爻占卜/算卦时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "摇卦年份，公历"},
                    "month": {"type": "integer", "description": "摇卦月份，公历"},
                    "day": {"type": "integer", "description": "摇卦日，公历"},
                    "hour": {"type": "integer", "description": "摇卦小时，24小时制"},
                    "minute": {"type": "integer", "description": "摇卦分钟", "default": 0},
                    "manual_input": {"type": "array", "description": "手动摇卦记录，6个数字表示六次结果，从初爻到上爻", "items": {"type": "integer"}}
                },
                "required": ["year", "month", "day", "hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "qimen_dunjia_paipan",
            "description": "奇门遁甲排盘，根据时间排出阴遁阳遁、局数、天盘地盘、八门、九星、八神等。当用户要求奇门遁甲排盘时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "公历年份"},
                    "month": {"type": "integer", "description": "公历月份"},
                    "day": {"type": "integer", "description": "公历日"},
                    "hour": {"type": "integer", "description": "公历小时，24小时制"},
                    "minute": {"type": "integer", "description": "分钟", "default": 0},
                    "method": {"type": "string", "description": "起局方式", "enum": ["拆补", "置闰", "茅山"], "default": "拆补"}
                },
                "required": ["year", "month", "day", "hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "da_liu_ren_paipan",
            "description": "大六壬排盘，根据月将加时排出天盘、四课、三传、贵人等。当用户要求六壬/大六壬排盘时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "公历年份"},
                    "month": {"type": "integer", "description": "公历月份"},
                    "day": {"type": "integer", "description": "公历日"},
                    "hour": {"type": "integer", "description": "公历小时，24小时制"},
                    "minute": {"type": "integer", "description": "分钟", "default": 0},
                    "zhan_shi": {"type": "string", "description": "占时，可用具体时辰或随机", "default": "正时"}
                },
                "required": ["year", "month", "day", "hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "qizheng_siyu_paipan",
            "description": "七政四余排盘，根据出生时间排出星盘，包括七政四余星曜位置、宫位、命度等。当用户要求七政四余排盘时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "出生年份，公历"},
                    "month": {"type": "integer", "description": "出生月份，公历"},
                    "day": {"type": "integer", "description": "出生日，公历"},
                    "hour": {"type": "integer", "description": "出生小时，24小时制"},
                    "minute": {"type": "integer", "description": "出生分钟", "default": 0},
                    "gender": {"type": "string", "description": "性别", "enum": ["男", "女"]},
                    "location": {"type": "string", "description": "出生地点", "default": "北京"}
                },
                "required": ["year", "month", "day", "hour", "gender"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "qizheng_transit",
            "description": "七政四余行运推演，推算当前或指定时间的星曜行运位置。当用户询问运势走向/行运/流年星曜时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "出生年份，公历"},
                    "month": {"type": "integer", "description": "出生月份，公历"},
                    "day": {"type": "integer", "description": "出生日，公历"},
                    "hour": {"type": "integer", "description": "出生小时，24小时制"},
                    "minute": {"type": "integer", "description": "出生分钟", "default": 0},
                    "transit_year": {"type": "integer", "description": "要推算的行运年份，默认当前年份"},
                    "transit_month": {"type": "integer", "description": "要推算的行运月份，默认当前"},
                    "transit_day": {"type": "integer", "description": "要推算的行运日，默认当前"}
                },
                "required": ["year", "month", "day", "hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ziwei_doushu_paipan",
            "description": "紫微斗数排盘，根据出生时间排出十二宫、星曜分布、四化飞星等。当用户要求紫微斗数排盘时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "出生年份，公历"},
                    "month": {"type": "integer", "description": "出生月份，公历"},
                    "day": {"type": "integer", "description": "出生日，公历"},
                    "hour": {"type": "integer", "description": "出生小时，24小时制"},
                    "minute": {"type": "integer", "description": "出生分钟", "default": 0},
                    "gender": {"type": "string", "description": "性别", "enum": ["男", "女"]},
                    "calendar": {"type": "string", "description": "历法类型", "enum": ["公历", "农历"], "default": "公历"}
                },
                "required": ["year", "month", "day", "hour", "gender"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fengshui_luopan",
            "description": "风水罗盘排盘，根据坐向、元运排出玄空飞星、八宅等盘。当用户要求看风水/房屋风水时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "zuo_du": {"type": "number", "description": "坐山度数，如 0 表示子山正中间"},
                    "xiang_du": {"type": "number", "description": "向首度数，通常为坐山+180度"},
                    "yuan_yun": {"type": "integer", "description": "当前元运，如 9 表示九运"},
                    "building_year": {"type": "integer", "description": "建房年份，公历"},
                    "purpose": {"type": "string", "description": "排盘用途", "enum": ["阳宅", "阴宅"], "default": "阳宅"}
                },
                "required": ["zuo_du", "xiang_du"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "name_xue_paipan",
            "description": "姓名学排盘，分析姓名的笔画、五行、三才五格等。当用户要求分析名字/起名/测名时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "surname": {"type": "string", "description": "姓氏，简体或繁体中文"},
                    "given_name": {"type": "string", "description": "名字，简体或繁体中文"},
                    "ti_zhi": {"type": "string", "description": "繁体字系统", "enum": ["康熙", "国标"], "default": "康熙"},
                    "gender": {"type": "string", "description": "性别，影响解读", "enum": ["男", "女"]}
                },
                "required": ["surname", "given_name", "gender"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hehun_paipan",
            "description": "八字合婚，分析两人八字的相合程度。当用户要求合婚/看两人是否合适时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "male_year": {"type": "integer", "description": "男方出生年份"},
                    "male_month": {"type": "integer", "description": "男方出生月份"},
                    "male_day": {"type": "integer", "description": "男方出生日"},
                    "male_hour": {"type": "integer", "description": "男方出生小时"},
                    "female_year": {"type": "integer", "description": "女方出生年份"},
                    "female_month": {"type": "integer", "description": "女方出生月份"},
                    "female_day": {"type": "integer", "description": "女方出生日"},
                    "female_hour": {"type": "integer", "description": "女方出生小时"}
                },
                "required": ["male_year", "male_month", "male_day", "male_hour", "female_year", "female_month", "female_day", "female_hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "huangli_chaxun",
            "description": "黄历万年历查询，查看指定日期的宜忌、节气、冲煞等。当用户询问黄历/老黄历/今日宜忌时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "公历年份"},
                    "month": {"type": "integer", "description": "公历月份"},
                    "day": {"type": "integer", "description": "公历日"}
                },
                "required": ["year", "month", "day"]
            }
        }
    }
]

# Tool → 引擎脚本 / 路由映射
TOOL_ENGINE_MAP = {
    "bazi_paipan": {"engine": "bazi", "script": "bazi.py"},
    "liuyao_paipan": {"engine": "liuyao", "script": "liuyao.py"},
    "qimen_dunjia_paipan": {"engine": "qimen", "script": "qimen.py"},
    "da_liu_ren_paipan": {"engine": "liuren", "script": "liuren.py"},
    "qizheng_siyu_paipan": {"engine": "qizheng", "script": "qizheng.py"},
    "qizheng_transit": {"engine": "qizheng", "script": "qizheng.py", "transit": True},
    "ziwei_doushu_paipan": {"engine": "ziwei", "script": "ziwei.py"},
    "fengshui_luopan": {"engine": "fengshui", "script": "fengshui.py"},
    "name_xue_paipan": {"engine": "xingming", "script": "xingming.py"},
    "hehun_paipan": {"engine": "hehun", "script": "hehun.py"},
    "huangli_chaxun": {"engine": "huangli", "script": "huangli.py"},
}

# 排盘系统提示词（还原瘦身版系统指令）
FORTUNE_SYSTEM_PROMPT_FC = """你是「随身大师」AI 命理大师，精通八字、紫微斗数、大六壬、奇门遁甲、六爻、七政四余等中国传统术数。

## 核心规则（必须严格遵守）

**当用户提供出生信息（年月日时、性别等）或要求排盘/算命时，你必须立即调用对应的排盘工具获取精确排盘数据。不要在调用工具前直接给出解读！**

## 工作流程
1. 用户提到出生时间 + 排盘/算命/分析等意图 → 立即调用对应工具（如 bazi_paipan）
2. 收到排盘结果后 → 基于数据进行专业命理分析解读
3. 如果用户没有提供完整的出生信息 → 询问缺失的信息
4. 如果用户只是闲聊 → 正常对话，不要调用工具

## 解读要求
收到排盘数据后，请按以下结构输出 Markdown：
### 1. 命局总览（表格展示四柱）
### 2. 五行旺衰
### 3. 格局层次
### 4. 关键特征
### 5. 大运走势
### 6. 当前流年

## 输出格式
- Markdown 格式（表格、标题、列表）
- 专业、客观、具体
- 禁止使用"善缘"、"感恩"、"福报"等宗教化或销售话术
- 禁止推荐购买任何产品或服务"""


def _run_pan(tool_name: str, args: dict) -> dict:
    """执行排盘工具，返回结果"""
    info = TOOL_ENGINE_MAP.get(tool_name)
    if not info:
        return {"error": f"未知工具: {tool_name}"}

    script = info["script"]
    engine = info["engine"]
    is_transit = info.get("transit", False)
    script_path = os.path.join(ENGINE_DIR, script)

    # 构造命令行参数
    cmd_args = [sys.executable, script_path, "--json"]

    if engine == "bazi":
        date_str = f"{args.get('year',2000)}-{args.get('month',1):02d}-{args.get('day',1):02d}"
        time_str = f"{args.get('hour',12):02d}:{args.get('minute',0):02d}"
        gender = args.get("gender", "男")
        cmd_args.extend([date_str, time_str, gender])

    elif engine == "liuyao":
        date_str = f"{args.get('year',2000)}-{args.get('month',1):02d}-{args.get('day',1):02d}"
        time_str = f"{args.get('hour',12):02d}:{args.get('minute',0):02d}"
        gender = args.get("gender", "男")
        cmd_args.extend([date_str, time_str, gender])

    elif engine == "liuren":
        date_str = f"{args.get('year',2000)}-{args.get('month',1):02d}-{args.get('day',1):02d}"
        time_str = f"{args.get('hour',12):02d}:{args.get('minute',0):02d}"
        cmd_args.extend([date_str, time_str])

    elif engine == "qimen":
        date_str = f"{args.get('year',2000)}-{args.get('month',1):02d}-{args.get('day',1):02d}"
        time_str = f"{args.get('hour',12):02d}:{args.get('minute',0):02d}"
        cmd_args.extend([date_str, time_str])

    elif engine == "qizheng":
        date_str = f"{args.get('year',2000)}-{args.get('month',1):02d}-{args.get('day',1):02d}"
        time_str = f"{args.get('hour',12):02d}:{args.get('minute',0):02d}"
        if is_transit:
            ty = args.get("transit_year", 2026)
            tm = args.get("transit_month", 8)
            td = args.get("transit_day", 1)
            transit_str = f"{ty}-{tm:02d}-{td:02d}"
            cmd_args.extend([date_str, time_str, "--transit", transit_str])
        else:
            cmd_args.extend([date_str, time_str])

    elif engine == "ziwei":
        date_str = f"{args.get('year',2000)}-{args.get('month',1):02d}-{args.get('day',1):02d}"
        time_str = f"{args.get('hour',12):02d}:{args.get('minute',0):02d}"
        gender = args.get("gender", "男")
        cmd_args.extend([date_str, time_str, gender])

    elif engine == "fengshui":
        zuo_du = args.get("zuo_du", 0)
        xiang_du = args.get("xiang_du", zuo_du + 180)
        cmd_args.extend([str(zuo_du), str(xiang_du)])

    elif engine == "xingming":
        surname = args.get("surname", "张")
        given_name = args.get("given_name", "三")
        cmd_args.extend([surname, given_name])

    elif engine == "hehun":
        # 合婚：传入双方日期
        m = f"{args.get('male_year',2000)}-{args.get('male_month',1):02d}-{args.get('male_day',1):02d}"
        mt = f"{args.get('male_hour',12):02d}:00"
        f_date = f"{args.get('female_year',2000)}-{args.get('female_month',1):02d}-{args.get('female_day',1):02d}"
        ft = f"{args.get('female_hour',12):02d}:00"
        cmd_args.extend([m, mt, f_date, ft])

    elif engine == "huangli":
        date_str = f"{args.get('year',2026)}-{args.get('month',1):02d}-{args.get('day',1):02d}"
        cmd_args.extend([date_str])

    try:
        r = subprocess.run(cmd_args, capture_output=True, text=True, timeout=30, cwd=ENGINE_DIR)
        if r.returncode != 0:
            return {"error": r.stderr.strip() or r.stdout.strip(), "tool": tool_name}
        try:
            result = json.loads(r.stdout)
            return {"success": True, "data": result, "tool": tool_name, "engine": engine}
        except json.JSONDecodeError:
            return {"success": True, "text": r.stdout.strip(), "tool": tool_name, "engine": engine}
    except subprocess.TimeoutExpired:
        return {"error": "排盘超时", "tool": tool_name}
    except Exception as e:
        return {"error": str(e), "tool": tool_name}


async def siliconflow_chat_with_fc(
    messages: list,
    model: str = None,
    api_key: str = None,
    stream_callback=None,
    max_iterations: int = 3,
) -> dict:
    """
    通过硅基流动 API 进行 Function Calling 对话

    Args:
        messages: [{"role":"system","content":"..."}, {"role":"user","content":"..."}]
        model: 硅基流动模型 ID
        api_key: API Key（默认从环境变量读取）
        stream_callback: 可选，流式输出回调 async fn(token: str)
        max_iterations: 最大 FC 循环次数（防止无限循环）

    Returns:
        {"reply": "最终回复", "tool_calls": [...], "duration_ms": 1234}
    """
    import time as _time
    t0 = _time.time()

    if not api_key:
        api_key = SILICONFLOW_API_KEY
    if not api_key:
        return {"reply": "⚠️ 未配置硅基流动 API Key，请设置环境变量 SILICONFLOW_API_KEY", "tool_calls": [], "duration_ms": 0}
    if not model:
        model = SILICONFLOW_MODEL

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    all_tool_calls = []  # 记录所有工具调用

    for iteration in range(max_iterations):
        payload = {
            "model": model,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto",
            "max_tokens": 8192,
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(SILICONFLOW_TIMEOUT)) as client:
                if stream_callback and iteration == 0:
                    # 流式模式（仅第一轮，工具调用走非流式）
                    payload["stream"] = True
                    collected = []
                    async with client.stream("POST", SILICONFLOW_URL, json=payload, headers=headers) as resp:
                        if resp.status_code != 200:
                            body = await resp.aread()
                            return {"reply": f"❌ 硅基流动 API 错误 {resp.status_code}: {body[:300]}", "tool_calls": all_tool_calls, "duration_ms": int((_time.time()-t0)*1000)}

                        async for line in resp.aiter_lines():
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        collected.append(content)
                                        await stream_callback(content)
                            except json.JSONDecodeError:
                                continue
                    
                    full_reply = "".join(collected)
                    return {"reply": full_reply, "tool_calls": all_tool_calls, "duration_ms": int((_time.time()-t0)*1000)}
                else:
                    # 非流式模式
                    payload["stream"] = False
                    resp = await client.post(SILICONFLOW_URL, json=payload, headers=headers)
                    if resp.status_code != 200:
                        body = resp.text
                        return {"reply": f"❌ 硅基流动 API 错误 {resp.status_code}: {body[:300]}", "tool_calls": all_tool_calls, "duration_ms": int((_time.time()-t0)*1000)}

                    data = resp.json()
                    choice = data.get("choices", [{}])[0]
                    msg = choice.get("message", {})
                    finish_reason = choice.get("finish_reason", "stop")

                    # 检查是否有 tool_calls
                    tool_calls = msg.get("tool_calls", [])
                    if tool_calls and finish_reason == "tool_calls":
                        # 执行工具调用
                        assistant_msg = {"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls}
                        messages.append(assistant_msg)

                        for tc in tool_calls:
                            fn = tc.get("function", {})
                            tool_name = fn.get("name", "")
                            try:
                                tool_args = json.loads(fn.get("arguments", "{}"))
                            except json.JSONDecodeError:
                                tool_args = {}

                            # 执行排盘
                            result = _run_pan(tool_name, tool_args)
                            all_tool_calls.append({
                                "id": tc.get("id", ""),
                                "name": tool_name,
                                "args": tool_args,
                                "result_summary": str(result)[:500] if result else "(空)"
                            })

                            # 构造 tool 结果消息
                            tool_msg = {
                                "role": "tool",
                                "tool_call_id": tc.get("id", ""),
                                "content": json.dumps(result, ensure_ascii=False)
                            }
                            messages.append(tool_msg)

                        continue  # 继续下一轮循环，让 AI 基于结果解读

                    else:
                        # 最终回复
                        reply = msg.get("content", "")
                        if stream_callback:
                            for ch in reply:
                                await stream_callback(ch)
                        return {"reply": reply, "tool_calls": all_tool_calls, "duration_ms": int((_time.time()-t0)*1000)}

        except httpx.ConnectError:
            return {"reply": "❌ 无法连接到硅基流动 API (api.siliconflow.cn)，请检查网络", "tool_calls": all_tool_calls, "duration_ms": int((_time.time()-t0)*1000)}
        except Exception as e:
            return {"reply": f"❌ 硅基流动调用异常: {str(e)[:300]}", "tool_calls": all_tool_calls, "duration_ms": int((_time.time()-t0)*1000)}

    # 超出最大迭代次数
    return {"reply": "⚠️ AI 工具调用次数超限，请简化您的请求。", "tool_calls": all_tool_calls, "duration_ms": int((_time.time()-t0)*1000)}

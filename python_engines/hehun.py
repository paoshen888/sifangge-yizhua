"""
八字合婚引擎 — 五行互补 / 生肖配对 / 日柱相合 / 综合评分
纯本地计算，¥0 费用

用法:
  python hehun.py 1996-03-10 08:00 男 1995-08-15 12:00 女
  python hehun.py 1996-03-10 08:00 男 1995-08-15 12:00 女 --json
"""

import sys
import json
import subprocess
import os

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))

# 十二地支
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 地支六合
LIU_HE = {
    ("子", "丑"): "土", ("丑", "子"): "土",
    ("寅", "亥"): "木", ("亥", "寅"): "木",
    ("卯", "戌"): "火", ("戌", "卯"): "火",
    ("辰", "酉"): "金", ("酉", "辰"): "金",
    ("巳", "申"): "水", ("申", "巳"): "水",
    ("午", "未"): "土", ("未", "午"): "土",
}

# 地支三合
SAN_HE = {
    ("申", "子", "辰"): "水局",
    ("亥", "卯", "未"): "木局",
    ("寅", "午", "戌"): "火局",
    ("巳", "酉", "丑"): "金局",
}

# 地支六冲
LIU_CHONG = {
    ("子", "午"), ("午", "子"),
    ("丑", "未"), ("未", "丑"),
    ("寅", "申"), ("申", "寅"),
    ("卯", "酉"), ("酉", "卯"),
    ("辰", "戌"), ("戌", "辰"),
    ("巳", "亥"), ("亥", "巳"),
}

# 地支三刑
SAN_XING = {
    ("寅", "巳", "申"), ("丑", "戌", "未"), ("子", "卯"), ("卯", "子"),
    ("辰", "辰"), ("午", "午"), ("酉", "酉"), ("亥", "亥"),
}

# 地支相害
LIU_HAI = {
    ("子", "未"), ("未", "子"),
    ("丑", "午"), ("午", "丑"),
    ("寅", "巳"), ("巳", "寅"),
    ("卯", "辰"), ("辰", "卯"),
    ("申", "亥"), ("亥", "申"),
    ("酉", "戌"), ("戌", "酉"),
}

# 天干五合
GAN_HE = {
    ("甲", "己"): "土", ("己", "甲"): "土",
    ("乙", "庚"): "金", ("庚", "乙"): "金",
    ("丙", "辛"): "水", ("辛", "丙"): "水",
    ("丁", "壬"): "木", ("壬", "丁"): "木",
    ("戊", "癸"): "火", ("癸", "戊"): "火",
}

# 天干五冲
GAN_CHONG = {
    ("甲", "庚"), ("庚", "甲"),
    ("乙", "辛"), ("辛", "乙"),
    ("丙", "壬"), ("壬", "丙"),
    ("丁", "癸"), ("癸", "丁"),
}

# 生肖配对
ZODIAC = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
ZODIAC_COMPAT = {
    "鼠": {"大吉": ["牛", "龙", "猴"], "忌配": ["马", "兔", "羊"]},
    "牛": {"大吉": ["鼠", "蛇", "鸡"], "忌配": ["羊", "马", "狗"]},
    "虎": {"大吉": ["猪", "马", "狗"], "忌配": ["猴", "蛇"]},
    "兔": {"大吉": ["狗", "猪", "羊"], "忌配": ["鸡", "龙", "鼠"]},
    "龙": {"大吉": ["鸡", "鼠", "猴"], "忌配": ["狗", "兔", "龙"]},
    "蛇": {"大吉": ["猴", "鸡", "牛"], "忌配": ["猪", "虎"]},
    "马": {"大吉": ["羊", "虎", "狗"], "忌配": ["鼠", "牛"]},
    "羊": {"大吉": ["马", "兔", "猪"], "忌配": ["牛", "狗", "鼠"]},
    "猴": {"大吉": ["蛇", "鼠", "龙"], "忌配": ["虎", "猪"]},
    "鸡": {"大吉": ["龙", "蛇", "牛"], "忌配": ["兔", "狗"]},
    "狗": {"大吉": ["虎", "兔", "马"], "忌配": ["龙", "鸡", "牛"]},
    "猪": {"大吉": ["兔", "羊", "虎"], "忌配": ["蛇", "猴"]},
}

# 纳音五行
NAYIN_WX = {
    "海中金": "金", "炉中火": "火", "大林木": "木", "路旁土": "土",
    "剑锋金": "金", "山头火": "火", "松柏木": "木", "城头土": "土",
    "白蜡金": "金", "霹雳火": "火", "杨柳木": "木", "城头土": "土",
    "沙中金": "金", "山下火": "火", "平地木": "木", "壁上土": "土",
    "金箔金": "金", "覆灯火": "火", "石榴木": "木", "屋上土": "土",
    "涧下水": "水", "天河水": "水", "长流水": "水", "大溪水": "水",
    "泉中水": "水", "大海水": "水",
}

# 五行相生相克
WX_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WX_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def call_bazi(date_str, time_str, gender):
    """调用八字引擎"""
    r = subprocess.run(
        [sys.executable, os.path.join(ENGINE_DIR, "bazi.py"), date_str, time_str, gender, "--json"],
        capture_output=True, text=True, timeout=30, cwd=ENGINE_DIR
    )
    if r.returncode == 0:
        try:
            return json.loads(r.stdout)
        except:
            pass
    return None


def parse_bazi(data):
    """提取关键信息"""
    if not data:
        return None
    p = data["pillars"]
    return {
        "四柱": {k: {"干": p[k]["天干"], "支": p[k]["地支"]} for k in ["年柱", "月柱", "日柱", "时柱"]},
        "日主": data["ri_gan"],
        "日支": p["日柱"]["地支"],
        "五行": data["wu_xing_counts"],
        "纳音": data["na_yin"],
        "生肖": data["lunar"]["生肖"] if "生肖" in data.get("lunar", {}) else "未知",
        "性别": "男" if data.get("sex") == "男" else "女",
    }


def analyze_hehun(m, f):
    """合婚分析"""
    items = []
    score = 50  # 基础分

    # 1. 生肖配对 (15分)
    m_zodiac = m["生肖"]
    f_zodiac = f["生肖"]
    if f_zodiac in ZODIAC_COMPAT.get(m_zodiac, {}).get("大吉", []):
        score += 15
        items.append(("生肖大吉", 15, f"{m_zodiac}与{f_zodiac}生肖相合"))
    elif f_zodiac in ZODIAC_COMPAT.get(m_zodiac, {}).get("忌配", []):
        score -= 10
        items.append(("生肖忌配", -10, f"{m_zodiac}与{f_zodiac}生肖不合"))
    else:
        items.append(("生肖平", 0, f"{m_zodiac}与{f_zodiac}生肖一般"))

    # 2. 日柱相合 (15分)
    m_day = m["日支"]
    f_day = f["日支"]
    if (m_day, f_day) in LIU_HE:
        score += 15
        items.append(("日支六合", 15, f"男日支{m_day}与女日支{f_day}六合"))
    elif (m_day, f_day) in LIU_CHONG:
        score -= 12
        items.append(("日支六冲", -12, f"男日支{m_day}与女日支{f_day}六冲"))
    elif (m_day, f_day) in LIU_HAI:
        score -= 8
        items.append(("日支相害", -8, f"男日支{m_day}与女日支{f_day}相害"))
    else:
        items.append(("日支平", 0, f"男日支{m_day}女日支{f_day}无冲合"))

    # 3. 年柱纳音 (10分)
    m_nx = m["纳音"]["年"]
    f_nx = f["纳音"]["年"]
    m_wx = NAYIN_WX.get(m_nx, "土")
    f_wx = NAYIN_WX.get(f_nx, "土")
    if WX_SHENG.get(m_wx) == f_wx:
        score += 10
        items.append(("纳音相生", 10, f"男{m_wx}({m_nx})生女{f_wx}({f_nx})"))
    elif WX_SHENG.get(f_wx) == m_wx:
        score += 6
        items.append(("纳音相生", 6, f"女{f_wx}({f_nx})生男{m_wx}({m_nx})"))
    elif m_wx == f_wx:
        score += 5
        items.append(("纳音相同", 5, f"同为{m_wx}({m_nx})"))
    elif WX_KE.get(m_wx) == f_wx:
        score -= 8
        items.append(("纳音相克", -8, f"男{m_wx}克女{f_wx}"))
    elif WX_KE.get(f_wx) == m_wx:
        score -= 6
        items.append(("纳音被克", -6, f"女{f_wx}克男{m_wx}"))

    # 4. 五行互补 (15分)
    m_wxs = m["五行"]
    f_wxs = f["五行"]
    m_weak = min(m_wxs, key=m_wxs.get)
    f_weak = min(f_wxs, key=f_wxs.get)
    if m_wxs.get(f_weak, 0) >= 2 and f_wxs.get(m_weak, 0) >= 2:
        score += 15
        items.append(("五行互补", 15, f"男缺{m_weak}女旺(f_{f_weak}={f_wxs.get(f_weak,0)}), 女缺{f_weak}男旺(m_{m_weak}={m_wxs.get(m_weak,0)})"))
    elif m_wxs.get(f_weak, 0) > 0 or f_wxs.get(m_weak, 0) > 0:
        score += 8
        items.append(("五行部分互补", 8, "一方可补另一方"))

    # 5. 天干合 (10分)
    m_gan = m["日主"]
    f_gan = f["日主"]
    if (m_gan, f_gan) in GAN_HE:
        score += 10
        items.append(("日干五合", 10, f"{m_gan}{f_gan}合化{GAN_HE[(m_gan,f_gan)]}"))
    elif (m_gan, f_gan) in GAN_CHONG:
        score -= 8
        items.append(("日干相冲", -8, f"{m_gan}与{f_gan}天干相冲"))

    # 6. 月柱检查 (5分)
    m_month = m["四柱"]["月柱"]["支"]
    f_month = f["四柱"]["月柱"]["支"]
    if m_month == f_month:
        score += 5
        items.append(("月柱相同", 5, "同气相求，性格相近"))
    elif (m_month, f_month) in LIU_HE:
        score += 4
        items.append(("月支六合", 4, f"月柱{m_month}{f_month}六合"))

    # 判定等级
    if score >= 80:
        grade = "A 天作之合"
    elif score >= 65:
        grade = "B 上等婚配"
    elif score >= 50:
        grade = "C 中等婚配"
    elif score >= 35:
        grade = "D 下等婚配"
    else:
        grade = "E 不宜婚配"

    return {
        "总分": score,
        "等级": grade,
        "评分项": [{"项目": n, "分值": s, "说明": d} for n, s, d in items],
        "建议": _get_advice(score, items),
    }


def _get_advice(score, items):
    advices = []
    if score >= 70:
        advices.append("八字匹配度较高，婚姻基础坚实")
    elif score >= 50:
        advices.append("八字匹配度中等，需后天磨合经营")
    else:
        advices.append("八字冲克较多，建议深入合婚后再做决定")

    chong_items = [i for i in items if i[0] in ("日支六冲", "日支相害", "纳音相克", "日干相冲")]
    if chong_items:
        advices.append(f"存在{len(chong_items)}项冲克，需注意沟通方式和时机选择")
    return advices


def print_hehun(result):
    print("╔═══════════════════════════════════════════════╗")
    print("║            八 字 合 婚 分 析                  ║")
    print("╠═══════════════════════════════════════════════╣")

    m = result["男方"]
    f = result["女方"]
    print(f"║ 男方: {m['日主']}日主  生肖: {m['生肖']}")
    print(f"║ 女方: {f['日主']}日主  生肖: {f['生肖']}")
    print("╠═══════════════════════════════════════════════╣")

    analysis = result["合婚"]
    print(f"║ 综合评分: {analysis['总分']}分  {analysis['等级']}")
    print("╠═══════════════════════════════════════════════╣")

    for item in analysis["评分项"]:
        sign = "+" if item['分值'] > 0 else ""
        print(f"║ {item['项目']:8s} {sign}{item['分值']:3d}  {item['说明']}")

    print("╠═══════════════════════════════════════════════╣")
    print("║ 五行: 男", m["五行"], "| 女", f["五行"])
    print(f"║ 纳音: 男{m['纳音']['年']} | 女{f['纳音']['年']}")
    print("╚═══════════════════════════════════════════════╝")

    if analysis["建议"]:
        print("\n  💡 建议:")
        for adv in analysis["建议"]:
            print(f"    • {adv}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv

    if len(args) < 2:
        print("八字合婚 — 五行互补/生肖配对/日柱相合")
        print()
        print("用法:")
        print("  python hehun.py <男日期> <男时间> 男 <女日期> <女时间> 女")
        print("  python hehun.py 1996-03-10 08:00 男 1995-08-15 12:00 女")
        print("  python hehun.py 1996-03-10 08:00 男 1995-08-15 12:00 女 --json")
        return

    # 解析参数（简单处理：前三个是男方，后三个是女方）
    # 格式: date1 time1 gender1 date2 time2 gender2
    i = 0
    m_date = args[i]; i += 1
    m_time = args[i] if i < len(args) and ":" in args[i] else "12:00"
    if ":" in args[i]: i += 1
    m_gender = args[i] if i < len(args) and args[i] in ("男", "女") else "男"
    if i < len(args) and args[i] in ("男", "女"): i += 1
    f_date = args[i] if i < len(args) else "1995-08-15"; i += 1
    f_time = args[i] if i < len(args) and ":" in args[i] else "12:00"
    if i < len(args) and ":" in args[i]: i += 1
    f_gender = "女"

    print(f"  男方: {m_date} {m_time} {m_gender}")
    print(f"  女方: {f_date} {f_time} {f_gender}")
    print()

    m_bazi = call_bazi(m_date, m_time, m_gender)
    f_bazi = call_bazi(f_date, f_time, f_gender)

    if not m_bazi or not f_bazi:
        print("八字排盘失败，请检查日期格式")
        return

    m_info = parse_bazi(m_bazi)
    f_info = parse_bazi(f_bazi)

    analysis = analyze_hehun(m_info, f_info)

    result = {
        "男方": m_info,
        "女方": f_info,
        "合婚": analysis,
    }

    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print_hehun(result)


if __name__ == '__main__':
    main()

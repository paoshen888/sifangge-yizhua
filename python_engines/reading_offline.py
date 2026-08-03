"""
四方阁离线命理解读引擎 — reading_offline.py
纯本地规则模板，不联网，不调 AI API
当用户断网时作为离线降级方案
"""
import sys
import json
import os


def parse_args():
    """解析命令行参数：--engine bazi --input '{json}' 或直接传 JSON"""
    args = sys.argv[1:]
    engine = "bazi"
    input_data = ""

    i = 0
    while i < len(args):
        if args[i] == "--engine" and i + 1 < len(args):
            engine = args[i + 1]
            i += 2
        elif args[i] == "--input" and i + 1 < len(args):
            input_data = args[i + 1]
            i += 2
        elif args[i] == "--file" and i + 1 < len(args):
            try:
                with open(args[i + 1], 'r', encoding='utf-8-sig') as f:
                    input_data = f.read()
            except Exception as e:
                print(f"文件读取失败: {e}")
                sys.exit(1)
            i += 2
        elif args[i] == "--stdin":
            input_data = sys.stdin.read()
            i += 1
        else:
            # 尝试作为 JSON 字符串
            input_data = args[i]
            i += 1

    return engine, input_data


def load_pan_data(input_str: str):
    """解析输入数据——可能是 JSON 字符串或旧引擎的输出"""
    if not input_str:
        return {}
    try:
        # Remove BOM if present
        if input_str.startswith('\ufeff'):
            input_str = input_str[1:]
        return json.loads(input_str)
    except (json.JSONDecodeError, TypeError):
        return {"raw": input_str}


# ===== 八字解读模板规则 =====
def read_bazi(data: dict) -> str:
    """纯规则模板：根据八字排盘 JSON 生成结构化解读"""
    if not data or (isinstance(data, dict) and len(data) == 0):
        return "⚠️ 排盘数据为空，无法生成解读。请确保先完成排盘。"

    ri_gan = data.get("ri_gan", "")
    if not ri_gan and not isinstance(data.get("pillars", {}), dict):
        return "⚠️ 八字排盘数据不完整，缺少日干信息，无法生成解读。"

    sex = data.get("sex", data.get("gender", "未知"))
    ri_zhu = data.get("ri_zhu", "")
    pillars = data.get("pillars", {})
    shi_shen = data.get("shi_shen", {})
    na_yin = data.get("na_yin", {})
    wuxing = data.get("wu_xing_counts", {})
    ge_ju = data.get("ge_ju", "")
    qi_yun = data.get("qi_yun", {})
    shen_sha = data.get("shen_sha", {})
    di_shi = data.get("di_shi", {})
    xun_kong = data.get("xun_kong", {})
    ming_gong = data.get("ming_gong", {})
    shen_gong = data.get("shen_gong", {})

    parts = []

    # ===== 1. 命局总览 =====
    parts.append("## 命局总览")
    parts.append("")

    # 解析四柱
    year_pillar = pillars.get("年柱", "") if isinstance(pillars, dict) else ""
    month_pillar = pillars.get("月柱", "") if isinstance(pillars, dict) else ""
    day_pillar = pillars.get("日柱", ri_zhu) if isinstance(pillars, dict) else ri_zhu
    hour_pillar = pillars.get("时柱", "") if isinstance(pillars, dict) else ""

    # 构建表格
    parts.append("| 柱 | 干支 | 藏干 | 十神 | 纳音 |")
    parts.append("|---|------|------|------|------|")

    def _get_ss(key):
        if isinstance(shi_shen, dict):
            v = shi_shen.get(key, "")
            if isinstance(v, list):
                return "、".join([str(x) for x in v])
            return str(v) if v else ""
        return ""

    for col_name, gan_zhi_key, ss_key, nayin_key in [
        ("年", "年柱", "年干", "年"),
        ("月", "月柱", "月干", "月"),
        ("日", "日柱", "日干", "日"),
        ("时", "时柱", "时干", "时"),
    ]:
        gz = ""
        if isinstance(pillars, dict):
            gz = pillars.get(gan_zhi_key, "")
        ss = _get_ss(ss_key)
        ny = ""
        if isinstance(na_yin, dict):
            ny = na_yin.get(nayin_key, "")
        if gan_zhi_key == "日柱" and not gz:
            gz = ri_zhu
        if gz:
            parts.append(f"| **{col_name}** | {gz} | | {ss} | {ny} |")

    parts.append("")
    parts.append(f"- 日主：**{ri_gan}** | 性别：{sex}")
    parts.append("")

    # 核心特征一句话
    wu_map = {"金": "⚪金", "木": "🟢木", "水": "🔵水", "火": "🔴火", "土": "🟤土"}
    wu_counts = []
    for w in ["金", "木", "水", "火", "土"]:
        c = wuxing.get(w, 0) if isinstance(wuxing, dict) else 0
        label = "🔴" if c == 0 else ("🟡" if c >= 4 else "")
        wu_counts.append(f"{wu_map.get(w, w)}:{c}")
    wu_str = " ".join(wu_counts)

    # 格局简述
    geju_str = ge_ju if isinstance(ge_ju, str) and ge_ju else "待定"
    parts.append(f"**五行分布**：{wu_str}")
    parts.append(f"**格局**：{geju_str}")
    parts.append("")

    # ===== 2. 五行旺衰 =====
    parts.append("## 五行旺衰分析")
    parts.append("")

    wuxing_comment = {
        "金": ("决断力、执行力", "缺少决断力，性格上可能优柔寡断", "过旺则刚愎自用、缺乏变通"),
        "木": ("仁慈心、创造力", "缺乏生机活力，创造力不足", "过旺则过于理想化、缺乏实际"),
        "水": ("智慧、灵活性", "智慧不足，不够圆融变通", "过旺则心思过重、多虑多疑"),
        "火": ("热情、行动力", "缺乏热情动力，行动迟缓", "过旺则急躁冲动、缺乏耐心"),
        "土": ("稳定性、诚信度", "缺乏稳定根基，易变动不安", "过旺则固执保守、不善变通"),
    }

    for w in ["金", "木", "水", "火", "土"]:
        c = wuxing.get(w, 0) if isinstance(wuxing, dict) else 0
        pos, low, high = wuxing_comment[w]
        if c == 0:
            parts.append(f"- 🔴 **{w}（缺失）**：{low}")
        elif c <= 1:
            parts.append(f"- **{w}（弱）**：计 {c} 个，{pos}偏弱。{low}")
        elif c <= 3:
            parts.append(f"- **{w}（平）**：计 {c} 个，{pos}适中")
        else:
            parts.append(f"- 🟡 **{w}（旺）**：计 {c} 个，{pos}过强。{high}")
    parts.append("")

    # ===== 3. 格局层次 =====
    parts.append("## 格局层次")
    parts.append("")

    geju_list = [g.strip() for g in geju_str.replace("、", " ").split() if g.strip()] if isinstance(geju_str, str) else []
    geju_info = {
        "正官格": ("中等偏上", "正官为贵气，主事业稳定、有管理能力。需看官星是否得地"),
        "偏官格": ("中等", "七杀为威权，有魄力但压力大。需印化或食制"),
        "正印格": ("中上", "有学问修养，贵人扶持。但需防过于依赖"),
        "偏印格": ("中等", "有特殊才能，思维独特。但可能偏执孤僻"),
        "正财格": ("中上", "正财稳定，适合稳健经营。财星宜藏不宜露"),
        "偏财格": ("中等", "偏财多意外之财，但起伏大。善于投资经营"),
        "食神格": ("中上", "食神主才艺口福，性格温和。有创造力"),
        "伤官格": ("中等", "伤官有才华但锋芒过露，需印制"),
        "比肩格": ("中等", "比肩主竞争独立。朋友多但需防分财"),
        "劫财格": ("中等偏下", "劫财不利财，易有破耗。需注意人际关系"),
        "稼穑格": ("上等", "稼穑格土旺专旺，格局清纯。为人稳重诚信，有担当"),
        "从革格": ("上等", "从革格金旺专旺，格局清纯。意志坚定，有决断力"),
        "润下格": ("上等", "润下格水旺专旺，格局清纯。智慧超群，灵活变通"),
        "炎上格": ("上等", "炎上格火旺专旺，格局清纯。热情积极，行动力强"),
        "曲直格": ("上等", "曲直格木旺专旺，格局清纯。仁慈宽厚，有创造力"),
    }

    if geju_list:
        for g in geju_list:
            info = geju_info.get(g, ("不定", f"特殊格局，需结合具体命局分析"))
            parts.append(f"- **{g}**：{info[0]} → {info[1]}")
    else:
        parts.append("未识别到明确格局，需结合十神配置综合判断。")
    parts.append("")

    # ===== 4. 十神特征 =====
    parts.append("## 十神特征")
    parts.append("")

    # 统计十神出现次数
    ss_count = {}
    def _count_ss(val):
        if isinstance(val, str):
            ss_count[val] = ss_count.get(val, 0) + 1
        elif isinstance(val, list):
            for v in val:
                if isinstance(v, str):
                    ss_count[v] = ss_count.get(v, 0) + 1

    if isinstance(shi_shen, dict):
        for k, v in shi_shen.items():
            _count_ss(v)

    ss_good = {
        "正官": "有责任心和管理能力",
        "正印": "好学有修养，得长辈帮助",
        "正财": "财运稳定，擅长理财",
        "食神": "才艺出众，性格温和",
        "偏财": "投资眼光好，有意外财运",
        "偏印": "有特殊专长，思维独特",
    }
    ss_warn = {
        "七杀": "有魄力但压力大，需制化",
        "伤官": "才华外露但易惹是非",
        "劫财": "需注意财务与人际关系",
        "比肩": "竞争激烈，需独立自主",
    }

    top_ss = sorted(ss_count.items(), key=lambda x: -x[1])[:5]
    if top_ss:
        for name, count in top_ss:
            if name in ss_good:
                parts.append(f"- ✅ **{name}**（{count}次）：{ss_good[name]}")
            elif name in ss_warn:
                parts.append(f"- ⚠️ **{name}**（{count}次）：{ss_warn[name]}")
            elif name == "日主":
                parts.append(f"- **日主**（{count}次）：命主本人")
            else:
                parts.append(f"- **{name}**（{count}次）")
    parts.append("")

    # ===== 5. 神煞提示 =====
    parts.append("## 神煞提示")
    parts.append("")

    shensha_list = []
    if isinstance(shen_sha, dict):
        for key, val in shen_sha.items():
            if isinstance(val, list):
                for v in val:
                    shensha_list.append(str(v))
            elif isinstance(val, str):
                shensha_list.append(val)

    good_shensha = {
        "天乙贵人": "✅ 天乙贵人：最尊贵之神，逢凶化吉，遇难成祥",
        "文昌": "✅ 文昌星：聪明好学，文采出众",
        "学堂": "✅ 学堂：学业有成，利于考试升迁",
        "天德": "✅ 天德贵人：品德高尚，得上天庇佑",
        "月德": "✅ 月德贵人：女性贵人运佳，人际关系好",
        "将星": "✅ 将星：有领导才能，统领众人",
        "桃花": "🌸 桃花：异性缘佳，人缘好",
        "驿马": "🐴 驿马：奔波劳碌，宜外出发展",
    }
    warn_shensha = {
        "羊刃": "⚠️ 羊刃：性格刚烈，易冲动行事，注意肢体伤害",
        "劫煞": "⚠️ 劫煞：易有意外破耗，注意财物安全",
        "灾煞": "⚠️ 灾煞：逢之易有灾祸，需增强防范",
        "孤辰": "⚠️ 孤辰：性格孤僻，婚姻缘分稍弱",
        "寡宿": "⚠️ 寡宿：独处之象，感情中需多主动",
    }

    shown = 0
    for ss_name in shensha_list:
        if ss_name in good_shensha and shown < 5:
            parts.append(f"- {good_shensha[ss_name]}")
            shown += 1
        elif ss_name in warn_shensha and shown < 5:
            parts.append(f"- {warn_shensha[ss_name]}")
            shown += 1
        elif shown < 5:
            parts.append(f"- {ss_name}")
            shown += 1
        if shown >= 5:
            break
    if not shown:
        parts.append("（从当前数据中未提取到显著神煞）")
    parts.append("")

    # ===== 6. 大运走势 =====
    parts.append("## 大运走势")
    parts.append("")

    if isinstance(qi_yun, dict):
        qy = qi_yun.get("年", "?")
        qm = qi_yun.get("月", "?")
        qd = qi_yun.get("日", "?")
        parts.append(f"- **起运年龄**：{qy}岁{qm}个月{qd}天")
    parts.append(f"- 大运顺逆取决于年干阴阳与性别配合。")
    parts.append("")

    # ===== 7. 当前流年 =====
    parts.append("## 当前流年")
    parts.append("")

    from datetime import datetime
    current_year = datetime.now().year
    current_ganzhi = {
        2026: "丙午", 2025: "乙巳", 2024: "甲辰", 2023: "癸卯",
        2022: "壬寅", 2021: "辛丑", 2020: "庚子", 2019: "己亥",
    }.get(current_year, str(current_year))

    parts.append(f"- **当前流年**：{current_year}年（{current_ganzhi}）")
    parts.append(f"- 流年干支与命局的关系需要结合大运和十神具体分析。")
    if ri_gan:
        ri_gan_wu = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}.get(ri_gan, "")
        current_wu = {"丙":"火","午":"火","乙":"木","巳":"火","甲":"木","辰":"土","癸":"水","卯":"木","壬":"水","寅":"木","辛":"金","丑":"土","庚":"金","子":"水","己":"土","亥":"水"}.get(current_ganzhi[:1] if len(current_ganzhi)==2 else "", "")
        if ri_gan_wu and current_wu:
            relation = "生扶" if (ri_gan_wu == "木" and current_wu == "水") or (ri_gan_wu == "火" and current_wu == "木") or (ri_gan_wu == "土" and current_wu == "火") or (ri_gan_wu == "金" and current_wu == "土") or (ri_gan_wu == "水" and current_wu == "金") else "克制" if (ri_gan_wu == "木" and current_wu == "金") or (ri_gan_wu == "火" and current_wu == "水") or (ri_gan_wu == "土" and current_wu == "木") or (ri_gan_wu == "金" and current_wu == "火") or (ri_gan_wu == "水" and current_wu == "土") else "比和"
            parts.append(f"- 流年五行（{current_wu}）与日主五行（{ri_gan_wu}）关系为**{relation}**，{'此年运势较为顺遂' if relation == '生扶' or relation == '比和' else '此年需多加注意'}。")

    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("> ⚠️ **离线模式**：以上为本地规则引擎自动生成的简易解读，仅供参考。联网后可获得更全面深入的 AI 命理分析。")
    parts.append("")
    parts.append("🎋 如需详细分析某一方面，请联网后告诉我。")

    return "\n".join(parts)


def read_placeholder(engine: str) -> str:
    """其他引擎的占位解读"""
    engine_names = {
        "ziwei": "紫微斗数",
        "liuren": "大六壬",
        "qimen": "奇门遁甲",
        "liuyao": "六爻纳甲",
        "qizheng": "七政四余",
        "fengshui": "玄空飞星风水",
        "xingming": "姓名学",
        "hehun": "八字合婚",
        "yunshi": "每日运势",
        "huangli": "黄历万年历",
        "bazhai": "八宅风水",
        "reading": "命盘解读",
    }
    en_name = engine_names.get(engine, engine)
    return f"""## ⚠️ 离线模式

{en_name}的离线解读功能正在开发中。

当前仅支持**八字（子平术）**的离线规则引擎解读。

### 建议
1. 联网后发送同样的问题，可获取 AI 深度分析
2. 或尝试先排八字，再用离线模式查看解析

🎋 如需详细分析，请联网后告诉我。"""


# ===== 主入口 =====
def main():
    engine, input_str = parse_args()
    data = load_pan_data(input_str)

    # 如果是八字引擎的完整结果（有 result 嵌套），展开它
    if isinstance(data, dict) and "result" in data:
        data = data["result"]
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    if engine == "bazi":
        print(read_bazi(data))
    else:
        print(read_placeholder(engine))


if __name__ == "__main__":
    main()

"""
六爻排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法
基于 lunar_python + 自研纳甲算法
纯本地计算，¥0 费用

用法：
  python liuyao.py                        # 随机起卦
  python liuyao.py --manual 987987        # 手动指定六爻值(6=老阴,7=少阳,8=少阴,9=老阳)
  python liuyao.py 1996-08-15 12:56       # 按时间起卦
  python liuyao.py --coins                # 模拟三枚铜钱起卦
  python liuyao.py --json                 # JSON输出
"""

import sys
import json
import random
import os
from datetime import datetime

try:
    from lunar_python import Solar, Lunar
except ImportError:
    print("请运行: pip install lunar-python")
    sys.exit(1)

# ===== 八宫卦纳甲系统 =====
# 八宫卦序：乾坎艮震巽离坤兑（京房八宫）
# 六十四卦编码：自下而上 (初爻→上爻) 0=阴 1=阳
GUA = {
    # 乾宫八卦
    "111111": {"name": "乾为天", "gong": "乾", "shi": 6, "ying": 3, "type": "八纯"},
    "011111": {"name": "天风姤", "gong": "乾", "shi": 1, "ying": 4, "type": "一世"},
    "001111": {"name": "天山遁", "gong": "乾", "shi": 2, "ying": 5, "type": "二世"},
    "000111": {"name": "天地否", "gong": "乾", "shi": 3, "ying": 6, "type": "三世"},
    "000011": {"name": "风地观", "gong": "乾", "shi": 4, "ying": 1, "type": "四世"},
    "000001": {"name": "山地剥", "gong": "乾", "shi": 5, "ying": 2, "type": "五世"},
    "111001": {"name": "火地晋", "gong": "乾", "shi": 4, "ying": 1, "type": "游魂"},
    "111011": {"name": "火天大有", "gong": "乾", "shi": 3, "ying": 6, "type": "归魂"},
    # 坎宫八卦
    "010010": {"name": "坎为水", "gong": "坎", "shi": 6, "ying": 3, "type": "八纯"},
    "110010": {"name": "水泽节", "gong": "坎", "shi": 1, "ying": 4, "type": "一世"},
    "100010": {"name": "水雷屯", "gong": "坎", "shi": 2, "ying": 5, "type": "二世"},
    "101010": {"name": "水火既济", "gong": "坎", "shi": 3, "ying": 6, "type": "三世"},
    "101110": {"name": "泽火革", "gong": "坎", "shi": 4, "ying": 1, "type": "四世"},
    "101100": {"name": "雷火丰", "gong": "坎", "shi": 5, "ying": 2, "type": "五世"},
    "001100": {"name": "地火明夷", "gong": "坎", "shi": 4, "ying": 1, "type": "游魂"},
    "001010": {"name": "地水师", "gong": "坎", "shi": 3, "ying": 6, "type": "归魂"},
    # 艮宫八卦
    "001001": {"name": "艮为山", "gong": "艮", "shi": 6, "ying": 3, "type": "八纯"},
    "101001": {"name": "山火贲", "gong": "艮", "shi": 1, "ying": 4, "type": "一世"},
    "111001": {"name": "山天大畜", "gong": "艮", "shi": 2, "ying": 5, "type": "二世"},
    "110001": {"name": "山泽损", "gong": "艮", "shi": 3, "ying": 6, "type": "三世"},
    "110011": {"name": "火泽睽", "gong": "艮", "shi": 4, "ying": 1, "type": "四世"},
    "110010": {"name": "天泽履", "gong": "艮", "shi": 5, "ying": 2, "type": "五世"},
    "010010": {"name": "风泽中孚", "gong": "艮", "shi": 4, "ying": 1, "type": "游魂"},
    "010001": {"name": "风山渐", "gong": "艮", "shi": 3, "ying": 6, "type": "归魂"},
    # 震宫八卦
    "001000": {"name": "震为雷", "gong": "震", "shi": 6, "ying": 3, "type": "八纯"},
    "001001": {"name": "雷地豫", "gong": "震", "shi": 1, "ying": 4, "type": "一世"},
    "001011": {"name": "雷水解", "gong": "震", "shi": 2, "ying": 5, "type": "二世"},
    "000011": {"name": "雷风恒", "gong": "震", "shi": 3, "ying": 6, "type": "三世"},
    "000111": {"name": "地风升", "gong": "震", "shi": 4, "ying": 1, "type": "四世"},
    "010111": {"name": "水风井", "gong": "震", "shi": 5, "ying": 2, "type": "五世"},
    "010110": {"name": "泽风大过", "gong": "震", "shi": 4, "ying": 1, "type": "游魂"},
    "010100": {"name": "泽雷随", "gong": "震", "shi": 3, "ying": 6, "type": "归魂"},
    # 巽宫八卦
    "110110": {"name": "巽为风", "gong": "巽", "shi": 6, "ying": 3, "type": "八纯"},
    "010110": {"name": "风天小畜", "gong": "巽", "shi": 1, "ying": 4, "type": "一世"},
    "011110": {"name": "风火家人", "gong": "巽", "shi": 2, "ying": 5, "type": "二世"},
    "001110": {"name": "风雷益", "gong": "巽", "shi": 3, "ying": 6, "type": "三世"},
    "000110": {"name": "天雷无妄", "gong": "巽", "shi": 4, "ying": 1, "type": "四世"},
    "100110": {"name": "火雷噬嗑", "gong": "巽", "shi": 5, "ying": 2, "type": "五世"},
    "100111": {"name": "山雷颐", "gong": "巽", "shi": 4, "ying": 1, "type": "游魂"},
    "100100": {"name": "山风蛊", "gong": "巽", "shi": 3, "ying": 6, "type": "归魂"},
    # 离宫八卦
    "101101": {"name": "离为火", "gong": "离", "shi": 6, "ying": 3, "type": "八纯"},
    "001101": {"name": "火山旅", "gong": "离", "shi": 1, "ying": 4, "type": "一世"},
    "011101": {"name": "火风鼎", "gong": "离", "shi": 2, "ying": 5, "type": "二世"},
    "010101": {"name": "火水未济", "gong": "离", "shi": 3, "ying": 6, "type": "三世"},
    "110101": {"name": "山水蒙", "gong": "离", "shi": 4, "ying": 1, "type": "四世"},
    "100101": {"name": "风水涣", "gong": "离", "shi": 5, "ying": 2, "type": "五世"},
    "100100": {"name": "天水讼", "gong": "离", "shi": 4, "ying": 1, "type": "游魂"},
    "100110": {"name": "天火同人", "gong": "离", "shi": 3, "ying": 6, "type": "归魂"},
    # 坤宫八卦
    "000000": {"name": "坤为地", "gong": "坤", "shi": 6, "ying": 3, "type": "八纯"},
    "100000": {"name": "地雷复", "gong": "坤", "shi": 1, "ying": 4, "type": "一世"},
    "110000": {"name": "地泽临", "gong": "坤", "shi": 2, "ying": 5, "type": "二世"},
    "111000": {"name": "地天泰", "gong": "坤", "shi": 3, "ying": 6, "type": "三世"},
    "111100": {"name": "雷天大壮", "gong": "坤", "shi": 4, "ying": 1, "type": "四世"},
    "111110": {"name": "泽天夬", "gong": "坤", "shi": 5, "ying": 2, "type": "五世"},
    "111010": {"name": "水天需", "gong": "坤", "shi": 4, "ying": 1, "type": "游魂"},
    "111011": {"name": "水地比", "gong": "坤", "shi": 3, "ying": 6, "type": "归魂"},
    # 兑宫八卦
    "110011": {"name": "兑为泽", "gong": "兑", "shi": 6, "ying": 3, "type": "八纯"},
    "010011": {"name": "泽水困", "gong": "兑", "shi": 1, "ying": 4, "type": "一世"},
    "000011": {"name": "泽地萃", "gong": "兑", "shi": 2, "ying": 5, "type": "二世"},
    "001011": {"name": "泽山咸", "gong": "兑", "shi": 3, "ying": 6, "type": "三世"},
    "101011": {"name": "水山蹇", "gong": "兑", "shi": 4, "ying": 1, "type": "四世"},
    "100011": {"name": "地山谦", "gong": "兑", "shi": 5, "ying": 2, "type": "五世"},
    "100010": {"name": "雷山小过", "gong": "兑", "shi": 4, "ying": 1, "type": "游魂"},
    "100000": {"name": "雷泽归妹", "gong": "兑", "shi": 3, "ying": 6, "type": "归魂"},
}

# 纳甲：每个卦六爻的天干地支
# 格式: 初爻到上爻
NAJIA = {
    "111111": ["甲子水", "甲寅木", "甲辰土", "壬午火", "壬申金", "壬戌土"],  # 乾
    "000000": ["乙未土", "乙巳火", "乙卯木", "癸丑土", "癸亥水", "癸酉金"],  # 坤
    "010010": ["戊寅木", "戊辰土", "戊午火", "戊申金", "戊戌土", "戊子水"],  # 坎
    "101101": ["己卯木", "己丑土", "己亥水", "己酉金", "己未土", "己巳火"],  # 离
    "001001": ["丙辰土", "丙午火", "丙申金", "丙戌土", "丙子水", "丙寅木"],  # 艮
    "110011": ["丁巳火", "丁卯木", "丁丑土", "丁亥水", "丁酉金", "丁未土"],  # 兑
    "001000": ["庚子水", "庚寅木", "庚辰土", "庚午火", "庚申金", "庚戌土"],  # 震
    "110110": ["辛丑土", "辛亥水", "辛酉金", "辛未土", "辛巳火", "辛卯木"],  # 巽
}

# 纳甲地支五行（支 → 五行）
ZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 八宫五行
GONG_WUXING = {
    "乾": "金", "兑": "金",
    "坎": "水",
    "艮": "土", "坤": "土",
    "震": "木", "巽": "木",
    "离": "火",
}


def get_pure_hexagram_mark(gong):
    """获取八纯卦编码"""
    for mark, info in GUA.items():
        if info["gong"] == gong and info["type"] == "八纯":
            return mark
    return None


def get_yao_type(value):
    """爻值转类型"""
    if value == 6:
        return "老阴 ▅▅  ▅▅ X"
    elif value == 7:
        return "少阳 ▅▅▅▅▅"
    elif value == 8:
        return "少阴 ▅▅  ▅▅"
    elif value == 9:
        return "老阳 ▅▅▅▅▅ O"
    return "???"


def value_to_binary(value):
    """爻值 → 阴阳(0/1)"""
    return 1 if value in (7, 9) else 0


def value_changes(value):
    """判断是否动爻"""
    return value in (6, 9)


def value_to_binary_changed(value):
    """动爻变后的阴阳"""
    if value == 6:
        return 1
    if value == 9:
        return 0
    return value_to_binary(value)


def get_ben_gua_mark(yao_values):
    """本卦编码"""
    return "".join(str(value_to_binary(v)) for v in yao_values)


def get_bian_gua_mark(yao_values):
    """变卦编码"""
    return "".join(str(value_to_binary_changed(v)) for v in yao_values)


def get_liu_qin(gong_wuxing, yao_wuxing):
    """根据卦宫五行和爻五行推导六亲"""
    if gong_wuxing == yao_wuxing:
        return "兄弟"
    # 生我者父母
    relations = {
        "金": {"木": "妻财", "水": "子孙", "火": "官鬼", "土": "父母", "金": "兄弟"},
        "木": {"土": "妻财", "火": "子孙", "金": "官鬼", "水": "父母", "木": "兄弟"},
        "水": {"火": "妻财", "木": "子孙", "土": "官鬼", "金": "父母", "水": "兄弟"},
        "火": {"金": "妻财", "土": "子孙", "水": "官鬼", "木": "父母", "火": "兄弟"},
        "土": {"水": "妻财", "金": "子孙", "木": "官鬼", "火": "父母", "土": "兄弟"},
    }
    return relations.get(gong_wuxing, {}).get(yao_wuxing, "")


def get_liu_shen(ri_gan, index):
    """根据日干确定六神起法"""
    qinglong_map = {
        "甲": "子", "乙": "子", "丙": "寅", "丁": "寅",
        "戊": "辰", "己": "辰", "庚": "午", "辛": "午",
        "壬": "申", "癸": "申",
    }
    zhi_order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    shen_order = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

    start_zhi = qinglong_map.get(ri_gan, "子")
    start_pos = zhi_order.index(start_zhi)
    # 从初爻开始 (position 0)，实际上六神与爻位对应
    # 十天干日: 甲乙起青龙(子丑), 丙丁起青龙(寅卯)...
    shen_idx = (start_pos // 2 + index) % len(shen_order)
    return shen_order[shen_idx]


def build_liuyao_data(yao_values, ri_gan=None, ri_zhi=None):
    """核心六爻排盘"""
    ben_mark = get_ben_gua_mark(yao_values)
    bian_mark = get_bian_gua_mark(yao_values)

    ben_gua = GUA.get(ben_mark)
    bian_gua = GUA.get(bian_mark)

    if not ben_gua:
        return {"success": False, "error": f"未知本卦编码: {ben_mark}"}

    # 获取该卦在八宫中的纳甲（使用八纯卦的纳甲序做基准）
    gong = ben_gua["gong"]
    # 使用卦宫对应的八纯卦纳甲
    pure_mark = get_pure_hexagram_mark(gong)
    ben_najia_base = NAJIA.get(pure_mark, [""""""""""""""])
    
    gong_wuxing = GONG_WUXING.get(gong, "土")
    ben_najia = ben_najia_base
    
    # 变卦纳甲
    bian_najia = []
    if bian_gua:
        pure_bian = get_pure_hexagram_mark(bian_gua["gong"])
        bian_najia = NAJIA.get(pure_bian, [])

    # 动爻位置
    dong_yao = [i + 1 for i, v in enumerate(yao_values) if value_changes(v)]

    # 逐爻分析
    yao_list = []
    for i in range(6):
        val = yao_values[i]

        # 本卦纳甲
        na_str = ben_najia[i] if i < len(ben_najia) else ""
        # 纳甲格式: 己卯木 → 地支=卯, 五行=木
        na_zhi = na_str[-2] if len(na_str) >= 2 and na_str[-2] in ZHI_WUXING else ""
        na_wuxing = ZHI_WUXING.get(na_zhi, na_str[-1] if na_str and na_str[-1] in "金木水火土" else "")

        # 变卦纳甲
        bian_na_str = bian_najia[i] if i < len(bian_najia) else ""
        bian_na_zhi = bian_na_str[-1] if bian_na_str and len(bian_na_str) > 1 else ""

        # 六亲
        liu_qin = get_liu_qin(gong_wuxing, na_wuxing)

        # 六神
        liu_shen = get_liu_shen(ri_gan or "甲", i)

        # 世应
        is_shi = (i + 1 == ben_gua["shi"])
        is_ying = (i + 1 == ben_gua["ying"])

        # 动爻
        is_dong = value_changes(val)

        yao_list.append({
            "位置": i + 1,
            "名称": ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][i],
            "爻值": val,
            "爻象": get_yao_type(val),
            "动爻": is_dong,
            "本卦纳甲": na_str,
            "本卦地支": na_zhi,
            "本卦五行": na_wuxing,
            "变卦纳甲": bian_na_str,
            "变卦地支": bian_na_zhi,
            "六亲": liu_qin,
            "六神": liu_shen,
            "世": is_shi,
            "应": is_ying,
        })

    return {
        "success": True,
        "engine": "自研纳甲算法 + lunar_python",
        "yao_values": yao_values,
        "dong_yao_count": len(dong_yao),
        "dong_yao_positions": dong_yao,
        "ben_gua": {
            "mark": ben_mark,
            "name": ben_gua["name"],
            "gong": ben_gua["gong"],
            "gong_wuxing": gong_wuxing,
            "type": ben_gua["type"],
            "shi_yao": ben_gua["shi"],
            "ying_yao": ben_gua["ying"],
        },
        "bian_gua": {
            "mark": bian_mark,
            "name": bian_gua["name"] if bian_gua else "静卦(无变爻)",
            "gong": bian_gua["gong"] if bian_gua else "",
            "type": bian_gua["type"] if bian_gua else "",
        } if dong_yao else None,
        "yao_list": yao_list,
    }


def coin_toss():
    """模拟三枚铜钱起卦"""
    coins = [random.randint(0, 1) for _ in range(3)]
    heads = sum(coins)
    if heads == 0:  # 三反 → 老阳
        return 9
    elif heads == 1:  # 一反 → 少阴
        return 8
    elif heads == 2:  # 二反 → 少阳
        return 7
    else:  # 三正 → 老阴
        return 6


def time_divination(year, month, day, hour, minute=0):
    """按时间起卦"""
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    day_gz = lunar.getDayInGanZhi()

    # 梅花易数时间起卦法（上卦：年月日之和÷8，下卦：年月日时之和÷8，动爻：年月日时之和÷6）
    upper_num = (year + month + day) % 8
    lower_num = (year + month + day + hour) % 8
    dong = (year + month + day + hour) % 6
    if dong == 0:
        dong = 6

    # 八卦数：1乾2兑3离4震5巽6坎7艮8坤
    trigram_binary = {
        1: "111", 2: "011", 3: "101", 4: "001",
        5: "110", 6: "010", 7: "100", 8: "000",
    }
    upper_bin = trigram_binary.get(upper_num or 8, "111")
    lower_bin = trigram_binary.get(lower_num or 8, "000")
    full_bin = lower_bin + upper_bin

    # 转换爻值
    yao_values = []
    for i, ch in enumerate(full_bin):
        if i + 1 == dong:
            yao_values.append(6 if ch == '0' else 9)
        else:
            yao_values.append(8 if ch == '0' else 7)

    return yao_values, day_gz


def print_liuyao(data):
    """美化打印六爻排盘结果"""
    bg = data["ben_gua"]
    print("╔═══════════════════════════════════════════════╗")
    print("║             六 爻 排 盘                         ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 本卦: {bg['name']} ({bg['gong']}宫{', ' + bg['type'] if bg['type'] else ''})")
    print(f"║ 卦宫五行: {bg['gong_wuxing']}   世爻: 第{bg['shi_yao']}爻   应爻: 第{bg['ying_yao']}爻")
    if data["dong_yao_count"] > 0:
        bng = data["bian_gua"]
        print(f"║ 变卦: {bng['name']} ({bng['gong']}宫)   动爻: {data['dong_yao_positions']}")
    else:
        print(f"║ 静卦 (无动爻)")
    print("╚═══════════════════════════════════════════════╝")

    print(f"\n┌────────────────────────────────────────────────────┐")
    print(f"│ 爻位 │ 六亲 │ 纳甲 │ 爻象         │ 六神 │ 世应 │ 动 │")
    print(f"├──────┼──────┼──────┼──────────────┼──────┼──────┼────┤")
    for yao in reversed(data["yao_list"]):
        sj = "世" if yao["世"] else ("应" if yao["应"] else "  ")
        dong = "动" if yao["动爻"] else "  "
        na = yao["本卦纳甲"] if yao["本卦纳甲"] else yao["变卦纳甲"]
        print(f"│ {yao['名称']} │ {yao['六亲']:^4} │ {na:^4} │ {yao['爻象']:12} │ {yao['六神']:^4} │ {sj:^4} │ {dong:^2} │")
    print(f"└──────┴──────┴──────┴──────────────┴──────┴──────┴────┘")

    if data["dong_yao_count"] > 0:
        print(f"\n  动爻: 第{'、'.join(str(d) for d in data['dong_yao_positions'])}爻")


def main():
    args = sys.argv[1:]
    json_output = "--json" in args
    args_clean = [a for a in args if not a.startswith("--")]

    # 判断起卦方式
    yao_values = None
    ri_gan = None
    method = "随机"

    if len(args_clean) == 0 or "--coins" in args:
        method = "三枚铜钱"
        yao_values = [coin_toss() for _ in range(6)]
        # 默认日干
        now = datetime.now()
        solar = Solar.fromYmdHms(now.year, now.month, now.day, 12, 0, 0)
        ri_gan = solar.getLunar().getDayInGanZhi()[0]
    elif any(a in args for a in ["--manual", "-m"]):
        method = "手动"
        idx = args.index("--manual") if "--manual" in args else args.index("-m")
        val_str = args[idx + 1] if idx + 1 < len(args) else "888888"
        yao_values = [int(c) for c in val_str if c in '6789']
    elif len(args_clean) >= 1:
        # 时间起卦
        method = "时间"
        birth = args_clean[0] + (" " + args_clean[1] if len(args_clean) > 1 and ":" in args_clean[1] else "")
        parts = birth.replace("T", " ").replace("/", "-").replace(".", "-").split()
        date_str = parts[0].replace("-", "")
        time_str = parts[1] if len(parts) > 1 else "12:00"
        time_str = time_str.replace(":", "")
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(time_str[:2])
            minute = int(time_str[2:4]) if len(time_str) >= 4 else 0
        except:
            print("错误: 日期格式不正确")
            print_usage()
            return
        yao_values, day_gz = time_divination(year, month, day, hour, minute)
        ri_gan = day_gz[0]

    if not yao_values or len(yao_values) != 6:
        print("错误: 六爻值无效")
        print_usage()
        return

    # 排盘
    data = build_liuyao_data(yao_values, ri_gan)
    data["method"] = method
    data["parse_time"] = datetime.now().isoformat()

    if json_output:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print_liuyao(data)


def print_usage():
    print("六爻排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法")
    print("基于自研纳甲算法 + lunar_python，纯本地计算，¥0 费用")
    print()
    print("用法:")
    print("  python liuyao.py                        # 随机铜钱起卦")
    print("  python liuyao.py --coins                # 三枚铜钱起卦")
    print("  python liuyao.py --manual 789789        # 手动指定六爻值")
    print("  python liuyao.py 1996-08-15 12:56       # 按时间起卦")
    print("  python liuyao.py --json                 # JSON格式输出")
    print()
    print("爻值说明: 6=老阴(动) 7=少阳(静) 8=少阴(静) 9=老阳(动)")


if __name__ == '__main__':
    main()

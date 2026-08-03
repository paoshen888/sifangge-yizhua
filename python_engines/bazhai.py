"""
八宅排盘 + 紫白飞星排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法
纯本地计算，¥0 费用

用法：
  python bazhai.py 1996-08-15 12:56 男
  python bazhai.py 1996-08-15 12:56 男 --json
  python bazhai.py 1996-08-15 12:56 男 --zibai  # 仅紫白飞星
"""

import sys
import json
from datetime import datetime

try:
    from lunar_python import Solar, Lunar
except ImportError:
    print("请运行: pip install lunar-python")
    sys.exit(1)

# ===== 八宅 =====
# 八卦 → 卦名, 五行, 方位, 东西四命
BAGUA_INFO = {
    1: {"name": "坎", "wuxing": "水", "fangwei": "北", "group": "东四命"},
    2: {"name": "坤", "wuxing": "土", "fangwei": "西南", "group": "西四命"},
    3: {"name": "震", "wuxing": "木", "fangwei": "东", "group": "东四命"},
    4: {"name": "巽", "wuxing": "木", "fangwei": "东南", "group": "东四命"},
    6: {"name": "乾", "wuxing": "金", "fangwei": "西北", "group": "西四命"},
    7: {"name": "兑", "wuxing": "金", "fangwei": "西", "group": "西四命"},
    8: {"name": "艮", "wuxing": "土", "fangwei": "东北", "group": "西四命"},
    9: {"name": "离", "wuxing": "火", "fangwei": "南", "group": "东四命"},
}

# 八宅吉凶位（各方位的四吉四凶，以命卦/宅卦为准）
BAZHAI_POSITIONS = {
    1: {  # 坎命/坎宅
        "生气": "巽(东南)", "天医": "震(东)", "延年": "离(南)", "伏位": "坎(北)",
        "绝命": "坤(西南)", "五鬼": "艮(东北)", "六煞": "乾(西北)", "祸害": "兑(西)",
    },
    2: {  # 坤命/坤宅
        "生气": "艮(东北)", "天医": "兑(西)", "延年": "乾(西北)", "伏位": "坤(西南)",
        "绝命": "坎(北)", "五鬼": "震(东)", "六煞": "离(南)", "祸害": "巽(东南)",
    },
    3: {  # 震命/震宅
        "生气": "离(南)", "天医": "坎(北)", "延年": "巽(东南)", "伏位": "震(东)",
        "绝命": "兑(西)", "五鬼": "坤(西南)", "六煞": "艮(东北)", "祸害": "乾(西北)",
    },
    4: {  # 巽命/巽宅
        "生气": "坎(北)", "天医": "离(南)", "延年": "震(东)", "伏位": "巽(东南)",
        "绝命": "艮(东北)", "五鬼": "乾(西北)", "六煞": "兑(西)", "祸害": "坤(西南)",
    },
    6: {  # 乾命/乾宅
        "生气": "兑(西)", "天医": "艮(东北)", "延年": "坤(西南)", "伏位": "乾(西北)",
        "绝命": "离(南)", "五鬼": "震(东)", "六煞": "坎(北)", "祸害": "巽(东南)",
    },
    7: {  # 兑命/兑宅
        "生气": "乾(西北)", "天医": "坤(西南)", "延年": "艮(东北)", "伏位": "兑(西)",
        "绝命": "震(东)", "五鬼": "离(南)", "六煞": "巽(东南)", "祸害": "坎(北)",
    },
    8: {  # 艮命/艮宅
        "生气": "坤(西南)", "天医": "乾(西北)", "延年": "兑(西)", "伏位": "艮(东北)",
        "绝命": "巽(东南)", "五鬼": "坎(北)", "六煞": "震(东)", "祸害": "离(南)",
    },
    9: {  # 离命/离宅
        "生气": "震(东)", "天医": "巽(东南)", "延年": "坎(北)", "伏位": "离(南)",
        "绝命": "乾(西北)", "五鬼": "兑(西)", "六煞": "坤(西南)", "祸害": "艮(东北)",
    },
}


def calc_ming_gua(solar, sex):
    """计算八宅命卦"""
    year = solar.getYear()
    lunar = solar.getLunar()

    # 命卦计算方法：公历年份后两位数之和÷9 取余
    # (1900-1999年用此公式)
    if 1900 <= year <= 1999:
        base = year - 1900
        sum_digits = base // 10 + base % 10
        gua_num = (10 - sum_digits % 9) % 9
        if gua_num == 0:
            gua_num = 9
        # 命卦调整：男取余，女取互补
        if sex == 1:  # 男
            pass
        else:  # 女
            gua_num_temp = (5 + sum_digits) % 9
            if gua_num_temp == 0:
                gua_num_temp = 9
            gua_num = gua_num_temp
    elif 2000 <= year <= 2099:
        base = year - 2000
        sum_digits = base // 10 + base % 10
        if sex == 1:
            gua_num = (9 - sum_digits % 9) % 9 or 9
        else:
            gua_num = (6 + sum_digits % 9) % 9 or 9
    else:
        gua_num = 1

    if gua_num == 5:
        gua_num = 8 if sex == 2 else 2  # 女艮男坤

    return gua_num


def build_bazhai_data(solar, sex):
    """八宅排盘"""
    gua_num = calc_ming_gua(solar, sex)
    info = BAGUA_INFO.get(gua_num, BAGUA_INFO[1])
    positions = BAZHAI_POSITIONS.get(gua_num, BAZHAI_POSITIONS[1])

    return {
        "命卦": gua_num,
        "命卦名": info["name"],
        "五行": info["wuxing"],
        "方位": info["fangwei"],
        "东西四命": info["group"],
        "吉凶方位": positions,
    }


def calc_year_zibai(year):
    """计算年紫白飞星入中宫数"""
    # 年紫白: (11 - year%9) 的简化
    remainder = (year % 9)
    if remainder == 0:
        remainder = 9
    zhong_gong = (11 - remainder) % 9 or 9
    return zhong_gong


def build_zibai_data(solar):
    """紫白飞星排盘"""
    year = solar.getYear()
    zhong = calc_year_zibai(year)

    # 九宫飞星顺飞轨迹: 中→乾→兑→艮→离→坎→坤→震→巽
    fly_path = [5, 6, 7, 8, 9, 1, 2, 3, 4]

    # 以中宫起星，按轨迹排布
    gong_wei = {}
    idx = fly_path.index(zhong)
    for pos in fly_path:
        star = fly_path[(idx + fly_path.index(pos)) % 9]
        if star == 0:
            star = 9
        gong_wei[pos] = star
        idx = fly_path.index(star)

    # 正确的飞星算法：从中宫推
    result = {}
    star_seq = [(zhong + i - 1) % 9 + 1 for i in range(9)]

    gan_names = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
    fly_order = [5, 6, 7, 8, 9, 1, 2, 3, 4]

    for i, pos in enumerate(fly_order):
        result[gan_names[pos]] = star_seq[i]

    return {
        "年份": year,
        "入中星": star_seq[0],
        "飞星分布": result,
    }


def print_bazhai(data):
    """美化打印八宅结果"""
    b = data["bazhai"]
    print("╔═══════════════════════════════════════════════╗")
    print("║             八 宅 命 卦                          ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 命卦: {b['命卦']} {b['命卦名']} ({b['五行']})")
    print(f"║ 方位: {b['方位']}   命别: {b['东西四命']}")
    print("╚═══════════════════════════════════════════════╝")

    pos = b["吉凶方位"]
    print(f"\n┌─── 八宅吉凶方位 ──────────────────────────┐")
    print(f"│ 四吉:                                          │")
    print(f"│   生气(最大吉): {pos['生气']:20s}         │")
    print(f"│   天医(次吉):   {pos['天医']:20s}         │")
    print(f"│   延年(中吉):   {pos['延年']:20s}         │")
    print(f"│   伏位(小吉):   {pos['伏位']:20s}         │")
    print(f"├──────────────────────────────────────────────┤")
    print(f"│ 四凶:                                          │")
    print(f"│   绝命(最大凶): {pos['绝命']:20s}         │")
    print(f"│   五鬼(次凶):   {pos['五鬼']:20s}         │")
    print(f"│   六煞(中凶):   {pos['六煞']:20s}         │")
    print(f"│   祸害(小凶):   {pos['祸害']:20s}         │")
    print(f"└──────────────────────────────────────────────┘")


def print_zibai(data):
    """美化打印紫白飞星"""
    z = data["zibai"]
    fs = z["飞星分布"]
    print(f"\n┌──────────── 紫白飞星 {z['年份']}年 ────────────┐")
    print(f"│        (入中星: {z['入中星']} )                              │")
    print(f"├────────────┬────────────┬────────────┤")
    print(f"│  巽({fs.get('巽','')})       │  离({fs.get('离','')})       │  坤({fs.get('坤','')})       │")
    print(f"├────────────┼────────────┼────────────┤")
    print(f"│  震({fs.get('震','')})       │  中({fs.get('中','')})       │  兑({fs.get('兑','')})       │")
    print(f"├────────────┼────────────┼────────────┤")
    print(f"│  艮({fs.get('艮','')})       │  坎({fs.get('坎','')})       │  乾({fs.get('乾','')})       │")
    print(f"└────────────┴────────────┴────────────┘")

    # 星色
    color_map = {1: "白(吉)", 2: "黑(凶)", 3: "碧(凶)", 4: "绿(凶)",
                 5: "黄(凶)", 6: "白(吉)", 7: "赤(凶)", 8: "白(吉)", 9: "紫(吉)"}
    print(f"  紫白星: 1{color_map[1]} 6{color_map[6]} 8{color_map[8]} 9{color_map[9]}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    zibai_only = "--zibai" in sys.argv

    if len(args) < 1:
        print("八宅+紫白排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法")
        print("纯本地计算，¥0 费用")
        print()
        print("用法:")
        print("  python bazhai.py <日期> <性别>          # 八宅命卦+紫白飞星")
        print("  python bazhai.py <日期> <性别> --json")
        print("  python bazhai.py <日期> <性别> --zibai  # 仅紫白飞星")
        print()
        print("示例:")
        print("  python bazhai.py 1996-08-15 12:56 男")
        return

    # 性别在最后一个非选项参数
    sex_arg = None
    for a in reversed(args):
        if a in ("男", "女", "0", "1"):
            sex_arg = a
            break
    sex = 0 if sex_arg in ("女", "0") else 1

    # 日期在第一个参数，时间可选在第二个
    birth = args[0]
    if len(args) > 1 and ":" in args[1]:
        birth += " " + args[1]

    parts = birth.replace("T", " ").replace("/", "-").replace(".", "-").split()
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else "12:00"

    # 支持多种日期格式: 1996 / 1996-03 / 1996-03-10 / 19960310
    clean = date_part.replace("-", "")
    try:
        year = int(clean[:4])
        month = int(clean[4:6]) if len(clean) >= 6 else 6
        day = int(clean[6:8]) if len(clean) >= 8 else 15
        tp = time_part.replace(":", "")
        hour = int(tp[:2]) if len(tp) >= 2 else 12
        minute = int(tp[2:4]) if len(tp) >= 4 else 0
    except Exception as e:
        print(f"错误: {e}")
        return

    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)

    bazhai_data = build_bazhai_data(solar, sex)
    zibai_data = build_zibai_data(solar)

    result = {
        "bazhai": bazhai_data,
        "zibai": zibai_data,
        "parse_time": datetime.now().isoformat(),
        "engine": "自研 + lunar_python",
        "gregorian": {
            "year": year, "month": month, "day": day, "hour": hour, "minute": minute
        }
    }

    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        if not zibai_only:
            print_bazhai(result)
        print_zibai(result)


if __name__ == '__main__':
    main()

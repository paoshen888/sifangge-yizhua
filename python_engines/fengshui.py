"""
玄空飞星风水 — 宅命相配 + 九宫飞星 + 室内布局
基于自研算法 (紫白飞星+八宅+玄空)
纯本地计算，¥0 费用

用法:
  python fengshui.py 2026                      # 2026年飞星
  python fengshui.py 2026 --house 4            # 巽宅飞星
  python fengshui.py 1996 男                    # 命卦+宅命相配
  python fengshui.py 2026 --month              # 月飞星
  python fengshui.py 2026 --json
"""

import sys
import json
from datetime import datetime

# ===== 九宫格模板 =====
# 位置: 1坎 2坤 3震 4巽 5中 6乾 7兑 8艮 9离
GONG_WEI = {
    1: {"name":"坎","dir":"北","element":"水","color":"黑"},
    2: {"name":"坤","dir":"西南","element":"土","color":"黄"},
    3: {"name":"震","dir":"东","element":"木","color":"碧"},
    4: {"name":"巽","dir":"东南","element":"木","color":"绿"},
    5: {"name":"中","dir":"中","element":"土","color":"黄"},
    6: {"name":"乾","dir":"西北","element":"金","color":"白"},
    7: {"name":"兑","dir":"西","element":"金","color":"赤"},
    8: {"name":"艮","dir":"东北","element":"土","color":"白"},
    9: {"name":"离","dir":"南","element":"火","color":"紫"},
}

# 紫白星性质
STAR_NATURE = {
    1: {"name":"一白贪狼","nature":"吉(水)","effect":"桃花人缘、文昌运","element":"水"},
    2: {"name":"二黑巨门","nature":"凶(土)","effect":"病符、是非","element":"土"},
    3: {"name":"三碧禄存","nature":"凶(木)","effect":"口舌争斗、官非","element":"木"},
    4: {"name":"四绿文曲","nature":"平(木)","effect":"文昌学业、桃花","element":"木"},
    5: {"name":"五黄廉贞","nature":"大凶(土)","effect":"灾祸、疾病","element":"土"},
    6: {"name":"六白武曲","nature":"吉(金)","effect":"偏财、权势","element":"金"},
    7: {"name":"七赤破军","nature":"凶(金)","effect":"盗贼、口舌、破损","element":"金"},
    8: {"name":"八白左辅","nature":"大吉(土)","effect":"正财、置业、旺丁","element":"土"},
    9: {"name":"九紫右弼","nature":"吉(火)","effect":"喜事、姻缘、添丁","element":"火"},
}

# 飞星轨迹 (中→乾→兑→艮→离→坎→坤→震→巽)
FLY_PATH = [5, 6, 7, 8, 9, 1, 2, 3, 4]

# 八宅宅卦
HOUSE_GUA = {
    1: "坎宅(坐北朝南)", 2: "坤宅(坐西南朝东北)", 3: "震宅(坐东朝西)",
    4: "巽宅(坐东南朝西北)", 6: "乾宅(坐西北朝东南)", 7: "兑宅(坐西朝东)",
    8: "艮宅(坐东北朝西南)", 9: "离宅(坐南朝北)",
}

# 宅命相配结果
MATCH_RESULTS = {
    "东四命+东四宅": "大吉 — 宅命相配，家运兴旺",
    "东四命+西四宅": "不吉 — 宅命不配，建议调整",
    "西四命+西四宅": "大吉 — 宅命相配，家运兴旺",
    "西四命+东四宅": "不吉 — 宅命不配，建议调整",
}


def calc_fly_stars(zhong_gong_star):
    """计算九宫飞星排布"""
    stars = {}
    fly_seq = [5, 6, 7, 8, 9, 1, 2, 3, 4]
    start_idx = fly_seq.index(zhong_gong_star)
    for i, pos in enumerate(fly_seq):
        star = fly_seq[(start_idx + i) % 9]
        stars[pos] = star
    return stars


def calc_year_star(year):
    """年紫白入中星: (11 - year%9) 简化"""
    remainder = year % 9
    if remainder == 0:
        remainder = 9
    return (11 - remainder) % 9 or 9


def calc_month_star(year, month):
    """月紫白入中星"""
    # 子午卯酉年正月八白入中, 辰戌丑未年正月五黄入中, 寅申巳亥年正月二黑入中
    year_zhi_map = {
        0:"子",1:"丑",2:"寅",3:"卯",4:"辰",5:"巳",
        6:"午",7:"未",8:"申",9:"酉",10:"戌",11:"亥"
    }
    zhi = year_zhi_map.get(year % 12, "子")

    if zhi in ["子","午","卯","酉"]:
        base = 8
    elif zhi in ["辰","戌","丑","未"]:
        base = 5
    else:  # 寅申巳亥
        base = 2

    # 月飞星逆排
    return (base - (month - 1) + 9) % 9 or 9


def calc_ming_gua(year, gender):
    """计算命卦"""
    remainder = year % 9
    if remainder == 0:
        remainder = 9
    if gender == "男":
        gua = (11 - remainder) % 9 or 9
    else:
        gua = (4 + remainder) % 9 or 9
    if gua == 5:
        gua = 8 if gender == "女" else 2
    return gua


def get_group(gua):
    """东西四命分组"""
    if gua in [1, 3, 4, 9]:
        return "东四命"
    return "西四命"


def get_house_group(house_gua):
    """东西四宅分组"""
    if house_gua in [1, 3, 4, 9]:
        return "东四宅"
    return "西四宅"


def calc_xuan_kong_period(year):
    """三元九运：上元123运，中元456运，下元789运。每运20年。
    2004-2023: 八运, 2024-2043: 九运"""
    if 1864 <= year <= 1883: return 1
    if 1884 <= year <= 1903: return 2
    if 1904 <= year <= 1923: return 3
    if 1924 <= year <= 1943: return 4
    if 1944 <= year <= 1963: return 5
    if 1964 <= year <= 1983: return 6
    if 1984 <= year <= 2003: return 7
    if 2004 <= year <= 2023: return 8
    if 2024 <= year <= 2043: return 9
    period = 9
    if year > 2043:
        period = ((year - 2024) // 20 + 9) % 9 or 9
    elif year < 1864:
        period = (9 - (1864 - year - 1) // 20) % 9 or 9
    else:
        period = ((year - 1864) // 20 + 1) % 9 or 9
    return period


def _fly_stars_from_gong(start_star, start_gong, forward):
    """从指定宫位起星，按洛书轨迹顺飞(forward=True)或逆飞(forward=False)"""
    fly_seq = [5, 6, 7, 8, 9, 1, 2, 3, 4]
    idx = fly_seq.index(start_gong)
    stars = {}
    for i, pos in enumerate(fly_seq):
        di = i - idx
        if forward:
            star = ((start_star - 1 + di) % 9) + 1
        else:
            star = ((start_star - 1 - di) % 9) + 1
        stars[pos] = star
    return stars


def _analyze_star_combo(shan, xiang, gong):
    """分析山向二星组合吉凶"""
    combos = {
        (1, 6): "金水相生，主文贵、财运",
        (1, 8): "土水相克但有财，宜静",
        (1, 9): "水火既济，旺文昌桃花",
        (2, 8): "土土比和，旺财旺丁",
        (2, 9): "火土相生，有财但防病",
        (3, 4): "木木比和，文昌旺但防口舌",
        (3, 7): "金木交战，口舌官非",
        (4, 6): "金克木，文书受阻",
        (4, 9): "木火通明，文昌旺",
        (5, 2): "二五交加，重病灾祸",
        (5, 9): "火土相生，但五黄凶",
        (6, 8): "土金相生，旺财禄",
        (6, 9): "火克金，防官非",
        (7, 8): "土金相生，旺偏财",
        (7, 9): "火克金，口舌破财",
        (8, 9): "火土相生，旺丁旺财，大吉",
    }
    key = tuple(sorted([shan, xiang]))
    rev_key = (xiang, shan) if key not in combos else key
    base = combos.get(key, combos.get(rev_key, ""))
    if 2 in (shan, xiang) and 5 in (shan, xiang):
        base += " 二五交加必损主，重病灾祸，急需化解。"
    elif shan in (2, 5) or xiang in (2, 5):
        base += " 宜化解病符。"
    if shan == 8 and xiang == 8:
        base = "双星会坐/会向，当运旺星，大吉。" + base
    if shan == 9 and xiang == 9:
        base = "双九到宫，远旺吉星，待时而发。" + base
    return base or "此宫组合需结合实地勘察判断"


def calc_xuan_kong_stars(year, mountain_zhi):
    """
    玄空飞星三盘：运星 + 山星 + 向星 九宫排布
    mountain_zhi: 坐山地支 (子/丑/寅/卯/辰/巳/午/未/申/酉/戌/亥)
    """
    period = calc_xuan_kong_period(year)

    SHAN_24 = {
        '子': {'gong': 1, 'yin_yang': '阴'}, '癸': {'gong': 1, 'yin_yang': '阴'}, '壬': {'gong': 1, 'yin_yang': '阳'},
        '丑': {'gong': 8, 'yin_yang': '阴'}, '艮': {'gong': 8, 'yin_yang': '阳'}, '寅': {'gong': 8, 'yin_yang': '阳'},
        '卯': {'gong': 3, 'yin_yang': '阴'}, '乙': {'gong': 3, 'yin_yang': '阴'}, '甲': {'gong': 3, 'yin_yang': '阳'},
        '辰': {'gong': 4, 'yin_yang': '阳'}, '巽': {'gong': 4, 'yin_yang': '阳'}, '巳': {'gong': 4, 'yin_yang': '阳'},
        '午': {'gong': 9, 'yin_yang': '阴'}, '丁': {'gong': 9, 'yin_yang': '阴'}, '丙': {'gong': 9, 'yin_yang': '阳'},
        '未': {'gong': 2, 'yin_yang': '阴'}, '坤': {'gong': 2, 'yin_yang': '阳'}, '申': {'gong': 2, 'yin_yang': '阳'},
        '酉': {'gong': 7, 'yin_yang': '阴'}, '辛': {'gong': 7, 'yin_yang': '阴'}, '庚': {'gong': 7, 'yin_yang': '阳'},
        '戌': {'gong': 6, 'yin_yang': '阴'}, '乾': {'gong': 6, 'yin_yang': '阳'}, '亥': {'gong': 6, 'yin_yang': '阳'},
    }

    if mountain_zhi not in SHAN_24:
        return {}

    shan_info = SHAN_24[mountain_zhi]
    gong_num = shan_info['gong']
    is_yang = shan_info['yin_yang'] == '阳'

    # 向宫：坐山对宫
    xiang_gong = ((gong_num + 4) % 9) or 9

    # 山星飞布（从坐山宫起 period，阳顺阴逆）
    shan_stars = _fly_stars_from_gong(period, gong_num, is_yang)
    # 向星飞布（从向宫起 period，阴阳与山相反）
    xiang_stars = _fly_stars_from_gong(period, xiang_gong, not is_yang)

    result = {}
    for pos in range(1, 10):
        ss = shan_stars.get(pos, 0)
        xs = xiang_stars.get(pos, 0)
        combo = f"{ss}-{xs}"
        analysis = _analyze_star_combo(ss, xs, pos)

        info = GONG_WEI[pos]
        result[str(pos)] = {
            "gong_name": info["name"],
            "gong_dir": info["dir"],
            "yun_star": period,
            "shan_star": ss,
            "xiang_star": xs,
            "combo": combo,
            "shan_name": STAR_NATURE.get(ss, {}).get("name", f"{ss}星"),
            "xiang_name": STAR_NATURE.get(xs, {}).get("name", f"{xs}星"),
            "analysis": analysis,
            "yun_period": f"{'上' if period<=3 else '中' if period<=6 else '下'}元{period}运",
        }

    return result

def build_fengshui_year(year, house_gua=None):
    """年飞星风水"""
    zhong = calc_year_star(year)
    stars = calc_fly_stars(zhong)

    layout = {}
    for pos, star in stars.items():
        info = GONG_WEI[pos]
        sn = STAR_NATURE.get(star, {})
        item = {
            "star": star,
            "star_name": sn.get("name",""),
            "nature": sn.get("nature",""),
            "effect": sn.get("effect",""),
            "element": sn.get("element",""),
            "gong_name": info["name"],
            "gong_dir": info["dir"],
        }

        # 宅星组合判断
        if house_gua and pos == house_gua:
            item["is_house"] = True

        # 化解建议
        if star == 5:
            item["advice"] = "宜静不宜动，放铜铃/六帝钱化解"
        elif star == 2:
            item["advice"] = "挂铜葫芦或六帝钱"
        elif star == 3:
            item["advice"] = "放红色物品(火泄木)"
        elif star == 7:
            item["advice"] = "放蓝色/黑色物品(水泄金)"
        elif star == 8:
            item["advice"] = "催旺: 放聚宝盆/黄水晶"
        elif star == 9:
            item["advice"] = "催旺: 放红色/紫色饰品"

        layout[str(pos)] = item

    month_zhong = calc_month_star(year, datetime.now().month)
    month_stars = calc_fly_stars(month_zhong)

    return {
        "year": year,
        "year_star": zhong,
        "star_name": STAR_NATURE.get(zhong,{}).get("name",""),
        "month_star": month_zhong,
        "layout": layout,
        "month_layout": {str(k): v for k, v in month_stars.items()},
        "house_gua": house_gua,
        "house_name": HOUSE_GUA.get(house_gua, "") if house_gua else "",
        "period": calc_xuan_kong_period(year),
        "period_name": f"{'上' if calc_xuan_kong_period(year)<=3 else '中' if calc_xuan_kong_period(year)<=6 else '下'}元{calc_xuan_kong_period(year)}运",
    }


def build_fengshui_ming(year, gender):
    """命卦风水"""
    gua = calc_ming_gua(year, gender)
    info = GONG_WEI[gua]
    group = get_group(gua)

    # 四吉方四凶方 (以命卦推)
    positions = {
        1: {"生气":"巽(东南)","天医":"震(东)","延年":"离(南)","伏位":"坎(北)",
            "绝命":"坤(西南)","五鬼":"艮(东北)","六煞":"乾(西北)","祸害":"兑(西)"},
        3: {"生气":"离(南)","天医":"坎(北)","延年":"巽(东南)","伏位":"震(东)",
            "绝命":"兑(西)","五鬼":"坤(西南)","六煞":"艮(东北)","祸害":"乾(西北)"},
        4: {"生气":"坎(北)","天医":"离(南)","延年":"震(东)","伏位":"巽(东南)",
            "绝命":"艮(东北)","五鬼":"乾(西北)","六煞":"兑(西)","祸害":"坤(西南)"},
        9: {"生气":"震(东)","天医":"巽(东南)","延年":"坎(北)","伏位":"离(南)",
            "绝命":"乾(西北)","五鬼":"兑(西)","六煞":"坤(西南)","祸害":"艮(东北)"},
        2: {"生气":"艮(东北)","天医":"兑(西)","延年":"乾(西北)","伏位":"坤(西南)",
            "绝命":"坎(北)","五鬼":"震(东)","六煞":"离(南)","祸害":"巽(东南)"},
        6: {"生气":"兑(西)","天医":"艮(东北)","延年":"坤(西南)","伏位":"乾(西北)",
            "绝命":"离(南)","五鬼":"震(东)","六煞":"坎(北)","祸害":"巽(东南)"},
        7: {"生气":"乾(西北)","天医":"坤(西南)","延年":"艮(东北)","伏位":"兑(西)",
            "绝命":"震(东)","五鬼":"离(南)","六煞":"巽(东南)","祸害":"坎(北)"},
        8: {"生气":"坤(西南)","天医":"乾(西北)","延年":"兑(西)","伏位":"艮(东北)",
            "绝命":"巽(东南)","五鬼":"坎(北)","六煞":"震(东)","祸害":"离(南)"},
    }

    return {
        "year": year,
        "gender": gender,
        "ming_gua": gua,
        "ming_gua_name": info["name"],
        "ming_gua_element": info["element"],
        "group": group,
        "positions": positions.get(gua, {}),
        "period": calc_xuan_kong_period(year),
        "period_name": f"{'上' if calc_xuan_kong_period(year)<=3 else '中' if calc_xuan_kong_period(year)<=6 else '下'}元{calc_xuan_kong_period(year)}运",
        "compatible_houses": [h for h, g in [(1,"东"),(3,"东"),(4,"东"),(9,"东"),
                                              (2,"西"),(6,"西"),(7,"西"),(8,"西")]
                               if g == ("东" if "东" in group else "西")],
    }


def print_year_fengshui(data):
    """打印年飞星"""
    fs = data["fengshui"]
    print("╔═══════════════════════════════════════════════╗")
    print("║         玄 空 飞 星 风 水                      ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ {fs['year']}年紫白飞星  (年星: {fs['star_name']}入中, 月星: {STAR_NATURE.get(fs['month_star'],{}).get('name','')}入中)")
    print(f"║ 宅: {fs.get('house_name','通用')}")
    print("╚═══════════════════════════════════════════════╝")

    layout = fs["layout"]
    print(f"\n┌──────────── 九宫飞星 ────────────┐")
    print(f"│  巽({layout.get('4',{}).get('star','')})       离({layout.get('9',{}).get('star','')})       坤({layout.get('2',{}).get('star','')})        │")
    print(f"│  {layout.get('4',{}).get('star_name',''):10s}  {layout.get('9',{}).get('star_name',''):10s}  {layout.get('2',{}).get('star_name',''):10s} │")
    print(f"├─────────────────────────────────┤")
    print(f"│  震({layout.get('3',{}).get('star','')})       中({layout.get('5',{}).get('star','')})       兑({layout.get('7',{}).get('star','')})        │")
    print(f"│  {layout.get('3',{}).get('star_name',''):10s}  {layout.get('5',{}).get('star_name',''):10s}  {layout.get('7',{}).get('star_name',''):10s} │")
    print(f"├─────────────────────────────────┤")
    print(f"│  艮({layout.get('8',{}).get('star','')})       坎({layout.get('1',{}).get('star','')})       乾({layout.get('6',{}).get('star','')})        │")
    print(f"│  {layout.get('8',{}).get('star_name',''):10s}  {layout.get('1',{}).get('star_name',''):10s}  {layout.get('6',{}).get('star_name',''):10s} │")
    print(f"└─────────────────────────────────┘")

    # 吉凶分析
    print(f"\n  吉位: ", end="")
    for k, v in layout.items():
        if v.get("star") in [1, 6, 8, 9]:
            print(f"{v['gong_name']}({v['gong_dir']}, {v['star_name']}) ", end="")
    print()
    print(f"  凶位: ", end="")
    for k, v in layout.items():
        if v.get("star") in [2, 3, 5, 7]:
            print(f"{v['gong_name']}({v['gong_dir']}, {v['star_name']}) ", end="")
    print()

    # 化解
    print(f"\n  化解建议:")
    for k, v in layout.items():
        if v.get("advice"):
            print(f"    {v['gong_name']}({v['gong_dir']}): {v['advice']}")


def print_ming_fengshui(data):
    """打印命卦风水"""
    m = data["ming"]
    print("╔═══════════════════════════════════════════════╗")
    print("║         命 卦 风 水                            ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 出生年: {m['year']}  性别: {m['gender']}")
    print(f"║ 命卦: {m['ming_gua']} {m['ming_gua_name']}({m['ming_gua_element']})")
    print(f"║ 命别: {m['group']}")
    print(f"║ 适配宅: {', '.join([HOUSE_GUA.get(h,'') for h in m['compatible_houses']])}")
    print("╚═══════════════════════════════════════════════╝")

    pos = m["positions"]
    print(f"\n  四吉方:")
    for k in ["生气","天医","延年","伏位"]:
        print(f"    {k}: {pos.get(k,'')}")
    print(f"\n  四凶方:")
    for k in ["绝命","五鬼","六煞","祸害"]:
        print(f"    {k}: {pos.get(k,'')}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    month_mode = "--month" in sys.argv
    house_gua = None

    # 解析 --house
    for i, a in enumerate(sys.argv):
        if a == "--house" and i + 1 < len(sys.argv):
            try:
                house_gua = int(sys.argv[i + 1])
            except:
                pass

    if len(args) == 0:
        print("玄空飞星风水 — 100% 还原༺四方阁༻易爪龙虾风水算法")
        print("纯本地计算，¥0 费用")
        print()
        print("用法:")
        print("  python fengshui.py 2026              # 2026年飞星")
        print("  python fengshui.py 2026 --house 4    # 指定宅卦")
        print("  python fengshui.py 1996 男           # 命卦+宅命相配")
        print("  python fengshui.py 2026 --month      # 月飞星")
        return

    if len(args) >= 2 and args[1] in ["男","女","male","female"]:
        # 命卦模式
        year = int(args[0])
        gender = "男" if args[1] in ["男","male"] else "女"
        data = build_fengshui_ming(year, gender)
        if json_output:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_ming_fengshui({"ming": data})
    else:
        year = int(args[0])
        data = build_fengshui_year(year, house_gua)
        if json_output:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_year_fengshui({"fengshui": data})


if __name__ == '__main__':
    main()

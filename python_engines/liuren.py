"""
大六壬排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法
基于 kinliuren (Python 大六壬库) + lunar_python (节气/干支计算)
纯本地计算，¥0 费用

用法：
  python liuren.py 1996-08-15 12:56
  python liuren.py 1996-08-15 12:56 --json
  python liuren.py 2026-07-30 16:30
"""

import sys
import json
import os
from datetime import datetime

try:
    from kinliuren import kinliuren
    from lunar_python import Solar, Lunar
except ImportError as e:
    print(f"错误: 缺少依赖 - {e}")
    print("请运行: pip install kinliuren lunar-python")
    sys.exit(1)

# 节气 → kinliuren 节气名映射
JIE_QI_MAP = {
    "立春": "立春", "雨水": "雨水", "惊蛰": "驚蟄", "春分": "春分",
    "清明": "清明", "谷雨": "穀雨", "立夏": "立夏", "小满": "小滿",
    "芒种": "芒種", "夏至": "夏至", "小暑": "小暑", "大暑": "大暑",
    "立秋": "立秋", "处暑": "處暑", "白露": "白露", "秋分": "秋分",
    "寒露": "寒露", "霜降": "霜降", "立冬": "立冬", "小雪": "小雪",
    "大雪": "大雪", "冬至": "冬至", "小寒": "小寒", "大寒": "大寒",
}

# 农历月份 → kinliuren 月名映射 (正月→冬月→腊月)
LUNAR_MONTH_MAP = {
    1: "正", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六",
    7: "七", 8: "八", 9: "九", 10: "十", 11: "十一", 12: "腊",
}


def get_jieqi_and_lunar(solar):
    """
    从 Solar 对象获取当前节气（用于确定月将）和农历月
    """
    lunar = solar.getLunar()

    # 获取上一个节气（作为六壬的节气参数）
    jie_qi_list = lunar.getJieQiList() if hasattr(lunar, 'getJieQiList') else {}

    # 计算当前节气：使用 lunar_python 的 getCurrentJieQi 或 getPrevJieQi
    prev_jie = lunar.getPrevJieQi() if hasattr(lunar, 'getPrevJieQi') else None
    current_qi = lunar.getCurrentQi() if hasattr(lunar, 'getCurrentQi') else lunar.getCurrentJieQi()

    # 获取月将对应的节气（上一个节气）
    if prev_jie:
        jie_name = str(prev_jie.getName()) if hasattr(prev_jie, 'getName') else str(prev_jie)
    else:
        # fallback: 查 solar.getJieQiList 或推算
        jie_name = _fallback_jieqi(solar)

    jie_name_s = JIE_QI_MAP.get(jie_name, jie_name)

    # 农历月份
    lunar_month = lunar.getMonth()
    lunar_month_name = LUNAR_MONTH_MAP.get(lunar_month, str(lunar_month))

    return jie_name_s, lunar_month_name, lunar


def _fallback_jieqi(solar):
    """备用节气计算（月将=太阳所在宫对应的节气）"""
    y = solar.getYear()
    m = solar.getMonth()
    d = solar.getDay()

    # 简化版：基于公历日期粗略推断月将
    # 实际上应该用精确节气时间，这里做近似
    jieqi_table = [
        (1, 6, "小寒"), (1, 21, "大寒"), (2, 4, "立春"), (2, 19, "雨水"),
        (3, 6, "惊蛰"), (3, 21, "春分"), (4, 5, "清明"), (4, 20, "谷雨"),
        (5, 6, "立夏"), (5, 21, "小满"), (6, 6, "芒种"), (6, 22, "夏至"),
        (7, 7, "小暑"), (7, 23, "大暑"), (8, 8, "立秋"), (8, 23, "处暑"),
        (9, 8, "白露"), (9, 23, "秋分"), (10, 8, "寒露"), (10, 24, "霜降"),
        (11, 8, "立冬"), (11, 22, "小雪"), (12, 7, "大雪"), (12, 22, "冬至"),
    ]

    prev_jie = None
    for jm, jd, jn in jieqi_table:
        if (jm < m) or (jm == m and jd <= d):
            prev_jie = jn
        else:
            break

    return prev_jie or "小寒"


def build_liuren_data(solar):
    """
    核心六壬排盘函数
    输入: solar (Solar对象)
    输出: 完整的大六壬排盘数据结构
    """
    jieqi, lunar_month, lunar = get_jieqi_and_lunar(solar)

    # 日干支和时干支
    day_gz = lunar.getDayInGanZhi()
    time_gz = lunar.getTimeInGanZhi()

    # 调用 kinliuren 起课
    try:
        liuren_result = kinliuren.Liuren(jieqi, lunar_month, day_gz, time_gz).result(0)
    except Exception as e:
        return {
            "success": False,
            "error": f"kinliuren 起课失败: {str(e)}",
            "debug": {
                "jieqi": jieqi,
                "lunar_month": lunar_month,
                "day_gz": day_gz,
                "time_gz": time_gz,
            }
        }

    # 解析四课
    si_ke_detail = liuren_result.get("四課", {})
    ke1 = si_ke_detail.get("一課", ["", ""])
    ke2 = si_ke_detail.get("二課", ["", ""])
    ke3 = si_ke_detail.get("三課", ["", ""])
    ke4 = si_ke_detail.get("四課", ["", ""])

    # 解析三传
    san_chuan = liuren_result.get("三傳", {})
    chu_chuan = san_chuan.get("初傳", ["", "", "", ""])
    zhong_chuan = san_chuan.get("中傳", ["", "", "", ""])
    mo_chuan = san_chuan.get("末傳", ["", "", "", ""])

    # 解析天地盘
    tiandi = liuren_result.get("天地盤", {})
    tian_pan = tiandi.get("天盤", [])
    di_pan = tiandi.get("地盤", [])
    tian_jiang = tiandi.get("天將", [])

    # 地转天盘 / 地转天将
    di_zhuan_tian = liuren_result.get("地轉天盤", {})
    di_zhuan_jiang = liuren_result.get("地轉天將", {})

    # 神煞 (如果kinliuren返回了)
    shen_sha = liuren_result.get("神煞", {})

    # 格局
    ge_ju = liuren_result.get("格局", [])

    return {
        "success": True,
        "engine": "kinliuren",
        # 基础信息
        "gregorian": {
            "year": solar.getYear(),
            "month": solar.getMonth(),
            "day": solar.getDay(),
            "hour": solar.getHour(),
            "minute": solar.getMinute(),
        },
        "lunar": {
            "year": lunar.getYear(),
            "month": lunar.getMonth(),
            "day": lunar.getDay(),
            "year_ganzhi": lunar.getYearInGanZhi(),
            "month_ganzhi": lunar.getMonthInGanZhi(),
            "day_ganzhi": day_gz,
            "time_ganzhi": time_gz,
            "shengxiao": lunar.getYearShengXiao(),
        },
        # 起课参数
        "jie_qi": jieqi,
        "lunar_month_name": lunar_month,
        # 四课
        "si_ke": {
            "一课": {"干支": ke1[0] if len(ke1) > 0 else "", "天将": ke1[1] if len(ke1) > 1 else ""},
            "二课": {"干支": ke2[0] if len(ke2) > 0 else "", "天将": ke2[1] if len(ke2) > 1 else ""},
            "三课": {"干支": ke3[0] if len(ke3) > 0 else "", "天将": ke3[1] if len(ke3) > 1 else ""},
            "四课": {"干支": ke4[0] if len(ke4) > 0 else "", "天将": ke4[1] if len(ke4) > 1 else ""},
        },
        # 三传
        "san_chuan": {
            "初传": {"支": chu_chuan[0] if len(chu_chuan) > 0 else "", "将": chu_chuan[1] if len(chu_chuan) > 1 else "",
                   "六亲": chu_chuan[2] if len(chu_chuan) > 2 else "", "遁干": chu_chuan[3] if len(chu_chuan) > 3 else ""},
            "中传": {"支": zhong_chuan[0] if len(zhong_chuan) > 0 else "",
                   "将": zhong_chuan[1] if len(zhong_chuan) > 1 else "",
                   "六亲": zhong_chuan[2] if len(zhong_chuan) > 2 else "",
                   "遁干": zhong_chuan[3] if len(zhong_chuan) > 3 else ""},
            "末传": {"支": mo_chuan[0] if len(mo_chuan) > 0 else "", "将": mo_chuan[1] if len(mo_chuan) > 1 else "",
                   "六亲": mo_chuan[2] if len(mo_chuan) > 2 else "", "遁干": mo_chuan[3] if len(mo_chuan) > 3 else ""},
        },
        # 天地盘
        "tian_di_pan": {
            "天盘": tian_pan,
            "地盘": di_pan,
            "天将": tian_jiang,
            "地转天盘": di_zhuan_tian,
            "地转天将": di_zhuan_jiang,
        },
        # 天将名称（中文全称映射）
        "tian_jiang_names": {
            "贵": "贵人", "蛇": "螣蛇", "雀": "朱雀", "合": "六合",
            "勾": "勾陈", "龙": "青龙", "空": "天空", "虎": "白虎",
            "常": "太常", "玄": "玄武", "阴": "太阴", "后": "天后",
        },
        # 格局
        "ge_ju": ge_ju,
        # 日马
        "日马": liuren_result.get("日馬", ""),
        # 神煞 (补充自研六壬神煞)
        "shen_sha": _build_liuren_shensha(day_gz[0], day_gz[1], solar),
    }


# ===== 六壬神煞系统 (自研) =====
def _build_liuren_shensha(ri_gan, ri_zhi, solar):
    """构建六壬专用神煞"""
    lunar = solar.getLunar()
    month_zhi = lunar.getMonthInGanZhi()[1] if len(lunar.getMonthInGanZhi())>1 else ""

    shensha = {}

    # 干德: 甲德在寅, 乙德在申, 丙德在巳, 丁德在亥...
    gan_de = {"甲":"寅","乙":"申","丙":"巳","丁":"亥","戊":"巳",
              "己":"寅","庚":"申","辛":"巳","壬":"亥","癸":"巳"}
    shensha["干德"] = gan_de.get(ri_gan, "")

    # 支德: 子德在巳, 丑德在午...
    zhi_de = {"子":"巳","丑":"午","寅":"未","卯":"申","辰":"酉","巳":"戌",
              "午":"亥","未":"子","申":"丑","酉":"寅","戌":"卯","亥":"辰"}
    shensha["支德"] = zhi_de.get(ri_zhi, "")

    # 天喜: 正月起戌, 二月起亥...
    tian_xi = ["戌","亥","子","丑","寅","卯","辰","巳","午","未","申","酉"]
    month_num = lunar.getMonth() - 1
    if 0 <= month_num < 12:
        shensha["天喜"] = tian_xi[month_num]

    # 天赦: 春季戊寅, 夏季甲午, 秋季戊申, 冬季甲子
    jie_qi = get_jieqi_and_lunar(solar)[0]
    season = ""
    for sq, jis in [("春",["立春","雨水","惊蛰","春分","清明","谷雨"]),
                     ("夏",["立夏","小满","芒种","夏至","小暑","大暑"]),
                     ("秋",["立秋","处暑","白露","秋分","寒露","霜降"]),
                     ("冬",["立冬","小雪","大雪","冬至","小寒","大寒"])]:
        if jie_qi in jis:
            season = sq
            break
    tianshe = {"春":"戊寅","夏":"甲午","秋":"戊申","冬":"甲子"}
    shensha["天赦日"] = tianshe.get(season, "")

    # 月厌
    yue_yan = ["戌","酉","申","未","午","巳","辰","卯","寅","丑","子","亥"]
    if 0 <= month_num < 12:
        shensha["月厌"] = yue_yan[month_num]

    # 劫煞
    jie_sha_map = {"子":"巳","丑":"寅","寅":"亥","卯":"申","辰":"巳","巳":"寅",
                    "午":"亥","未":"申","申":"巳","酉":"寅","戌":"亥","亥":"申"}
    shensha["劫煞"] = jie_sha_map.get(ri_zhi, "")

    # 灾煞
    zai_sha = {"子":"午","丑":"卯","寅":"子","卯":"酉","辰":"午","巳":"卯",
               "午":"子","未":"酉","申":"午","酉":"卯","戌":"子","亥":"酉"}
    shensha["灾煞"] = zai_sha.get(ri_zhi, "")

    # 贵人 (日干)
    gui_ren = {"甲":"丑未","乙":"子申","丙":"亥酉","丁":"亥酉","戊":"丑未",
               "己":"子申","庚":"丑未","辛":"午寅","壬":"卯巳","癸":"卯巳"}
    shensha["贵人"] = gui_ren.get(ri_gan, "")

    # 驿马
    yi_ma = {"子":"寅","丑":"亥","寅":"申","卯":"巳","辰":"寅","巳":"亥",
             "午":"申","未":"巳","申":"寅","酉":"亥","戌":"申","亥":"巳"}
    shensha["驿马"] = yi_ma.get(ri_zhi, "")

    return shensha


def print_liuren(data):
    """美化打印大六壬排盘结果"""
    print("╔═══════════════════════════════════════════════╗")
    print("║             大 六 壬 排 盘                     ║")
    print("╠═══════════════════════════════════════════════╣")

    g = data["gregorian"]
    l = data["lunar"]
    print(f"║ 公历: {g['year']}年{g['month']}月{g['day']}日 {g['hour']:02d}:{g['minute']:02d}")
    print(f"║ 农历: {l['year_ganzhi']}年 {l['month']}月{l['day']}日 ({l['shengxiao']})")
    print(f"║ 日干支: {l['day_ganzhi']}  时干支: {l['time_ganzhi']}")
    print(f"║ 节气: {data['jie_qi']}  农历月: {data['lunar_month_name']}月")
    print("╚═══════════════════════════════════════════════╝")

    # 四课
    sk = data["si_ke"]
    tjn = data["tian_jiang_names"]
    print(f"\n┌────────── 四 课 ──────────┐")
    print(f"│  四(末)│   三   │   二   │   一   │")
    print(f"├────────┼────────┼────────┼────────┤")
    ke4_str = f"{sk['四课']['干支']} {tjn.get(sk['四课']['天将'], sk['四课']['天将'])}"
    ke3_str = f"{sk['三课']['干支']} {tjn.get(sk['三课']['天将'], sk['三课']['天将'])}"
    ke2_str = f"{sk['二课']['干支']} {tjn.get(sk['二课']['天将'], sk['二课']['天将'])}"
    ke1_str = f"{sk['一课']['干支']} {tjn.get(sk['一课']['天将'], sk['一课']['天将'])}"
    print(f"│{ke4_str:^8}│{ke3_str:^8}│{ke2_str:^8}│{ke1_str:^8}│")
    print(f"├────────┴────────┴────────┴────────┤")
    # 日干支在下
    ri_gan = l['day_ganzhi']
    print(f"│              {ri_gan}                 │")
    print(f"└───────────────────────────────────┘")

    # 三传
    sc = data["san_chuan"]
    print(f"\n┌────────── 三 传 ──────────┐")
    print(f"├────────┬────────┬────────┤")
    print(f"│  初传  │  中传  │  末传  │")
    print(f"├────────┼────────┼────────┤")
    chu = f"{sc['初传']['支']} {tjn.get(sc['初传']['将'], sc['初传']['将'])}"
    zhong = f"{sc['中传']['支']} {tjn.get(sc['中传']['将'], sc['中传']['将'])}"
    mo = f"{sc['末传']['支']} {tjn.get(sc['末传']['将'], sc['末传']['将'])}"
    print(f"│{chu:^8}│{zhong:^8}│{mo:^8}│")
    print(f"└────────┴────────┴────────┘")

    # 格局
    if data.get("ge_ju"):
        print(f"\n┌─ 格局 ─────────────────────────────────┐")
        print(f"│  {'  '.join(data['ge_ju'])}                        │")
        print(f"└────────────────────────────────────────┘")

    # 天地盘简化版
    tp = data["tian_di_pan"]
    if tp.get("天盘"):
        print(f"\n┌──────────────── 天地盘 ────────────────┐")
        print(f"│       巳  午  未  申                  │")
        print(f"│     辰            酉                  │")
        print(f"│     卯            戌                  │")
        print(f"│     寅  丑  子  亥                    │")
        print(f"└────────────────────────────────────────┘")
        print(f"\n  天将顺布: {' '.join(tp['天将'][:6])}")
        print(f"            {' '.join(tp['天将'][6:])}")

    # 神煞
    ss = data.get("shen_sha", {})
    if ss:
        print(f"\n┌─ 主要神煞 ─────────────────────────────┐")
        items = list(ss.items())[:12]  # 最多显示12个
        line = ""
        for i, (k, v) in enumerate(items):
            line += f"{k}:{v}  "
            if (i + 1) % 3 == 0:
                print(f"│  {line}│")
                line = ""
        if line:
            print(f"│  {line}│")
        print(f"└────────────────────────────────────────┘")


def main():
    args = sys.argv[1:]

    if len(args) < 1:
        print("大六壬排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法")
        print("基于 kinliuren + lunar_python，纯本地计算，¥0 费用")
        print()
        print("用法: python liuren.py <日期时间> [选项]")
        print()
        print("示例:")
        print("  python liuren.py 1996-08-15 12:56")
        print("  python liuren.py 19960815 1256")
        print("  python liuren.py 1996-08-15 12:56 --json")
        return

    birth_str = args[0] + (" " + args[1] if len(args) > 1 and not args[1].startswith("--") else "")
    json_output = "--json" in args

    # 解析日期
    parts = birth_str.replace("T", " ").replace("/", "-").replace(".", "-").split()
    date_str = parts[0].replace("-", "")
    time_str = parts[1] if len(parts) > 1 else "12:00"
    time_str = time_str.replace(":", "")

    try:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[:2]) if len(time_str) >= 2 else 12
        minute = int(time_str[2:4]) if len(time_str) >= 4 else 0
    except Exception as e:
        print(f"错误: 无法解析日期 '{birth_str}' - {e}")
        sys.exit(1)

    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    data = build_liuren_data(solar)
    data["parse_time"] = datetime.now().isoformat()

    if not data.get("success"):
        print(f"❌ 排盘失败: {data.get('error', '未知错误')}")
        sys.exit(1)

    if json_output:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print_liuren(data)


if __name__ == '__main__':
    main()

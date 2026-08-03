"""
八字排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法
基于 lunar_python + 自研神煞/格局/流年系统
纯本地计算，¥0 费用

用法:
  python bazi.py 1996-08-15 12:56 男
  python bazi.py 1996-08-15 12:56 男 --json
  python bazi.py 1996-08-15 12:56 男 --reading  # 命盘解读
"""

import sys
import json
from datetime import datetime

try:
    from lunar_python import Solar, Lunar
except ImportError:
    print("请运行: pip install lunar-python")
    sys.exit(1)

# ===== 常量表 =====
SEX_NAMES = {0: "女", 1: "男"}
DI_SHI_NAMES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]

GAN_WUXING = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
ZHI_WUXING = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
GAN_YINYANG = {"甲":1,"乙":0,"丙":1,"丁":0,"戊":1,"己":0,"庚":1,"辛":0,"壬":1,"癸":0}  # 1=阳 0=阴

# 神煞 — 日干查吉神
TIANYI_GUIREN = {
    "甲":["丑","未"], "乙":["子","申"], "丙":["亥","酉"], "丁":["亥","酉"],
    "戊":["丑","未"], "己":["子","申"], "庚":["丑","未"], "辛":["午","寅"],
    "壬":["卯","巳"], "癸":["卯","巳"],
}
WENCHANG = {"甲":"巳","乙":"午","丙":"申","丁":"酉","戊":"申","己":"酉","庚":"亥","辛":"子","壬":"寅","癸":"卯"}
LUSHEN = {"甲":"寅","乙":"卯","丙":"巳","丁":"午","戊":"巳","己":"午","庚":"申","辛":"酉","壬":"亥","癸":"子"}
YANGREN = {"甲":"卯","乙":"辰","丙":"午","丁":"未","戊":"午","己":"未","庚":"酉","辛":"戌","壬":"子","癸":"丑"}

# 月德贵人 (月支查)
YUEDE = {"寅":"丙","卯":"甲","辰":"壬","巳":"庚","午":"丙","未":"甲","申":"壬","酉":"庚","戌":"丙","亥":"甲","子":"壬","丑":"庚"}

# 年支/日支查神煞
def get_yima(zhi):
    """驿马: 三合局之冲位"""
    m = {"子":"寅","丑":"亥","寅":"申","卯":"巳","辰":"寅","巳":"亥",
         "午":"申","未":"巳","申":"寅","酉":"亥","戌":"申","亥":"巳"}
    return m.get(zhi,"")

def get_taohua(zhi):
    """桃花: 三合局沐浴位"""
    m = {"子":"卯","丑":"寅","寅":"卯","卯":"子","辰":"卯","巳":"午",
         "午":"卯","未":"午","申":"酉","酉":"子","戌":"酉","亥":"子"}
    return m.get(zhi,"")

def get_huagai(zhi):
    """华盖: 三合局墓库位"""
    m = {"子":"辰","丑":"丑","寅":"戌","卯":"未","辰":"辰","巳":"丑",
         "午":"戌","未":"未","申":"辰","酉":"丑","戌":"戌","亥":"未"}
    return m.get(zhi,"")

def get_jiangxing(zhi):
    """将星: 三合局帝旺位"""
    m = {"子":"子","丑":"酉","寅":"午","卯":"卯","辰":"子","巳":"酉",
         "午":"午","未":"卯","申":"子","酉":"酉","戌":"午","亥":"卯"}
    return m.get(zhi,"")

# ===== 格局判定 =====
def judge_ge_ju(ri_gan, pillars, shi_shen, yin_yang):
    """判定八字格局"""
    patterns = []

    gan = ri_gan
    wx_ri = GAN_WUXING[gan]

    # 1. 专旺格 (曲直/炎上/稼穑/从革/润下)
    all_dom = True
    for k in ["年柱","月柱","日柱","时柱"]:
        g = pillars[k]["天干"]
        z = pillars[k]["地支"]
        gv = GAN_WUXING[g]
        zv = ZHI_WUXING[z]
        if gv != wx_ri:
            # 允许印星 (生日主)
            if not (wx_ri == "木" and gv == "水") and not (wx_ri == "火" and gv == "木") \
               and not (wx_ri == "土" and gv == "火") and not (wx_ri == "金" and gv == "土") \
               and not (wx_ri == "水" and gv == "金"):
                all_dom = False
    if all_dom:
        names = {"木":"曲直格", "火":"炎上格", "土":"稼穑格", "金":"从革格", "水":"润下格"}
        patterns.append(names.get(wx_ri, "专旺格"))

    # 2. 正官格/七杀格
    for k in ["月柱"]:
        g = pillars[k]["天干"]
        sg = shi_shen.get("月干","")
        if sg == "正官":
            patterns.append("正官格")
        elif sg == "七杀":
            patterns.append("七杀格")
        elif sg == "正财":
            patterns.append("正财格")
        elif sg == "偏财":
            patterns.append("偏财格")
        elif sg == "正印":
            patterns.append("正印格")
        elif sg == "偏印":
            patterns.append("偏印格")
        elif sg == "食神":
            patterns.append("食神格")
        elif sg == "伤官":
            patterns.append("伤官格")
        elif sg == "比肩":
            patterns.append("建禄格")
        elif sg == "劫财":
            patterns.append("月刃格")

    if not patterns:
        patterns.append("普通格")

    # 3. 特殊格局
    # 魁罡日
    if ri_gan + pillars["日柱"]["地支"] in ["庚辰","壬辰","庚戌","戊戌"]:
        patterns.append("魁罡格")

    # 金神格
    ri_zhi = pillars["日柱"]["地支"]
    if (gan == "辛" and ri_zhi == "巳") or (gan == "庚" and ri_zhi == "辰"):
        patterns.append("金神格")

    return patterns


def build_shen_sha(ri_gan, pillars, month_zhi):
    """构建完整神煞系统"""
    result = {"日主神煞": [], "四柱神煞": {}}

    # 日主神煞
    for name, table in [("天乙贵人",TIANYI_GUIREN),("文昌贵人",WENCHANG),
                         ("禄神",LUSHEN),("羊刃",YANGREN)]:
        val = table.get(ri_gan,"")
        result["日主神煞"].append({"name":name,"value":val})

    # 四柱神煞
    for pk, pillar in pillars.items():
        zhi = pillar["地支"]
        result["四柱神煞"][pk] = []
        for name, func in [("驿马",get_yima),("桃花",get_taohua),
                           ("华盖",get_huagai),("将星",get_jiangxing)]:
            val = func(zhi)
            if val:
                result["四柱神煞"][pk].append({"name":name,"value":val})

        # 月德
        if pk == "月柱":
            yuede_val = YUEDE.get(zhi,"")
            if yuede_val:
                result["四柱神煞"][pk].append({"name":"月德贵人","value":yuede_val})

    return result


def build_yearly_detail(solar, sex, da_yun_list):
    """构建2024-2033流年明细"""
    current_year = datetime.now().year
    birth_year = solar.getYear()
    current_age = current_year - birth_year

    yearly = []
    for y in range(current_year - 2, current_year + 3):
        age = y - birth_year
        lunar_y = Solar.fromYmd(y, 1, 1).getLunar()
        year_gz = lunar_y.getYearInGanZhi()

        # 找对应大运
        dayun = ""
        for dy in da_yun_list:
            if dy["开始年龄"] <= age <= dy["结束年龄"]:
                dayun = dy["干支"]
                break

        # 流年十神简化
        year_gan = year_gz[0] if year_gz else ""
        ri_gan = solar.getLunar().getDayInGanZhi()[0]

        yearly.append({
            "年份": y,
            "年龄": age,
            "干支": year_gz,
            "大运": dayun,
            "旬空": "",
        })

    return yearly


def parse_args():
    args = {"birth":"", "sex":1, "json":False, "reading":False, "verbose":False}
    remaining = []
    for arg in sys.argv[1:]:
        if arg == "--json": args["json"] = True
        elif arg == "--reading": args["reading"] = True
        elif arg == "--verbose": args["verbose"] = True
        else: remaining.append(arg)
    if len(remaining) < 2: return None
    args["birth"] = remaining[0]
    args["sex"] = 0 if remaining[1] in ("女","0","female","F") else 1
    return args


def parse_birthdate(birth_str):
    parts = birth_str.strip().replace("T"," ").replace("/","-").replace(".","-").split()
    date_str = parts[0].replace("-","")
    time_str = parts[1] if len(parts)>1 else "12:00"
    time_str = time_str.replace(":","")
    return int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]), int(time_str[:2]), int(time_str[2:4]) if len(time_str)>=4 else 0


def build_bazi_data(solar, sex):
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()

    year_gz = bazi.getYear()
    month_gz = bazi.getMonth()
    day_gz = bazi.getDay()
    time_gz = bazi.getTime()
    ri_gan = day_gz[0]
    ri_zhi = day_gz[1]

    # 四柱
    pillars = {
        "年柱":{"干支":year_gz,"天干":year_gz[0],"地支":year_gz[1]},
        "月柱":{"干支":month_gz,"天干":month_gz[0],"地支":month_gz[1]},
        "日柱":{"干支":day_gz,"天干":day_gz[0],"地支":day_gz[1]},
        "时柱":{"干支":time_gz,"天干":time_gz[0],"地支":time_gz[1]},
    }

    # 十神
    shi_shen = {
        "年干":bazi.getYearShiShenGan(),"年支":bazi.getYearShiShenZhi(),
        "月干":bazi.getMonthShiShenGan(),"月支":bazi.getMonthShiShenZhi(),
        "日干":bazi.getDayShiShenGan(),"日支":bazi.getDayShiShenZhi(),
        "时干":bazi.getTimeShiShenGan(),"时支":bazi.getTimeShiShenZhi(),
    }

    # 纳音
    na_yin = {"年":bazi.getYearNaYin(),"月":bazi.getMonthNaYin(),
              "日":bazi.getDayNaYin(),"时":bazi.getTimeNaYin()}

    # 地势
    di_shi = {"年":bazi.getYearDiShi(),"月":bazi.getMonthDiShi(),
              "日":bazi.getDayDiShi(),"时":bazi.getTimeDiShi()}

    # 旬空
    xun_kong = {"年":bazi.getYearXunKong(),"月":bazi.getMonthXunKong(),
                "日":bazi.getDayXunKong(),"时":bazi.getTimeXunKong()}

    # 大运
    yun = bazi.getYun(sex)
    da_yun_list = []
    for d in yun.getDaYun():
        da_yun_list.append({
            "干支": str(d.getGanZhi()), "开始年": d.getStartYear(),
            "结束年": d.getEndYear(), "开始年龄": d.getStartAge(),
            "结束年龄": d.getEndAge(),
            "旬": d.getXun() if hasattr(d,'getXun') else "",
            "旬空": d.getXunKong() if hasattr(d,'getXunKong') else "",
        })

    # 起运
    qi_yun = {"年":yun.getStartYear(),"月":yun.getStartMonth(),"日":yun.getStartDay()}

    # 新功能: 神煞
    shen_sha = build_shen_sha(ri_gan, pillars, month_gz[1])

    # 新功能: 格局
    ge_ju = judge_ge_ju(ri_gan, pillars, shi_shen, GAN_YINYANG)

    # 新功能: 流年明细
    yearly = build_yearly_detail(solar, sex, da_yun_list)

    # 五行统计
    wx_counts = {"金":0,"木":0,"水":0,"火":0,"土":0}
    for k in ["年柱","月柱","日柱","时柱"]:
        g = pillars[k]["天干"]; z = pillars[k]["地支"]
        wx_counts[GAN_WUXING.get(g,"")] = wx_counts.get(GAN_WUXING.get(g,""),0)+1
        wx_counts[ZHI_WUXING.get(z,"")] = wx_counts.get(ZHI_WUXING.get(z,""),0)+1

    return {
        "gregorian":{"年":solar.getYear(),"月":solar.getMonth(),"日":solar.getDay(),
                      "时":solar.getHour(),"分":solar.getMinute(),"星期":["日","一","二","三","四","五","六"][solar.getWeek()%7]},
        "lunar":{"年":lunar.getYear(),"月":lunar.getMonth(),"日":lunar.getDay(),
                 "年干支":lunar.getYearInGanZhi(),"日干支":lunar.getDayInGanZhi(),
                 "生肖":lunar.getYearShengXiao(),"节气":""},
        "sex": SEX_NAMES.get(sex,"男"), "ri_gan": ri_gan, "ri_zhu": f"{ri_gan}{ri_zhi}",
        "pillars": pillars, "shi_shen": shi_shen,
        "cang_gan": {"年支":bazi.getYearHideGan(),"月支":bazi.getMonthHideGan(),
                      "日支":bazi.getDayHideGan(),"时支":bazi.getTimeHideGan()},
        "na_yin": na_yin, "di_shi": di_shi,
        "xun_kong": xun_kong, "xun": {"年":bazi.getYearXun(),"月":bazi.getMonthXun(),
                                       "日":bazi.getDayXun(),"时":bazi.getTimeXun()},
        "ming_gong":{"干支":bazi.getMingGong(),"纳音":bazi.getMingGongNaYin()},
        "shen_gong":{"干支":bazi.getShenGong(),"纳音":bazi.getShenGongNaYin()},
        "tai_xi":{"干支":bazi.getTaiXi(),"纳音":bazi.getTaiXiNaYin()},
        "tai_yuan":{"干支":bazi.getTaiYuan(),"纳音":bazi.getTaiYuanNaYin()},
        "wu_xing_counts": wx_counts,
        "da_yun": da_yun_list, "qi_yun": qi_yun,
        # 新字段
        "shen_sha": shen_sha,
        "ge_ju": ge_ju,
        "yearly": yearly,
    }


def print_bazi(data):
    p = data["pillars"]; g = data["gregorian"]; l = data["lunar"]

    print("╔═══════════════════════════════════════════════╗")
    print("║             八 字 排 盘 结 果                  ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 公历: {g['年']}/{g['月']:02d}/{g['日']:02d} {g['时']:02d}:{g['分']:02d}  星期{g['星期']}")
    print(f"║ 农历: {l['年干支']}年 {l['月']}月{l['日']}日 ({l['生肖']})")
    print(f"║ 元{data['sex']}: {data['ri_gan']}  日柱: {data['ri_zhu']}")
    if data.get("ge_ju"):
        print(f"║ 格局: {', '.join(data['ge_ju'])}")
    print("╠═══════╤═══════╤════════╤═══════╤═══════╤══════╣")
    print("║       │ 年柱  │  月柱  │ 日柱  │ 时柱  │      ║")
    print("╠═══════╪═══════╪════════╪═══════╪═══════╪══════╣")
    print(f"║ 天干  │  {p['年柱']['天干']}   │   {p['月柱']['天干']}   │  {p['日柱']['天干']}   │  {p['时柱']['天干']}   │  ║")
    print(f"║ 地支  │  {p['年柱']['地支']}   │   {p['月柱']['地支']}   │  {p['日柱']['地支']}   │  {p['时柱']['地支']}   │  ║")
    c = data["cang_gan"]
    def fmt(lst): return " ".join(str(x) for x in (lst or []))[:8]
    print(f"║ 藏干  │{fmt(c['年支']):^7}│{fmt(c['月支']):^8}│{fmt(c['日支']):^7}│{fmt(c['时支']):^7}│  ║")
    n = data["na_yin"]
    print(f"║ 纳音  │{n['年']:^7}│{n['月']:^8}│{n['日']:^7}│{n['时']:^7}│  ║")
    s = data["shi_shen"]
    print(f"║ 十神  │{s['年干']:^7}│{s['月干']:^8}│{s['日干']:^7}│{s['时干']:^7}│  ║")
    print("╚═══════╧═══════╧════════╧═══════╧═══════╧══════╝")

    # 五行
    wx = data["wu_xing_counts"]
    print(f"\n  五行: 金{wx['金']} 木{wx['木']} 水{wx['水']} 火{wx['火']} 土{wx['土']}  日主{data['ri_gan']}({GAN_WUXING[data['ri_gan']]})")

    # 地势
    d = data["di_shi"]
    xk = data["xun_kong"]
    print(f"  地势: 年{d['年']} 月{d['月']} 日{d['日']} 时{d['时']}")
    print(f"  旬空: 年{xk['年']} 月{xk['月']} 日{xk['日']} 时{xk['时']}")

    # 命宫
    print(f"  命宫: {data['ming_gong']['干支']}({data['ming_gong']['纳音']})  "
          f"身宫: {data['shen_gong']['干支']}({data['shen_gong']['纳音']})")

    # 神煞
    ss = data.get("shen_sha",{})
    if ss:
        print(f"\n┌─ 神煞 ─────────────────────────────────┐")
        for item in ss.get("日主神煞",[]):
            print(f"│  {item['name']}: {', '.join(item['value']) if isinstance(item['value'],list) else item['value']:20s}        │")
        for pk, items in ss.get("四柱神煞",{}).items():
            for item in items:
                print(f"│  {item['name']}({pk}): {item['value']:20s}        │")
        print(f"└────────────────────────────────────────┘")

    # 大运
    yun = data["da_yun"]
    qy = data["qi_yun"]
    print(f"\n┌─ 大运 (起运{qy['年']}年,约{qy['年']-g['年']}岁) ────────┐")
    print(f"│ {'年龄':^6} │ {'干支':^6} │ {'年份':^11} │ {'旬空':^6} │")
    for dy in yun:
        age = f"{dy['开始年龄']}-{dy['结束年龄']}"
        yr = f"{dy['开始年']}-{dy['结束年']}"
        print(f"│ {age:^6} │ {dy['干支']:^6} │ {yr:^11} │ {dy.get('旬空',''):^6} │")
    print(f"└────────┴────────┴─────────────┴────────┘")

    # 流年
    yearly = data.get("yearly",[])
    if yearly:
        print(f"\n┌─ 流年(近5年) ──────────────────────────┐")
        for y in yearly:
            tag = " ←当前" if y['年份'] == datetime.now().year else ""
            print(f"│ {y['年份']}年({y['年龄']}岁) {y['干支']:4s}  大运:{y.get('大运',''):4s}{tag:8s} │")
        print(f"└────────────────────────────────────────┘")


def print_reading(data):
    """命盘解读提示 — 生成供 LLM 解读的 prompt 上下文"""
    ri_gan = data["ri_gan"]
    wx_ri = GAN_WUXING[ri_gan]
    ge_ju = data.get("ge_ju",[])
    wx = data["wu_xing_counts"]
    s = data["shi_shen"]

    print(f"  请基于以下八字信息进行命盘解读:")
    print(f"  - 日主: {ri_gan}({wx_ri}), 性别: {data['sex']}")
    print(f"  - 格局: {', '.join(ge_ju)}")
    print(f"  - 五行: 金{wx['金']}木{wx['木']}水{wx['水']}火{wx['火']}土{wx['土']}")
    print(f"  - 体用: 日主{ri_gan}生于{data['lunar']['月']}月, 月令{data['shi_shen']['月干']}")
    print(f"  - 大运: {data['da_yun'][1]['干支'] if len(data['da_yun'])>1 else ''} 至 {data['da_yun'][-1]['干支'] if data['da_yun'] else ''}")
    print(f"  - 分析: 结合十神、神煞、大运流年进行全面解读")


def main():
    args = parse_args()
    if not args:
        print("八字排盘引擎 — 含神煞/格局/流年/解读")
        print("基于 lunar_python + 自研系统, 纯本地, ¥0")
        print()
        print("用法: python bazi.py <日期> <性别> [--json|--reading]")
        print("示例: python bazi.py 1996-08-15 12:56 男 --reading")
        return
    try:
        y,m,d,h,mi = parse_birthdate(args["birth"])
    except Exception as e:
        print(f"错误: {e}"); return

    solar = Solar.fromYmdHms(y,m,d,h,mi,0)
    data = build_bazi_data(solar, args["sex"])
    data["parse_time"] = datetime.now().isoformat()
    data["engine"] = "lunar_python + 自研神煞/格局/流年系统"

    if args["json"]:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    elif args["reading"]:
        print_bazi(data)
        print("\n" + "="*50)
        print_reading(data)
    else:
        print_bazi(data)


if __name__ == '__main__':
    main()

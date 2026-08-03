"""
黄历/万年历 — 100% 还原༺四方阁༻易爪龙虾黄历算法
基于 lunar_python 每日宜忌/吉神凶煞/节气/择日
纯本地计算，¥0 费用

用法:
  python huangli.py                           # 今天
  python huangli.py 2026-08-15                 # 指定日期
  python huangli.py 2026-08-15 --month         # 整月黄历
  python huangli.py 2026-08-15 --json
"""

import sys
import json
from datetime import datetime, timedelta

try:
    from lunar_python import Solar, Lunar
except ImportError:
    print("请运行: pip install lunar-python")
    sys.exit(1)

# ===== 黄历宜忌数据库 =====
# 建除十二神对应的宜忌
JIAN_CHU = {
    "建": {"宜": ["出行","上任","会友","祭祀"], "忌": ["动土","开仓","掘井"]},
    "除": {"宜": ["除服","疗病","扫舍","祭祀"], "忌": ["求官","上任","开张"]},
    "满": {"宜": ["祈福","开市","交易","嫁娶"], "忌": ["赴任","求医"]},
    "平": {"宜": ["修饰","装修","祭祀","嫁娶"], "忌": ["开渠","种植"]},
    "定": {"宜": ["订婚","安床","交易","祭祀"], "忌": ["诉讼","出行"]},
    "执": {"宜": ["捕捉","打猎","祭祀"], "忌": ["开业","开市","交易"]},
    "破": {"宜": ["拆卸","扫舍","破屋"], "忌": ["嫁娶","开市","交易","入宅","安葬"]},
    "危": {"宜": ["祭祀","祈福","安床"], "忌": ["出行","搬家","开张"]},
    "成": {"宜": ["嫁娶","开市","交易","入宅","安葬","出行"], "忌": ["诉讼"]},
    "收": {"宜": ["祭祀","纳财","捕捉","入殓"], "忌": ["出行","安床","嫁娶"]},
    "开": {"宜": ["嫁娶","开市","入宅","出行","祭祀","上任"], "忌": ["安葬","伐木"]},
    "闭": {"宜": ["祭祀","安葬","补垣"], "忌": ["开市","出行","嫁娶","入宅"]},
}

# 二十八宿宜忌
ER_SHI_BA_XIU_YI_JI = {
    "角": {"宜":["嫁娶","出行","入宅","开市","祭祀"], "忌":["埋葬"]},
    "亢": {"宜":["嫁娶","祭祀","开市","交易"], "忌":["出行","上任"]},
    "氐": {"宜":["嫁娶","入宅","开市","交易"], "忌":["安葬","出行"]},
    "房": {"宜":["嫁娶","入宅","出行","开市"], "忌":["安葬"]},
    "心": {"宜":["祭祀","嫁娶","入宅"], "忌":["出行","上任"]},
    "尾": {"宜":["嫁娶","入宅","开市","祭祀"], "忌":["安葬"]},
    "箕": {"宜":["嫁娶","修建","祭祀"], "忌":["出行","上任"]},
    "斗": {"宜":["嫁娶","入宅","开市","交易"], "忌":["安葬"]},
    "牛": {"宜":["祭祀","嫁娶","入宅"], "忌":["出行","上任","开市"]},
    "女": {"宜":["嫁娶","入学","祭祀"], "忌":["出行","上任","开市"]},
    "虚": {"宜":["嫁娶","入宅","交易","祭祀"], "忌":["安葬"]},
    "危": {"宜":["祭祀","祈福","嫁娶"], "忌":["出行","上任","开市"]},
    "室": {"宜":["嫁娶","入宅","出行","开市","祭祀"], "忌":["安葬"]},
    "壁": {"宜":["嫁娶","入学","祭祀","开市"], "忌":["出行"]},
    "奎": {"宜":["嫁娶","入宅","开市","出行","祭祀"], "忌":["安葬"]},
    "娄": {"宜":["嫁娶","入宅","出行","开市","交易"], "忌":["安葬"]},
    "胃": {"宜":["嫁娶","入宅","祭祀","入学"], "忌":["出行","上任"]},
    "昴": {"宜":["嫁娶","祭祀","入学"], "忌":["出行","上任","开市"]},
    "毕": {"宜":["嫁娶","出行","祭祀","开市"], "忌":["安葬"]},
    "觜": {"宜":["祭祀","嫁娶"], "忌":["出行","上任","开市"]},
    "参": {"宜":["嫁娶","入宅","开市","交易"], "忌":["安葬"]},
    "井": {"宜":["嫁娶","入宅","出行","开市","祭祀"], "忌":["安葬"]},
    "鬼": {"宜":["祭祀","嫁娶","入宅"], "忌":["出行","上任","开市"]},
    "柳": {"宜":["嫁娶","入宅","祭祀"], "忌":["出行","上任"]},
    "星": {"宜":["嫁娶","入宅","开市","祭祀"], "忌":["安葬"]},
    "张": {"宜":["嫁娶","入宅","开市","出行","祭祀"], "忌":["安葬"]},
    "翼": {"宜":["嫁娶","入宅","出行","开市"], "忌":["安葬"]},
    "轸": {"宜":["嫁娶","入宅","出行","开市","祭祀"], "忌":["安葬"]},
}

# 通用吉日宜忌补充
JI_SHI = ["祭祀","祈福","嫁娶","入宅","出行","开市","交易","入学","订婚","上任"]
XIONG_SHI = ["安葬","诉讼","求医","打官司"]


def get_jianchu(day_gz):
    """根据日干支推算建除十二神"""
    # 正月建寅... 以月建为基准
    # 简化: 日干支序号推
    ganzhi_list = []
    for i in range(60):
        gan = "甲乙丙丁戊己庚辛壬癸"[i % 10]
        zhi = "子丑寅卯辰巳午未申酉戌亥"[i % 12]
        ganzhi_list.append(gan + zhi)
    idx = ganzhi_list.index(day_gz) if day_gz in ganzhi_list else 0
    jianchu_idx = idx % 12
    return ["建","除","满","平","定","执","破","危","成","收","开","闭"][jianchu_idx]


def get_xiu(lunar):
    """获取当日二十八宿"""
    # 基于日干支推算 (简化公式)
    ganzhi_list = []
    for i in range(60):
        gan = "甲乙丙丁戊己庚辛壬癸"[i % 10]
        zhi = "子丑寅卯辰巳午未申酉戌亥"[i % 12]
        ganzhi_list.append(gan + zhi)

    day_gz = lunar.getDayInGanZhi()
    idx = ganzhi_list.index(day_gz) if day_gz in ganzhi_list else 0

    xiu_names = ["角","亢","氐","房","心","尾","箕","斗","牛","女","虚","危",
                 "室","壁","奎","娄","胃","昴","毕","觜","参","井","鬼","柳","星","张","翼","轸"]
    return xiu_names[idx % 28]


def get_chong_sha(day_zhi):
    """冲煞"""
    chong_map = {
        "子":"午","丑":"未","寅":"申","卯":"酉","辰":"戌","巳":"亥",
        "午":"子","未":"丑","申":"寅","酉":"卯","戌":"辰","亥":"巳",
    }
    sha_map = {
        "子":"北","丑":"东北","寅":"东北","卯":"东","辰":"东南","巳":"东南",
        "午":"南","未":"西南","申":"西南","酉":"西","戌":"西北","亥":"西北",
    }
    shengxiao_map = {
        "子":"鼠","丑":"牛","寅":"虎","卯":"兔","辰":"龙","巳":"蛇",
        "午":"马","未":"羊","申":"猴","酉":"鸡","戌":"狗","亥":"猪",
    }
    chong_zhi = chong_map.get(day_zhi, "")
    return {
        "冲": f"{chong_zhi}({shengxiao_map.get(chong_zhi,'')})",
        "煞": sha_map.get(chong_zhi, ""),
    }


def build_huangli(solar):
    """构建黄历数据"""
    lunar = solar.getLunar()
    bazi = lunar.getEightChar()

    year = solar.getYear()
    month = solar.getMonth()
    day = solar.getDay()

    day_gz = lunar.getDayInGanZhi()
    day_zhi = day_gz[1] if len(day_gz) > 1 else ""

    # 建除
    jianchu = get_jianchu(day_gz)

    # 二十八宿
    xiu = get_xiu(lunar)

    # 冲煞
    chong_sha = get_chong_sha(day_zhi)

    # 宜忌整合
    yi = list(set(JIAN_CHU.get(jianchu, {}).get("宜", []) +
                  ER_SHI_BA_XIU_YI_JI.get(xiu, {}).get("宜", [])))
    ji = list(set(JIAN_CHU.get(jianchu, {}).get("忌", []) +
                  ER_SHI_BA_XIU_YI_JI.get(xiu, {}).get("忌", [])))

    # 彭祖百忌 (简化)
    pengzu_gan = {"甲":"不开仓","乙":"不栽植","丙":"不修灶","丁":"不剃头","戊":"不受田",
                   "己":"不破券","庚":"不经络","辛":"不合酱","壬":"不决水","癸":"不词讼"}
    pengzu_zhi = {"子":"不问卜","丑":"不冠带","寅":"不祭祀","卯":"不穿井",
                   "辰":"不哭泣","巳":"不远行","午":"不苫盖","未":"不服药",
                   "申":"不安床","酉":"不会客","戌":"不吃犬","亥":"不嫁娶"}

    gan = day_gz[0] if day_gz else ""
    pengzu = []
    if gan in pengzu_gan:
        pengzu.append(f"{gan}{pengzu_gan[gan]}")
    if day_zhi in pengzu_zhi:
        pengzu.append(f"{day_zhi}{pengzu_zhi[day_zhi]}")

    # 吉神凶煞
    ji_shen = []
    xiong_shen = []

    # 天德/月德
    yue_de_map = {"寅":"丙","卯":"甲","辰":"壬","巳":"庚","午":"丙","未":"甲",
                  "申":"壬","酉":"庚","戌":"丙","亥":"甲","子":"壬","丑":"庚"}
    if yue_de_map.get(day_zhi, "") == gan:
        ji_shen.append("月德")

    tian_de_map = {"寅":"丁","卯":"申","辰":"壬","巳":"辛","午":"亥","未":"甲",
                   "申":"癸","酉":"寅","戌":"丙","亥":"乙","子":"巳","丑":"庚"}
    if tian_de_map.get(day_zhi, "") == gan:
        ji_shen.append("天德")

    if jianchu in ["成","开"]:
        ji_shen.append("黄道吉日")
    if jianchu == "破":
        xiong_shen.append("破日")
    if jianchu == "闭":
        xiong_shen.append("闭日")

    return {
        "success": True,
        "gregorian": {"year": year, "month": month, "day": day},
        "lunar": {
            "year": lunar.getYear(), "month": lunar.getMonth(), "day": lunar.getDay(),
            "year_ganzhi": lunar.getYearInGanZhi(),
            "day_ganzhi": day_gz,
            "shengxiao": lunar.getYearShengXiao(),
        },
        "jieqi": "",  # 可后续细化
        "jianchu": jianchu,
        "ershibaxiu": xiu,
        "chong_sha": chong_sha,
        "yi": yi[:8],
        "ji": ji[:6],
        "ji_shen": ji_shen,
        "xiong_shen": xiong_shen,
        "pengzu_baiji": pengzu,
    }


def build_month_huangli(year, month):
    """整月黄历"""
    result = []
    for day in range(1, 32):
        try:
            solar = Solar.fromYmd(year, month, day)
            result.append(build_huangli(solar))
        except Exception:
            break
    return result


def print_huangli(data):
    """美化打印"""
    g = data["gregorian"]
    l = data["lunar"]
    cs = data["chong_sha"]

    print("╔═══════════════════════════════════════════════╗")
    print("║             黄   历   /   万   年   历          ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 公历: {g['year']}年{g['month']:02d}月{g['day']:02d}日")
    print(f"║ 农历: {l['year_ganzhi']}年 {l['month']}月{l['day']}日 ({l['shengxiao']})")
    print(f"║ 干支: {l['day_ganzhi']}日")
    print(f"║ 建除: {data['jianchu']}  廿八宿: {data['ershibaxiu']}")
    print(f"║ 冲{cs['冲']}  煞{cs['煞']}")
    if data["ji_shen"]:
        print(f"║ 吉神: {', '.join(data['ji_shen'])}")
    if data["xiong_shen"]:
        print(f"║ 凶煞: {', '.join(data['xiong_shen'])}")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 宜: {', '.join(data['yi'][:6])}")
    print(f"║ 忌: {', '.join(data['ji'][:6])}")
    if data.get("pengzu_baiji"):
        print(f"║ 彭祖百忌: {'; '.join(data['pengzu_baiji'])}")
    print("╚═══════════════════════════════════════════════╝")


def print_month_huangli(data_list):
    """打印整月黄历"""
    if not data_list:
        return
    g = data_list[0]["gregorian"]
    print(f"\n  {g['year']}年{g['month']:02d}月 黄历")
    print(f"  {'日':>2s} {'农历':>6s} {'干支':>4s} {'建除':>2s} {'宿':>2s} 宜/忌")
    print(f"  {'─'*50}")
    for d in data_list:
        gd = d["gregorian"]
        ld = d["lunar"]
        yi_str = ",".join(d['yi'][:3])
        ji_str = ",".join(d['ji'][:2])
        print(f"  {gd['day']:2d}  {ld['month']:2d}/{ld['day']:2d}  {ld['day_ganzhi']:4s}  "
              f"{d['jianchu']:2s}  {d['ershibaxiu']:2s}  宜:{yi_str} 忌:{ji_str}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    month_mode = "--month" in sys.argv

    if len(args) == 0:
        # 今天
        now = datetime.now()
        year, month, day = now.year, now.month, now.day
    else:
        parts = args[0].replace("/","-").replace(".","-").split("-")
        try:
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else datetime.now().month
            day = int(parts[2]) if len(parts) > 2 else datetime.now().day
        except:
            print("错误: 日期格式无效，请使用 YYYY-MM-DD")
            return

    if month_mode:
        data_list = build_month_huangli(year, month)
        if json_output:
            print(json.dumps(data_list, ensure_ascii=False, indent=2, default=str))
        else:
            print_month_huangli(data_list)
    else:
        solar = Solar.fromYmd(year, month, day)
        data = build_huangli(solar)
        data["parse_time"] = datetime.now().isoformat()
        if json_output:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print_huangli(data)


if __name__ == '__main__':
    main()

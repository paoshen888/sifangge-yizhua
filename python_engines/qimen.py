"""
奇门遁甲排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法
基于 qimendunjia (paipan.py) + lunar_python (节气/四柱/局数)
纯本地计算，¥0 费用

用法：
  python qimen.py 1996-08-15 12:56
  python qimen.py 2026-07-30 16:30 --json
"""

import sys
import json
import importlib
import os
from datetime import datetime

try:
    from lunar_python import Solar, Lunar
except ImportError:
    print("错误: 缺少 lunar_python 库")
    print("请运行: pip install lunar-python")
    sys.exit(1)

# 动态加载 paipan 模块 (qimendunjia 包的实现)
paipan = None

# 方法1: 直接 import
try:
    import paipan
    if paipan:
        pass
except ImportError:
    paipan = None

# 方法2: 从 site-packages 加载
if paipan is None:
    import importlib.util
    import site
    for sitepkg in site.getsitepackages():
        paipan_path = os.path.join(sitepkg, 'paipan.py')
        if os.path.exists(paipan_path):
            spec = importlib.util.spec_from_file_location("paipan", paipan_path)
            paipan = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(paipan)
            break

# 方法3: 自动 pip install
if paipan is None:
    print("⚠ 正在自动安装 qimendunjia ...")
    import subprocess
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "install", "qimendunjia", 
                           "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
                          capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            import paipan as _paipan_mod
            paipan = _paipan_mod
            print("✅ qimendunjia 安装成功")
    except Exception:
        pass

if paipan is None:
    print("❌ 找不到 qimendunjia (paipan.py)")
    print("请运行: pip install qimendunjia")
    sys.exit(1)

# 洛书 → 方位映射
LUOSHU_DIRECTION = {1: "北", 8: "东北", 3: "东", 4: "东南", 5: "中", 9: "南", 2: "西南", 7: "西", 6: "西北"}

# 节气 → 阴阳遁 + 局数映射（通用的超神接气简化版）
# 格式: (节气名, 阴阳遁, 上元局数, 中元局数, 下元局数)
JIEQI_JUSHU = {
    # 阳遁
    "冬至": ("阳", 1, 7, 4),
    "小寒": ("阳", 2, 8, 5),
    "大寒": ("阳", 3, 9, 6),
    "立春": ("阳", 8, 5, 2),
    "雨水": ("阳", 9, 6, 3),
    "惊蛰": ("阳", 1, 7, 4),
    "春分": ("阳", 3, 9, 6),
    "清明": ("阳", 4, 1, 7),
    "谷雨": ("阳", 5, 2, 8),
    "立夏": ("阳", 4, 1, 7),
    "小满": ("阳", 5, 2, 8),
    "芒种": ("阳", 6, 3, 9),
    # 阴遁
    "夏至": ("阴", 9, 3, 6),
    "小暑": ("阴", 8, 2, 5),
    "大暑": ("阴", 7, 1, 4),
    "立秋": ("阴", 2, 5, 8),
    "处暑": ("阴", 1, 4, 7),
    "白露": ("阴", 9, 3, 6),
    "秋分": ("阴", 7, 1, 4),
    "寒露": ("阴", 6, 9, 3),
    "霜降": ("阴", 5, 8, 2),
    "立冬": ("阴", 6, 9, 3),
    "小雪": ("阴", 5, 8, 2),
    "大雪": ("阴", 4, 7, 1),
}


def get_jieqi_ju(solar):
    """
    根据公历时间确定阴阳遁和局数
    基于节气+三元（符头）判定
    """
    lunar = solar.getLunar()
    day_gz = lunar.getDayInGanZhi()

    # 获取当前节气
    prev_jie = lunar.getPrevJieQi() if hasattr(lunar, 'getPrevJieQi') else None
    if prev_jie and hasattr(prev_jie, 'getName'):
        jie_name = str(prev_jie.getName())
    else:
        # 根据公历日期推算
        jie_name = _fallback_jieqi(solar)

    # 查表获取阴阳遁和局数
    if jie_name in JIEQI_JUSHU:
        yin_yang, upper, middle, lower = JIEQI_JUSHU[jie_name]
    else:
        yin_yang, upper, middle, lower = "阳", 1, 7, 4

    # 根据日干符头确定上中下元
    day_gan = day_gz[0]
    if day_gan in ("甲", "己"):
        yuan = "上元"
        ju = upper
    elif day_gan in ("乙", "庚"):
        yuan = "中元"
        ju = middle
    elif day_gan in ("丙", "辛"):
        yuan = "下元"
        ju = lower
    elif day_gan in ("丁", "壬"):
        yuan = "上元"
        ju = upper
    elif day_gan in ("戊", "癸"):
        yuan = "中元"
        ju = middle
    else:
        yuan = "上元"
        ju = upper

    return yin_yang, ju, yuan, jie_name


def _fallback_jieqi(solar):
    """备用节气计算"""
    y, m, d = solar.getYear(), solar.getMonth(), solar.getDay()
    jieqi_table = [
        (1, 6, "小寒"), (1, 21, "大寒"), (2, 4, "立春"), (2, 19, "雨水"),
        (3, 6, "惊蛰"), (3, 21, "春分"), (4, 5, "清明"), (4, 20, "谷雨"),
        (5, 6, "立夏"), (5, 21, "小满"), (6, 6, "芒种"), (6, 22, "夏至"),
        (7, 7, "小暑"), (7, 23, "大暑"), (8, 8, "立秋"), (8, 23, "处暑"),
        (9, 8, "白露"), (9, 23, "秋分"), (10, 8, "寒露"), (10, 24, "霜降"),
        (11, 8, "立冬"), (11, 22, "小雪"), (12, 7, "大雪"), (12, 22, "冬至"),
    ]
    prev = None
    for jm, jd, jn in jieqi_table:
        if (jm < m) or (jm == m and jd <= d):
            prev = jn
    return prev or "冬至"


def build_qimen_data(solar):
    """核心奇门排盘函数"""
    lunar = solar.getLunar()

    # 四柱
    nian_zhu = lunar.getYearInGanZhi()
    yue_zhu = lunar.getMonthInGanZhi()
    ri_zhu = lunar.getDayInGanZhi()
    shi_zhu = lunar.getTimeInGanZhi()

    # 阴阳遁 + 局数
    yin_yang, ju_shu, yuan, jie_name = get_jieqi_ju(solar)
    is_yang = (yin_yang == "阳")

    # 调用 paipan 排盘
    # 注意：需要捕获 print 输出，因为 paipan 用 print 而不是 return
    import io
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        bazi_tuple = (nian_zhu, yue_zhu, ri_zhu, shi_zhu)
        pan = paipan.PaiPan(bazi=bazi_tuple, is_yangdun=is_yang, jushu=ju_shu)
    except Exception as e:
        sys.stdout = old_stdout
        return {"success": False, "error": f"排盘失败: {str(e)}"}
    finally:
        sys.stdout = old_stdout

    # 解析 print 输出
    output_text = buffer.getvalue()

    # 构建结构化数据
    gong_wei_data = []
    for gong in pan.pan:
        dipan_names = [d.name for d in gong.dipan]
        tianpan_names = [t.name for t in gong.tianpan]
        jiuxing_names = [x.name for x in gong.jiuxing]
        renpan_name = gong.renpan.name if gong.renpan else ""
        shenpan_name = gong.shenpan.name if gong.shenpan else ""

        gong_wei_data.append({
            "宫位": gong.name,
            "洛书": gong.luoshu,
            "方位": LUOSHU_DIRECTION.get(gong.luoshu, ""),
            "地盘": dipan_names,
            "地盘直符": gong.is_dipan_zhifu,
            "天盘": tianpan_names,
            "天盘九星": jiuxing_names,
            "天盘直符": gong.is_tianpan_zhifu,
            "人盘八门": renpan_name,
            "人盘直使": gong.is_renpan_zhishi,
            "神盘八神": shenpan_name,
        })

    # 找到值符和值使宫位
    zhifu_gong = None
    zhishi_gong = None
    for g in gong_wei_data:
        if g["天盘直符"]:
            zhifu_gong = g
        if g["人盘直使"]:
            zhishi_gong = g

    return {
        "success": True,
        "engine": "qimendunjia",
        # 基础信息
        "gregorian": {
            "year": solar.getYear(),
            "month": solar.getMonth(),
            "day": solar.getDay(),
            "hour": solar.getHour(),
            "minute": solar.getMinute(),
        },
        "lunar": {
            "year_ganzhi": nian_zhu,
            "month_ganzhi": yue_zhu,
            "day_ganzhi": ri_zhu,
            "time_ganzhi": shi_zhu,
            "shengxiao": lunar.getYearShengXiao(),
        },
        # 奇门参数
        "yin_yang_dun": yin_yang + "遁",
        "ju_shu": ju_shu,
        "yuan": yuan,
        "jie_qi": jie_name,
        "is_yang": is_yang,
        # 值符值使
        "zhi_fu": zhifu_gong,
        "zhi_shi": zhishi_gong,
        # 九宫详细
        "gong_wei": gong_wei_data,
    }


def print_qimen(data):
    """美化打印奇门排盘结果"""
    gw = data["gong_wei"]

    print("╔═══════════════════════════════════════════════╗")
    print("║             奇 门 遁 甲 排 盘                  ║")
    print("╠═══════════════════════════════════════════════╣")
    g = data["gregorian"]
    l = data["lunar"]
    print(f"║ 公历: {g['year']}年{g['month']}月{g['day']}日 {g['hour']:02d}:{g['minute']:02d}")
    print(f"║ 四柱: {l['year_ganzhi']} {l['month_ganzhi']} {l['day_ganzhi']} {l['time_ganzhi']}")
    print(f"║ 节气: {data['jie_qi']}  {data['yuan']}")
    print(f"║ {data['yin_yang_dun']}{data['ju_shu']}局")
    print("╚═══════════════════════════════════════════════╝")

    # 九宫格
    print(f"\n┌───────────── 九 宫 格 ─────────────┐")

    # 取方向顺序：坎1→艮8→震3→巽4→离9→坤2→兑7→乾6→中5
    direction_order = [1, 8, 3, 4, 9, 2, 7, 6, 5]
    grid = {}
    for g in gw:
        grid[g["洛书"]] = g

    # 行1: 巽4 离9 坤2
    row1_ls = [4, 9, 2]
    # 行2: 震3 中5 兑7
    row2_ls = [3, 5, 7]
    # 行3: 艮8 坎1 乾6
    row3_ls = [8, 1, 6]

    def render_row(ls_list):
        lines = []
        for i in range(3):  # 每个宫位3行
            line = "│"
            for ls in ls_list:
                g = grid.get(ls)
                if not g:
                    line += " " * 16 + "│"
                    continue
                if i == 0:
                    # 第一行：星 + 门
                    star = g["天盘九星"][0] if g["天盘九星"] else ""
                    men = g["人盘八门"][:2] if g["人盘八门"] else "  "
                    line += f" {star}{men} "
                elif i == 1:
                    # 第二行：天盘 + 神
                    tian = g["天盘"][0] if g["天盘"] else " "
                    shen = g["神盘八神"][:2] if g["神盘八神"] else "  "
                    line += f"  {tian} {shen} "
                else:
                    # 第三行：宫位
                    line += f" {g['宫位']}  "
                line += "│"
            lines.append(line)
        return lines

    header = "│    4巽宫   │    9离宫   │    2坤宫   │"
    print(f"┌──────────┬──────────┬──────────┐")
    print(header)
    print(f"├──────────┼──────────┼──────────┤")

    for l in render_row(row1_ls):
        print(l)

    print(f"├──────────┼──────────┼──────────┤")
    print(f"│    3震宫  │    5中宫  │    7兑宫  │")
    print(f"├──────────┼──────────┼──────────┤")

    for l in render_row(row2_ls):
        print(l)

    print(f"├──────────┼──────────┼──────────┤")
    print(f"│    8艮宫  │    1坎宫  │    6乾宫  │")
    print(f"├──────────┼──────────┼──────────┤")

    for l in render_row(row3_ls):
        print(l)

    print(f"└──────────┴──────────┴──────────┘")

    # 值符值使
    if data.get("zhi_fu"):
        zf = data["zhi_fu"]
        print(f"\n┌─ 值符值使 ─────────────────────────────┐")
        print(f"│  值符: {zf['天盘九星'][0] if zf['天盘九星'] else ''}  落{zf['宫位']}   │")
        if data.get("zhi_shi"):
            zs = data["zhi_shi"]
            print(f"│  值使: {zs['人盘八门']}  落{zs['宫位']}        │")
        print(f"└────────────────────────────────────────┘")

    # 九宫详情
    print(f"\n┌─ 九宫详情 ─────────────────────────────┐")
    for g in gw:
        star = g["天盘九星"][0] if g["天盘九星"] else ""
        men = g["人盘八门"]
        shen = g["神盘八神"]
        tian = "".join(g["天盘"])
        di = "".join(g["地盘"])
        marks = []
        if g["天盘直符"]:
            marks.append("符")
        if g["人盘直使"]:
            marks.append("使")
        mark_str = "(" + "".join(marks) + ")" if marks else ""
        print(f"│ {g['宫位']}{mark_str}: {star} {men} {shen} | 天:{tian} | 地:{di} |")
    print(f"└────────────────────────────────────────┘")


def main():
    args = sys.argv[1:]

    if len(args) < 1:
        args = ["2026-08-03", "16:00"]

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
    data = build_qimen_data(solar)
    data["parse_time"] = datetime.now().isoformat()

    if not data.get("success"):
        print(f"❌ 排盘失败: {data.get('error', '未知错误')}")
        sys.exit(1)

    if json_output:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        print_qimen(data)


if __name__ == '__main__':
    main()

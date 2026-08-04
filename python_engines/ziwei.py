"""
紫微斗数排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法
基于 archlizheng/ziwei-ai-html-report 离线引擎
纯本地计算，¥0 费用

用法：
  python ziwei.py 1996-08-15 12:56 男
  python ziwei.py 1996-08-15 12:56 男 --json
  python ziwei.py 1996-08-15 12:56 男 --compact     # 紧凑模式
"""

import sys
import os
import json
from datetime import datetime

# ziwei_offline 引擎路径（同目录）


def build_ziwei_data(year, month, day, hour, minute, sex):
    """
    调用 ziwei_offline 引擎排盘
    sex: 1=男, 0=女
    """
    try:
        import ziwei_offline as z
    except ImportError as e:
        return {"success": False, "error": f"缺少依赖: {e}"}

    gender = "male" if sex == 1 else "female"

    try:
        payload = z.generate_chart(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            gender=gender,
        )
        # 追加当前流年数据
        current_year = datetime.now().year
        try:
            yearly = z.build_yearly_data(payload, current_year)
            payload["current_yearly"] = yearly
        except Exception as ex:
            import traceback
            payload["current_yearly"] = {"error": str(ex), "trace": traceback.format_exc()}
        return {"success": True, "payload": payload}
    except Exception as e:
        return {"success": False, "error": str(e)}


def print_ziwei(data):
    """美化打印紫微斗数排盘"""
    p = data["payload"]

    print("╔═══════════════════════════════════════════════╗")
    print("║             紫 微 斗 数 排 盘                    ║")
    print("╠═══════════════════════════════════════════════╣")

    birth = p["birth"]
    lunar = p["lunar"]
    ygz = p["yearGanZhi"]

    print(f"║ 阳历: {birth['solar']} {birth['localTime']}")
    print(f"║ 农历: {ygz['text']}年 {lunar['month']}月{lunar['day']}日")
    print(f"║ 时柱: {birth['timeBranch']}时    性别: {'男' if birth['gender']=='male' else '女'}")
    print(f"║ 五行局: {p['fiveElementsClass']}    命宫: {p['lifePalace']['stem']}{p['lifePalace']['branch']}")
    print(f"║ 身宫: {p['bodyPalace']['stem']}{p['bodyPalace']['branch']}    引擎: {p['engine']}")
    print("╚═══════════════════════════════════════════════╝")

    print(f"\n┌─ 十二宫详表 ───────────────────────────────┐")
    for palace in p["palaces"]:
        name = palace["name"]
        stem = palace["stem"]
        branch = palace["branch"]
        decade = palace.get("decadalRange", "")

        # 主星
        majors = [s["name"] for s in palace.get("majorStars", [])]
        # 亮度
        brightness = ""
        for s in palace.get("majorStars", []):
            if s.get("brightness"):
                brightness += f"{s['name']}({s['brightness']}) "

        stars_list = []
        for s in palace.get("majorStars", []):
            b = f"({s['brightness']})" if s.get("brightness") else ""
            stars_list.append(f"{s['name']}{b}")

        minors = [s["name"] for s in palace.get("minorStars", [])]
        adjectives = [s["name"] for s in palace.get("adjectiveStars", [])]

        all_stars = stars_list + minors + adjectives
        stars_str = "、".join(all_stars) if all_stars else "（空宫）"

        tags = []
        if palace.get("isLifePalace"):
            tags.append("命")
        if palace.get("isBodyPalace"):
            tags.append("身")
        tag_str = f" [{''.join(tags)}]" if tags else ""

        print(f"│ {stem}{branch} {name:4s} 大限{decade:5s} | {stars_str:40s} {tag_str} │")

    print(f"└──────────────────────────────────────────────┘")

    # 流年
    yy = p.get("current_yearly")
    if yy and not yy.get("error"):
        print(f"\n┌─ 2026流年 ─────────────────────────────────┐")
        print(f"│ 流年: {yy.get('stem','')}{yy.get('branch','')}年")
        if yy.get('mutagens'):
            print(f"│ 四化: {', '.join(yy['mutagens'])}")
        if yy.get('palaceName'):
            print(f"│ 流年命宫: {yy['palaceName']}({yy.get('palaceBranch','')})")
        cd = yy.get('currentDecadal',{})
        if cd:
            print(f"│ 大限: {cd.get('palaceName','')}({cd.get('branch','')})  {cd.get('nominalAge','')}岁")
        print(f"└──────────────────────────────────────────────┘")

    # 四化
    if p.get("siHua"):
        print(f"\n  四化: ", end="")
        for sh in p["siHua"]:
            print(f"{sh['star']}化{sh['type']}  ", end="")
        print()


def main():
    args = sys.argv[1:]

    if len(args) < 1 or args[0] in ("--help", "-h"):
        print("紫微斗数排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法")
        print("基于 archlizheng/ziwei-ai-html-report 离线引擎")
        print("纯本地计算，¥0 费用")
        print()
        print("用法:")
        print("  python ziwei.py <日期> <时间> <性别>")
        print("  python ziwei.py <日期> <时间> <性别> --json")
        print("  python ziwei.py <日期> <时间> <性别> --compact")
        print()
        print("示例:")
        print("  python ziwei.py 1996-08-15 12:56 男")
        print("  python ziwei.py 1996-08-15 12:56 男 --json")
        return

    json_output = "--json" in args
    compact = "--compact" in args
    args_clean = [a for a in args if not a.startswith("--")]

    birth = args_clean[0] + (" " + args_clean[1] if len(args_clean) > 1 and ":" in args_clean[1] else "")
    sex = 0 if len(args_clean) >= 2 and args_clean[-1] in ("女", "0") else 1

    parts = birth.replace("T", " ").replace("/", "-").replace(".", "-").split()
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
        print(f"错误: {e}")
        return

    data = build_ziwei_data(year, month, day, hour, minute, sex)

    if not data["success"]:
        print(f"❌ 排盘失败: {data.get('error', '未知错误')}")
        return

    if json_output:
        if compact:
            # 精简 JSON
            compact_data = {
                "birth": data["payload"]["chart"]["birth"],
                "lunar": data["payload"]["chart"]["lunar"],
                "fiveElements": data["payload"]["chart"]["fiveElementsClass"],
                "lifePalace": data["payload"]["chart"]["lifePalace"],
                "bodyPalace": data["payload"]["chart"]["bodyPalace"],
                "palaces": [],
            }
            for p in data["payload"]["chart"]["palaces"]:
                compact_data["palaces"].append({
                    "name": p["name"],
                    "stem": p["stem"],
                    "branch": p["branch"],
                    "majorStars": [s["name"] for s in p.get("majorStars", [])],
                    "minorStars": [s["name"] for s in p.get("minorStars", [])],
                })
            print(json.dumps(compact_data, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(data["payload"], ensure_ascii=False, indent=2, default=str))
    else:
        print_ziwei(data)


if __name__ == '__main__':
    main()

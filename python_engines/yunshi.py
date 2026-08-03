"""
每日运势生成器 — 基于八字+黄历+五行生克
纯本地计算，¥0 费用

用法:
  python yunshi.py 1996-03-10 08:00 男              # 今日运势
  python yunshi.py 1996-03-10 08:00 男 2026-08-15   # 指定日期
  python yunshi.py 1996-03-10 08:00 男 --week       # 本周运势
  python yunshi.py 1996-03-10 08:00 男 --json
"""

import sys
import json
import subprocess
import os
from datetime import datetime, timedelta

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))

# 日干支吉凶参考
DAY_STEM_BRANCH_ADVICE = {
    "甲": {"宜": ["制定计划", "学习进修", "拜访贵人"], "忌": ["冲动决策", "大额投资"]},
    "乙": {"宜": ["合作洽谈", "文书签约", "婚恋交友"], "忌": ["独断专行", "涉险运动"]},
    "丙": {"宜": ["社交活动", "公开演讲", "展现才华"], "忌": ["与人争执", "过度消费"]},
    "丁": {"宜": ["细致工作", "投资理财", "家庭聚会"], "忌": ["急躁冒进", "熬夜伤身"]},
    "戊": {"宜": ["稳定理财", "置业购房", "祭祀祈福"], "忌": ["频繁变动", "高风险投机"]},
    "己": {"宜": ["内部整理", "养生保健", "学习充电"], "忌": ["外出远行", "重大决策"]},
    "庚": {"宜": ["果敢进取", "创业开拓", "运动锻炼"], "忌": ["优柔寡断", "过度劳累"]},
    "辛": {"宜": ["精益求精", "细节把控", "法律事务"], "忌": ["粗心大意", "贪多嚼不烂"]},
    "壬": {"宜": ["远行旅游", "社交联谊", "学习新知"], "忌": ["闭门造车", "消极懈怠"]},
    "癸": {"宜": ["静养调息", "智慧谋划", "暗中布局"], "忌": ["高调张扬", "无谓消耗"]},
}

# 五行日运
WUXING_DAY_TIPS = {
    "木": {"强": "宜克制消费欲，多运动", "弱": "宜学习进修，多亲近自然"},
    "火": {"强": "宜冷静克制，注意心脑血管", "弱": "宜社交活动，展现自我"},
    "土": {"强": "宜节食健脾，减少应酬", "弱": "宜稳扎稳打，置业投资"},
    "金": {"强": "宜收敛锋芒，注意呼吸系统", "弱": "宜果断决策，把握时机"},
    "水": {"强": "宜节制饮酒，保护肾脏", "弱": "宜交友游乐，拓展人脉"},
}

# 黄历建除十二神
JIANCHU_LUCK = {
    "建": "宜出行求财，忌动土修造",
    "除": "宜打扫清除、治病服药",
    "满": "宜祭祀祈福，忌栽种置业",
    "平": "万事平顺，宜按部就班",
    "定": "宜订婚签约，忌诉讼争辩",
    "执": "宜捕捉狩猎、入学祭祀",
    "破": "忌大事，宜破除旧习",
    "危": "宜保守谨慎，忌冒险决策",
    "成": "百事皆宜，大利婚嫁签约",
    "收": "宜收获入仓、置产纳财",
    "开": "宜开业开工、婚嫁出行",
    "闭": "宜埋葬祭祀，忌开业开张",
}


def call_engine(script, *args):
    r = subprocess.run(
        [sys.executable, os.path.join(ENGINE_DIR, script)] + list(args) + ["--json"],
        capture_output=True, text=True, timeout=30, cwd=ENGINE_DIR
    )
    if r.returncode == 0:
        try:
            return json.loads(r.stdout)
        except:
            pass
    return None


def get_yunshi(bazi, huangli, sex):
    """生成每日运势"""
    tips = []
    score = 70  # 基础运势分

    # 1. 日主与当日干关系
    day_gan = huangli["lunar"]["day_ganzhi"][0] if huangli else "丙"
    master_gan = bazi["ri_gan"]

    # 天干关系
    GAN_RELATION = {
        ("甲", "甲"): ("比肩", 5, ""), ("甲", "乙"): ("劫财", -3, ""),
        ("甲", "丙"): ("食神", 8, ""), ("甲", "丁"): ("伤官", -5, ""),
        ("甲", "戊"): ("偏财", 10, ""), ("甲", "己"): ("正财", 8, ""),
        ("甲", "庚"): ("七杀", -8, ""), ("甲", "辛"): ("正官", 5, ""),
        ("甲", "壬"): ("偏印", 3, ""), ("甲", "癸"): ("正印", 6, ""),
    }

    # 简化日主天干关系
    gan_idx = "甲乙丙丁戊己庚辛壬癸"
    master_idx = gan_idx.index(master_gan)
    day_idx = gan_idx.index(day_gan)
    diff = (day_idx - master_idx) % 10

    rel_names = ["比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"]
    rel_scores = [5, -2, 8, -4, 10, 8, -7, 5, 3, 6]
    rel_name = rel_names[diff]
    rel_score = rel_scores[diff]
    score += rel_score

    tips.append({
        "类别": "日干关系",
        "内容": f"今日日干{day_gan}，与你的日主{master_gan}形成「{rel_name}」关系",
        "吉凶": "吉" if rel_score > 0 else "平" if rel_score >= -3 else "凶",
    })

    # 2. 黄历宜忌
    if huangli and huangli.get("yi"):
        tips.append({
            "类别": "今日宜",
            "内容": "、".join(huangli["yi"][:4]),
            "吉凶": "吉",
        })
    if huangli and huangli.get("ji"):
        tips.append({
            "类别": "今日忌",
            "内容": "、".join(huangli["ji"][:3]),
            "吉凶": "注意",
        })

    # 3. 建除
    if huangli and huangli.get("jianchu"):
        jc = huangli["jianchu"]
        jc_tip = JIANCHU_LUCK.get(jc, "")
        if "忌" in jc_tip or "不宜" in jc_tip:
            score -= 5
            tips.append({
                "类别": "建除提醒",
                "内容": f"今日「{jc}日」— {jc_tip}",
                "吉凶": "注意",
            })
        elif "宜" in jc_tip or "大利" in jc_tip:
            score += 8
            tips.append({
                "类别": "建除提醒",
                "内容": f"今日「{jc}日」— {jc_tip}",
                "吉凶": "吉",
            })

    # 4. 冲煞
    if huangli and huangli.get("chong_sha"):
        chong = huangli["chong_sha"].get("冲", "")
        bazi_zodiac = bazi.get("lunar", {}).get("生肖", "")
        if bazi_zodiac and bazi_zodiac in chong:
            score -= 10
            tips.append({
                "类别": "生肖冲煞",
                "内容": f"今日冲{chong}，与你的生肖{bazi_zodiac}相冲，大事不宜",
                "吉凶": "凶",
            })

    # 5. 今日五行建议
    if huangli:
        day_wx = ""
        wx_map = {"甲": "木", "乙": "木", "丙": "火", "丁": "火",
                   "戊": "土", "己": "土", "庚": "金", "辛": "金",
                   "壬": "水", "癸": "水"}
        day_wx = wx_map.get(day_gan, "土")
        wx_counts = bazi["wu_xing_counts"]
        wx_strength = "强" if wx_counts.get(day_wx, 0) >= 3 else "弱"
        wx_tip = WUXING_DAY_TIPS.get(day_wx, {}).get(wx_strength, f"今日{day_wx}气{ wx_strength}")

        tips.append({
            "类别": "五行日运",
            "内容": f"今日{day_wx}日（{wx_strength}），{wx_tip}",
            "吉凶": "吉",
        })

    # 综合评价
    if score >= 80:
        overall = "大吉"
        color = "红色/紫色"
        direction = huangli.get("chong_sha", {}).get("煞", "南") + "（避）"
    elif score >= 65:
        overall = "吉利"
        color = "绿色/蓝色"
        direction = "东方"
    elif score >= 50:
        overall = "平顺"
        color = "白色/黄色"
        direction = "家或办公室"
    elif score >= 35:
        overall = "小凶"
        color = "黑色/深蓝"
        direction = "宜静不宜动"
    else:
        overall = "谨慎"
        color = "深色系"
        direction = "尽量避开外出"

    return {
        "综合运势": overall,
        "综合评分": score,
        "幸运色": color,
        "吉方": direction,
        "详情": tips,
        "今日宜": huangli.get("yi", [])[:4] if huangli else [],
        "今日忌": huangli.get("ji", [])[:3] if huangli else [],
    }


def print_yunshi(result, date_str, sex_label):
    gender = "男" if sex_label == "男" else "女"
    print("╔═══════════════════════════════════════════════╗")
    print("║             每 日 运 势                         ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 命主: {date_str} ({gender})")
    print(f"║ 综合运势: {result['综合运势']}  ({result['综合评分']}分)")
    print(f"║ 幸运色: {result['幸运色']}    吉方: {result['吉方']}")
    print("╠═══════════════════════════════════════════════╣")

    for tip in result["详情"]:
        icon = {"吉": "✅", "凶": "❌", "注意": "⚠️"}.get(tip["吉凶"], "•")
        print(f"║ {icon} [{tip['类别']}] {tip['内容']}")

    print("╚═══════════════════════════════════════════════╝")

    if result["今日宜"]:
        print(f"\n  📗 宜: {' | '.join(result['今日宜'])}")
    if result["今日忌"]:
        print(f"  📕 忌: {' | '.join(result['今日忌'])}")


def generate_weekly(bazi, sex, start_date):
    """生成一周运势"""
    results = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        hl = call_engine("huangli.py", ds)
        yun = get_yunshi(bazi, hl, sex)
        results.append({
            "日期": ds,
            "星期": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()],
            **yun,
        })
    return results


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    week_mode = "--week" in sys.argv

    if len(args) < 1:
        print("每日运势 — 八字+黄历+五行综合")
        print()
        print("用法:")
        print("  python yunshi.py 1996-03-10 08:00 男              # 今日运势")
        print("  python yunshi.py 1996-03-10 08:00 男 2026-08-15   # 指定日期")
        print("  python yunshi.py 1996-03-10 08:00 男 --week       # 本周运势")
        return

    birth = args[0] + (" " + args[1] if len(args) > 1 and ":" in args[1] else "")
    sex = "男" if len(args) >= 2 and args[-1] in ("男", "1") else "女"

    parts = birth.split()
    bazi_date = parts[0]
    bazi_time = parts[1] if len(parts) > 1 else "12:00"

    target_date = datetime.now()
    if len(args) >= 3 and not args[-1] in ("男", "女"):
        try:
            target_date = datetime.strptime(args[-1], "%Y-%m-%d")
        except:
            pass

    date_str = target_date.strftime("%Y-%m-%d")

    # 调用八字
    bazi = call_engine("bazi.py", bazi_date, bazi_time, sex)
    if not bazi:
        print("八字排盘失败")
        return

    # 调用黄历
    huangli = call_engine("huangli.py", date_str)

    if week_mode:
        results = generate_weekly(bazi, sex, target_date)
        if json_output:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print("╔═══════════════════════════════════════════════╗")
            print("║             一 周 运 势                         ║")
            print("╚═══════════════════════════════════════════════╝")
            print()
            for r in results:
                stars = "★" * (r["综合评分"] // 15) + "☆" * (6 - r["综合评分"] // 15)
                print(f"  {r['日期']} {r['星期']}  {stars}  {r['综合运势']} ({r['综合评分']}分)")
                if r.get("详情"):
                    best = [t for t in r["详情"] if t["吉凶"] == "吉"][:1]
                    worst = [t for t in r["详情"] if t["吉凶"] in ("凶", "注意")][:1]
                    for t in best:
                        print(f"    👍 {t['内容'][:40]}")
                    for t in worst:
                        print(f"    ⚠️ {t['内容'][:40]}")
                print()
    else:
        yunshi = get_yunshi(bazi, huangli, sex)
        if json_output:
            print(json.dumps(yunshi, ensure_ascii=False, indent=2, default=str))
        else:
            print_yunshi(yunshi, date_str, sex)


if __name__ == '__main__':
    main()

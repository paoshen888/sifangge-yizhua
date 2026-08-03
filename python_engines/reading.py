"""
༺四方阁༻易爪龙虾命盘解读引擎
将八字/紫微/六壬/奇门等排盘结果整合为标准解读 Prompt
供 LLM 直接生成命理分析报告

用法:
  python reading.py 1996-08-15 12:56 男
  python reading.py 1996-08-15 12:56 男 --full   # 全引擎解读
"""

import sys
import json
import subprocess
import os
from datetime import datetime

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_engine(script, *args):
    """调用排盘引擎,返回解析后的 dict"""
    cmd = [sys.executable, script] + list(args) + ["--json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25, cwd=ENGINE_DIR)
        return json.loads(r.stdout)
    except:
        return {"error": "引擎调用失败"}


def format_liuren_section(liuren):
    """将六壬排盘数据格式化为解读提示"""
    if not liuren or not liuren.get("success"):
        return ""

    parts = []
    parts.append(f"""
## 三、大六壬课传分析

### 3.1 课传基础
- 占时: {liuren['lunar']['year_ganzhi']}年{liuren['lunar']['month_ganzhi']}月{liuren['lunar']['day_ganzhi']}日{liuren['lunar']['time_ganzhi']}时
- 节气: {liuren.get('jie_qi', '')}""")

    # 四课
    parts.append("\n### 3.2 四课")
    for name, info in liuren.get("si_ke", {}).items():
        parts.append(f"- {name}: {info['干支']} ({info['天将']})")

    # 三传
    sc = liuren.get("san_chuan", {})
    parts.append("\n### 3.3 三传")
    for name in ["初传", "中传", "末传"]:
        item = sc.get(name, {})
        parts.append(f"- {name}: {item.get('支','')} ({item.get('将','')}) 六亲:{item.get('六亲','')} 遁干:{item.get('遁干','')}")

    # 课体判断
    ke4 = sc.get("初传", {}).get("干支", "")
    parts.append(f"""
### 3.4 课传解读要点
- 分析四课贼克/比用/涉害等课体
- 分析三传生克关系和吉凶
- 判断事体的发展趋势和应期
- 结合天将神煞综合断课""")

    return "\n".join(parts)


def format_qimen_section(qimen):
    """将奇门排盘数据格式化为解读提示"""
    if not qimen or not qimen.get("success"):
        return ""

    parts = []
    yin_yang = qimen.get("yin_yang_dun", "")
    ju_shu = qimen.get("ju_shu", "")
    yuan = qimen.get("yuan", "")

    parts.append(f"""
## 四、奇门遁甲分析

### 4.1 排盘基础
- 局数: {yin_yang}{ju_shu}局 ({yuan})
- 节气: {qimen.get('jie_qi', '')}
- 时辰: {qimen['lunar']['year_ganzhi']}年{qimen['lunar']['month_ganzhi']}月{qimen['lunar']['day_ganzhi']}日{qimen['lunar']['time_ganzhi']}时""")

    # 值符值使
    zf = qimen.get("zhi_fu", {})
    zs = qimen.get("zhi_shi", {})
    parts.append(f"""
### 4.2 值符值使
- 值符: {zf.get('宫位','')} {', '.join(zf.get('天盘九星',[]))} ({', '.join(zf.get('天盘',[]))})
- 值使: {zs.get('宫位','')} {zs.get('人盘八门','')}""")

    # 各宫简要
    parts.append("\n### 4.3 九宫概览")
    for gong in qimen.get("gong_wei", [])[:9]:
        gong_name = gong.get("宫位", "")
        tian_pan = ",".join(gong.get("天盘", []))
        men = gong.get("人盘八门", "")
        xing = ",".join(gong.get("天盘九星", []))
        shen = gong.get("神盘八神", "")
        parts.append(f"- {gong_name}|星:{xing}|门:{men}|神:{shen}|天盘:{tian_pan}")

    parts.append(f"""
### 4.4 奇门解读要点
- 分析日干落宫与时干落宫的生克关系
- 判断值符值使的吉凶含义
- 结合八门、九星、八神综合断事
- 判断所测之事在奇门局中的吉凶应期""")

    return "\n".join(parts)


def build_reading_prompt(year, month, day, hour, minute, sex, full_mode=False):
    """构建完整命盘解读 Prompt"""
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}"
    gender = "男" if sex == 1 else "女"

    # 1. 八字
    bazi = run_engine("bazi.py", date_str, time_str, gender)

    # 2. 紫微
    ziwei_raw = run_engine("ziwei.py", date_str, time_str, gender)

    # 3. 当前年份
    now = datetime.now()

    # === 构建 Prompt ===
    parts = []

    parts.append(f"""你是一位精通中国传统命理学的专家。请基于以下排盘数据，对此命主进行全面的命理分析。

## 命主基本信息
- 出生时间: {year}年{month}月{day}日 {time_str} ({gender})
- 当前时间: {now.year}年{now.month}月{now.day}日
- 当前年龄: {now.year - year}岁
""")

    # === 八字分析 ===
    if bazi and "pillars" in bazi:
        p = bazi["pillars"]
        parts.append(f"""
## 一、八字命盘分析

### 1.1 四柱八字
```
年柱: {p['年柱']['干支']}  月柱: {p['月柱']['干支']}
日柱: {p['日柱']['干支']}  时柱: {p['时柱']['干支']}
```

- **日主**: {bazi['ri_gan']}({bazi['ri_gan']}元{bazi['sex']})
- **格局**: {', '.join(bazi.get('ge_ju', ['暂无']))}

### 1.2 五行力量
- 金:{bazi['wu_xing_counts']['金']} 木:{bazi['wu_xing_counts']['木']} 水:{bazi['wu_xing_counts']['水']} 火:{bazi['wu_xing_counts']['火']} 土:{bazi['wu_xing_counts']['土']}

### 1.3 十神配置
- 年: {bazi['shi_shen']['年干']}  月: {bazi['shi_shen']['月干']}  日: {bazi['shi_shen']['日干']}  时: {bazi['shi_shen']['时干']}

### 1.4 纳音
- {bazi['na_yin']['年']} / {bazi['na_yin']['月']} / {bazi['na_yin']['日']} / {bazi['na_yin']['时']}

### 1.5 地势与旬空
- 地势: 年{bazi['di_shi']['年']} 月{bazi['di_shi']['月']} 日{bazi['di_shi']['日']} 时{bazi['di_shi']['时']}
- 旬空: 年{bazi['xun_kong']['年']} 月{bazi['xun_kong']['月']} 日{bazi['xun_kong']['日']} 时{bazi['xun_kong']['时']}

### 1.6 大运走势
""")
        for dy in bazi.get("da_yun", [])[:5]:
            parts.append(f"- {dy['开始年龄']}-{dy['结束年龄']}岁: {dy['干支']} ({dy['开始年']}-{dy['结束年']})  旬空: {dy.get('旬空','')}")

        # 神煞
        ss = bazi.get("shen_sha", {})
        if ss:
            parts.append("\n### 1.7 神煞\n")
            parts.append("**日主神煞**:")
            for item in ss.get("日主神煞", []):
                v = item['value']
                if isinstance(v, list):
                    v = ", ".join(v)
                parts.append(f"- {item['name']}: {v}")

    # === 紫微斗数 ===
    # ziwei 返回的是平铺 JSON（非 nested payload）
    ziwei = ziwei_raw if isinstance(ziwei_raw, dict) and "palaces" in ziwei_raw else ziwei_raw.get("payload", {})
    if ziwei and ziwei.get("palaces"):
        parts.append(f"""
## 二、紫微斗数分析

### 2.1 命盘基础
- 五行局: {ziwei.get('fiveElementsClass', '')}
- 命宫: {ziwei.get('lifePalace',{}).get('stem','')}{ziwei.get('lifePalace',{}).get('branch','')}
- 身宫: {ziwei.get('bodyPalace',{}).get('stem','')}{ziwei.get('bodyPalace',{}).get('branch','')}

### 2.2 十二宫主星
""")
        for palace in ziwei.get("palaces", []):
            majors = [f"{s['name']}({s.get('brightness','')})" for s in palace.get("majorStars", [])]
            minors = [s["name"] for s in palace.get("minorStars", [])]
            all_stars = majors + minors
            stars_str = "、".join(all_stars) if all_stars else "空宫"
            tags = []
            if palace.get("isLifePalace"):
                tags.append("命")
            if palace.get("isBodyPalace"):
                tags.append("身")
            tag = f"[{''.join(tags)}]" if tags else ""
            decade = palace.get("decadalRange", "")
            parts.append(f"- {palace['stem']}{palace['branch']} **{palace['name']}** (大限{decade}){tag}: {stars_str}")

        # 流年
        yy = ziwei.get("current_yearly", {})
        if yy and not yy.get("error"):
            parts.append(f"""
### 2.3 {now.year}流年
- 流年: {yy.get('stem','')}{yy.get('branch','')}年
- 流年四化: {', '.join(yy.get('mutagens', []))}
- 流年命宫: {yy.get('palaceName','')}({yy.get('palaceBranch','')})
""")

    # === 六壬 (full_mode) ===
    if full_mode:
        liuren = run_engine("liuren.py", date_str, time_str)
        parts.append(format_liuren_section(liuren))

    # === 奇门 (full_mode) ===
    if full_mode:
        qimen = run_engine("qimen.py", date_str, time_str)
        parts.append(format_qimen_section(qimen))

    # === 解读指引 ===
    section_num = "五" if full_mode else "三"
    parts.append(f"""
## {section_num}、解读要求

请按以下结构输出命理分析报告：

### A. 命格总论
- 日主{ bazi['ri_gan'] if bazi else '?' }的强弱、喜忌
- 整体格局特点（富贵层次、适合的发展方向）

### B. 事业财运
- 适合的行业方向
- 财运走势（结合大运分析）
- 当前{now.year}年事业机会

### C. 感情婚姻
- 配偶宫分析
- 桃花运情况
- 婚姻稳定性

### D. 健康提示
- 五行偏颇的健康影响
- 需要注意的脏腑

### E. 当前运势 ({now.year}年)
- 结合流年+大运的综合判断
- 吉凶建议
- 关键月份/季节提醒""")

    # 全引擎模式增加六壬+奇门解读要求
    if full_mode:
        parts.append(f"""
### F. 大六壬课传分析
- 四课结构揭示的事体状态
- 三传发展趋势和吉凶判断
- 结合天将神煞的应期预测
- 课体类别（贼克/比用/涉害/遥克/昴星/别责/八专/伏吟/反吟）

### G. 奇门遁甲局象分析
- 日干落宫与时干落宫的生克关系
- 值符值使的吉凶含义
- 八门九星对当前事务的影响
- 奇门局的整体吉凶判断和建议

### H. 综合结论
- 八字+紫微+六壬+奇门交叉验证
- 各派学说共同指向的趋势
- 最终建议和注意事项""")

    parts.append("""
请使用专业但通俗的语言，每个结论都要有命理依据支撑。避免绝对化的断言，用"倾向""建议""注意"等措辞。
""")

    return "\n".join(parts)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full_mode = "--full" in sys.argv

    if len(args) < 1:
        print("༺四方阁༻易爪龙虾命盘解读引擎")
        print("将八字+紫微+六壬等排盘结果整合为LLM解读Prompt")
        print()
        print("用法:")
        print("  python reading.py <日期> <性别>       # 八字+紫微")
        print("  python reading.py <日期> <性别> --full # 全引擎")
        return

    birth = args[0] + (" " + args[1] if len(args) > 1 and ":" in args[1] else "")
    sex = 0 if len(args) >= 2 and args[-1] in ("女", "0") else 1

    parts = birth.replace("T", " ").replace("/", "-").replace(".", "-").split()
    date_str = parts[0].replace("-", "")
    time_str = parts[1] if len(parts) > 1 else "12:00"
    time_str = time_str.replace(":", "")

    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    hour = int(time_str[:2]) if len(time_str) >= 2 else 12
    minute = int(time_str[2:4]) if len(time_str) >= 4 else 0

    print("=" * 70)
    print("  ༺四方阁༻易爪龙虾 · 命盘解读 Prompt")
    print("=" * 70)
    print()
    print(f"  命主: {year}年{month}月{day}日 {hour:02d}:{minute:02d} ({'男' if sex == 1 else '女'})")
    print(f"  引擎: 八字 + 紫微斗数" + (" + 六壬 + 奇门" if full_mode else ""))
    print(f"  Prompt长度: 待生成...")
    print()

    prompt = build_reading_prompt(year, month, day, hour, minute, sex, full_mode)

    print(prompt)
    print()
    print("=" * 70)
    print("  将此 Prompt 发送给 LLM 即可获得完整命盘解读报告")
    print("=" * 70)


if __name__ == '__main__':
    main()

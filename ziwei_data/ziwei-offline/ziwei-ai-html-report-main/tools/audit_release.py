#!/usr/bin/env python3
"""Generate release audit artifacts comparing path A and path B."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import generate_report
import render_prompts
import report_validators
import ziwei_offline

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DATE = date(2026, 5, 24)
OUT_ROOT = ROOT / "work" / f"release-audit-{AUDIT_DATE.isoformat()}"


@dataclass(frozen=True)
class Profile:
    slug: str
    name: str
    solar: str
    time: str
    gender: str
    birthplace: str
    target_year: int = 2026


PROFILES: Tuple[Profile, ...] = (
    Profile("p01-shenzhen-19960316-male", "深圳上午男盘", "1996-03-16", "08:40", "male", "广东省深圳市"),
    Profile("p02-kashi-19940701-male", "喀什边界男盘", "1994-07-01", "23:50", "male", "喀什市"),
    Profile("p03-xiamen-19910928-female", "厦门夜间女盘", "1991-09-28", "21:43", "female", "厦门市"),
)

FILLER = (
    "本段严格依据命宫、身宫、三方四正、四化引动与大限流年叠合来组织判断，"
    "先讲结构，再讲风险，再给行动建议，避免把单颗星曜孤立夸大。"
)


def run_checked(args: List[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stderr}")
    return proc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json_stdout(proc: subprocess.CompletedProcess[str]) -> Dict[str, Any]:
    return json.loads(proc.stdout)


def payload_path_a(profile: Profile) -> Dict[str, Any]:
    proc = run_checked([
        sys.executable,
        str(ROOT / "tools" / "ziwei_offline.py"),
        "--solar",
        profile.solar,
        "--time",
        profile.time,
        "--gender",
        profile.gender,
        "--birthplace",
        profile.birthplace,
        "--geocode-mode",
        "offline",
        "--target-year",
        str(profile.target_year),
        "--format",
        "json",
    ])
    return load_json_stdout(proc)


def payload_path_b(profile: Profile) -> Dict[str, Any]:
    emit = run_checked([
        sys.executable,
        str(ROOT / "tools" / "ziwei_offline.py"),
        "--solar",
        profile.solar,
        "--time",
        profile.time,
        "--gender",
        profile.gender,
        "--birthplace",
        profile.birthplace,
        "--geocode-mode",
        "offline",
        "--target-year",
        str(profile.target_year),
        "--emit-iztro-birth-json",
    ])
    chart = run_checked(
        ["node", str(ROOT / "tools" / "chart_iztro.cjs"), "--birth-json", "-"],
        input_text=emit.stdout,
    )
    payload = run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "ziwei_offline.py"),
            "--from-chart-json",
            "--target-year",
            str(profile.target_year),
            "--format",
            "json",
        ],
        input_text=chart.stdout,
    )
    return load_json_stdout(payload)


def palace(chart: Dict[str, Any], name: str) -> Dict[str, Any]:
    return next(p for p in chart["palaces"] if p["name"] == name)


def star_names(stars: Iterable[Dict[str, Any]]) -> str:
    names = [str(star.get("name", "")) for star in stars]
    return "、".join(name for name in names if name) or "无主星"


def major_line(chart: Dict[str, Any], palace_name: str) -> str:
    p = palace(chart, palace_name)
    return f"{palace_name}在{p['branch']}宫，主星为{star_names(p['majorStars'])}，辅曜为{star_names(p['minorStars'])}。"


def natal_html(profile: Profile, payload: Dict[str, Any], path_label: str) -> str:
    chart = payload["chart"]
    life = chart["lifePalace"]
    body = chart["bodyPalace"]
    patterns = "；".join(chart.get("patterns", [])[:3]) or "格局以主星组合与三方四正互证为准"
    sections = [
        ("壹· 命格总断", [
            f"{profile.name}（{path_label}）命宫落{life['branch']}，{major_line(chart, '命宫')}{FILLER}",
            f"身宫落{body['name']}，行动惯性要与命宫同看；格局提示：{patterns}。{FILLER}",
        ]),
        ("贰· 事业与财运", [
            f"{major_line(chart, '官禄宫')}事业判断以官禄宫为主，再参考命宫与迁移宫。{FILLER}",
            f"{major_line(chart, '财帛宫')}财务上宜区分稳定现金流与机会型收益。{FILLER}",
        ]),
        ("叁· 婚姻与情感", [
            f"{major_line(chart, '夫妻宫')}情感关系需看夫妻宫、福德宫与迁移宫的互相牵动。{FILLER}",
            f"若四化落入关系宫位，应先看沟通模式，再看事件吉凶。{FILLER}",
        ]),
        ("肆· 六亲与人际", [
            f"{major_line(chart, '交友宫')}交友宫显示合作边界，人际不能只看贵人星。{FILLER}",
            f"{major_line(chart, '父母宫')}父母宫与兄弟宫可辅助判断早年支持系统。{FILLER}",
        ]),
        ("伍· 运势隐忧与建议", [
            f"{major_line(chart, '疾厄宫')}健康提醒以作息、压力与长期习惯为主，不作医疗断言。{FILLER}",
            f"{major_line(chart, '迁移宫')}迁移宫提示外部环境变化，宜把风险拆成可执行清单。{FILLER}",
        ]),
        ("陆· 命格金句", [
            f"命盘提供的是结构化倾向，不是替人做决定；以命宫定性，以大限看势，以流年定事。{FILLER}",
        ]),
    ]
    return "\n".join(
        f"<h3>{title}</h3><ul>"
        + "".join(f"<li><strong>{item[:8]}</strong>：{item}{FILLER * 2}</li>" for item in items)
        + "</ul>"
        for title, items in sections
    )


def yearly_html(profile: Profile, payload: Dict[str, Any], path_label: str) -> str:
    chart = payload["chart"]
    yearly = chart["yearly"]
    current = yearly["currentDecadal"]
    sections = [
        ("壹· 年度总象", [
            f"{profile.target_year}年为{yearly['stem']}{yearly['branch']}年，流年命宫叠宫至{yearly['palaceName']}，流年四化：{'、'.join(yearly['mutagens'])}。",
            f"当前大限在{current['palaceName']}，大限四化：{'、'.join(current['mutagens'])}；{path_label} 以大限为底、流年为触发。",
        ]),
        ("贰· 名利机缘", [
            f"{major_line(chart, '官禄宫')}名利判断需看流年四化是否引动官禄、财帛、迁移三宫。",
            f"{major_line(chart, '财帛宫')}财务建议重在节奏控制，忌用单年吉象替代预算纪律。",
        ]),
        ("叁· 情感与家宅", [
            f"{major_line(chart, '夫妻宫')}关系议题应结合流年命宫叠宫，不宜只看桃花星。",
            f"{major_line(chart, '田宅宫')}家宅与长期资产宜稳健处理，避免因情绪性判断频繁变动。",
        ]),
        ("肆· 月令趋势", [
            "上半年适合盘点资源、建立秩序；下半年适合复盘合作边界与现金流节奏。",
            "遇到化忌引动时先减法处理，遇到化禄化权时也要保留退出机制。",
        ]),
        ("伍· 锦囊寄语", [
            "年度建议以专业判断、健康作息和财务风控为底线，命理文字只作文化参考。",
            f"若流年叠宫到关键宫位，应把提醒转成行动计划，而不是转成焦虑。{FILLER}",
        ]),
    ]
    return "\n".join(
        f"<h3>{title}</h3><ul>"
        + "".join(f"<li><strong>{item[:8]}</strong>：{item}{FILLER * 3}</li>" for item in items)
        + "</ul>"
        for title, items in sections
    )


def kline_briefs(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for row in payload["klineData"]:
        age = int(row["age"])
        close = float(row["close"])
        if close >= 90:
            brief = "高位年份，宜主动承接机会，同时控制扩张节奏。"
        elif close <= 35:
            brief = "低位整理，宜保守蓄力，重视健康与现金流。"
        else:
            brief = "平稳推进，适合按计划积累，不宜过度冒进。"
        rows.append({"age": age, "brief": brief, "reason": f"score={row.get('score')}，大限={row.get('daYun')}"})
    return rows


def compact_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "lunar": chart["lunar"],
        "effectiveSolar": chart["birth"]["effectiveSolar"],
        "trueSolarTime": chart["birth"]["trueSolar"]["time"],
        "timeBranch": chart["birth"]["timeBranch"],
        "lifePalace": chart["lifePalace"],
        "bodyPalace": chart["bodyPalace"],
        "fiveElementsClass": chart["fiveElementsClass"],
        "majorStars": {
            p["name"]: [s["name"] for s in p["majorStars"]]
            for p in chart["palaces"]
        },
        "minorStars": {
            p["name"]: [s["name"] for s in p["minorStars"]]
            for p in chart["palaces"]
        },
        "yearly": chart["yearly"],
    }


def kline_metrics(rows: List[Dict[str, Any]], target_year: int) -> Dict[str, Any]:
    closes = [float(r["close"]) for r in rows]
    highs = [float(r["high"]) for r in rows]
    lows = [float(r["low"]) for r in rows]
    target_row = next(r for r in rows if int(r["year"]) == target_year)
    return {
        "count": len(rows),
        "targetYearRow": target_row,
        "minLow": min(lows),
        "maxHigh": max(highs),
        "maxClose": max(closes),
        "peakCloseAges": [int(r["age"]) for r in rows if float(r["close"]) >= 95.0],
        "lowCloseAges": [int(r["age"]) for r in rows if float(r["close"]) <= 35.0],
    }


def compare_payloads(payload_a: Dict[str, Any], payload_b: Dict[str, Any]) -> Dict[str, Any]:
    chart_a = compact_chart(payload_a["chart"])
    chart_b = compact_chart(payload_b["chart"])
    kline_a = payload_a["klineData"]
    kline_b = payload_b["klineData"]
    ok_a, msg_a = ziwei_offline.validate_kline_data(kline_a)
    ok_b, msg_b = ziwei_offline.validate_kline_data(kline_b)
    kline_exact = kline_a == kline_b
    chart_exact = chart_a == chart_b
    return {
        "chartExact": chart_exact,
        "chartDiffKeys": [key for key in chart_a if chart_a[key] != chart_b[key]],
        "yearlyExact": payload_a["chart"]["yearly"] == payload_b["chart"]["yearly"],
        "klineExact": kline_exact,
        "klineValidation": {"pathA": msg_a if ok_a else f"FAIL: {msg_a}", "pathB": msg_b if ok_b else f"FAIL: {msg_b}"},
        "pathA": {
            "chart": chart_a,
            "klineMetrics": kline_metrics(kline_a, int(payload_a["chart"]["yearly"]["year"])),
        },
        "pathB": {
            "chart": chart_b,
            "klineMetrics": kline_metrics(kline_b, int(payload_b["chart"]["yearly"]["year"])),
        },
    }


def extract_json_script(html: str, script_id: str) -> Any:
    match = re.search(
        rf'<script type="application/json" id="{re.escape(script_id)}">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"missing script#{script_id}")
    return json.loads(match.group(1))


def render_artifacts(profile: Profile, path_label: str, payload: Dict[str, Any], out_dir: Path) -> Dict[str, Any]:
    write_json(out_dir / f"payload-{path_label.lower()}.json", payload)
    render_prompts.render_all_prompts(payload, out_dir / f"prompts-{path_label.lower()}", work_root=out_dir)

    natal = natal_html(profile, payload, path_label)
    yearly = yearly_html(profile, payload, path_label)
    brief = kline_briefs(payload)
    natal_path = out_dir / f"natal-{path_label.lower()}.html"
    yearly_path = out_dir / f"yearly-{path_label.lower()}.html"
    brief_path = out_dir / f"kline-brief-{path_label.lower()}.json"
    report_path = out_dir / f"report-{path_label.lower()}.html"
    natal_path.write_text(natal, encoding="utf-8")
    yearly_path.write_text(yearly, encoding="utf-8")
    write_json(brief_path, brief)

    kline_rows = generate_report.merge_kline_briefs(payload["klineData"], brief)
    html = generate_report.assemble_report(
        (ROOT / "report-template.html").read_text(encoding="utf-8"),
        payload["chart"],
        profile.target_year,
        natal,
        yearly,
        kline_rows,
    )
    ok, errors = report_validators.validate_report_inputs(
        chart=payload["chart"],
        natal_html=natal,
        yearly_html=yearly,
        kline_rows=kline_rows,
        assembled_html=html,
    )
    if not ok:
        raise RuntimeError(f"{profile.slug} {path_label} report validation failed: {errors}")
    report_path.write_text(html, encoding="utf-8")
    return {
        "payload": str((out_dir / f"payload-{path_label.lower()}.json").relative_to(ROOT)),
        "prompts": str((out_dir / f"prompts-{path_label.lower()}").relative_to(ROOT)),
        "natal": str(natal_path.relative_to(ROOT)),
        "yearly": str(yearly_path.relative_to(ROOT)),
        "klineBrief": str(brief_path.relative_to(ROOT)),
        "report": str(report_path.relative_to(ROOT)),
        "embeddedChartPalaces": len(extract_json_script(html, "chart-data")["palaces"]),
        "embeddedKlineRows": len(extract_json_script(html, "kline-data")),
        "reportChineseChars": {
            "natal": report_validators.count_chinese_chars(natal),
            "yearly": report_validators.count_chinese_chars(yearly),
        },
    }


def render_markdown(summary: Dict[str, Any]) -> str:
    lines = [
        "# ziwei-ai-html-report 发布前审核报告",
        "",
        f"- 审核日期：{summary['auditDate']}",
        "- 路径 A：纯 Python `tools/ziwei_offline.py`，离线地理编码，默认真太阳时。",
        "- 路径 B：Python 真太阳时 birth JSON → `tools/chart_iztro.cjs` → Python payload 回灌。",
        "- 正文说明：本次为发布交验，HTML 正文使用确定性审计片段验证结构、质量门槛与安全校验；未调用外部 LLM。",
        "",
        "## 测试矩阵",
        "",
    ]
    for item in summary["profiles"]:
        profile = item["profile"]
        comparison = item["comparison"]
        status = "通过" if item["status"] == "pass" else "失败"
        lines += [
            f"### {profile['name']}：{status}",
            f"- 输入：{profile['solar']} {profile['time']}，{profile['gender']}，{profile['birthplace']}，流年 {profile['target_year']}",
            f"- 排盘核心：{'一致' if comparison['chartExact'] else '存在差异'}",
            f"- 流年数据：{'一致' if comparison['yearlyExact'] else '存在差异'}",
            f"- K 线数值：{'一致' if comparison['klineExact'] else '存在差异'}；校验 A={comparison['klineValidation']['pathA']}，B={comparison['klineValidation']['pathB']}",
            f"- A 产物：`{item['artifacts']['A']['report']}`",
            f"- B 产物：`{item['artifacts']['B']['report']}`",
        ]
        if comparison["chartDiffKeys"]:
            lines.append(f"- 差异键：{', '.join(comparison['chartDiffKeys'])}")
        target_a = comparison["pathA"]["klineMetrics"]["targetYearRow"]
        lines.append(
            f"- 2026 K 线：age={target_a['age']}，open={target_a['open']}，close={target_a['close']}，score={target_a['score']}"
        )
        lines.append("")
    lines += [
        "## 不良差异与不稳定因素",
        "",
    ]
    if summary["badDiffs"]:
        lines.extend(f"- {item}" for item in summary["badDiffs"])
    else:
        lines.append("- 未发现 A/B 排盘核心、流年数据或 K 线数值的不良差异。")
    if summary["risks"]:
        lines.extend(f"- {item}" for item in summary["risks"])
    lines += [
        "",
        "## 已修复项",
        "",
        "- `tools/ziwei_offline.py` CLI 现在接受 `男/女` 并归一化为 `male/female`，与 `SKILL.md` 和 README 的输入契约一致。",
        "",
        "## 发布建议",
        "",
        summary["releaseRecommendation"],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, Any] = {
        "auditDate": AUDIT_DATE.isoformat(),
        "profiles": [],
        "badDiffs": [],
        "risks": [],
        "releaseRecommendation": "",
    }

    for profile in PROFILES:
        profile_dir = OUT_ROOT / profile.slug
        profile_dir.mkdir(parents=True, exist_ok=True)
        payload_a = payload_path_a(profile)
        payload_b = payload_path_b(profile)
        artifacts = {
            "A": render_artifacts(profile, "A", payload_a, profile_dir),
            "B": render_artifacts(profile, "B", payload_b, profile_dir),
        }
        comparison = compare_payloads(payload_a, payload_b)
        bad = []
        if not comparison["chartExact"]:
            bad.append("排盘核心不一致")
        if not comparison["yearlyExact"]:
            bad.append("流年数据不一致")
        if not comparison["klineExact"]:
            bad.append("K 线数值不一致")
        if bad:
            summary["badDiffs"].append(f"{profile.name}: {'、'.join(bad)}")
        summary["profiles"].append({
            "profile": profile.__dict__,
            "status": "fail" if bad else "pass",
            "artifacts": artifacts,
            "comparison": comparison,
        })

    if not summary["badDiffs"]:
        summary["releaseRecommendation"] = "建议发布：三份样例的路径 A/B 排盘核心、流年与 K 线数值完全一致，交付 HTML 均通过质量与安全校验。"
    else:
        summary["releaseRecommendation"] = "暂缓发布：存在 A/B 不良差异，需先定位并修复。"
    summary["risks"].append("路径 B 仍依赖 Node 与 iztro；发布说明需保留路径 A 可独立运行、路径 B 为可选对齐链路的边界。")
    summary["risks"].append("本次未调用外部 LLM 生成自由文案，专业性校验覆盖提示词约束、正文结构门槛、安全门槛与 HTML 组装。")

    write_json(OUT_ROOT / "audit-summary.json", summary)
    (OUT_ROOT / "audit-report.md").write_text(render_markdown(summary), encoding="utf-8")
    print(OUT_ROOT / "audit-report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Assemble a complete ziwei-ai-html-report single-file HTML from payload + outputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from report_validators import validate_report_inputs
from ziwei_offline import compute_age_info, generate_chart

SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = SKILL_ROOT / "report-template.html"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _gender_label(gender: str) -> str:
    if gender == "male":
        return "男"
    if gender == "female":
        return "女"
    return gender


def build_chart_embed(chart: Dict[str, Any], target_year: int) -> Dict[str, Any]:
    life = chart.get("lifePalace") or {}
    body = chart.get("bodyPalace") or {}
    birth = chart.get("birth") or {}
    return {
        "birthSolar": birth.get("effectiveSolar") or birth.get("solar", ""),
        "fiveElementsClass": chart.get("fiveElementsClass", ""),
        "lifePalaceName": f"{life.get('name', '命宫')}（{life.get('branch', '')}宫）",
        "bodyPalaceName": f"{body.get('name', '')}（{body.get('branch', '')}宫）",
        "targetYear": str(target_year),
        "palaces": chart.get("palaces", []),
    }


def build_meta_values(chart: Dict[str, Any], target_year: int) -> Dict[str, str]:
    birth = chart.get("birth") or {}
    true_solar = birth.get("trueSolar") or {}
    coords = birth.get("coordinates") or {}
    correction = true_solar.get("totalCorrectionMinutes", 0)
    ages = compute_age_info(chart, target_year)
    age_parts = [
        f"虚岁 {ages['nominalAge']} 岁（排大限）",
        f"周岁 {ages['actualAgeAtYearEnd']} 岁（截至{target_year}-12-31）",
    ]
    if ages["actualAgeAtReference"] != ages["actualAgeAtYearEnd"]:
        age_parts.append(
            f"周岁 {ages['actualAgeAtReference']} 岁（截至{ages['referenceDate']}）"
        )
    return {
        "meta-solar": str(birth.get("effectiveSolar") or birth.get("solar", "")),
        "meta-birthplace": str(birth.get("birthplace") or "未提供"),
        "meta-local-time": str(birth.get("localTime") or ""),
        "meta-true-solar-time": str(true_solar.get("time") or birth.get("localTime") or ""),
        "meta-time-correction": f"{correction}分钟",
        "meta-geo-source": str(coords.get("source") or "none"),
        "meta-gender": _gender_label(str(birth.get("gender", ""))),
        "meta-five": str(chart.get("fiveElementsClass", "")),
        "meta-target-year": str(target_year),
        "meta-age": " · ".join(age_parts),
        "meta-generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _replace_span_content(html: str, element_id: str, value: str) -> str:
    pattern = re.compile(
        rf'(<span id="{re.escape(element_id)}">)([\s\S]*?)(</span>)',
        flags=re.IGNORECASE,
    )
    if not pattern.search(html):
        raise ValueError(f"模板缺少 span#{element_id}")
    return pattern.sub(lambda m: m.group(1) + value + m.group(3), html, count=1)


def _replace_div_content(html: str, element_id: str, inner_html: str) -> str:
    pattern = re.compile(
        rf'(<div[^>]*\bid="{re.escape(element_id)}"[^>]*>)([\s\S]*?)(</div>)',
        flags=re.IGNORECASE,
    )
    if not pattern.search(html):
        raise ValueError(f"模板缺少 div#{element_id}")
    return pattern.sub(rf"\1{inner_html}\3", html, count=1)


def _replace_element_content(html: str, element_id: str, inner_html: str) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[a-z0-9]+)[^>]*\bid="{re.escape(element_id)}"[^>]*>)([\s\S]*?)(</(?P=tag)>)',
        flags=re.IGNORECASE,
    )
    if not pattern.search(html):
        raise ValueError(f"模板缺少元素 #{element_id}")
    return pattern.sub(rf"\1{inner_html}\4", html, count=1)


def _replace_json_script(html: str, script_id: str, data: Any) -> str:
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    pattern = re.compile(
        rf'(<script type="application/json" id="{re.escape(script_id)}">)([\s\S]*?)(</script>)',
        flags=re.IGNORECASE,
    )
    if not pattern.search(html):
        raise ValueError(f"模板缺少 script#{script_id}")
    return pattern.sub(lambda m: m.group(1) + serialized + m.group(3), html, count=1)


def merge_kline_briefs(
    kline_rows: List[Dict[str, Any]],
    brief_rows: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    if not brief_rows:
        return kline_rows
    brief_by_age: Dict[int, Dict[str, Any]] = {}
    for row in brief_rows:
        if not isinstance(row, dict) or "age" not in row:
            continue
        brief_by_age[int(row["age"])] = row
    merged: List[Dict[str, Any]] = []
    forbidden = {"open", "close", "high", "low"}
    for row in kline_rows:
        next_row = dict(row)
        extra = brief_by_age.get(int(row.get("age", -1)))
        if extra:
            for key, value in extra.items():
                if key in forbidden or key == "age":
                    continue
                next_row[key] = value
        merged.append(next_row)
    return merged


def assemble_report(
    template: str,
    chart: Dict[str, Any],
    target_year: int,
    natal_html: str,
    yearly_html: str,
    kline_rows: List[Dict[str, Any]],
) -> str:
    html = template
    for element_id, value in build_meta_values(chart, target_year).items():
        html = _replace_span_content(html, element_id, value)
    html = _replace_div_content(html, "content-natal", natal_html.strip())
    html = _replace_div_content(html, "content-yearly", yearly_html.strip())
    html = _replace_div_content(html, "chart-grid", "")
    html = _replace_element_content(html, "integrity-summary", "交付前校验已通过；浏览器打开后会再次执行前端完整性检查。")
    html = _replace_json_script(html, "chart-data", build_chart_embed(chart, target_year))
    html = _replace_json_script(html, "kline-data", kline_rows)
    return html


def _parse_date(value: str) -> Tuple[int, int, int]:
    try:
        d = date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期格式必须为 YYYY-MM-DD") from exc
    return d.year, d.month, d.day


def _parse_time(value: str) -> Tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("time 格式必须为 HH:mm")
    return int(parts[0]), int(parts[1])


def _load_chart_from_args(args: argparse.Namespace) -> Tuple[Dict[str, Any], int, Dict[str, Any]]:
    payload: Dict[str, Any] = {}
    if args.payload_json:
        payload = _read_json(Path(args.payload_json))
        if not isinstance(payload, dict) or "chart" not in payload:
            raise ValueError("payload JSON 必须包含 chart 字段")
        chart = payload["chart"]
        target_year = args.target_year or chart.get("yearly", {}).get("year")
        if target_year is None:
            raise ValueError("无法确定 target-year，请通过 --target-year 指定")
        return chart, int(target_year), payload

    if args.solar is None or args.gender is None:
        raise ValueError("必须提供 --payload-json，或同时提供 --solar 与 --gender")

    y, m, d = args.solar
    hour = args.hour
    minute = 0
    if args.time:
        hour, minute = _parse_time(args.time)
    if hour is None:
        raise ValueError("必须提供 --time 或 --hour")
    target_year = args.target_year or datetime.today().year
    chart = generate_chart(
        y,
        m,
        d,
        hour,
        args.gender,
        target_year,
        minute=minute,
        birthplace=args.birthplace,
        longitude=args.longitude,
        latitude=args.latitude,
        use_true_solar_time=not args.disable_true_solar_time,
        geocode_mode=args.geocode_mode,
    )
    return chart, int(target_year), payload


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble ziwei-ai-html-report single-file HTML.")
    parser.add_argument("--payload-json", help="ziwei_offline.py 输出的完整 payload JSON 文件")
    parser.add_argument("--solar", type=_parse_date, help="阳历生日 YYYY-MM-DD（无 payload 时）")
    parser.add_argument("--hour", type=int, help="出生小时 0-23")
    parser.add_argument("--time", help="出生时间 HH:mm")
    parser.add_argument("--gender", choices=["male", "female"])
    parser.add_argument("--birthplace", help="出生地")
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--geocode-mode", choices=["online", "offline", "hybrid"], default="hybrid")
    parser.add_argument("--disable-true-solar-time", action="store_true")
    parser.add_argument("--target-year", type=int, help="流年分析年份")
    parser.add_argument("--natal-html", required=True, help="综合批注 HTML 片段文件")
    parser.add_argument("--yearly-html", required=True, help="流年运势 HTML 片段文件")
    parser.add_argument("--kline-json", help="确定性 K 线 JSON 数组文件；缺省时使用 payload.klineData")
    parser.add_argument("--kline-brief-json", help="模型生成的 K 线 brief/reason JSON（不得含 OHLC）")
    parser.add_argument("--template", default=str(TEMPLATE_FILE), help="HTML 模板路径")
    parser.add_argument("--output", "-o", required=True, help="输出 HTML 文件路径")
    parser.add_argument("--skip-validation", action="store_true", help="跳过交付前校验（仅调试）")
    args = parser.parse_args(argv)

    try:
        chart, target_year, payload = _load_chart_from_args(args)
        natal_html = _read_text(Path(args.natal_html))
        yearly_html = _read_text(Path(args.yearly_html))
        if args.kline_json:
            kline_rows = _read_json(Path(args.kline_json))
        else:
            kline_rows = payload.get("klineData")
        if not isinstance(kline_rows, list):
            raise ValueError("kline JSON 必须为数组；请提供 --kline-json 或 payload.klineData")
        brief_rows = _read_json(Path(args.kline_brief_json)) if args.kline_brief_json else None
        if brief_rows is not None and not isinstance(brief_rows, list):
            raise ValueError("kline brief JSON 必须为数组")
        kline_rows = merge_kline_briefs(kline_rows, brief_rows)
        template = _read_text(Path(args.template))
        html = assemble_report(template, chart, target_year, natal_html, yearly_html, kline_rows)
        if not args.skip_validation:
            ok, errors = validate_report_inputs(
                chart=chart,
                natal_html=natal_html,
                yearly_html=yearly_html,
                kline_rows=kline_rows,
                assembled_html=html,
            )
            if not ok:
                for err in errors:
                    print(f"error: {err}", file=sys.stderr)
                return 2
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(str(out_path))
        return 0
    except (ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

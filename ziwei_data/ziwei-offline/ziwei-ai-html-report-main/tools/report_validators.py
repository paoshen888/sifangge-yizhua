#!/usr/bin/env python3
"""Output quality validators for ziwei-ai-html-report HTML assembly."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ziwei_offline import validate_chart_integrity, validate_kline_data

NATAL_SECTION_MARKERS: Tuple[str, ...] = ("壹·", "贰·", "叁·", "肆·", "伍·", "陆·")
YEARLY_SECTION_MARKERS: Tuple[str, ...] = ("壹·", "贰·", "叁·", "肆·", "伍·")

NATAL_PALACE_ANCHORS: Tuple[str, ...] = (
    "命宫",
    "福德宫",
    "官禄宫",
    "财帛宫",
    "夫妻宫",
    "迁移宫",
    "交友宫",
    "疾厄宫",
)

PLACEHOLDER_PATTERNS: Tuple[re.Pattern[str], ...] = (
    re.compile(r"请填入"),
    re.compile(r"Agent："),
    re.compile(r"\{\{[A-Z_]+\}\}"),
)

DISCLAIMER_MARKERS: Tuple[str, ...] = (
    "术数推演仅供参考",
    "切勿执着",
    "不具有预测效力",
)

_CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")

# Model-generated HTML fragments must not contain executable markup.
_FRAGMENT_SCRIPT_RE = re.compile(r"<\s*script\b", re.IGNORECASE)
_FRAGMENT_EVENT_ATTR_RE = re.compile(
    r"""\s(?:on[a-z]+)\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""",
    re.IGNORECASE,
)
_FRAGMENT_JAVASCRIPT_URL_RE = re.compile(r"javascript\s*:", re.IGNORECASE)
_EXTERNAL_SCRIPT_SRC_RE = re.compile(
    r"""<\s*script\b[^>]*\bsrc\s*=\s*(?:"[^"]*"|'[^']*')""",
    re.IGNORECASE,
)


def count_chinese_chars(text: str) -> int:
    return len(_CHINESE_RE.findall(text))


def _strip_html(text: str) -> str:
    no_script = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
    no_tags = re.sub(r"<[^>]+>", "", no_script)
    return re.sub(r"\s+", "", no_tags)


def _missing_sections(text: str, markers: Sequence[str]) -> List[str]:
    missing = []
    for marker in markers:
        if marker not in text and marker.replace("·", "") not in text:
            missing.append(marker)
    return missing


def validate_natal_content(
    html_or_text: str,
    *,
    min_chars: int = 1200,
    min_anchors: int = 5,
) -> Tuple[bool, str]:
    plain = _strip_html(html_or_text)
    missing = _missing_sections(plain, NATAL_SECTION_MARKERS)
    if missing:
        return False, f"综合批注缺少章节：{', '.join(missing)}"
    if count_chinese_chars(plain) < min_chars:
        return False, f"综合批注中文字数不足（需≥{min_chars}，当前 {count_chinese_chars(plain)}）"
    anchors = sum(1 for name in NATAL_PALACE_ANCHORS if name in plain)
    if anchors < min_anchors:
        return False, f"综合批注宫位锚点不足（需≥{min_anchors}，当前 {anchors}）"
    return True, "ok"


def validate_yearly_content(
    html_or_text: str,
    *,
    min_chars: int = 800,
) -> Tuple[bool, str]:
    plain = _strip_html(html_or_text)
    missing = _missing_sections(plain, YEARLY_SECTION_MARKERS)
    if missing:
        return False, f"流年报告缺少章节：{', '.join(missing)}"
    if count_chinese_chars(plain) < min_chars:
        return False, f"流年报告中文字数不足（需≥{min_chars}，当前 {count_chinese_chars(plain)}）"
    if "流年四化" not in plain and "四化" not in plain:
        return False, "流年报告未提及流年四化"
    if "大限四化" not in plain and ("大限" not in plain or "四化" not in plain):
        return False, "流年报告未提及当前大限四化"
    if "叠" not in plain and "叠宫" not in plain:
        return False, "流年报告未提及流年命宫叠宫"
    return True, "ok"


def _html_visible_text(html: str) -> str:
    no_comments = re.sub(r"<!--[\s\S]*?-->", "", html)
    no_scripts = re.sub(r"<script[\s\S]*?</script>", "", no_comments, flags=re.IGNORECASE)
    return no_scripts


def validate_safe_html_fragment(html_or_text: str, *, label: str = "HTML 片段") -> Tuple[bool, str]:
    """Reject executable or script-bearing markup in model-generated content fragments."""
    if _FRAGMENT_SCRIPT_RE.search(html_or_text):
        return False, f"{label} 不允许包含 <script> 标签"
    if _FRAGMENT_EVENT_ATTR_RE.search(html_or_text):
        return False, f"{label} 不允许包含事件属性（如 onclick、onerror）"
    if _FRAGMENT_JAVASCRIPT_URL_RE.search(html_or_text):
        return False, f"{label} 不允许包含 javascript: URL"
    return True, "ok"


def validate_html_delivery(html: str) -> Tuple[bool, str]:
    if "<!DOCTYPE html>" not in html and "<!doctype html>" not in html.lower():
        return False, "HTML 交付物缺少 DOCTYPE"
    for marker in DISCLAIMER_MARKERS:
        if marker not in html:
            return False, f"HTML 缺少免责声明关键句：{marker}"
    if _EXTERNAL_SCRIPT_SRC_RE.search(html):
        return False, "HTML 不允许外链脚本（<script src=...>）"
    visible = _html_visible_text(html)
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(visible):
            return False, f"HTML 仍含占位符或 Agent 提示：{pattern.pattern}"
    return True, "ok"


def validate_chart_payload(chart: Dict[str, Any]) -> Tuple[bool, str]:
    try:
        validate_chart_integrity(chart)
    except ValueError as exc:
        return False, str(exc)
    palaces = chart.get("palaces", [])
    if len(palaces) != 12:
        return False, "chart.palaces 必须为 12 宫"
    return True, "ok"


def validate_kline_payload(kline_rows: List[Dict[str, Any]]) -> Tuple[bool, str]:
    return validate_kline_data(kline_rows)


def validate_report_inputs(
    *,
    chart: Dict[str, Any],
    natal_html: str,
    yearly_html: str,
    kline_rows: List[Dict[str, Any]],
    assembled_html: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """Run all pre-delivery checks; returns (ok, error_messages)."""
    errors: List[str] = []
    for ok, msg in (
        validate_chart_payload(chart),
        validate_safe_html_fragment(natal_html, label="综合批注"),
        validate_safe_html_fragment(yearly_html, label="流年报告"),
        validate_natal_content(natal_html),
        validate_yearly_content(yearly_html),
        validate_kline_payload(kline_rows),
    ):
        if not ok:
            errors.append(msg)
    if assembled_html is not None:
        ok, msg = validate_html_delivery(assembled_html)
        if not ok:
            errors.append(msg)
    return (len(errors) == 0, errors)

#!/usr/bin/env python3
"""Render system/user prompts from prompts.md + ziwei_offline payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FILE = SKILL_ROOT / "prompts.md"

_SECTION_RE = re.compile(r"^##\s+(?:0\.|0b\.|[1-4]\.\s+.+)$", re.MULTILINE)
_FENCE_RE = re.compile(r"```(?:\w+)?\n([\s\S]*?)```", re.MULTILINE)
_SUBSECTION_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _extract_fenced_blocks(section_text: str) -> List[str]:
    return [m.group(1).strip() for m in _FENCE_RE.finditer(section_text)]


def _split_sections(md: str) -> Dict[str, str]:
    parts: Dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(md))
    for i, match in enumerate(matches):
        title = match.group(0).strip()[3:].strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        parts[title] = md[start:end]
    return parts


def _section_by_prefix(sections: Dict[str, str], prefix: str, *, exact: bool = False) -> str:
    for title, body in sections.items():
        if exact:
            if title == prefix:
                return body
        elif title.startswith(prefix):
            return body
    raise KeyError(f"prompts.md 缺少章节：{prefix}")


def _subsection(body: str, heading_prefix: str) -> str:
    matches = list(_SUBSECTION_RE.finditer(body))
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        if title.startswith(heading_prefix):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            return body[start:end]
    raise KeyError(f"prompts.md 缺少子章节：{heading_prefix}")


def build_natal_system(sections: Dict[str, str]) -> str:
    main = _section_by_prefix(sections, "1. 紫微命盘综合批注（系统提示词）", exact=True)
    blocks = _extract_fenced_blocks(main)
    if not blocks:
        raise ValueError("综合批注 system 提示词块为空")
    system = blocks[0]
    for sub_prefix in ("1d.", "1c."):
        try:
            extra_blocks = _extract_fenced_blocks(_subsection(main, sub_prefix))
            if extra_blocks:
                system += "\n\n" + extra_blocks[-1]
        except KeyError:
            pass
    return system.strip()


def build_yearly_system(sections: Dict[str, str]) -> str:
    main = _section_by_prefix(sections, "2. 年度流年运势（系统提示词）", exact=True)
    blocks = _extract_fenced_blocks(main)
    if not blocks:
        raise ValueError("流年 system 提示词块为空")
    system = blocks[0]
    try:
        extra_blocks = _extract_fenced_blocks(_subsection(main, "2c."))
        if extra_blocks:
            system += "\n\n" + extra_blocks[-1]
    except KeyError:
        pass
    return system.strip()


def build_kline_system(sections: Dict[str, str]) -> str:
    main = _section_by_prefix(sections, "3. 人生 K 线", exact=False)
    blocks = _extract_fenced_blocks(main)
    if not blocks:
        raise ValueError("K 线 system 提示词块为空")
    return blocks[0].strip()


def _gender_display(chart: Dict[str, Any]) -> str:
    g = chart.get("birth", {}).get("gender", "")
    if g == "male":
        return "男"
    if g == "female":
        return "女"
    return str(g)


def _parse_solar_parts(chart: Dict[str, Any]) -> Tuple[int, int, int]:
    solar = chart.get("birth", {}).get("effectiveSolar") or chart.get("birth", {}).get("solar", "")
    y, m, d = map(int, str(solar).split("-"))
    return y, m, d


def build_natal_user(payload: Dict[str, Any], sections: Dict[str, str]) -> str:
    chart = payload["chart"]
    y, m, d = _parse_solar_parts(chart)
    main = _section_by_prefix(sections, "1. 紫微命盘综合批注（系统提示词）", exact=True)
    template_body = _subsection(main, "1b.")
    blocks = _extract_fenced_blocks(template_body)
    if not blocks:
        raise ValueError("综合批注 user 模板为空")
    context = payload.get("natalContext", "")
    if not context:
        raise ValueError("payload 缺少 natalContext")
    return (
        blocks[0]
        .replace("{{Y}}", str(y))
        .replace("{{M}}", str(m))
        .replace("{{D}}", str(d))
        .replace("{{GENDER}}", _gender_display(chart))
        .replace("{{FIVE_ELEMENTS_CLASS}}", str(chart.get("fiveElementsClass", "")))
        .replace("{{CONTEXT}}", context)
    ).strip()


def build_yearly_user(payload: Dict[str, Any], sections: Dict[str, str], target_year: int) -> str:
    chart = payload["chart"]
    by, bm, bd = _parse_solar_parts(chart)
    main = _section_by_prefix(sections, "2. 年度流年运势（系统提示词）", exact=True)
    template_body = _subsection(main, "2b.")
    blocks = _extract_fenced_blocks(template_body)
    if not blocks:
        raise ValueError("流年 user 模板为空")
    natal = payload.get("natalContext", "")
    yearly = payload.get("yearlyContext", "")
    if not natal or not yearly:
        raise ValueError("payload 缺少 natalContext 或 yearlyContext")
    return (
        blocks[0]
        .replace("{{YEAR}}", str(target_year))
        .replace("{{BY}}", str(by))
        .replace("{{BM}}", str(bm))
        .replace("{{BD}}", str(bd))
        .replace("{{GENDER}}", _gender_display(chart))
        .replace("{{FIVE_ELEMENTS_CLASS}}", str(chart.get("fiveElementsClass", "")))
        .replace("{{NATAL_CONTEXT}}", natal)
        .replace("{{YEARLY_CONTEXT}}", yearly)
    ).strip()


def build_kline_user(payload: Dict[str, Any], sections: Dict[str, str]) -> str:
    kline = payload.get("klineContext", "")
    if kline:
        return kline.strip()
    main = _section_by_prefix(sections, "3. 人生 K 线", exact=False)
    template_body = _subsection(main, "3b.")
    blocks = _extract_fenced_blocks(template_body)
    if not blocks:
        raise ValueError("K 线 user 模板为空且 payload 无 klineContext")
    return blocks[0].strip()


def render_all_prompts(
    payload: Dict[str, Any],
    out_dir: Path,
    *,
    prompts_md: Optional[Path] = None,
    work_root: Optional[Path] = None,
) -> Dict[str, Any]:
    if "chart" not in payload:
        raise ValueError("payload 必须包含 chart 字段")
    chart = payload["chart"]
    target_year = int(
        chart.get("yearly", {}).get("year")
        or payload.get("targetYear")
        or __import__("datetime").date.today().year
    )

    md = _read_text(prompts_md or PROMPTS_FILE)
    sections = _split_sections(md)

    prompts_dir = out_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "natal.system.md": build_natal_system(sections),
        "natal.user.md": build_natal_user(payload, sections),
        "yearly.system.md": build_yearly_system(sections),
        "yearly.user.md": build_yearly_user(payload, sections, target_year),
        "kline.system.md": build_kline_system(sections),
        "kline.user.md": build_kline_user(payload, sections),
    }

    written: Dict[str, str] = {}
    hashes: Dict[str, str] = {}
    for name, content in files.items():
        path = prompts_dir / name
        path.write_text(content + "\n", encoding="utf-8")
        written[name] = str(path.relative_to(out_dir))
        hashes[name] = _sha256(content)

    birth = chart.get("birth", {})
    wr = work_root or out_dir
    manifest = {
        "version": "2",
        "promptsSource": str((prompts_md or PROMPTS_FILE).resolve()),
        "payloadSummary": {
            "solar": birth.get("effectiveSolar") or birth.get("solar"),
            "localTime": birth.get("localTime"),
            "gender": birth.get("gender"),
            "birthplace": birth.get("birthplace"),
            "fiveElementsClass": chart.get("fiveElementsClass"),
            "targetYear": target_year,
            "hasKlineData": isinstance(payload.get("klineData"), list),
        },
        "promptFiles": written,
        "promptHashes": hashes,
        "agentContract": {
            "description": "Agent 按 manifest 调用模型写综合/流年正文；K 线 OHLC 必须使用 payload.klineData。",
            "requiredOutputs": [
                {
                    "id": "natal",
                    "path": str(wr / "natal.html"),
                    "format": "html",
                    "systemPrompt": written["natal.system.md"],
                    "userPrompt": written["natal.user.md"],
                },
                {
                    "id": "yearly",
                    "path": str(wr / "yearly.html"),
                    "format": "html",
                    "systemPrompt": written["yearly.system.md"],
                    "userPrompt": written["yearly.user.md"],
                },
                {
                    "id": "klineBrief",
                    "path": str(wr / "kline-brief.json"),
                    "format": "json",
                    "systemPrompt": written["kline.system.md"],
                    "userPrompt": written["kline.user.md"],
                    "note": "模型只能返回 age/brief/reason，不得返回或改写 open/high/low/close。",
                },
            ],
            "forbiddenInProduction": ["--skip-validation", "模型生成或覆盖 K 线 OHLC"],
        },
        "assemble": {
            "command": (
                "python3 tools/generate_report.py "
                f"--payload-json {wr / 'payload.json'} "
                f"--natal-html {wr / 'natal.html'} "
                f"--yearly-html {wr / 'yearly.html'} "
                f"--kline-brief-json {wr / 'kline-brief.json'} "
                f"-o {wr / 'report.html'}"
            ),
        },
    }
    manifest_path = out_dir / "prompt-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render natal/yearly/kline system+user prompts from prompts.md and payload JSON."
    )
    parser.add_argument("--payload-json", required=True, help="ziwei_offline.py --format json 输出文件")
    parser.add_argument("--out-dir", required=True, help="输出目录（写入 prompts/ 与 prompt-manifest.json）")
    parser.add_argument("--work-root", help="manifest 中产物路径前缀，默认等于 --out-dir")
    parser.add_argument("--prompts-md", default=str(PROMPTS_FILE), help="提示词源文件，默认 prompts.md")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(_read_text(Path(args.payload_json)))
        if not isinstance(payload, dict):
            raise ValueError("payload 必须为 JSON 对象")
        out_dir = Path(args.out_dir)
        work_root = Path(args.work_root) if args.work_root else out_dir
        render_all_prompts(
            payload,
            out_dir,
            prompts_md=Path(args.prompts_md),
            work_root=work_root,
        )
        print(json.dumps({"manifest": str(out_dir / "prompt-manifest.json"), "promptsDir": str(out_dir / "prompts")}, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

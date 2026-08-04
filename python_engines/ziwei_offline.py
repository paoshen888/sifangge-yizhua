#!/usr/bin/env python3
"""Offline Zi Wei Dou Shu chart generator for the ziwei-ai-html-report skill.

Core logic is Python standard library only (no app imports). Optional path:
pipe a chart JSON from ``tools/chart_iztro.cjs`` (iztro, same config as app)
into ``--from-chart-json`` — iztro is then a Node dependency of the skill, not
of this file.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
import math
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
PALACE_BRANCHES = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
PALACE_NAMES = ["命宫", "兄弟宫", "夫妻宫", "子女宫", "财帛宫", "疾厄宫", "迁移宫", "交友宫", "官禄宫", "田宅宫", "福德宫", "父母宫"]
YANG_STEMS = {"甲", "丙", "戊", "庚", "壬"}


# 1900-2100 lunar data. Bit layout follows the common Chinese calendar compact
# table: low 4 bits = leap month, 0x10000 = leap month has 30 days, month bits
# 0x8000..0x10 represent month 1..12 (1 means 30 days, 0 means 29 days).
LUNAR_INFO = [
    0x04BD8, 0x04AE0, 0x0A570, 0x054D5, 0x0D260, 0x0D950, 0x16554, 0x056A0, 0x09AD0, 0x055D2,
    0x04AE0, 0x0A5B6, 0x0A4D0, 0x0D250, 0x1D255, 0x0B540, 0x0D6A0, 0x0ADA2, 0x095B0, 0x14977,
    0x04970, 0x0A4B0, 0x0B4B5, 0x06A50, 0x06D40, 0x1AB54, 0x02B60, 0x09570, 0x052F2, 0x04970,
    0x06566, 0x0D4A0, 0x0EA50, 0x06E95, 0x05AD0, 0x02B60, 0x186E3, 0x092E0, 0x1C8D7, 0x0C950,
    0x0D4A0, 0x1D8A6, 0x0B550, 0x056A0, 0x1A5B4, 0x025D0, 0x092D0, 0x0D2B2, 0x0A950, 0x0B557,
    0x06CA0, 0x0B550, 0x15355, 0x04DA0, 0x0A5D0, 0x14573, 0x052D0, 0x0A9A8, 0x0E950, 0x06AA0,
    0x0AEA6, 0x0AB50, 0x04B60, 0x0AAE4, 0x0A570, 0x05260, 0x0F263, 0x0D950, 0x05B57, 0x056A0,
    0x096D0, 0x04DD5, 0x04AD0, 0x0A4D0, 0x0D4D4, 0x0D250, 0x0D558, 0x0B540, 0x0B6A0, 0x195A6,
    0x095B0, 0x049B0, 0x0A974, 0x0A4B0, 0x0B27A, 0x06A50, 0x06D40, 0x0AF46, 0x0AB60, 0x09570,
    0x04AF5, 0x04970, 0x064B0, 0x074A3, 0x0EA50, 0x06B58, 0x055C0, 0x0AB60, 0x096D5, 0x092E0,
    0x0C960, 0x0D954, 0x0D4A0, 0x0DA50, 0x07552, 0x056A0, 0x0ABB7, 0x025D0, 0x092D0, 0x0CAB5,
    0x0A950, 0x0B4A0, 0x0BAA4, 0x0AD50, 0x055D9, 0x04BA0, 0x0A5B0, 0x15176, 0x052B0, 0x0A930,
    0x07954, 0x06AA0, 0x0AD50, 0x05B52, 0x04B60, 0x0A6E6, 0x0A4E0, 0x0D260, 0x0EA65, 0x0D530,
    0x05AA0, 0x076A3, 0x096D0, 0x04BD7, 0x04AD0, 0x0A4D0, 0x1D0B6, 0x0D250, 0x0D520, 0x0DD45,
    0x0B5A0, 0x056D0, 0x055B2, 0x049B0, 0x0A577, 0x0A4B0, 0x0AA50, 0x1B255, 0x06D20, 0x0ADA0,
    0x14B63, 0x09370, 0x049F8, 0x04970, 0x064B0, 0x168A6, 0x0EA50, 0x06B20, 0x1A6C4, 0x0AAE0,
    0x0A2E0, 0x0D2E3, 0x0C960, 0x0D557, 0x0D4A0, 0x0DA50, 0x05D55, 0x056A0, 0x0A6D0, 0x055D4,
    0x052D0, 0x0A9B8, 0x0A950, 0x0B4A0, 0x0B6A6, 0x0AD50, 0x055A0, 0x0ABA4, 0x0A5B0, 0x052B0,
    0x0B273, 0x06930, 0x07337, 0x06AA0, 0x0AD50, 0x14B55, 0x04B60, 0x0A570, 0x054E4, 0x0D160,
    0x0E968, 0x0D520, 0x0DAA0, 0x16AA6, 0x056D0, 0x04AE0, 0x0A9D4, 0x0A2D0, 0x0D150, 0x0F252,
    0x0D520,
]


SIHUA_TABLE = {
    "甲": {"化禄": "廉贞", "化权": "破军", "化科": "武曲", "化忌": "太阳"},
    "乙": {"化禄": "天机", "化权": "天梁", "化科": "紫微", "化忌": "太阴"},
    "丙": {"化禄": "天同", "化权": "天机", "化科": "文昌", "化忌": "廉贞"},
    "丁": {"化禄": "太阴", "化权": "天同", "化科": "天机", "化忌": "巨门"},
    "戊": {"化禄": "贪狼", "化权": "太阴", "化科": "右弼", "化忌": "天机"},
    "己": {"化禄": "武曲", "化权": "贪狼", "化科": "天梁", "化忌": "文曲"},
    "庚": {"化禄": "太阳", "化权": "武曲", "化科": "太阴", "化忌": "天同"},
    "辛": {"化禄": "巨门", "化权": "太阳", "化科": "文曲", "化忌": "文昌"},
    "壬": {"化禄": "天梁", "化权": "紫微", "化科": "左辅", "化忌": "武曲"},
    "癸": {"化禄": "破军", "化权": "巨门", "化科": "太阴", "化忌": "贪狼"},
}

WUHU_START = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
KUIYUE_TABLE = {"甲": ("丑", "未"), "乙": ("子", "申"), "丙": ("亥", "酉"), "丁": ("亥", "酉"), "戊": ("丑", "未"), "己": ("子", "申"), "庚": ("丑", "未"), "辛": ("午", "寅"), "壬": ("卯", "巳"), "癸": ("卯", "巳")}
LUCUN_TABLE = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳", "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
TIANMA_GROUP_TABLE = {"申": "寅午戌", "寅": "申子辰", "巳": "亥卯未", "亥": "巳酉丑"}

MAJOR_STAR_DESCRIPTIONS = {
    "紫微": "帝座之星，主尊贵、统御、格局。",
    "天机": "谋略之星，主机变、思虑、技术。",
    "太阳": "光明之星，主名望、外显、助人。",
    "武曲": "财帛之星，主执行、理财、刚毅。",
    "天同": "福德之星，主温和、享受、人缘。",
    "廉贞": "囚杀之星，主原则、欲望、变化。",
    "天府": "库藏之星，主稳重、资源、包容。",
    "太阴": "阴柔之星，主财富、情感、细腻。",
    "贪狼": "桃花才艺之星，主欲望、交际、才华。",
    "巨门": "口舌暗曜，主表达、疑虑、是非。",
    "天相": "印绶之星，主辅佐、制度、体面。",
    "天梁": "荫寿之星，主护持、原则、长辈缘。",
    "七杀": "将星，主开创、决断、波折。",
    "破军": "耗星，主破旧立新、变革、起伏。",
}

STAR_BASE_SCORE = {
    "紫微": 18,
    "天机": 10,
    "太阳": 12,
    "武曲": 11,
    "天同": 9,
    "廉贞": 8,
    "天府": 16,
    "太阴": 11,
    "贪狼": 10,
    "巨门": 6,
    "天相": 12,
    "天梁": 11,
    "七杀": 7,
    "破军": 6,
    "左辅": 10,
    "右弼": 10,
    "文昌": 9,
    "文曲": 9,
    "天魁": 11,
    "天钺": 11,
    "擎羊": -12,
    "陀罗": -10,
    "火星": -8,
    "铃星": -8,
    "地空": -9,
    "地劫": -9,
    "禄存": 12,
    "天马": 8,
    "红鸾": 6,
    "天喜": 6,
    "天刑": -4,
    "天姚": 3,
    "天哭": -3,
    "天虚": -3,
    "龙池": 4,
    "凤阁": 4,
    "华盖": 2,
    "咸池": -2,
    "天德": 5,
    "月德": 5,
    "天官": 4,
    "天福": 4,
    "解神": 5,
    "天巫": 3,
    "天月": -2,
    "阴煞": -5,
    "台辅": 3,
    "封诰": 3,
    "三台": 4,
    "八座": 4,
    "恩光": 3,
    "天贵": 3,
}

BRIGHTNESS_COEF = {
    "庙": 1.5,
    "旺": 1.3,
    "得": 1.1,
    "利": 1.0,
    "平": 0.9,
    "不": 0.7,
    "陷": 0.5,
}

# 与 iztro/lib/data/stars.js STARS_INFO 对齐；数组下标从寅宫起（PALACE_BRANCHES 顺序）。
_BRIGHTNESS_CODE_ZH = {
    "miao": "庙",
    "wang": "旺",
    "de": "得",
    "li": "利",
    "ping": "平",
    "bu": "不",
    "xian": "陷",
}

_MAJOR_STAR_BRIGHTNESS_CODES: Dict[str, List[str]] = {
    "紫微": ["wang", "wang", "de", "wang", "miao", "miao", "wang", "wang", "de", "wang", "ping", "miao"],
    "天机": ["de", "wang", "li", "ping", "miao", "xian", "de", "wang", "li", "ping", "miao", "xian"],
    "太阳": ["wang", "miao", "wang", "wang", "wang", "de", "de", "xian", "bu", "xian", "xian", "bu"],
    "武曲": ["de", "li", "miao", "ping", "wang", "miao", "de", "li", "miao", "ping", "wang", "miao"],
    "天同": ["li", "ping", "ping", "miao", "xian", "bu", "wang", "ping", "ping", "miao", "wang", "bu"],
    "廉贞": ["miao", "ping", "li", "xian", "ping", "li", "miao", "ping", "li", "xian", "ping", "li"],
    "天府": ["miao", "de", "miao", "de", "wang", "miao", "de", "wang", "miao", "de", "miao", "miao"],
    "太阴": ["wang", "xian", "xian", "xian", "bu", "bu", "li", "bu", "wang", "miao", "miao", "miao"],
    "贪狼": ["ping", "li", "miao", "xian", "wang", "miao", "ping", "li", "miao", "xian", "wang", "miao"],
    "巨门": ["miao", "miao", "xian", "wang", "wang", "bu", "miao", "miao", "xian", "wang", "wang", "bu"],
    "天相": ["miao", "xian", "de", "de", "miao", "de", "miao", "xian", "de", "de", "miao", "miao"],
    "天梁": ["miao", "miao", "miao", "xian", "miao", "wang", "xian", "de", "miao", "xian", "miao", "wang"],
    "七杀": ["miao", "wang", "miao", "ping", "wang", "miao", "miao", "miao", "miao", "ping", "wang", "miao"],
    "破军": ["de", "xian", "wang", "ping", "miao", "wang", "de", "xian", "wang", "ping", "miao", "wang"],
}

_JU_DISPLAY = {2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}

MINOR_STAR_ORDER = [
    "左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "天马",
    "擎羊", "陀罗", "火星", "铃星", "地空", "地劫",
]

SEMANTIC_FILE = Path(__file__).with_name("knowledge_semantics.json")
LOCATION_FILE = Path(__file__).with_name("cn_locations.json")


def _load_semantics() -> Dict[str, Any]:
    try:
        return json.loads(SEMANTIC_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


SEMANTICS = _load_semantics()
if SEMANTICS.get("major_star_descriptions"):
    MAJOR_STAR_DESCRIPTIONS = SEMANTICS["major_star_descriptions"]


def _load_location_fallbacks() -> Dict[str, Dict[str, float]]:
    try:
        data = json.loads(LOCATION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    cleaned: Dict[str, Dict[str, float]] = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        try:
            lng = float(value["longitude"])
            lat = float(value["latitude"])
        except Exception:
            continue
        cleaned[key] = {"longitude": lng, "latitude": lat}
    return cleaned


LOCATION_FALLBACKS = _load_location_fallbacks()


@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    is_leap: bool = False


def _year_info(year: int) -> int:
    if year < 1900 or year > 2100:
        raise ValueError("仅支持 1900-2100 年之间的阳历日期")
    return LUNAR_INFO[year - 1900]


def leap_month(year: int) -> int:
    return _year_info(year) & 0xF


def leap_month_days(year: int) -> int:
    if leap_month(year) == 0:
        return 0
    return 30 if (_year_info(year) & 0x10000) else 29


def lunar_month_days(year: int, month: int) -> int:
    if not 1 <= month <= 12:
        raise ValueError("农历月份必须在 1-12 之间")
    return 30 if (_year_info(year) & (0x10000 >> month)) else 29


def lunar_year_days(year: int) -> int:
    return sum(lunar_month_days(year, month) for month in range(1, 13)) + leap_month_days(year)


def solar_to_lunar(year: int, month: int, day: int) -> LunarDate:
    target = _dt.date(year, month, day)
    base = _dt.date(1900, 1, 31)
    if target < base or target > _dt.date(2100, 12, 31):
        raise ValueError("仅支持 1900-01-31 至 2100-12-31 的阳历日期")

    offset = (target - base).days
    lunar_year = 1900
    while lunar_year <= 2100:
        days = lunar_year_days(lunar_year)
        if offset < days:
            break
        offset -= days
        lunar_year += 1

    leap = leap_month(lunar_year)
    lunar_month = 1
    is_leap = False
    while lunar_month <= 12:
        days = leap_month_days(lunar_year) if is_leap else lunar_month_days(lunar_year, lunar_month)
        if offset < days:
            return LunarDate(lunar_year, lunar_month, offset + 1, is_leap)

        offset -= days
        if leap == lunar_month and not is_leap:
            is_leap = True
        else:
            is_leap = False
            lunar_month += 1

    raise ValueError("农历转换失败")


def hour_branch_index(hour: int) -> int:
    if not 0 <= hour <= 23:
        raise ValueError("出生小时必须在 0-23 之间")
    if hour == 23:
        return 0
    return ((hour + 1) // 2) % 12


def hour_branch_index_from_time(local_dt: _dt.datetime) -> int:
    minutes = local_dt.hour * 60 + local_dt.minute
    if minutes >= 23 * 60 or minutes < 60:
        return 0
    return ((local_dt.hour + 1) // 2) % 12


def compute_longitude_correction_minutes(longitude: float) -> float:
    """Longitude correction relative to UTC+8 standard meridian 120E."""
    return (float(longitude) - 120.0) * 4.0


def compute_equation_of_time_minutes(date: _dt.date) -> float:
    """Approximate equation of time in minutes.

    Positive value means apparent solar time ahead of mean solar time.
    Formula uses NOAA approximation and is sufficient for hour-branch routing.
    """
    day_of_year = date.timetuple().tm_yday
    b = 2 * math.pi * (day_of_year - 81) / 364.0
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def compute_true_solar_datetime(local_datetime: _dt.datetime, longitude: float) -> Tuple[_dt.datetime, float, float]:
    lng_delta = compute_longitude_correction_minutes(longitude)
    eot_delta = compute_equation_of_time_minutes(local_datetime.date())
    total = lng_delta + eot_delta
    return local_datetime + _dt.timedelta(minutes=total), lng_delta, eot_delta


def _normalize_place(value: str) -> str:
    return value.strip().replace(" ", "")


def _resolve_fallback_location(birthplace: str) -> Optional[Dict[str, float]]:
    normalized = _normalize_place(birthplace)
    if not normalized:
        return None
    if normalized in LOCATION_FALLBACKS:
        return LOCATION_FALLBACKS[normalized]
    for key, value in LOCATION_FALLBACKS.items():
        nkey = _normalize_place(key)
        if normalized in nkey or nkey in normalized:
            return value
    return None


def _geocode_online(birthplace: str) -> Optional[Dict[str, float]]:
    endpoint = os.getenv("ZIWEI_GEOCODE_ENDPOINT", "https://nominatim.openstreetmap.org/search")
    params = {"format": "json", "limit": 1, "q": birthplace}
    url = f"{endpoint}?{urlencode(params)}"
    headers = {"User-Agent": os.getenv("ZIWEI_GEOCODE_USER_AGENT", "ziwei-offline/1.0")}
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=3.0) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None
    if not isinstance(payload, list) or not payload:
        return None
    first = payload[0]
    try:
        lat = float(first["lat"])
        lng = float(first["lon"])
    except Exception:
        return None
    return {"longitude": lng, "latitude": lat}


def resolve_coordinates(
    birthplace: Optional[str],
    longitude: Optional[float],
    latitude: Optional[float],
    geocode_mode: str = "hybrid",
) -> Tuple[Optional[float], Optional[float], str]:
    if longitude is not None and latitude is not None:
        return float(longitude), float(latitude), "manual"
    if not birthplace:
        return None, None, "none"
    mode = geocode_mode.lower()
    if mode not in {"online", "offline", "hybrid"}:
        raise ValueError("geocode-mode 必须为 online/offline/hybrid")

    if mode in {"online", "hybrid"}:
        online = _geocode_online(birthplace)
        if online:
            return online["longitude"], online["latitude"], "online"
    if mode in {"offline", "hybrid"}:
        offline = _resolve_fallback_location(birthplace)
        if offline:
            return offline["longitude"], offline["latitude"], "offline"
    return None, None, "none"


def year_ganzhi(year: int) -> Tuple[str, str]:
    idx = (year - 1984) % 60
    return TIANGAN[idx % 10], BRANCHES[idx % 12]


def add_branch(branch: str, steps: int) -> str:
    idx = PALACE_BRANCHES.index(branch)
    return PALACE_BRANCHES[(idx + steps) % 12]


def branch_index(branch: str) -> int:
    return PALACE_BRANCHES.index(branch)


def life_palace_branch(lunar_month: int, hour_idx: int) -> str:
    # 来源: docs/rules-baseline.md（排盘算法要点）
    # 等价公式: (14 + month - hour_idx) % 12
    return PALACE_BRANCHES[(lunar_month - 1 - hour_idx) % 12]


def body_palace_branch(lunar_month: int, hour_idx: int) -> str:
    # 来源: docs/rules-baseline.md（排盘算法要点）
    # 等价公式: (month + hour_idx) % 12
    return PALACE_BRANCHES[(lunar_month - 1 + hour_idx) % 12]


def effective_lunar_month_for_placement(lunar: LunarDate) -> int:
    if lunar.is_leap and lunar.day > 15:
        return min(12, lunar.month + 1)
    return lunar.month


def palace_stems(year_stem: str) -> Dict[str, str]:
    # 来源: docs/rules-baseline.md（排盘算法要点）
    start_idx = TIANGAN.index(WUHU_START[year_stem])
    return {branch: TIANGAN[(start_idx + i) % 10] for i, branch in enumerate(PALACE_BRANCHES)}


def major_star_brightness(star_name: str, branch: str) -> Optional[str]:
    codes = _MAJOR_STAR_BRIGHTNESS_CODES.get(star_name)
    if not codes:
        return None
    try:
        idx = PALACE_BRANCHES.index(branch)
    except ValueError:
        return None
    code = codes[idx]
    if not code:
        return None
    return _BRIGHTNESS_CODE_ZH.get(code, code)


def _sort_palace_stars(palaces: List[Dict[str, Any]]) -> None:
    minor_rank = {name: idx for idx, name in enumerate(MINOR_STAR_ORDER)}
    for palace in palaces:
        palace["minorStars"].sort(key=lambda star: minor_rank.get(star.get("name", ""), 999))


def five_elements_class(stem: str, branch: str) -> Tuple[str, int]:
    stem_num = {"甲": 1, "乙": 1, "丙": 2, "丁": 2, "戊": 3, "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5}
    branch_num = {"子": 1, "丑": 1, "午": 1, "未": 1, "寅": 2, "卯": 2, "申": 2, "酉": 2, "辰": 3, "巳": 3, "戌": 3, "亥": 3}
    wuxing = {1: "木", 2: "金", 3: "水", 4: "火", 5: "土"}
    ju_map = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}
    total = stem_num[stem] + branch_num[branch]
    if total > 5:
        total -= 5
    element = wuxing[total]
    num = ju_map[element]
    return f"{element}{_JU_DISPLAY[num]}局", num


def ziwei_position(lunar_day: int, ju_num: int) -> str:
    # 来源: docs/rules-baseline.md（排盘算法要点）
    if ju_num not in {2, 3, 4, 5, 6}:
        raise ValueError("五行局数必须为 2-6")
    if not 1 <= lunar_day <= 30:
        raise ValueError("农历日期必须在 1-30")
    quotient, remainder = divmod(lunar_day, ju_num)
    if remainder == 0:
        position = quotient
    else:
        add_num = ju_num - remainder
        new_quotient = (lunar_day + add_num) // ju_num
        position = new_quotient - add_num if add_num % 2 == 1 else new_quotient + add_num
    while position > 12:
        position -= 12
    while position < 1:
        position += 12
    return PALACE_BRANCHES[position - 1]


def arrange_major_stars(ziwei_branch: str) -> Dict[str, str]:
    ziwei_idx = branch_index(ziwei_branch)
    # 与 iztro/App 对齐：紫微在寅时天府同在寅，此后沿寅申轴镜像。
    tianfu_idx = (-ziwei_idx) % 12

    stars = {
        "紫微": ziwei_idx,
        "天机": (ziwei_idx - 1) % 12,
    }
    stars["太阳"] = (stars["天机"] - 2) % 12
    stars["武曲"] = (stars["太阳"] - 1) % 12
    stars["天同"] = (stars["武曲"] - 1) % 12
    stars["廉贞"] = (stars["天同"] - 3) % 12

    stars["天府"] = tianfu_idx
    stars["太阴"] = (tianfu_idx + 1) % 12
    stars["贪狼"] = (stars["太阴"] + 1) % 12
    stars["巨门"] = (stars["贪狼"] + 1) % 12
    stars["天相"] = (stars["巨门"] + 1) % 12
    stars["天梁"] = (stars["天相"] + 1) % 12
    stars["七杀"] = (stars["天梁"] + 1) % 12
    stars["破军"] = (stars["七杀"] + 4) % 12

    return {name: PALACE_BRANCHES[idx] for name, idx in stars.items()}


def auxiliary_stars(lunar_month: int, hour_idx: int, year_stem: str, year_branch: str) -> Dict[str, str]:
    # 来源: docs/rules-baseline.md（排盘算法要点）
    result: Dict[str, str] = {}
    result["左辅"] = add_branch("辰", lunar_month - 1)
    result["右弼"] = add_branch("戌", -(lunar_month - 1))
    result["文昌"] = add_branch("戌", -hour_idx)
    result["文曲"] = add_branch("辰", hour_idx)
    result["天魁"], result["天钺"] = KUIYUE_TABLE[year_stem]

    lucun = LUCUN_TABLE[year_stem]
    result["禄存"] = lucun
    result["擎羊"] = add_branch(lucun, 1)
    result["陀罗"] = add_branch(lucun, -1)

    fire_start = _group_lookup(year_branch, {"丑": "寅午戌", "寅": "申子辰", "卯": "巳酉丑", "酉": "亥卯未"})
    bell_start = _group_lookup(year_branch, {"卯": "寅午戌", "戌": "申子辰巳酉丑亥卯未"})
    result["火星"] = add_branch(fire_start, hour_idx)
    result["铃星"] = add_branch(bell_start, hour_idx)
    result["地劫"] = add_branch("亥", hour_idx)
    result["地空"] = add_branch("亥", -hour_idx)
    # 天马按年支三合局定位
    result["天马"] = _group_lookup(year_branch, TIANMA_GROUP_TABLE)
    return result


def _group_lookup(branch: str, mapping: Dict[str, str]) -> str:
    for value, group in mapping.items():
        if branch in group:
            return value
    raise ValueError(f"无法识别地支分组: {branch}")


def mutagen_by_star(stem: str) -> Dict[str, str]:
    return {star: hua for hua, star in SIHUA_TABLE[stem].items()}


def arrange_palaces(ming_branch: str, body_branch: str, stems: Dict[str, str], ju_num: int, year_stem: str, gender: str) -> List[Dict[str, Any]]:
    ming_idx = branch_index(ming_branch)
    decadal_map = decadal_ranges(ming_branch, ju_num, year_stem, gender)
    palaces: List[Dict[str, Any]] = []
    for i, name in enumerate(PALACE_NAMES):
        branch = PALACE_BRANCHES[(ming_idx - i) % 12]
        palaces.append({
            "name": name,
            "branch": branch,
            "stem": stems[branch],
            "majorStars": [],
            "minorStars": [],
            "adjectiveStars": [],
            "isLifePalace": branch == ming_branch,
            "isBodyPalace": branch == body_branch,
            "decadalRange": decadal_map.get(branch),
        })
    return palaces


def decadal_ranges(ming_branch: str, ju_num: int, year_stem: str, gender: str) -> Dict[str, str]:
    # 来源: docs/rules-baseline.md（排盘算法要点）
    if ju_num not in {2, 3, 4, 5, 6}:
        raise ValueError("五行局必须在水二局到火六局之间")
    is_yang = year_stem in YANG_STEMS
    forward = (is_yang and gender == "male") or ((not is_yang) and gender == "female")
    direction = 1 if forward else -1
    start_idx = branch_index(ming_branch)
    result = {}
    for i in range(12):
        start_age = ju_num + i * 10
        branch = PALACE_BRANCHES[(start_idx + i * direction) % 12]
        result[branch] = f"{start_age}-{start_age + 9}"
    return result


def _add_star_to_palaces(palaces: List[Dict[str, Any]], branch: str, star: Dict[str, Any], kind: str) -> None:
    for palace in palaces:
        if palace["branch"] == branch:
            palace[kind].append(star)
            return


def nominal_age(lunar_birth_year: int, target_year: int) -> int:
    """虚岁：流年分析年 − 农历生年 + 1（大限、流年叠宫口径）。"""
    return target_year - lunar_birth_year + 1


def actual_age_on(birth_year: int, birth_month: int, birth_day: int, on: _dt.date) -> int:
    """周岁：按阳历生日计算截至某日已满的周岁。"""
    age = on.year - birth_year
    if (on.month, on.day) < (birth_month, birth_day):
        age -= 1
    return max(0, age)


def _parse_birth_solar(chart: Dict[str, Any]) -> Tuple[int, int, int]:
    birth = chart.get("birth") or {}
    solar = birth.get("effectiveSolar") or birth.get("solar") or ""
    y, m, d = map(int, str(solar).split("-"))
    return y, m, d


def compute_age_info(
    chart: Dict[str, Any],
    target_year: int,
    reference: Optional[_dt.date] = None,
) -> Dict[str, Any]:
    """返回虚岁与周岁（年末 / 参考日）对照，供报告与流年上下文展示。"""
    ref = reference or _dt.date.today()
    by, bm, bd = _parse_birth_solar(chart)
    lunar_year = int(chart["lunar"]["year"])
    nominal = nominal_age(lunar_year, target_year)
    at_year_end = actual_age_on(by, bm, bd, _dt.date(target_year, 12, 31))
    at_ref = actual_age_on(by, bm, bd, ref)
    return {
        "nominalAge": nominal,
        "actualAgeAtYearEnd": at_year_end,
        "actualAgeAtReference": at_ref,
        "referenceDate": ref.isoformat(),
        "targetYear": target_year,
        "lunarBirthYear": lunar_year,
    }


def _current_decadal(chart: Dict[str, Any], target_year: int) -> Dict[str, Any]:
    ages = compute_age_info(chart, target_year)
    age = ages["nominalAge"]
    for palace in chart["palaces"]:
        start, end = [int(x) for x in palace["decadalRange"].split("-")]
        if start <= age <= end:
            return {
                "age": age,
                **ages,
                "palaceName": palace["name"],
                "branch": palace["branch"],
                "stem": palace["stem"],
                "mutagens": sihua_list(palace["stem"]),
            }
    return {
        "age": age,
        **ages,
        "palaceName": "命宫",
        "branch": chart["lifePalace"]["branch"],
        "stem": chart["lifePalace"]["stem"],
        "mutagens": sihua_list(chart["lifePalace"]["stem"]),
    }


def sihua_list(stem: str) -> List[str]:
    return [f"{star}{hua}" for hua, star in SIHUA_TABLE[stem].items()]


def generate_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    gender: str,
    target_year: Optional[int] = None,
    *,
    minute: int = 0,
    birthplace: Optional[str] = None,
    longitude: Optional[float] = None,
    latitude: Optional[float] = None,
    use_true_solar_time: bool = True,
    geocode_mode: str = "hybrid",
) -> Dict[str, Any]:
    if gender not in {"male", "female"}:
        raise ValueError("gender 必须为 male 或 female")

    analysis_year = target_year or _dt.date.today().year
    if analysis_year < 1900 or analysis_year > 2100:
        raise ValueError("target-year 必须在 1900-2100 之间")
    if not 0 <= minute <= 59:
        raise ValueError("出生分钟必须在 0-59 之间")

    solar = _dt.date(year, month, day)
    birth_local_dt = _dt.datetime(year, month, day, hour, minute)
    resolved_lng, resolved_lat, geo_source = resolve_coordinates(birthplace, longitude, latitude, geocode_mode=geocode_mode)
    true_solar_applied = bool(use_true_solar_time and resolved_lng is not None)
    lng_delta = 0.0
    eot_delta = 0.0
    effective_dt = birth_local_dt
    if true_solar_applied:
        effective_dt, lng_delta, eot_delta = compute_true_solar_datetime(birth_local_dt, resolved_lng)
    hour_idx = hour_branch_index_from_time(effective_dt)
    late_zi = effective_dt.hour == 23
    effective_solar = solar + _dt.timedelta(days=1) if late_zi else solar
    if true_solar_applied:
        effective_solar = effective_dt.date() + (_dt.timedelta(days=1) if late_zi else _dt.timedelta(days=0))
    lunar = solar_to_lunar(effective_solar.year, effective_solar.month, effective_solar.day)
    year_stem, year_branch = year_ganzhi(lunar.year)
    stems = palace_stems(year_stem)

    placement_month = effective_lunar_month_for_placement(lunar)
    ming = life_palace_branch(placement_month, hour_idx)
    body = body_palace_branch(placement_month, hour_idx)
    ming_stem = stems[ming]
    five_label, ju_num = five_elements_class(ming_stem, ming)
    ziwei = ziwei_position(lunar.day, ju_num)
    palaces = arrange_palaces(ming, body, stems, ju_num, year_stem, gender)

    star_mutagens = mutagen_by_star(year_stem)
    for star, branch in arrange_major_stars(ziwei).items():
        item = {"name": star, "description": MAJOR_STAR_DESCRIPTIONS.get(star, "")}
        brightness = major_star_brightness(star, branch)
        if brightness:
            item["brightness"] = brightness
        if star in star_mutagens:
            item["mutagen"] = star_mutagens[star]
        _add_star_to_palaces(palaces, branch, item, "majorStars")

    for star, branch in auxiliary_stars(placement_month, hour_idx, year_stem, year_branch).items():
        item = {"name": star}
        if star in star_mutagens:
            item["mutagen"] = star_mutagens[star]
        _add_star_to_palaces(palaces, branch, item, "minorStars")

    _sort_palace_stars(palaces)
    life_palace = next(p for p in palaces if p["name"] == "命宫")
    body_palace = next(p for p in palaces if p["isBodyPalace"])
    chart = {
        "engine": "ziwei-ai-html-report offline-python",
        "calendarRange": "1900-2100",
        "birth": {
            "solar": solar.isoformat(),
            "effectiveSolar": effective_solar.isoformat(),
            "hour": hour,
            "minute": minute,
            "localTime": birth_local_dt.strftime("%H:%M"),
            "timeBranch": BRANCHES[hour_idx],
            "lateZi": late_zi,
            "gender": gender,
            "birthplace": birthplace or "",
            "coordinates": {
                "longitude": resolved_lng,
                "latitude": resolved_lat,
                "source": geo_source,
            },
            "trueSolar": {
                "enabled": bool(use_true_solar_time),
                "applied": true_solar_applied,
                "time": effective_dt.strftime("%Y-%m-%d %H:%M"),
                "longitudeCorrectionMinutes": round(lng_delta, 3),
                "equationOfTimeMinutes": round(eot_delta, 3),
                "totalCorrectionMinutes": round(lng_delta + eot_delta, 3),
                "fallbackUsed": geo_source == "offline",
                "note": "" if true_solar_applied else "缺少可用经纬度，已回退标准时计算",
            },
        },
        "lunar": {"year": lunar.year, "month": lunar.month, "day": lunar.day, "isLeapMonth": lunar.is_leap},
        "yearGanZhi": {"stem": year_stem, "branch": year_branch, "text": year_stem + year_branch},
        "fiveElementsClass": five_label,
        "fiveElementsNumber": ju_num,
        "lifePalace": {"name": life_palace["name"], "branch": life_palace["branch"], "stem": life_palace["stem"]},
        "bodyPalace": {"name": body_palace["name"], "branch": body_palace["branch"], "stem": body_palace["stem"]},
        "palaces": palaces,
        "natalMutagens": natal_mutagens(palaces),
        "patterns": detect_patterns({"palaces": palaces, "lifePalace": life_palace}),
    }
    chart["yearly"] = build_yearly_data(chart, analysis_year)
    validate_chart_integrity(chart)
    return chart


def natal_mutagens(palaces: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    result = []
    for palace in palaces:
        for star in palace["majorStars"] + palace["minorStars"]:
            if star.get("mutagen"):
                result.append({"star": star["name"], "sihua": star["mutagen"], "palace": palace["name"]})
    return result


def detect_patterns(chart_or_life: Dict[str, Any]) -> List[str]:
    life_palace = chart_or_life.get("lifePalace", chart_or_life)
    palaces = chart_or_life.get("palaces", [life_palace])
    majors = {s["name"] for s in life_palace["majorStars"]}
    minors = {s["name"] for s in life_palace.get("minorStars", [])}
    patterns = []
    life_branch = life_palace.get("branch", "")
    rules = SEMANTICS.get("pattern_rules") or []
    rule_sources = SEMANTICS.get("pattern_rule_sources") or {}
    all_major_names = {star["name"] for p in palaces for star in p.get("majorStars", [])}
    all_minor_names = {star["name"] for p in palaces for star in p.get("minorStars", [])}
    for rule in rules:
        scope = rule.get("scope", "all_major_presence")
        must_have = set(rule.get("must_have_stars", []))
        any_1 = set(rule.get("any_stars", []))
        any_2 = set(rule.get("any_stars_2", []))
        any_minor = set(rule.get("any_minor_stars", []))
        branch_limit = set(rule.get("requires_life_branch_in", []))
        if scope == "life_palace_same_palace":
            life_majors = {s["name"] for s in life_palace.get("majorStars", [])}
            if must_have and not must_have.issubset(life_majors):
                continue
            if any_1 and not (any_1 & life_majors):
                continue
            if any_2 and not (any_2 & life_majors):
                continue
        elif scope == "same_palace_major_minor":
            matched = False
            for palace in palaces:
                palace_major = {s["name"] for s in palace.get("majorStars", [])}
                palace_minor = {s["name"] for s in palace.get("minorStars", [])}
                if must_have and not must_have.issubset(palace_major):
                    continue
                if any_1 and not (any_1 & palace_major):
                    continue
                if any_2 and not (any_2 & palace_major):
                    continue
                if any_minor and not (any_minor & palace_minor):
                    continue
                matched = True
                break
            if not matched:
                continue
        else:
            if must_have and not must_have.issubset(all_major_names):
                continue
            if any_1 and not (any_1 & all_major_names):
                continue
            if any_2 and not (any_2 & all_major_names):
                continue
            if any_minor and not (any_minor & all_minor_names):
                continue
        if branch_limit and life_branch not in branch_limit:
            continue
        msg = rule.get("message", "")
        src = rule_sources.get(rule.get("id", ""))
        patterns.append(f"{msg}（来源：{src}）" if msg and src else msg)

    if not patterns:
        if {"紫微", "天府"} <= majors and life_branch in {"寅", "申"}:
            patterns.append("紫府同宫：紫微与天府同在命宫，若再得吉曜会照，主格局稳厚。")
        if {"紫微", "七杀"} <= majors:
            patterns.append("紫杀同宫：权威与冲劲并见，有开创气，但宜戒急躁。")
        if ({"天机", "太阴"} & majors) and ({"天同", "天梁"} & majors):
            patterns.append("机月同梁倾向：适合制度型、文教策划或服务协同场景。")
        if {"贪狼"} <= majors and ({"火星", "铃星"} & minors):
            patterns.append("火贪/铃贪倾向：易现爆发式机会，宜控风险与节奏。")
    if not majors:
        patterns.append("命宫无主星：需重视对宫与三方四正，人生变化性较强。")
    for star in life_palace["majorStars"]:
        if star.get("mutagen") == "化忌":
            patterns.append(f"{star['name']}化忌入命：该星所主事项易成执着与课题。")
    return patterns


def build_yearly_data(chart: Dict[str, Any], target_year: int) -> Dict[str, Any]:
    stem, branch = year_ganzhi(target_year)
    palace = next((p for p in chart["palaces"] if p["branch"] == branch), None)
    return {
        "year": target_year,
        "stem": stem,
        "branch": branch,
        "mutagens": sihua_list(stem),
        "palaceName": palace["name"] if palace else "",
        "palaceBranch": branch,
        "currentDecadal": _current_decadal(chart, target_year),
    }


def _normalize_score(score: float) -> int:
    normalized = ((score - 20.0) / 70.0) * 100.0
    return max(0, min(100, round(normalized)))


def _seeded_unit(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    integer = int.from_bytes(digest[:8], "big")
    return integer / float(2**64 - 1)


def _seeded_between(seed: str, low: float, high: float) -> float:
    return low + (high - low) * _seeded_unit(seed)


def _star_score(star: Dict[str, Any], *, major: bool) -> float:
    name = str(star.get("name", ""))
    score = float(STAR_BASE_SCORE.get(name, 0))
    if major:
        brightness = str(star.get("brightness") or "平")
        score *= BRIGHTNESS_COEF.get(brightness, 1.0) * 1.2
    else:
        score *= 0.8
    mutagen = str(star.get("mutagen") or "")
    if "禄" in mutagen:
        score += 18
    elif "权" in mutagen:
        score += 15
    elif "科" in mutagen:
        score += 12
    elif "忌" in mutagen:
        score -= 22
    return score


def _palace_base_score(palace: Dict[str, Any]) -> float:
    score = 45.0
    for star in palace.get("majorStars", []):
        score += _star_score(star, major=True)
    for star in palace.get("minorStars", []):
        score += _star_score(star, major=False)
    return score


def _find_decadal_palace(chart: Dict[str, Any], age: int) -> Dict[str, Any]:
    if age < int(chart["fiveElementsNumber"]):
        life = next(p for p in chart["palaces"] if p["name"] == "命宫")
        return {**life, "decadalRange": f"1-{int(chart['fiveElementsNumber']) - 1}", "stem": "", "branch": "童限"}
    for palace in chart["palaces"]:
        start, end = [int(x) for x in palace["decadalRange"].split("-")]
        if start <= age <= end:
            return palace
    return next(p for p in chart["palaces"] if p["name"] == "命宫")


def _yearly_modifier(chart: Dict[str, Any], year: int) -> Tuple[float, List[str]]:
    data = build_yearly_data(chart, year)
    modifier = 0.0
    for item in data["mutagens"]:
        if "化禄" in item:
            modifier += 20
        elif "化权" in item:
            modifier += 16
        elif "化科" in item:
            modifier += 12
        elif "化忌" in item:
            modifier -= 25
    yearly_palace = next((p for p in chart["palaces"] if p["branch"] == data["palaceBranch"]), None)
    if yearly_palace:
        for star in yearly_palace.get("majorStars", []):
            modifier += STAR_BASE_SCORE.get(star.get("name", ""), 0) * 0.5
        for star in yearly_palace.get("minorStars", []):
            modifier += STAR_BASE_SCORE.get(star.get("name", ""), 0) * 0.3
    seed_base = f"{chart.get('yearGanZhi', {}).get('text', '')}:{chart.get('lifePalace', {}).get('branch', '')}:{year}"
    modifier += _seeded_between(seed_base + ":yearly", -7.5, 7.5)
    return modifier, data["mutagens"]


# K 线使用全生命 raw score 映射，允许少数高峰接近 100，但避免长段贴顶。
KLINE_TARGET_CAP = 98.0
KLINE_CLOSE_CAP = 98.0
KLINE_HIGH_CAP = 100.0


def _kline_visual_targets(raw_scores: List[float]) -> List[float]:
    """Map raw fortune scores to display scores without flattening high years."""
    if not raw_scores:
        return []
    if len(raw_scores) == 1:
        return [50.0]

    lo = min(raw_scores)
    hi = max(raw_scores)
    span = hi - lo
    ordered = sorted(range(len(raw_scores)), key=lambda i: (raw_scores[i], i))
    ranks = [0.0] * len(raw_scores)
    for rank, index in enumerate(ordered):
        ranks[index] = rank / (len(raw_scores) - 1)

    targets: List[float] = []
    for index, raw in enumerate(raw_scores):
        absolute = 100.0 / (1.0 + math.exp(-(raw - 55.0) / 22.0))
        relative = ranks[index] * 100.0
        if span > 1e-6:
            raw_position = ((raw - lo) / span) * 100.0
            relative = relative * 0.7 + raw_position * 0.3
        target = absolute * 0.7 + relative * 0.3
        targets.append(max(0.0, min(KLINE_TARGET_CAP, target)))
    return targets


def generate_kline_data(chart: Dict[str, Any], birth_year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Generate deterministic K-line data aligned with the app scoring model.

    The app's original model includes random intrayear noise. This offline
    variant uses a seeded pseudo-random term derived from chart facts, age and
    year, so the same chart always produces the same lifetime curve.
    """
    if birth_year is None:
        birth_year = int(chart["lunar"]["year"])
    drafts: List[Dict[str, Any]] = []
    decadal_scores: Dict[str, float] = {}
    seed_prefix = f"{chart.get('birth', {}).get('effectiveSolar', '')}:{chart.get('birth', {}).get('timeBranch', '')}:{chart.get('lifePalace', {}).get('branch', '')}"

    for age in range(1, 101):
        year = birth_year + age - 1
        stem, branch = year_ganzhi(year)
        palace = _find_decadal_palace(chart, age)
        da_yun_range = palace["decadalRange"]
        if da_yun_range not in decadal_scores:
            decadal_scores[da_yun_range] = _palace_base_score(palace)
        decadal_base = decadal_scores[da_yun_range]
        yearly_delta, mutagens = _yearly_modifier(chart, year)
        raw_target = decadal_base + yearly_delta
        drafts.append({
            "age": age,
            "year": year,
            "stem": stem,
            "branch": branch,
            "palace": palace,
            "rawTarget": raw_target,
            "yearlyMutagens": mutagens,
        })

    targets = _kline_visual_targets([row["rawTarget"] for row in drafts])
    rows: List[Dict[str, Any]] = []
    prev_close = 50.0

    for draft, target in zip(drafts, targets):
        age = int(draft["age"])
        year = int(draft["year"])
        stem = str(draft["stem"])
        branch = str(draft["branch"])
        palace = draft["palace"]
        da_yun_range = str(palace["decadalRange"])
        open_v = prev_close
        seed = f"{seed_prefix}:{age}:{year}"
        move_ratio = _seeded_between(seed + ":move", 0.3, 0.7)
        close_base = open_v + (target - open_v) * move_ratio
        noise = _seeded_between(seed + ":close", -5.0, 5.0)
        close_v = max(0.0, min(KLINE_CLOSE_CAP, close_base + noise))
        mid = (open_v + close_v) / 2.0
        body_top = max(open_v, close_v)
        body_bottom = min(open_v, close_v)
        volatility = abs(target - open_v) * 0.3 + _seeded_between(seed + ":volatility", 0.0, 8.0)
        upper_room = max(0.0, KLINE_HIGH_CAP - body_top)
        lower_room = max(0.0, body_bottom)
        high_boost = volatility * _seeded_between(seed + ":high", 0.25, 0.55)
        low_drop = volatility * _seeded_between(seed + ":low", 0.25, 0.55)
        if upper_room <= 0.01:
            high_ext = 0.0
        else:
            if target >= 97.0:
                high_ext = min(max(high_boost, upper_room * 0.55), upper_room * 0.8)
            else:
                high_room_ratio = 0.75 if target >= 96.0 else 0.5
                high_ext = min(high_boost, upper_room * high_room_ratio)
        high_v = max(body_top, min(KLINE_HIGH_CAP, body_top + high_ext))
        if lower_room <= 0.01:
            low_v = body_bottom
        else:
            soft_floor = 1.0 if body_bottom > 12.0 else 0.0
            low_v = max(soft_floor, body_bottom - min(low_drop, lower_room * 0.55))
        low_v = min(low_v, body_bottom)
        score = max(0, min(int(KLINE_HIGH_CAP), round((open_v + close_v + high_v + low_v) / 4.0)))
        dim_cap = int(KLINE_HIGH_CAP)

        def _dim(raw: float) -> int:
            return max(0, min(dim_cap, _normalize_score(raw)))

        rows.append({
            "age": age,
            "year": year,
            "ganZhi": stem + branch,
            "daYun": palace["stem"] + palace["branch"],
            "daYunRange": da_yun_range,
            "open": round(open_v, 2),
            "close": round(close_v, 2),
            "high": round(high_v, 2),
            "low": round(low_v, 2),
            "score": score,
            "dimensions": {
                "career": _dim(mid + _seeded_between(seed + ":career", -7.5, 7.5)),
                "wealth": _dim(mid * 0.95 + _seeded_between(seed + ":wealth", -7.5, 7.5)),
                "relationship": _dim(mid * 0.9 + _seeded_between(seed + ":relationship", -7.5, 7.5)),
                "health": _dim(mid * 0.92 + _seeded_between(seed + ":health", -7.5, 7.5)),
            },
            "yearlyMutagens": draft["yearlyMutagens"],
        })
        prev_close = round(close_v, 2)
    return rows


def _star_line(stars: Iterable[Dict[str, Any]]) -> str:
    chunks = []
    for star in stars:
        text = star["name"]
        if star.get("brightness"):
            text += f"({star['brightness']})"
        if star.get("mutagen"):
            text += f"[{star['mutagen']}]"
        chunks.append(text)
    return "、".join(chunks)


def _append_major_star_structured_block(lines: List[str], star: Dict[str, Any]) -> None:
    """按固定模板输出单颗主星语义（与 knowledge_semantics.json 对齐）。"""
    name = star["name"]
    desc = star.get("description", "")
    profiles = SEMANTICS.get("major_star_profiles") or {}
    raw_profile = profiles.get(name)
    profile: Dict[str, str] = raw_profile if isinstance(raw_profile, dict) else {}
    legacy_trait = (SEMANTICS.get("major_star_traits") or {}).get(name)
    source = (SEMANTICS.get("major_star_sources") or {}).get(name, "")
    lines.append(f"#### {name}")
    if desc:
        lines.append(f"- 简述：{desc}")
    if profile:
        if profile.get("优点"):
            lines.append(f"- 优点：{profile['优点']}")
        if profile.get("风险"):
            lines.append(f"- 风险：{profile['风险']}")
        if profile.get("适配场景"):
            lines.append(f"- 适配场景：{profile['适配场景']}")
    elif legacy_trait:
        lines.append(f"- 补充：{legacy_trait}")
    if source:
        lines.append(f"- 来源：{source}")
    lines.append("")


def build_prompt_context(chart: Dict[str, Any]) -> str:
    lines: List[str] = ["【命盘完整信息】", ""]
    birth = chart.get("birth", {})
    true_solar = birth.get("trueSolar", {})
    lines += [
        "## 时间修正信息",
        f"- 出生地：{birth.get('birthplace') or '未提供'}",
        f"- 标准时间：{birth.get('solar', '')} {birth.get('localTime', '')}",
        f"- 真太阳时：{true_solar.get('time', birth.get('localTime', ''))}",
        f"- 修正分钟：{true_solar.get('totalCorrectionMinutes', 0)}（经度{true_solar.get('longitudeCorrectionMinutes', 0)} + 时间方程{true_solar.get('equationOfTimeMinutes', 0)}）",
        f"- 时辰归属：{birth.get('timeBranch', '')}时",
        "",
    ]
    life = next(p for p in chart["palaces"] if p["name"] == "命宫")
    body = next(p for p in chart["palaces"] if p["isBodyPalace"])
    palace_sources = SEMANTICS.get("palace_focus_sources") or {}

    if life["majorStars"]:
        lines += ["## 命宫主星", ""]
        for star in life["majorStars"]:
            _append_major_star_structured_block(lines, star)

    lines += ["## 身宫位置", f"- 身宫在{body['name']}（{body['branch']}宫）", ""]
    for star in body["majorStars"]:
        _append_major_star_structured_block(lines, star)
    if not body["majorStars"]:
        lines.append("（身宫无主星，借对宫参考）")
        lines.append("")

    lines += ["## 十二宫星曜分布", ""]
    lines.append("（主星结构化释义见上文「命宫主星」「身宫位置」；本节为十二宫落宫与星曜组合事实。）")
    lines.append("")
    for palace in chart["palaces"]:
        label = f"{palace['name']}【身宫】" if palace["isBodyPalace"] else palace["name"]
        lines.append(f"### {label} ({palace['branch']}宫，大限{palace['decadalRange']}岁)")
        lines.append(f"- 宫干：{palace['stem']}")
        palace_focus = (SEMANTICS.get("palace_focus") or {}).get(palace["name"])
        palace_source = palace_sources.get(palace["name"])
        if palace_focus:
            if palace_source:
                lines.append(f"- 宫位要点：{palace_focus}（来源：{palace_source}）")
            else:
                lines.append(f"- 宫位要点：{palace_focus}")
        lines.append(f"- 主星：{_star_line(palace['majorStars']) or '无主星（借对宫星曜）'}")
        minor = _star_line(palace["minorStars"])
        if minor:
            lines.append(f"- 辅星：{minor}")
        lines.append("")

    if chart["natalMutagens"]:
        lines += ["## 本命四化分布"]
        for item in chart["natalMutagens"]:
            lines.append(f"- {item['star']}{item['sihua']}入{item['palace']}")
        lines.append("")

    lines += ["## 十二大限", "（每个大限10年，按五行局起运年龄与阴阳男女顺逆行排布）", ""]
    decadals = []
    for palace in chart["palaces"]:
        start = int(palace["decadalRange"].split("-")[0])
        decadals.append((start, palace))
    for _, palace in sorted(decadals):
        lines.append(f"### {palace['decadalRange']}岁：{palace['name']}")
        lines.append(f"- 大限天干：{palace['stem']}")
        lines.append(f"- 大限四化：{'、'.join(sihua_list(palace['stem']))}")
        lines.append("")

    lines += ["## 近年流年信息", ""]
    target = chart["yearly"]["year"]
    for year in range(target - 5, target + 6):
        data = build_yearly_data(chart, year)
        lines.append(f"- {year}年（{data['stem']}{data['branch']}）：流年命宫在{data['palaceName']}，四化：{'、'.join(data['mutagens'])}")
    lines.append("")

    if chart["patterns"]:
        lines += ["## 格局提示"]
        for pattern in chart["patterns"]:
            lines.append(f"- {pattern}")
        lines.append("")
    return "\n".join(lines)


def build_yearly_context(chart: Dict[str, Any], target_year: int) -> str:
    data = build_yearly_data(chart, target_year)
    current = data["currentDecadal"]
    lines = ["【流年盘信息】", "", "## 流年基础"]
    birth = chart.get("birth", {})
    true_solar = birth.get("trueSolar", {})
    lines += [
        f"- 时间口径：{'真太阳时' if true_solar.get('applied') else '标准时'}（{true_solar.get('time', birth.get('localTime', ''))}）"
    ]
    lines.append(f"- 流年：{target_year}年（{data['stem']}{data['branch']}年）")
    lines.append(f"- 流年四化：{'、'.join(data['mutagens'])}")
    lines.append(f"- 流年命宫位置：{data['palaceName']}（{data['palaceBranch']}宫）")
    lines += ["", "## 当前大限"]
    lines.append(f"- 当前虚岁：{current['age']}岁（大限、流年叠宫口径）")
    lines.append(
        f"- 当前周岁：截至{target_year}-12-31 为 {current['actualAgeAtYearEnd']} 岁"
    )
    ref = current.get("referenceDate", "")
    ref_age = current.get("actualAgeAtReference")
    if ref and ref_age is not None and ref_age != current["actualAgeAtYearEnd"]:
        lines.append(f"- 周岁（截至{ref}）：{ref_age} 岁")
    lines.append(f"- 大限天干：{current['stem']}")
    lines.append(f"- 大限四化：{'、'.join(current['mutagens'])}")
    lines.append(f"- 大限命宫位置：{current['palaceName']}（{current['branch']}宫）")
    lines += ["", "## 流年重点宫位星曜"]

    for name in ["命宫", "财帛宫", "官禄宫", "夫妻宫", "疾厄宫", "迁移宫"]:
        palace = next((p for p in chart["palaces"] if p["name"] == name), None)
        if not palace:
            continue
        lines.append(f"### {name}")
        lines.append(f"- 主星：{_star_line(palace['majorStars']) or '无主星'}")
        minor = _star_line(palace["minorStars"])
        if minor:
            lines.append(f"- 辅星：{minor}")
        lines.append("")
    return "\n".join(lines)


def build_kline_context(chart: Dict[str, Any]) -> str:
    lines = [
        "请根据以下命盘信息，为已由离线工具确定的 1-100 岁人生 K 线补充 brief 文案。",
        "注意：数值走势来自 payload.klineData；不得返回或改写 open、close、high、low。",
        "",
        "## 基本信息",
        f"- 出生年份: {chart['lunar']['year']}年",
        f"- 命宫主星: {_star_line(next(p for p in chart['palaces'] if p['name'] == '命宫')['majorStars']) or '无主星'}",
        f"- 身宫位置: {chart['bodyPalace']['name']}",
        f"- 身宫主星: {_star_line(next(p for p in chart['palaces'] if p['isBodyPalace'])['majorStars']) or '无主星'}",
        "",
        "## 本命四化",
    ]
    lines.append("、".join(f"{m['star']}{m['sihua']} → {m['palace']}" for m in chart["natalMutagens"]) or "无")
    lines += ["", "## 十二宫配置"]
    for p in chart["palaces"]:
        lines.append(f"{p['name']}({p['stem']}{p['branch']}): {_star_line(p['majorStars']) or '无主星'}" + (f" | {_star_line(p['minorStars'])}" if p["minorStars"] else ""))
    lines += ["", "## 大限走向"]
    for _, p in sorted((int(p["decadalRange"].split("-")[0]), p) for p in chart["palaces"]):
        lines.append(f"{p['decadalRange']}岁 → {p['name']}({p['stem']}) 四化:{'、'.join(sihua_list(p['stem']))}")
    lines += ["", "## 近期流年（参考）"]
    target = chart["yearly"]["year"]
    for year in range(target - 5, target + 6):
        data = build_yearly_data(chart, year)
        lines.append(f"{year}年({data['stem']}{data['branch']}) 四化:{'、'.join(data['mutagens'])} 命宫:{data['palaceName']}")
    lines.append("")
    lines.append("请生成 100 年的 K 线 brief JSON；每条仅包含 age 与 brief，可选 reason，不得包含 open、close、high、low。")
    return "\n".join(lines)


def validate_chart_integrity(chart: Dict[str, Any]) -> None:
    palaces = chart.get("palaces", [])
    if len(palaces) != 12:
        raise ValueError("命盘完整性校验失败：palaces 必须为 12 宫")
    if not chart.get("fiveElementsClass"):
        raise ValueError("命盘完整性校验失败：缺失 fiveElementsClass")
    if chart.get("fiveElementsNumber") not in {2, 3, 4, 5, 6}:
        raise ValueError("命盘完整性校验失败：fiveElementsNumber 需在 2-6")
    if not chart.get("natalMutagens"):
        raise ValueError("命盘完整性校验失败：本命四化不能为空")
    for palace in palaces:
        if not palace.get("decadalRange"):
            raise ValueError("命盘完整性校验失败：存在缺失 decadalRange 的宫位")
    yearly = chart.get("yearly", {})
    required_yearly = {"year", "stem", "branch", "mutagens", "palaceName", "currentDecadal"}
    if any(key not in yearly for key in required_yearly):
        raise ValueError("命盘完整性校验失败：yearly 信息不完整")


def validate_kline_data(kline_rows: List[Dict[str, Any]]) -> Tuple[bool, str]:
    if len(kline_rows) != 100:
        return False, "K线校验失败：必须恰好 100 条"
    ages = sorted(int(row.get("age", -1)) for row in kline_rows)
    if ages != list(range(1, 101)):
        return False, "K线校验失败：age 必须覆盖 1-100 且不重复"
    prev_close: Optional[float] = None
    for row in sorted(kline_rows, key=lambda x: int(x["age"])):
        open_v = float(row["open"])
        close_v = float(row["close"])
        high_v = float(row["high"])
        low_v = float(row["low"])
        if any(v < 0 or v > 100 for v in (open_v, close_v, high_v, low_v)):
            return False, f"K线校验失败：age={row['age']} 存在越界值"
        if high_v < max(open_v, close_v):
            return False, f"K线校验失败：age={row['age']} high 过低"
        if low_v > min(open_v, close_v):
            return False, f"K线校验失败：age={row['age']} low 过高"
        if int(row["age"]) == 1 and abs(open_v - 50.0) > 1e-6:
            return False, "K线校验失败：age=1 时 open 必须为 50"
        if prev_close is not None and abs(open_v - prev_close) > 1e-6:
            return False, f"K线校验失败：age={row['age']} 的 open 必须等于上一年 close"
        prev_close = close_v
    return True, "ok"


def build_payload(chart: Dict[str, Any], target_year: int) -> Dict[str, Any]:
    return {
        "chart": chart,
        "ageInfo": compute_age_info(chart, target_year),
        "natalContext": build_prompt_context(chart),
        "yearlyContext": build_yearly_context(chart, target_year),
        "klineContext": build_kline_context(chart),
        "klineData": generate_kline_data(chart),
    }


def _parse_date(value: str) -> Tuple[int, int, int]:
    try:
        d = _dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("日期格式必须为 YYYY-MM-DD") from exc
    return d.year, d.month, d.day


def _parse_time(value: str) -> Tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2 or any(part == "" for part in parts):
        raise ValueError("time 格式必须为 HH:mm")
    hh, mm = parts
    if len(hh) != 2 or len(mm) != 2 or not hh.isdigit() or not mm.isdigit():
        raise ValueError("time 格式必须为 HH:mm")
    hour = int(hh)
    minute = int(mm)
    if not 0 <= hour <= 23:
        raise ValueError("time 小时必须在 00-23 之间")
    if not 0 <= minute <= 59:
        raise ValueError("time 分钟必须在 00-59 之间")
    return hour, minute


def _parse_gender(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"male", "m", "男"}:
        return "male"
    if normalized in {"female", "f", "女"}:
        return "female"
    raise argparse.ArgumentTypeError("gender 须为 male/female 或 男/女")


def _cli_error(parser: argparse.ArgumentParser, message: str) -> int:
    parser.exit(2, f"error: {message}\n")
    return 2


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an offline Zi Wei Dou Shu chart context.")
    parser.add_argument(
        "--from-chart-json",
        action="store_true",
        help="从标准输入读取完整 chart 对象 JSON（如 tools/chart_iztro.cjs 输出），再生成 natalContext / yearlyContext / klineContext",
    )
    parser.add_argument("--solar", type=_parse_date, help="阳历生日，格式 YYYY-MM-DD")
    parser.add_argument("--hour", type=int, help="出生小时，0-23；兼容旧参数")
    parser.add_argument("--time", help="出生时间，格式 HH:mm；优先于 --hour")
    parser.add_argument("--gender", type=_parse_gender, help="性别：male/female 或 男/女")
    parser.add_argument("--birthplace", help="出生地，如 广东省佛山市顺德区")
    parser.add_argument("--longitude", type=float, help="经度（手工指定时优先）")
    parser.add_argument("--latitude", type=float, help="纬度（手工指定时优先）")
    parser.add_argument("--geocode-mode", choices=["online", "offline", "hybrid"], default="hybrid", help="出生地坐标解析模式")
    parser.add_argument("--disable-true-solar-time", action="store_true", help="禁用真太阳时，按标准时排盘")
    parser.add_argument("--target-year", type=int, default=_dt.date.today().year, help="流年分析年份")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="输出格式")
    parser.add_argument(
        "--emit-iztro-birth-json",
        action="store_true",
        help="仅输出一行 JSON：供 chart_iztro.cjs 使用的阳历日与时刻（真太阳时生效时与排盘用的 effective 时间一致）；不与完整 JSON 输出同时使用",
    )
    args = parser.parse_args(argv)

    if args.emit_iztro_birth_json and args.from_chart_json:
        return _cli_error(parser, "--emit-iztro-birth-json 不能与 --from-chart-json 同用")

    if args.from_chart_json:
        if args.solar or args.hour is not None or args.time or args.gender:
            return _cli_error(parser, "使用 --from-chart-json 时不要与 --solar/--time/--hour/--gender 混用")
        try:
            chart = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            return _cli_error(parser, f"stdin 不是合法 JSON: {exc}")
        if not isinstance(chart, dict):
            return _cli_error(parser, "stdin JSON 必须为 chart 对象")
        try:
            life_obj = next(p for p in chart["palaces"] if p.get("name") == "命宫")
            chart["patterns"] = detect_patterns({"palaces": chart["palaces"], "lifePalace": life_obj})
            chart["yearly"] = build_yearly_data(chart, args.target_year)
            validate_chart_integrity(chart)
        except (KeyError, ValueError, StopIteration) as exc:
            return _cli_error(parser, str(exc))
    else:
        if args.solar is None or args.gender is None:
            return _cli_error(parser, "必须提供 --solar 与 --gender，或使用 --from-chart-json")
        y, m, d = args.solar
        hour: Optional[int] = args.hour
        minute = 0
        if args.time:
            try:
                hour, minute = _parse_time(args.time)
            except ValueError as exc:
                return _cli_error(parser, str(exc))
        if hour is None:
            return _cli_error(parser, "必须提供 --time 或 --hour")
        if not 0 <= hour <= 23:
            return _cli_error(parser, "hour 必须在 0-23 之间")
        if (args.longitude is None) != (args.latitude is None):
            return _cli_error(parser, "longitude 与 latitude 必须同时提供")
        try:
            chart = generate_chart(
                y,
                m,
                d,
                hour,
                args.gender,
                args.target_year,
                minute=minute,
                birthplace=args.birthplace,
                longitude=args.longitude,
                latitude=args.latitude,
                use_true_solar_time=not args.disable_true_solar_time,
                geocode_mode=args.geocode_mode,
            )
        except ValueError as exc:
            return _cli_error(parser, str(exc))
        if args.emit_iztro_birth_json:
            ts = chart["birth"]["trueSolar"]["time"]
            if " " not in ts:
                return _cli_error(parser, "内部错误：trueSolar.time 格式异常")
            _, time_part = ts.split(" ", 1)
            emit_obj = {
                "solarDate": chart["birth"]["effectiveSolar"],
                "time": time_part,
                "timeIndex": BRANCHES.index(chart["birth"]["timeBranch"]),
                "gender": chart["birth"]["gender"],
                "trueSolarApplied": bool(chart["birth"]["trueSolar"].get("applied")),
            }
            print(json.dumps(emit_obj, ensure_ascii=False))
            return 0
    payload = build_payload(chart, args.target_year)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["natalContext"])
        print()
        print(payload["yearlyContext"])
        print()
        print(payload["klineContext"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

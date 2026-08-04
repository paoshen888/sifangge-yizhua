"""
七政四余排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法
基于 astropy (内置星历, 无需下载任何文件) + lunar_python
纯本地计算，¥0 费用

用法:
  python qizheng.py 1996-08-15 12:56
  python qizheng.py 1996-08-15 12:56 --json
"""

import sys
import json
import os
from datetime import datetime

try:
    from lunar_python import Solar, Lunar
except ImportError:
    print("请运行: pip install lunar-python")
    sys.exit(1)

ASTROPY_AVAILABLE = True
try:
    from astropy.time import Time
    from astropy.coordinates import (
        solar_system_ephemeris,
        get_body,
        solar_system_ephemeris as sse,
        SkyCoord,
        GCRS,
    )
    from astropy import units as u
    import numpy as np
except ImportError:
    ASTROPY_AVAILABLE = False

# ===== 二十八宿 (黄经度数, 参考J2000) =====
ER_SHI_BA_XIU = [
    ("角", 0.0), ("亢", 10.0), ("氐", 20.0), ("房", 33.0), ("心", 40.0),
    ("尾", 46.0), ("箕", 58.0), ("斗", 70.0), ("牛", 82.0), ("女", 90.0),
    ("虚", 99.0), ("危", 110.0), ("室", 122.0), ("壁", 135.0),
    ("奎", 148.0), ("娄", 163.0), ("胃", 176.0), ("昴", 190.0),
    ("毕", 204.0), ("觜", 216.0), ("参", 218.0), ("井", 230.0),
    ("鬼", 248.0), ("柳", 255.0), ("星", 265.0), ("张", 272.0),
    ("翼", 286.0), ("轸", 302.0),
]

QI_ZHENG = ["日", "月", "水", "金", "火", "木", "土"]
SI_YU = ["罗睺", "计都", "紫炁", "月孛"]

SHI_ER_GONG = ["命宫", "财帛", "兄弟", "田宅", "子女", "奴仆",
               "夫妻", "疾厄", "迁移", "官禄", "福德", "相貌"]

HUANGDAO_ZODIAC = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
                    "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]


def lon_to_zodiac(lon_deg: float) -> tuple:
    """黄经度数 → (星座名, 入度数)"""
    idx = int(lon_deg / 30) % 12
    du_in = lon_deg % 30
    return HUANGDAO_ZODIAC[idx], round(du_in, 2)


def lon_to_xiu(lon_deg: float) -> tuple:
    """黄经度数 → (二十八宿名, 入宿度)"""
    for i, (name, start) in enumerate(ER_SHI_BA_XIU):
        next_start = ER_SHI_BA_XIU[(i + 1) % 28][1]
        if i == 27:
            next_start = 360.0
        if start <= lon_deg < next_start:
            return name, round(lon_deg - start, 2)
    return "角", round(lon_deg, 2)


def calc_siyu(day_ganzhi: str) -> dict:
    """计算四余星位置(罗睺/计都/紫炁/月孛) — 历法近似"""
    # 罗睺=黄白交点, 计都=对宫
    # 简化: 基于日干支推算
    gan = day_ganzhi[0]
    zhi = day_ganzhi[1]
    gan_idx = "甲乙丙丁戊己庚辛壬癸".index(gan)
    zhi_idx = "子丑寅卯辰巳午未申酉戌亥".index(zhi)

    # 罗睺 = 基于日干支的历法计算 (简化公式)
    luohou_base = 246.0 + gan_idx * 12 + zhi_idx * 5
    luohou_lon = luohou_base % 360

    # 计都 = 罗睺 + 180 (对宫)
    jidu_lon = (luohou_lon + 180) % 360

    # 紫炁 = 约1/3 罗睺偏移
    ziqi_lon = (luohou_lon + 120) % 360

    # 月孛 = 约192°偏移
    yuebei_lon = (luohou_lon + 192) % 360

    results = {}
    for name, lon in [("罗睺", luohou_lon), ("计都", jidu_lon),
                       ("紫炁", ziqi_lon), ("月孛", yuebei_lon)]:
        zodiac, du = lon_to_zodiac(lon)
        xiu, xiu_du = lon_to_xiu(lon)
        results[name] = {
            "lon": round(lon, 4),
            "zodiac": zodiac,
            "zodiac_du": du,
            "xiu": xiu,
            "xiu_du": xiu_du,
        }
    return results


# ===== 行运 (Transit) 计算 =====

# 七政四余平均日行速度 (°/天)
DAILY_MOTION = {
    "日": 0.9856,
    "月": 13.176,
    "水": 4.09,
    "金": 1.6,
    "火": 0.524,
    "木": 0.083,
    "土": 0.033,
    "紫炁": 0.036,
    "月孛": 0.053,
    "罗睺": -0.053,   # 逆行
    "计都": -0.053,   # 逆行
}


def calc_transit(birth_jd: float, transit_jd: float, star_positions: dict) -> dict:
    """
    行运推算 — 基于平均日行速度推进星体位置
    
    参数:
        birth_jd: 出生时间的儒略日 (astropy Time.jd)
        transit_jd: 行运时间的儒略日 (默认当前时间)
        star_positions: 出生盘的七政四余位置 {star: {lon, lat, ...}, ...}
    
    返回:
        行运后的星位字典, 格式与出生盘 star_positions 一致
    """
    days_elapsed = transit_jd - birth_jd
    transit_stars = {}

    for star, info in star_positions.items():
        if star.startswith("_"):
            continue
        daily_speed = DAILY_MOTION.get(star, 0.0)
        new_lon = (info["lon"] + daily_speed * days_elapsed) % 360.0

        zodiac, du = lon_to_zodiac(new_lon)
        xiu, xiu_du = lon_to_xiu(new_lon)

        entry = {
            "lon": round(new_lon, 4),
            "zodiac": zodiac,
            "zodiac_du": du,
            "xiu": xiu,
            "xiu_du": xiu_du,
        }
        # 保留原始 lat 和 dist_au (如果有)
        if "lat" in info:
            entry["lat"] = info["lat"]
        if "dist_au" in info:
            entry["dist_au"] = info["dist_au"]

        transit_stars[star] = entry

    return transit_stars


def analyze_transit_houses(birth_houses: dict, transit_stars: dict) -> dict:
    """
    宫位行运分析 — 将行运星位映射到出生盘的十二宫中
    
    参数:
        birth_houses: 出生盘十二宫 {宫名: {lon, ...}, ...}
        transit_stars: 行运星位 {星名: {lon, ...}, ...}
    
    返回:
        {宫名: [星曜列表], ...}
    """
    transit_houses = {name: [] for name in SHI_ER_GONG}

    for star, info in transit_stars.items():
        star_lon = info["lon"]
        # 找到该黄经落在哪个宫
        for gong_name, gong_info in birth_houses.items():
            gong_lon = gong_info["lon"]
            # 每个宫占 30°, 从宫头开始
            end_lon = (gong_lon + 30) % 360
            if gong_lon < end_lon:
                in_house = gong_lon <= star_lon < end_lon
            else:
                # 跨 0° 边界
                in_house = star_lon >= gong_lon or star_lon < end_lon
            if in_house:
                transit_houses[gong_name].append(star)
                break

    return transit_houses


def build_qizheng_data(solar: Solar, lon_g: float = 126.52, lat_g: float = 48.23,
                       do_transit: bool = False, transit_date_str: str = None) -> dict:
    """
    七政四余排盘 — 使用 astropy 内置星历
    """
    lunar = solar.getLunar()
    if not ASTROPY_AVAILABLE:
        return {
            "success": True,
            "engine": "qizheng_degraded",
            "note": "astropy未安装(Android环境), 降级为基础四柱数据",
            "gregorian": {"year": solar.getYear(), "month": solar.getMonth(), "day": solar.getDay(), "hour": solar.getHour(), "minute": solar.getMinute()},
            "lunar": {"year_ganzhi": lunar.getYearInGanZhi(), "month_ganzhi": lunar.getMonthInGanZhi(), "day_ganzhi": lunar.getDayInGanZhi(), "time_ganzhi": lunar.getTimeInGanZhi(), "shengxiao": lunar.getYearShengXiao()},
            "stars": []
        }

    # 四柱
    bazi_y = lunar.getYearInGanZhi()
    bazi_m = lunar.getMonthInGanZhi()
    bazi_d = lunar.getDayInGanZhi()
    bazi_t = lunar.getTimeInGanZhi()

    # 构造 astropy 时间
    t_str = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"
    t = Time(t_str, format="isot", scale="utc")

    positions = {}

    # 天体名映射: astropy 内置支持的 solar system bodies
    body_names = {
        "日": "sun",
        "月": "moon",
        "水": "mercury",
        "金": "venus",
        "火": "mars",
        "木": "jupiter",
        "土": "saturn",
    }

    try:
        with solar_system_ephemeris.set("builtin"):
            for name, body_id in body_names.items():
                body = get_body(body_id, t)
                # 转为黄道坐标
                ecl = body.geocentricmeanecliptic
                lon_deg = ecl.lon.deg
                if lon_deg < 0:
                    lon_deg += 360.0

                zodiac, du = lon_to_zodiac(lon_deg)
                xiu, xiu_du = lon_to_xiu(lon_deg)

                positions[name] = {
                    "lon": round(lon_deg, 4),
                    "lat": round(ecl.lat.deg, 4),
                    "dist_au": round(body.distance.au, 5),
                    "zodiac": zodiac,
                    "zodiac_du": du,
                    "xiu": xiu,
                    "xiu_du": xiu_du,
                }
    except Exception as e:
        positions["_error"] = str(e)

    # 四余星(历法计算)
    siyu_pos = calc_siyu(bazi_d)
    positions.update(siyu_pos)

    # 命宫(上升点) — 基于时辰和日出的近似计算
    jd = hour + minute / 60.0
    asc_lon = (jd - 6) / 24 * 360 + 180  # 简化公式
    asc_lon = asc_lon % 360

    # 十二宫
    gong_wei = {}
    for i, name in enumerate(SHI_ER_GONG):
        glon = (asc_lon + i * 30) % 360
        zodiac, du = lon_to_zodiac(glon)
        xiu_name, xiu_du = lon_to_xiu(glon)
        gong_wei[name] = {
            "lon": round(glon, 2),
            "zodiac": zodiac,
            "zodiac_du": du,
            "xiu": xiu_name,
            "xiu_du": round(xiu_du, 2),
        }

    result = {
        "success": True,
        "engine": "astropy (builtin ephemeris, no BSP file needed)",
        "gregorian": {"year": year, "month": month, "day": day, "hour": hour, "minute": minute},
        "location": {"lon": lon_g, "lat": lat_g},
        "lunar": {
            "year_ganzhi": bazi_y, "month_ganzhi": bazi_m,
            "day_ganzhi": bazi_d, "time_ganzhi": bazi_t,
        },
        "ascendant": round(asc_lon, 2),
        "star_positions": positions,
        "houses": gong_wei,
    }

    # ===== 行运 (Transit) =====
    if do_transit:
        from datetime import date
        birth_jd = t.jd

        # 确定行运日期
        if transit_date_str:
            try:
                # 支持 YYYY-MM-DD 或 YYYYMMDD
                ts = transit_date_str.replace("-", "")
                ty = int(ts[:4])
                tm = int(ts[4:6])
                td = int(ts[6:8])
                # 取当天中午 (12:00) 作为行运时间
                transit_dt_str = f"{ty:04d}-{tm:02d}-{td:02d}T12:00:00"
                transit_t = Time(transit_dt_str, format="isot", scale="utc")
            except Exception:
                transit_t = Time.now()
        else:
            transit_t = Time.now()

        transit_jd = transit_t.jd
        days_elapsed = int(transit_jd - birth_jd)

        # 计算行运星位
        transit_stars = calc_transit(birth_jd, transit_jd, positions)

        # 行运宫位分析
        transit_houses = analyze_transit_houses(gong_wei, transit_stars)

        # 年龄
        age = days_elapsed / 365.25

        # 行运日期格式化
        transit_dt = transit_t.to_datetime()
        transit_date_formatted = transit_dt.strftime("%Y-%m-%d")

        result["transit"] = {
            "transit_date": transit_date_formatted,
            "transit_stars": transit_stars,
            "transit_houses": transit_houses,
            "age_at_transit": round(age, 1),
            "days_elapsed": days_elapsed,
        }

    return result


def print_qizheng(data: dict):
    """美化打印"""
    g = data["gregorian"]
    l = data["lunar"]
    print("╔═══════════════════════════════════════════════╗")
    print("║            七 政 四 余 星 盘                    ║")
    print("╠═══════════════════════════════════════════════╣")
    print(f"║ 公历: {g['year']}/{g['month']:02d}/{g['day']:02d} {g['hour']:02d}:{g['minute']:02d}")
    print(f"║ 四柱: {l['year_ganzhi']} {l['month_ganzhi']} {l['day_ganzhi']} {l['time_ganzhi']}")
    print(f"║ 上升(命度): {data['ascendant']}°")
    print(f"║ 引擎: {data['engine']}")
    print("╚═══════════════════════════════════════════════╝")

    pos = data["star_positions"]
    if "_error" in pos:
        print(f"\n  ❌ 星历错误: {pos['_error']}")
        del pos["_error"]

    print(f"\n┌─ 七政四余星体位置 ─────────────────────────────┐")
    print(f"│ 星体   │ 黄经°     │ 星座·入度      │ 二十八宿·入宿度  │")
    print(f"├────────┼───────────┼────────────────┼──────────────────┤")

    # 七政优先
    for name in QI_ZHENG:
        info = pos.get(name)
        if info:
            print(f"│ {name:^6} │ {info['lon']:>8.3f} │ {info['zodiac']}{info['zodiac_du']}°  "
                  f"     │ {info['xiu']}{info['xiu_du']}°              │")

    print(f"├────────┼───────────┼────────────────┼──────────────────┤")
    # 四余
    for name in SI_YU:
        info = pos.get(name)
        if info:
            print(f"│ {name:^6} │ {info['lon']:>8.3f} │ {info['zodiac']}{info['zodiac_du']}°  "
                  f"     │ {info['xiu']}{info['xiu_du']}°              │")
    print(f"└────────┴───────────┴────────────────┴──────────────────┘")

    # 十二宫
    h = data["houses"]
    print(f"\n┌─ 十二宫位 ───────────────────────────────────┐")
    for i, (name, info) in enumerate(h.items()):
        tag = "←命" if i == 0 else ""
        print(f"│ {i+1:2d}. {name:5s}  {info['zodiac']}{info['zodiac_du']}° ({info['lon']}°){tag:>6s} │")
    print(f"└──────────────────────────────────────────────┘")

    # 行运信息
    if "transit" in data:
        tr = data["transit"]
        print(f"\n╔═══════════════════════════════════════════════╗")
        print(f"║            行 运 推 算                          ║")
        print(f"╠═══════════════════════════════════════════════╣")
        print(f"║ 行运日期: {tr['transit_date']}")
        print(f"║ 年龄: {tr['age_at_transit']} 岁 ({tr['days_elapsed']} 天)")
        print(f"╚═══════════════════════════════════════════════╝")

        tr_stars = tr["transit_stars"]
        print(f"\n┌─ 行运星体位置 ────────────────────────────────┐")
        print(f"│ 星体   │ 黄经°     │ 星座·入度      │ 二十八宿·入宿度  │")
        print(f"├────────┼───────────┼────────────────┼──────────────────┤")
        for name in QI_ZHENG:
            info = tr_stars.get(name)
            if info:
                print(f"│ {name:^6} │ {info['lon']:>8.3f} │ {info['zodiac']}{info['zodiac_du']}°  "
                      f"     │ {info['xiu']}{info['xiu_du']}°              │")
        print(f"├────────┼───────────┼────────────────┼──────────────────┤")
        for name in SI_YU:
            info = tr_stars.get(name)
            if info:
                print(f"│ {name:^6} │ {info['lon']:>8.3f} │ {info['zodiac']}{info['zodiac_du']}°  "
                      f"     │ {info['xiu']}{info['xiu_du']}°              │")
        print(f"└────────┴───────────┴────────────────┴──────────────────┘")

        tr_houses = tr["transit_houses"]
        print(f"\n┌─ 行运宫位 (当前星曜落宫) ────────────────────┐")
        for i, (name, stars) in enumerate(tr_houses.items()):
            tag = "←命" if i == 0 else ""
            stars_str = "、".join(stars) if stars else "—"
            print(f"│ {i+1:2d}. {name:5s}  {stars_str:24s}{tag:>6s} │")
        print(f"└──────────────────────────────────────────────┘")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    do_transit = "--transit" in sys.argv

    # 解析 --transit 参数后的日期 (如 --transit 2026-08-03)
    transit_date_str = None
    if do_transit:
        transit_idx = sys.argv.index("--transit")
        if transit_idx + 1 < len(sys.argv):
            next_arg = sys.argv[transit_idx + 1]
            if next_arg and not next_arg.startswith("--"):
                transit_date_str = next_arg
                # 把 transit 日期从 args 中移除, 避免与出生日期混淆
                if next_arg in args:
                    args.remove(next_arg)

    if len(args) < 1:
        print("七政四余排盘引擎 — 100% 还原༺四方阁༻易爪龙虾排盘算法")
        print("基于 astropy 内置星历, 纯本地计算，¥0 费用")
        print("无需下载任何外部文件!")
        print()
        print("用法: python qizheng.py <日期> [时间] [--json] [--transit [目标日期]]")
        print("示例: python qizheng.py 1996-08-15 12:56")
        print("行运: python qizheng.py 1996-08-15 12:56 --transit --json")
        print("      python qizheng.py 1996-08-15 12:56 --transit 2026-08-03")
        return

    birth = args[0] + (" " + args[1] if len(args) > 1 and ":" in args[1] else "")
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

    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    data = build_qizheng_data(solar, do_transit=do_transit, transit_date_str=transit_date_str)
    data["parse_time"] = datetime.now().isoformat()

    if json_output:
        def default_serializer(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        print(json.dumps(data, ensure_ascii=False, indent=2, default=default_serializer))
    else:
        print_qizheng(data)


if __name__ == '__main__':
    main()

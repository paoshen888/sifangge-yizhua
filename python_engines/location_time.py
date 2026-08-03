# -*- coding: utf-8 -*-
"""
地理位置 + 时间转换引擎
功能: 城市经纬度查询, 真太阳时校正, 公历农历互转
数据: region.json (从原版 APK 提取, 501KB 中国城市数据)
"""

import json, os, math
from datetime import datetime, timedelta, timezone
from collections import OrderedDict

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ 加载地区数据 ============
_region_data = None

def _load_region():
    global _region_data
    if _region_data is not None:
        return _region_data
    path = os.path.join(DATA_DIR, "static", "region.json")
    if not os.path.exists(path):
        path = os.path.join(DATA_DIR, "region.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _region_data = json.load(f)
    else:
        _region_data = {}
    return _region_data

# ============ 城市经纬度查询 ============
def find_location(keyword):
    """模糊搜索城市, 返回经纬度列表
    region.json 格式: [{ province, cities: [{ city, longitude, latitude, counties: [{ county, longitude, latitude }] }] }]
    """
    data = _load_region()
    results = []
    kw = keyword.lower().strip()
    
    if not isinstance(data, list):
        return results
    
    for prov in data:
        pname = prov.get("province", "")
        cities = prov.get("cities", [])
        if not isinstance(cities, list):
            continue
        
        for city in cities:
            cname = city.get("city", "")
            clng = city.get("longitude", 0)
            clat = city.get("latitude", 0)
            
            # 匹配城市名
            if kw in cname.lower() or kw in cname or kw.replace("市","") in cname:
                results.append({
                    "name": cname,
                    "full_path": f"{pname}/{cname}",
                    "lat": float(clat) if clat else None,
                    "lng": float(clng) if clng else None,
                })
            
            # 匹配区县
            counties = city.get("counties", [])
            if isinstance(counties, list):
                for county in counties:
                    coname = county.get("county", "")
                    if kw in coname.lower() or kw in coname:
                        colng = county.get("longitude", clng)
                        colat = county.get("latitude", clat)
                        results.append({
                            "name": coname,
                            "full_path": f"{pname}/{cname}/{coname}",
                            "lat": float(colat) if colat else float(clat) if clat else None,
                            "lng": float(colng) if colng else float(clng) if clng else None,
                        })
            
            if len(results) >= 20:
                break
        if len(results) >= 20:
            break
    
    return results[:20]

# ============ 真太阳时校正 ============
# 标准子午线: 北京时间对应东经120°
STANDARD_MERIDIAN = 120.0

def true_solar_time(lng, dt):
    """
    根据经度计算真太阳时
    lng: 东经度数 (正数)
    dt: datetime 对象 (北京时间)
    返回: datetime 对象 (真太阳时)
    """
    # 经度差 → 时间差: 每度4分钟
    delta_deg = lng - STANDARD_MERIDIAN
    delta_minutes = delta_deg * 4.0
    
    # 均时差 (Equation of Time) 简化近似
    # DOY = day of year
    doy = dt.timetuple().tm_yday
    B = (360.0 / 365.0) * (doy - 81)
    B_rad = math.radians(B)
    eot = 9.87 * math.sin(2 * B_rad) - 7.53 * math.cos(B_rad) - 1.5 * math.sin(B_rad)
    # eot in minutes, 正值表示视太阳在平太阳之前
    
    total_offset = delta_minutes + eot
    return dt + timedelta(minutes=total_offset)


def correct_time(city, year, month, day, hour, minute=0):
    """
    根据城市名做真太阳时校正
    返回: { original, corrected, offset_minutes, city_info }
    """
    locs = find_location(city)
    if not locs:
        return {
            "error": f"未找到城市「{city}」",
            "original": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            "corrected": None,
            "used_default": True,
            "default_lng": 116.4,
            "default_lat": 39.9,
        }
    
    loc = locs[0]
    lng = loc.get("lng")
    lat = loc.get("lat")
    
    if lng is None:
        lng = 116.4  # 默认北京
        lat = 39.9
    
    dt = datetime(year, month, day, hour, minute)
    corrected = true_solar_time(lng, dt)
    offset = (corrected - dt).total_seconds() / 60.0
    
    return OrderedDict([
        ("city", loc["full_path"]),
        ("lat", round(lat, 4)),
        ("lng", round(lng, 4)),
        ("original", f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"),
        ("corrected", corrected.strftime("%Y-%m-%d %H:%M")),
        ("corrected_hour", corrected.hour),
        ("corrected_minute", corrected.minute),
        ("offset_minutes", round(offset, 1)),
        ("offset_desc", f"{'快' if offset > 0 else '慢'}{abs(offset):.0f}分钟"),
    ])


# ============ 公历 ↔ 农历互转 ============
try:
    from lunar_python import Solar, Lunar
    _LUNAR_AVAILABLE = True
except ImportError:
    _LUNAR_AVAILABLE = False

def solar_to_lunar(year, month, day):
    """公历 → 农历"""
    if not _LUNAR_AVAILABLE:
        return {"error": "lunar_python 未安装"}
    try:
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        return OrderedDict([
            ("solar", f"{year:04d}-{month:02d}-{day:02d}"),
            ("lunar", f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"),
            ("lunar_year", lunar.getYear()),
            ("lunar_month", lunar.getMonth()),
            ("lunar_day", lunar.getDay()),
            ("is_leap", "否" if lunar.getMonth() == lunar.getSolar().getLunar().getMonth() else "是"),
            ("year_ganzhi", lunar.getYearInGanZhi()),
            ("month_ganzhi", lunar.getMonthInGanZhi()),
            ("day_ganzhi", lunar.getDayInGanZhi()),
            ("shengxiao", lunar.getYearShengXiao()),
            ("festivals", lunar.getFestivals()),
            ("jieqi", lunar.getJieQi() if hasattr(lunar, 'getJieQi') else None),
        ])
    except Exception as e:
        return {"error": str(e)}


def lunar_to_solar(year, month, day, is_leap=False):
    """农历 → 公历"""
    if not _LUNAR_AVAILABLE:
        return {"error": "lunar_python 未安装"}
    try:
        lunar = Lunar.fromYmd(year, month, day)
        solar = lunar.getSolar()
        return OrderedDict([
            ("lunar", f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"),
            ("solar", solar.toString()),
            ("solar_year", solar.getYear()),
            ("solar_month", solar.getMonth()),
            ("solar_day", solar.getDay()),
        ])
    except Exception as e:
        return {"error": str(e)}

# ============ 命令行入口 (供 api_server.py 调用) ============
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: location_time.py <action> [args...]"}, ensure_ascii=False))
        sys.exit(0)
    
    action = sys.argv[1]
    try:
        if action == "find":
            keyword = sys.argv[2] if len(sys.argv) > 2 else "北京"
            results = find_location(keyword)
            print(json.dumps({"action": "find", "keyword": keyword, "results": results}, ensure_ascii=False, indent=2))
        
        elif action in ("s2l", "solar_to_lunar"):
            dt_str = sys.argv[2] if len(sys.argv) > 2 else "2024-03-15"
            parts = dt_str.replace("-", " ").replace("/", " ").split()
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            result = solar_to_lunar(y, m, d)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif action in ("l2s", "lunar_to_solar"):
            dt_str = sys.argv[2] if len(sys.argv) > 2 else "2024-01-01"
            parts = dt_str.replace("-", " ").replace("/", " ").split()
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            result = lunar_to_solar(y, m, d)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif action in ("correct", "tst", "true_solar"):
            dt_str = sys.argv[2] if len(sys.argv) > 2 else "2024-03-15 14:30"
            city = sys.argv[3] if len(sys.argv) > 3 else "北京"
            parts = dt_str.replace("-", " ").replace(":", " ").replace("T", " ").split()
            y, mo, d = int(parts[0]), int(parts[1]), int(parts[2])
            h = int(parts[3]) if len(parts) > 3 else 12
            mi = int(parts[4]) if len(parts) > 4 else 0
            result = correct_time(city, y, mo, d, h, mi)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        else:
            print(json.dumps({"error": f"未知动作: {action}"}, ensure_ascii=False))
    
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))

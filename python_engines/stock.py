"""
股票行情查询 — A股/港股/美股实时数据
基于新浪财经免费接口，纯本地查询

用法:
  python stock.py 600519                         # 查询贵州茅台
  python stock.py 000001 300750                  # 批量查询
  python stock.py --index                        # 三大指数
  python stock.py 600519 --json                  # JSON输出
  python stock.py --hot                          # 热门板块
"""

import sys
import json
import urllib.request
import re
from datetime import datetime

# 股票代码前缀映射
CODE_PREFIX = {
    "sh": ["60", "68", "900", "51"],
    "sz": ["00", "30", "002", "003", "200"],
}

INDEX_CODES = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
    "上证50": "sh000016",
    "沪深300": "sh000300",
    "中证500": "sh000905",
    "科创50": "sh000688",
}

HOT_SECTORS = {
    "人工智能": "BK0800",
    "新能源汽车": "BK0493",
    "芯片半导体": "BK0448",
    "光伏": "BK0478",
    "医药": "BK0465",
    "白酒": "BK0477",
    "军工": "BK0432",
    "券商": "BK0426",
    "银行": "BK0428",
    "地产": "BK0451",
    "电力": "BK0427",
    "煤炭": "BK0437",
    "钢铁": "BK0470",
    "有色": "BK0473",
    "石油": "BK0464",
}


def determine_market(code):
    """判断股票代码属于哪个市场"""
    code = code.strip()
    # 已带前缀
    if code.startswith("sh") or code.startswith("sz"):
        return code[:2], code[2:]
    if code.startswith("bk_"):
        return "bk", code[3:]
    if code.startswith("hk"):
        return "hk", code[2:]
    if code.startswith("gb_"):
        return "us", code[3:]
    # A股自动判断
    if code.startswith("60") or code.startswith("68") or code.startswith("900"):
        return "sh", code
    return "sz", code


def fetch_sina(code):
    """从新浪获取实时行情"""
    prefix, symbol = determine_market(code)

    if prefix == "hk":
        url = f"https://hq.sinajs.cn/list=rt_hk{symbol.zfill(5)}"
    elif prefix == "us":
        url = f"https://hq.sinajs.cn/list=gb_{symbol.lower()}"
    elif prefix == "bk":
        url = f"https://hq.sinajs.cn/list=bk_{symbol}"
    else:
        url = f"https://hq.sinajs.cn/list={prefix}{symbol}"

    req = urllib.request.Request(url, headers={
        "Referer": "https://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0",
    })

    try:
        resp = urllib.request.urlopen(req, timeout=5)
        raw = resp.read().decode("gbk", errors="ignore")
        # 提取 "..." 中的内容
        idx = raw.find('"')
        if idx == -1:
            return None
        start = idx + 1
        end = raw.find('"', start)
        if end == -1:
            return None
        return raw[start:end]
    except Exception:
        return None


def parse_sina_a(code, csv_str):
    """解析新浪A股行情数据 (纯csv字符串)"""
    fields = csv_str.split(",")
    if len(fields) < 32:
        return None

    try:
        current = float(fields[3]) if fields[3] else 0
        prev_close = float(fields[2]) if fields[2] else 0
        change = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        return {
            "代码": code,
            "名称": fields[0],
            "最新价": current,
            "涨跌幅": f"{change_pct:+.2f}%",
            "涨跌额": round(change, 2),
            "今开": float(fields[1]) if fields[1] else 0,
            "昨收": prev_close,
            "最高": float(fields[4]) if fields[4] else 0,
            "最低": float(fields[5]) if fields[5] else 0,
            "成交量(手)": int(fields[8]) if fields[8] else 0,
            "成交额(万)": int(float(fields[9])) if len(fields) > 9 and fields[9] else 0,
            "时间": f"{fields[30]} {fields[31]}" if len(fields) > 31 else "",
            "市场": "A股",
        }
    except (ValueError, IndexError):
        return None


def parse_sina_index(name, csv_str):
    """解析指数数据 (纯csv字符串)"""
    fields = csv_str.split(",")
    if len(fields) < 6:
        return None

    # 新浪指数格式: 名称, 最新, 昨收, 今开, 最高, 最低, ...
    try:
        current = float(fields[1]) if fields[1] else 0
        prev_close = float(fields[2]) if fields[2] else 0
        change = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        return {
            "名称": name,
            "代码": fields[0],
            "最新": current,
            "昨收": prev_close,
            "涨跌额": round(change, 2),
            "涨跌幅": f"{change_pct:+.2f}%",
            "成交量(手)": int(fields[7]) if len(fields) > 7 and fields[7] else 0,
            "成交额(万)": float(fields[8]) if len(fields) > 8 and fields[8] else 0,
        }
    except (ValueError, IndexError):
        return None


def fetch_sector(sector_name, sector_code):
    """获取板块行情"""
    csv_str = fetch_sina(f"bk_{sector_code}" if not sector_code.startswith("bk_") else sector_code)
    if not csv_str:
        if not sector_code.startswith("bk_"):
            csv_str = fetch_sina(sector_code)
    if not csv_str:
        return None

    try:
        fields = csv_str.split(",")
        if len(fields) >= 5:
            current = float(fields[1]) if fields[1] else 0
            prev = float(fields[2]) if fields[2] else 0
            chg_pct = (current - prev) / prev * 100 if prev else 0
            return {
                "板块": sector_name,
                "最新": round(current, 2),
                "涨跌额": round(current - prev, 2) if prev else 0,
                "涨跌幅": f"{chg_pct:+.2f}%",
                "领涨股": fields[4] if len(fields) > 4 else "",
            }
    except:
        pass
    return None


def get_stock_quote(code):
    """获取单只股票行情"""
    csv_str = fetch_sina(code)
    if not csv_str:
        return {"error": f"获取行情失败: {code}"}
    result = parse_sina_a(code, csv_str)
    if not result:
        return {"error": f"解析行情失败: {code}"}
    return result


def get_index_quotes():
    """获取主要指数"""
    results = []
    for name, code in INDEX_CODES.items():
        csv_str = fetch_sina(code)
        if csv_str:
            parsed = parse_sina_index(name, csv_str)
            if parsed:
                results.append(parsed)
    return results


def get_hot_sectors():
    """获取热门板块"""
    results = []
    for name, code in HOT_SECTORS.items():
        data = fetch_sector(name, code)
        if data:
            results.append(data)
    return results


def print_stock(result):
    """美化打印单只股票"""
    if "error" in result:
        print(f"  ❌ {result['error']}")
        return

    change_pct = result.get("涨跌幅", "0%")
    pct_val = float(change_pct.replace("%", "")) if change_pct else 0
    color = "🔴" if pct_val > 0 else "🟢" if pct_val < 0 else "⚪"

    print(f"\n  {color} {result['名称']}({result['代码']})  {result['市场']}")
    print(f"  {'─'*50}")
    print(f"  最新: {result['最新价']:.2f}    涨跌: {result['涨跌额']:.2f}   {change_pct}")
    print(f"  今开: {result['今开']:.2f}     最高: {result['最高']:.2f}")
    print(f"  昨收: {result['昨收']:.2f}     最低: {result['最低']:.2f}")
    print(f"  成交量: {result['成交量(手)']:,}手    成交额: {result['成交额(万)']:.0f}万")
    print(f"  时间: {result['时间']}")


def print_index_table(indices):
    """打印指数表"""
    print(f"\n  {'名称':8s} {'最新':>10s} {'涨跌':>8s} {'幅度':>8s}")
    print(f"  {'─'*40}")
    for idx in indices:
        name = idx['名称']
        price = f"{idx['最新']:,.2f}" if idx['最新'] < 100 else f"{idx['最新']:,.0f}"
        chg = f"{idx['涨跌额']:+.2f}"
        pct = idx['涨跌幅']
        print(f"  {name:8s} {price:>10s} {chg:>8s} {pct:>8s}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    show_index = "--index" in sys.argv
    show_hot = "--hot" in sys.argv

    if not args and not show_index and not show_hot:
        print("股票行情查询 — A股/港股/美股实时")
        print()
        print("用法:")
        print("  python stock.py 600519                    # 贵州茅台")
        print("  python stock.py 000001 300750             # 批量查询")
        print("  python stock.py --index                   # 三大指数")
        print("  python stock.py --hot                     # 热门板块")
        print("  python stock.py 600519 --json             # JSON输出")
        return

    results = {
        "时间": datetime.now().isoformat(),
        "数据": [],
    }

    # 指数
    if show_index:
        indices = get_index_quotes()
        results["指数"] = indices
        if not json_output:
            print("╔═══════════════════════════════════════════════╗")
            print("║            实 时 行 情                         ║")
            print("╚═══════════════════════════════════════════════╝")
            print_index_table(indices)

    # 热门板块
    if show_hot:
        sectors = get_hot_sectors()
        results["热门板块"] = sectors
        if not json_output:
            print(f"\n  {'板块':10s} {'最新':>8s} {'涨跌幅':>8s} {'领涨':10s}")
            print(f"  {'─'*42}")
            for s in sorted(sectors, key=lambda x: float(x.get('涨跌幅', '0%').replace('%', '')), reverse=True)[:10]:
                name = s['板块']
                price = f"{s['最新']:,.0f}"
                pct = s['涨跌幅']
                lead = s.get('领涨股', '')
                print(f"  {name:10s} {price:>8s} {pct:>8s} {lead:10s}")

    # 个股
    for code in args:
        result = get_stock_quote(code)
        if result:
            results["数据"].append(result)
            if not json_output:
                print_stock(result)

    if json_output:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()

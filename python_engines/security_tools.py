"""
AI安全工具箱 — 自然语言驱动的安全审计与渗透测试辅助
纯本地计算，10大模块

⚠️ 仅限授权范围内的安全测试/学习研究/自有系统审计
严禁对未授权目标使用本工具

用法:
  python security_tools.py scan --target 192.168.1.1        # 端口扫描
  python security_tools.py subdomain --domain example.com    # 子域名发现
  python security_tools.py headers --url https://example.com # HTTP头分析
  python security_tools.py encode --text "hello" --type b64  # 编码工具箱
  python security_tools.py hash --file test.txt              # 文件哈希
  python security_tools.py cve --keyword "log4j"             # CVE查询
  python security_tools.py whois --domain example.com        # Whois查询
  python security_tools.py dns --domain example.com          # DNS记录
  python security_tools.py ssl --host example.com            # SSL证书检查
  python security_tools.py info --target example.com         # 综合信息收集
"""

import sys
import json
import os
import socket
import ssl
import hashlib
import base64
import re
import urllib.request
import urllib.parse
from datetime import datetime

# ===== 1. 端口扫描 =====

def scan_ports(target, ports=None):
    """TCP端口扫描"""
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995,
                 1723, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017]

    services = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
        80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
        993: "IMAPS", 995: "POP3S", 1723: "PPTP", 3306: "MySQL",
        3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
        8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
    }

    results = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5)
            result = sock.connect_ex((target, port))
            sock.close()
            if result == 0:
                results.append({
                    "port": port,
                    "service": services.get(port, "Unknown"),
                    "status": "open",
                })
        except Exception:
            pass
    return results


# ===== 2. 子域名发现 =====

def discover_subdomains(domain):
    """常见子域名枚举"""
    common_subs = [
        "www", "mail", "ftp", "admin", "blog", "shop", "api", "dev",
        "staging", "test", "portal", "cdn", "m", "mobile", "app",
        "vpn", "remote", "webmail", "ns1", "ns2", "dns", "git",
        "wiki", "docs", "support", "help", "status", "monitor",
        "auth", "login", "sso", "dashboard", "manage", "panel",
    ]

    results = []
    for sub in common_subs:
        hostname = f"{sub}.{domain}"
        try:
            socket.gethostbyname(hostname)
            results.append({"subdomain": hostname, "resolved": True})
        except socket.gaierror:
            pass
    return results


# ===== 3. HTTP头分析 =====

def analyze_headers(url):
    """分析HTTP响应头"""
    if not url.startswith("http"):
        url = "https://" + url

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        headers = dict(resp.headers)

        security_checks = {}
        # 检查安全头
        checks = {
            "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
            "Content-Security-Policy": headers.get("Content-Security-Policy"),
            "X-Frame-Options": headers.get("X-Frame-Options"),
            "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
            "Referrer-Policy": headers.get("Referrer-Policy"),
            "Permissions-Policy": headers.get("Permissions-Policy"),
        }

        score = 0
        issues = []
        for name, value in checks.items():
            if value:
                score += 1
            else:
                issues.append(f"缺少 {name} 头")

        return {
            "url": url,
            "status_code": resp.status,
            "headers": headers,
            "security_score": score,
            "security_max": len(checks),
            "missing_headers": issues,
            "server": headers.get("Server", "未泄露"),
        }
    except Exception as e:
        return {"error": str(e)}


# ===== 4. 编码工具箱 =====

def encode_toolbox(text, enc_type):
    """编解码工具"""
    results = {}

    # Base64
    try:
        results["base64_encode"] = base64.b64encode(text.encode()).decode()
    except: pass
    try:
        results["base64_decode"] = base64.b64decode(text.encode()).decode()
    except: pass

    # URL编码
    try:
        results["url_encode"] = urllib.parse.quote(text)
    except: pass
    try:
        results["url_decode"] = urllib.parse.unquote(text)
    except: pass

    # Hex
    try:
        results["hex_encode"] = text.encode().hex()
    except: pass
    try:
        results["hex_decode"] = bytes.fromhex(text).decode()
    except: pass

    # MD5
    results["md5"] = hashlib.md5(text.encode()).hexdigest()
    # SHA256
    results["sha256"] = hashlib.sha256(text.encode()).hexdigest()

    if enc_type and enc_type in results:
        return {enc_type: results[enc_type]}
    return results


# ===== 5. 文件哈希 =====

def file_hash(filepath):
    """计算文件哈希"""
    if not os.path.exists(filepath):
        return {"error": "文件不存在"}

    with open(filepath, "rb") as f:
        data = f.read()

    return {
        "file": filepath,
        "size": len(data),
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


# ===== 6. CVE查询 =====

CVE_DB = {
    "log4j": [
        {"id": "CVE-2021-44228", "score": 10.0, "desc": "Log4Shell RCE", "year": 2021},
        {"id": "CVE-2021-45046", "score": 9.0, "desc": "Log4j2 信息泄露", "year": 2021},
    ],
    "spring": [
        {"id": "CVE-2022-22965", "score": 9.8, "desc": "Spring4Shell RCE", "year": 2022},
        {"id": "CVE-2022-22963", "score": 9.8, "desc": "Spring Cloud Function RCE", "year": 2022},
    ],
    "apache": [
        {"id": "CVE-2023-25690", "score": 9.8, "desc": "Apache HTTP Server RCE", "year": 2023},
    ],
    "nginx": [
        {"id": "CVE-2021-23017", "score": 7.2, "desc": "Nginx DNS Resolver Off-by-One", "year": 2021},
    ],
    "ssh": [
        {"id": "CVE-2024-6387", "score": 8.1, "desc": "OpenSSH regreSSHion RCE", "year": 2024},
    ],
    "openssl": [
        {"id": "CVE-2022-3602", "score": 7.5, "desc": "OpenSSL 3.x 缓冲区溢出", "year": 2022},
        {"id": "CVE-2022-3786", "score": 7.5, "desc": "OpenSSL X.509 DoS", "year": 2022},
    ],
}


def search_cve(keyword):
    """搜索CVE漏洞"""
    keyword_lower = keyword.lower()
    results = []

    for product, cves in CVE_DB.items():
        if keyword_lower in product:
            results.extend(cves)
        else:
            for cve in cves:
                if keyword_lower in cve["desc"].lower() or keyword_lower in cve["id"].lower():
                    results.append(cve)

    return results


# ===== 7. Whois查询辅助 =====

def whois_lookup(domain):
    """通过公共API查询域名信息"""
    try:
        url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())

        return {
            "domain": domain,
            "status": data.get("status", []),
            "nameservers": [ns.get("ldhName") for ns in data.get("nameservers", [])],
            "registered": data.get("events", [{}])[0].get("eventDate", "未知"),
        }
    except Exception as e:
        return {"error": str(e)}


# ===== 8. DNS记录查询 =====

def dns_lookup(domain):
    """DNS记录查询"""
    results = {}
    record_types = {
        "A": socket.getaddrinfo,
        "CNAME": lambda d: [(d,)],  # 简化
    }

    # A记录
    try:
        addrs = socket.getaddrinfo(domain, None)
        results["A"] = list(set(a[4][0] for a in addrs))
    except:
        results["A"] = []

    # MX记录 (简化)
    try:
        import dns.resolver
        mx = dns.resolver.resolve(domain, 'MX')
        results["MX"] = [str(r.exchange) for r in mx]
    except:
        results["MX"] = ["需安装 dnspython: pip install dnspython"]

    return results


# ===== 9. SSL证书检查 =====

def ssl_check(host, port=443):
    """检查SSL证书"""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                return {
                    "host": f"{host}:{port}",
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "not_before": cert.get("notBefore"),
                    "not_after": cert.get("notAfter"),
                    "san": [x[1] for x in cert.get("subjectAltName", [])],
                }
    except Exception as e:
        return {"error": str(e)}


# ===== 10. 综合信息收集 =====

def gather_info(target):
    """综合信息收集"""
    domain = target.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]

    return {
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "dns": dns_lookup(domain),
        "subdomains": discover_subdomains(domain),
        "ports": scan_ports(domain),
        "ssl": ssl_check(domain),
    }


# ===== 美化输出 =====

def print_section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


def print_result(data, indent=2):
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "headers" and isinstance(v, dict):
                print(f"  {' '*indent}{k}:")
                for hk, hv in list(v.items())[:10]:
                    print(f"  {' '*(indent+2)}{hk}: {hv}")
            elif isinstance(v, (list, dict)):
                print(f"  {' '*indent}{k}: {json.dumps(v, ensure_ascii=False, indent=indent+2)[:500]}")
            else:
                print(f"  {' '*indent}{k}: {v}")
    elif isinstance(data, list):
        for item in data[:20]:
            print(f"  {' '*indent}{json.dumps(item, ensure_ascii=False)}")


def main():
    if len(sys.argv) < 2:
        print("AI安全工具箱 — 9大安全模块")
        print()
        print("命令:")
        print("  scan --target <IP> [--ports 80,443,8080]")
        print("  subdomain --domain <domain>")
        print("  headers --url <url>")
        print("  encode --text <text> [--type b64|hex|url|md5|sha256]")
        print("  hash --file <path>")
        print("  cve --keyword <keyword>")
        print("  whois --domain <domain>")
        print("  dns --domain <domain>")
        print("  ssl --host <host> [--port 443]")
        print("  info --target <domain>")
        print()
        print("  ⚠️ 仅限授权范围 / 学习研究 / 自有系统审计")
        return

    cmd = sys.argv[1]
    json_output = "--json" in sys.argv

    # 解析参数
    params = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:]
            val = sys.argv[i + 1] if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--") else True
            params[key] = val
            if val is not True:
                i += 1
        i += 1

    result = None

    if cmd == "scan":
        target = params.get("target", "127.0.0.1")
        ports = None
        if "ports" in params:
            ports = [int(p) for p in params["ports"].split(",")]
        result = scan_ports(target, ports)
        if not json_output:
            print_section(f"端口扫描: {target}")
            for r in result:
                print(f"  [OPEN] {r['port']:6d}  {r['service']}")

    elif cmd == "subdomain":
        domain = params.get("domain", "example.com")
        result = discover_subdomains(domain)
        if not json_output:
            print_section(f"子域名: {domain}")
            for r in result:
                print(f"  [FOUND] {r['subdomain']}")
            if not result:
                print("  未发现常见子域名")

    elif cmd == "headers":
        url = params.get("url", "https://example.com")
        result = analyze_headers(url)
        if not json_output:
            print_section(f"HTTP头: {url}")
            print(f"  状态码: {result.get('status_code')}")
            print(f"  安全评分: {result.get('security_score')}/{result.get('security_max')}")
            for issue in result.get("missing_headers", []):
                print(f"  ⚠️ {issue}")

    elif cmd == "encode":
        text = params.get("text", "")
        enc_type = params.get("type", "")
        result = encode_toolbox(text, enc_type)
        if not json_output:
            print_section("编码工具")
            print_result(result)

    elif cmd == "hash":
        filepath = params.get("file", "")
        result = file_hash(filepath)
        if not json_output:
            print_section(f"文件哈希: {filepath}")
            print_result(result)

    elif cmd == "cve":
        keyword = params.get("keyword", "")
        result = search_cve(keyword)
        if not json_output:
            print_section(f"CVE搜索: {keyword}")
            for cve in result:
                print(f"  {cve['id']} (CVSS {cve['score']}) - {cve['desc']} ({cve['year']})")

    elif cmd == "whois":
        domain = params.get("domain", "example.com")
        result = whois_lookup(domain)
        if not json_output:
            print_section(f"Whois: {domain}")
            print_result(result)

    elif cmd == "dns":
        domain = params.get("domain", "example.com")
        result = dns_lookup(domain)
        if not json_output:
            print_section(f"DNS: {domain}")
            print_result(result)

    elif cmd == "ssl":
        host = params.get("host", "example.com")
        port = int(params.get("port", 443))
        result = ssl_check(host, port)
        if not json_output:
            print_section(f"SSL: {host}:{port}")
            print_result(result)

    elif cmd == "info":
        target = params.get("target", "example.com")
        result = gather_info(target)
        if not json_output:
            print_section(f"综合信息: {target}")
            print_result(result)

    else:
        result = {"error": f"未知命令: {cmd}"}
        print(result["error"])

    if json_output and result:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()

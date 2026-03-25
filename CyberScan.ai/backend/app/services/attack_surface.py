"""
Attack Surface Discovery — finds exposed assets, open ports, subdomains,
DNS records, tech stack, and email security posture.
"""

import asyncio
import socket
import re
from urllib.parse import urlparse
from typing import Dict, List, Any
import httpx
import structlog

logger = structlog.get_logger()

# Common ports to probe
COMMON_PORTS = [80, 443, 8080, 8443, 3000, 5000, 8000, 8888, 9000, 22, 21, 25, 3306, 5432, 6379, 27017]

# Common subdomains to check
COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "admin", "api", "dev", "staging", "test",
    "blog", "shop", "app", "portal", "vpn", "remote", "cdn", "static",
    "assets", "media", "img", "images", "docs", "help", "support",
    "dashboard", "panel", "cpanel", "webmail", "smtp", "pop", "imap",
]

# Sensitive paths to probe
SENSITIVE_PATHS = [
    ("/.env",              "critical", "Environment file exposed"),
    ("/.git/config",       "critical", "Git repository exposed"),
    ("/wp-config.php",     "critical", "WordPress config exposed"),
    ("/config.php",        "high",     "Config file exposed"),
    ("/phpinfo.php",       "high",     "PHP info page exposed"),
    ("/admin",             "medium",   "Admin panel accessible"),
    ("/administrator",     "medium",   "Admin panel accessible"),
    ("/wp-admin",          "medium",   "WordPress admin accessible"),
    ("/phpmyadmin",        "high",     "phpMyAdmin exposed"),
    ("/robots.txt",        "info",     "Robots.txt found"),
    ("/sitemap.xml",       "info",     "Sitemap found"),
    ("/.htaccess",         "medium",   "Apache config exposed"),
    ("/backup.zip",        "critical", "Backup archive exposed"),
    ("/backup.sql",        "critical", "Database backup exposed"),
    ("/db.sql",            "critical", "Database file exposed"),
    ("/server-status",     "high",     "Apache server-status exposed"),
    ("/api/v1",            "info",     "API endpoint found"),
    ("/api/v2",            "info",     "API endpoint found"),
    ("/swagger",           "medium",   "Swagger UI exposed"),
    ("/swagger-ui.html",   "medium",   "Swagger UI exposed"),
    ("/actuator",          "high",     "Spring Boot actuator exposed"),
    ("/console",           "high",     "Console endpoint exposed"),
]

# Tech fingerprints: header/html pattern → technology
TECH_FINGERPRINTS = [
    (r"wp-content|wp-includes|wordpress",   "WordPress",    "CMS"),
    (r"drupal",                              "Drupal",       "CMS"),
    (r"joomla",                              "Joomla",       "CMS"),
    (r"shopify",                             "Shopify",      "E-commerce"),
    (r"wix\.com",                            "Wix",          "Website Builder"),
    (r"squarespace",                         "Squarespace",  "Website Builder"),
    (r"x-powered-by.*php",                   "PHP",          "Language"),
    (r"x-powered-by.*asp\.net",              "ASP.NET",      "Framework"),
    (r"x-powered-by.*express",               "Express.js",   "Framework"),
    (r"server.*nginx",                       "Nginx",        "Web Server"),
    (r"server.*apache",                      "Apache",       "Web Server"),
    (r"server.*cloudflare",                  "Cloudflare",   "CDN/Proxy"),
    (r"server.*iis",                         "IIS",          "Web Server"),
    (r"react|__react",                       "React",        "Frontend"),
    (r"ng-version|angular",                  "Angular",      "Frontend"),
    (r"__vue",                               "Vue.js",       "Frontend"),
    (r"next\.js|__next",                     "Next.js",      "Framework"),
    (r"laravel",                             "Laravel",      "Framework"),
    (r"django",                              "Django",       "Framework"),
    (r"rails|ruby on rails",                 "Ruby on Rails","Framework"),
]


async def _check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


async def _check_subdomain(subdomain: str, domain: str, timeout: float = 3.0) -> Dict | None:
    """Check if a subdomain resolves."""
    fqdn = f"{subdomain}.{domain}"
    try:
        loop = asyncio.get_event_loop()
        ip = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyname, fqdn),
            timeout=timeout
        )
        return {"subdomain": fqdn, "ip": ip}
    except Exception:
        return None


async def _probe_path(base_url: str, path: str, severity: str, description: str) -> Dict | None:
    """Probe a URL path and return finding if accessible."""
    url = base_url.rstrip("/") + path
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=False,
                                      verify=False) as client:
            r = await client.get(url)
            if r.status_code in (200, 301, 302, 403):
                return {
                    "path": path,
                    "url": url,
                    "status_code": r.status_code,
                    "severity": severity,
                    "description": description,
                    "accessible": r.status_code == 200,
                }
    except Exception:
        pass
    return None


async def _get_dns_records(domain: str) -> Dict[str, List]:
    """Get DNS records using dnspython if available, else basic lookup."""
    records = {"A": [], "MX": [], "TXT": [], "NS": []}
    try:
        import dns.resolver
        for rtype in ["A", "MX", "TXT", "NS"]:
            try:
                answers = dns.resolver.resolve(domain, rtype, lifetime=5)
                records[rtype] = [str(r) for r in answers]
            except Exception:
                pass
    except ImportError:
        # Fallback: basic A record only
        try:
            loop = asyncio.get_event_loop()
            ip = await loop.run_in_executor(None, socket.gethostbyname, domain)
            records["A"] = [ip]
        except Exception:
            pass
    return records


def _detect_technologies(headers: Dict, html: str) -> List[Dict]:
    """Fingerprint technologies from headers and HTML."""
    techs = []
    combined = " ".join([
        " ".join(f"{k}: {v}" for k, v in headers.items()),
        html[:20000]
    ]).lower()

    seen = set()
    for pattern, name, category in TECH_FINGERPRINTS:
        if name not in seen and re.search(pattern, combined, re.IGNORECASE):
            techs.append({"name": name, "category": category})
            seen.add(name)
    return techs


def _check_email_security(txt_records: List[str]) -> List[Dict]:
    """Check SPF, DMARC, DKIM from TXT records."""
    findings = []
    txt_combined = " ".join(txt_records).lower()

    # SPF
    if "v=spf1" in txt_combined:
        findings.append({"check": "SPF Record", "status": "pass", "detail": "SPF record found — email spoofing protection active"})
    else:
        findings.append({"check": "SPF Record", "status": "fail", "detail": "No SPF record — domain vulnerable to email spoofing"})

    # DMARC
    if "v=dmarc1" in txt_combined:
        findings.append({"check": "DMARC Record", "status": "pass", "detail": "DMARC policy found — email authentication enforced"})
    else:
        findings.append({"check": "DMARC Record", "status": "fail", "detail": "No DMARC record — phishing emails can spoof this domain"})

    return findings


async def run_attack_surface_discovery(url: str) -> Dict[str, Any]:
    """
    Main entry point. Returns full attack surface report.
    """
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    result: Dict[str, Any] = {
        "domain": domain,
        "open_ports": [],
        "subdomains": [],
        "exposed_paths": [],
        "dns_records": {},
        "technologies": [],
        "email_security": [],
        "summary": {},
    }

    # Run all checks concurrently
    port_task      = asyncio.create_task(_scan_ports(domain))
    subdomain_task = asyncio.create_task(_scan_subdomains(domain))
    paths_task     = asyncio.create_task(_scan_paths(base_url))
    dns_task       = asyncio.create_task(_get_dns_records(domain))
    tech_task      = asyncio.create_task(_fingerprint_tech(url))

    open_ports, subdomains, exposed_paths, dns_records, tech_data = await asyncio.gather(
        port_task, subdomain_task, paths_task, dns_task, tech_task,
        return_exceptions=True
    )

    result["open_ports"]    = open_ports    if not isinstance(open_ports, Exception)    else []
    result["subdomains"]    = subdomains    if not isinstance(subdomains, Exception)    else []
    result["exposed_paths"] = exposed_paths if not isinstance(exposed_paths, Exception) else []
    result["dns_records"]   = dns_records   if not isinstance(dns_records, Exception)   else {}
    result["technologies"]  = tech_data.get("technologies", []) if not isinstance(tech_data, Exception) else []

    # Email security from TXT records
    txt = result["dns_records"].get("TXT", [])
    result["email_security"] = _check_email_security(txt)

    # Summary counts
    critical_paths = [p for p in result["exposed_paths"] if p["severity"] == "critical"]
    high_paths     = [p for p in result["exposed_paths"] if p["severity"] == "high"]
    result["summary"] = {
        "open_ports_count":    len(result["open_ports"]),
        "subdomains_found":    len(result["subdomains"]),
        "exposed_paths_count": len(result["exposed_paths"]),
        "critical_exposures":  len(critical_paths),
        "high_exposures":      len(high_paths),
        "technologies_found":  len(result["technologies"]),
    }

    logger.info("attack_surface_done", domain=domain, summary=result["summary"])
    return result


async def _scan_ports(host: str) -> List[Dict]:
    tasks = [_check_port(host, p) for p in COMMON_PORTS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    open_ports = []
    for port, is_open in zip(COMMON_PORTS, results):
        if is_open is True:
            service = {80:"HTTP", 443:"HTTPS", 22:"SSH", 21:"FTP", 25:"SMTP",
                       3306:"MySQL", 5432:"PostgreSQL", 6379:"Redis",
                       27017:"MongoDB", 8080:"HTTP-Alt", 8443:"HTTPS-Alt"}.get(port, "Unknown")
            risk = "high" if port in (22, 21, 25, 3306, 5432, 6379, 27017) else "info"
            open_ports.append({"port": port, "service": service, "risk": risk})
    return open_ports


async def _scan_subdomains(domain: str) -> List[Dict]:
    tasks = [_check_subdomain(sub, domain) for sub in COMMON_SUBDOMAINS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if r and not isinstance(r, Exception)]


async def _scan_paths(base_url: str) -> List[Dict]:
    tasks = [_probe_path(base_url, path, sev, desc) for path, sev, desc in SENSITIVE_PATHS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if r and not isinstance(r, Exception)]


async def _fingerprint_tech(url: str) -> Dict:
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True, verify=False) as client:
            r = await client.get(url)
            techs = _detect_technologies(dict(r.headers), r.text)
            return {"technologies": techs}
    except Exception:
        return {"technologies": []}

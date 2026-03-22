"""
SecureScout Scanner Engine
Performs actual security checks against target URLs.
Checks: HTTP headers, SSL/TLS, XSS indicators, server info leakage, etc.
"""

import asyncio
import ssl
import socket
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse
import httpx
import certifi
import structlog

logger = structlog.get_logger()

# ── Security Headers that MUST be present ────────────────────────────────────

REQUIRED_SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "severity": "high",
        "description": "HSTS not set. Browsers won't enforce HTTPS connections.",
        "recommendation": "Add: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
    },
    "Content-Security-Policy": {
        "severity": "high",
        "description": "No CSP found. XSS and data injection attacks are easier.",
        "recommendation": "Define a Content-Security-Policy header to restrict resource loading.",
    },
    "X-Content-Type-Options": {
        "severity": "medium",
        "description": "Missing X-Content-Type-Options. MIME-type sniffing attacks possible.",
        "recommendation": "Add: X-Content-Type-Options: nosniff",
    },
    "X-Frame-Options": {
        "severity": "medium",
        "description": "Missing X-Frame-Options. Site may be vulnerable to clickjacking.",
        "recommendation": "Add: X-Frame-Options: DENY or SAMEORIGIN",
    },
    "X-XSS-Protection": {
        "severity": "low",
        "description": "X-XSS-Protection not set. Legacy XSS filter won't activate.",
        "recommendation": "Add: X-XSS-Protection: 1; mode=block",
    },
    "Referrer-Policy": {
        "severity": "low",
        "description": "No Referrer-Policy. Full URL may leak to third parties.",
        "recommendation": "Add: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "Permissions-Policy": {
        "severity": "low",
        "description": "No Permissions-Policy. Browser features may be accessible unnecessarily.",
        "recommendation": "Add Permissions-Policy to restrict camera, microphone, geolocation, etc.",
    },
}

# Headers that should NOT expose sensitive data
SENSITIVE_HEADERS = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator"]

# Basic XSS-prone patterns in HTML source
XSS_PATTERNS = [
    ("document.write(", "Dangerous document.write() usage detected"),
    ("innerHTML =", "Unsanitized innerHTML assignment found"),
    ("eval(", "eval() usage detected — potential code injection"),
    ("onmouseover=", "Inline event handler (onmouseover) found"),
    ("javascript:void", "JavaScript pseudo-protocol in links"),
]


class ScannerEngine:
    """Core scanning engine. All checks are async."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    async def full_scan(self, url: str) -> Dict[str, Any]:
        """
        Run all checks against a URL. Returns structured findings dict.
        This is the main entry point called by the scan service.
        """
        start_time = time.monotonic()
        results = {
            "url": url,
            "raw_findings": [],
            "vulnerabilities": [],
            "ssl_valid": None,
            "ssl_expiry_days": None,
            "server_header": None,
            "response_time_ms": None,
        }

        try:
            # 1. Fetch the page (with timing)
            fetch_start = time.monotonic()
            response_data = await self._fetch_url(url)
            results["response_time_ms"] = int((time.monotonic() - fetch_start) * 1000)

            if response_data is None:
                results["raw_findings"].append({
                    "check": "URL Reachability",
                    "status": "fail",
                    "detail": "Could not reach the target URL. It may be down or unreachable.",
                })
                return results

            headers, html_content, status_code, final_url = response_data

            # 2. Security headers check
            header_findings, header_vulns = self._check_security_headers(headers)
            results["raw_findings"].extend(header_findings)
            results["vulnerabilities"].extend(header_vulns)

            # 3. Sensitive header leakage
            leak_findings, leak_vulns = self._check_header_leakage(headers)
            results["raw_findings"].extend(leak_findings)
            results["vulnerabilities"].extend(leak_vulns)
            results["server_header"] = headers.get("Server", headers.get("server"))

            # 4. SSL/TLS check
            ssl_findings, ssl_vulns, ssl_valid, ssl_days = await self._check_ssl(url)
            results["raw_findings"].extend(ssl_findings)
            results["vulnerabilities"].extend(ssl_vulns)
            results["ssl_valid"] = ssl_valid
            results["ssl_expiry_days"] = ssl_days

            # 5. HTTP → HTTPS redirect check
            redirect_findings = self._check_http_redirect(url, final_url)
            results["raw_findings"].extend(redirect_findings)

            # 6. Basic XSS pattern check in source
            xss_findings, xss_vulns = self._check_xss_patterns(html_content or "")
            results["raw_findings"].extend(xss_findings)
            results["vulnerabilities"].extend(xss_vulns)

            # 7. Cookie security check
            cookie_findings, cookie_vulns = self._check_cookies(headers)
            results["raw_findings"].extend(cookie_findings)
            results["vulnerabilities"].extend(cookie_vulns)

            # 8. Mixed content check
            mixed_findings = self._check_mixed_content(html_content or "", url)
            results["raw_findings"].extend(mixed_findings)

        except Exception as e:
            logger.error("scanner_error", url=url, error=str(e))
            results["raw_findings"].append({
                "check": "Scanner Error",
                "status": "warning",
                "detail": f"Partial scan — some checks could not complete: {str(e)[:200]}",
            })

        results["scan_duration_ms"] = int((time.monotonic() - start_time) * 1000)
        return results

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _fetch_url(self, url: str) -> Optional[Tuple]:
        """Fetch URL with httpx. Returns (headers, html, status_code, final_url)."""
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self.timeout,
                verify=certifi.where(),
                headers={"User-Agent": "SecureScout/1.0 Security Scanner"},
            ) as client:
                response = await client.get(url)
                html = response.text[:50000]  # Limit HTML to 50KB for XSS checks
                return dict(response.headers), html, response.status_code, str(response.url)
        except httpx.ConnectError:
            return None
        except httpx.TimeoutException:
            return None
        except Exception as e:
            logger.warning("fetch_error", url=url, error=str(e))
            return None

    def _check_security_headers(self, headers: Dict) -> Tuple[List, List]:
        """Check presence of required security headers."""
        findings = []
        vulns = []
        # Normalize header keys to title-case for lookup
        header_keys_lower = {k.lower(): v for k, v in headers.items()}

        for header_name, info in REQUIRED_SECURITY_HEADERS.items():
            present = header_name.lower() in header_keys_lower

            findings.append({
                "check": f"Security Header: {header_name}",
                "status": "pass" if present else "fail",
                "detail": "Header present" if present else info["description"],
            })

            if not present:
                vulns.append({
                    "name": f"Missing {header_name}",
                    "severity": info["severity"],
                    "description": info["description"],
                    "recommendation": info["recommendation"],
                    "references": [
                        "https://owasp.org/www-project-secure-headers/",
                        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers",
                    ],
                })

        return findings, vulns

    def _check_header_leakage(self, headers: Dict) -> Tuple[List, List]:
        """Check if sensitive server info is leaked in headers."""
        findings = []
        vulns = []
        header_keys_lower = {k.lower(): v for k, v in headers.items()}

        for h in SENSITIVE_HEADERS:
            value = header_keys_lower.get(h.lower())
            if value:
                findings.append({
                    "check": f"Header Leakage: {h}",
                    "status": "fail",
                    "detail": f"{h}: {value} — exposes server technology stack",
                })
                vulns.append({
                    "name": f"Server Information Disclosure ({h})",
                    "severity": "low",
                    "description": f"The header '{h}: {value}' reveals server technology, helping attackers fingerprint the stack.",
                    "recommendation": f"Remove or obfuscate the '{h}' response header in your server configuration.",
                    "references": [
                        "https://owasp.org/www-project-web-security-testing-guide/v42/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server"
                    ],
                })
            else:
                findings.append({
                    "check": f"Header Leakage: {h}",
                    "status": "pass",
                    "detail": f"{h} not exposed",
                })

        return findings, vulns

    async def _check_ssl(self, url: str) -> Tuple[List, List, Optional[bool], Optional[int]]:
        """Check SSL certificate validity and expiry."""
        findings = []
        vulns = []
        ssl_valid = None
        expiry_days = None

        parsed = urlparse(url)
        if parsed.scheme != "https":
            findings.append({
                "check": "SSL/TLS Certificate",
                "status": "fail",
                "detail": "Site does not use HTTPS at all.",
            })
            vulns.append({
                "name": "No HTTPS / SSL",
                "severity": "critical",
                "description": "The site uses plain HTTP. All traffic is unencrypted and visible to attackers.",
                "recommendation": "Obtain and install an SSL/TLS certificate (free via Let's Encrypt) and redirect all HTTP to HTTPS.",
                "references": ["https://letsencrypt.org/", "https://ssl.labs.com/"],
            })
            return findings, vulns, False, None

        hostname = parsed.hostname
        port = parsed.port or 443

        try:
            loop = asyncio.get_event_loop()
            cert_info = await loop.run_in_executor(
                None, self._get_cert_info, hostname, port
            )

            if cert_info:
                ssl_valid = cert_info["valid"]
                expiry_days = cert_info["days_remaining"]

                if not ssl_valid:
                    findings.append({
                        "check": "SSL/TLS Certificate",
                        "status": "fail",
                        "detail": "SSL certificate is invalid or expired.",
                    })
                    vulns.append({
                        "name": "Invalid/Expired SSL Certificate",
                        "severity": "critical",
                        "description": "The SSL certificate is expired or invalid. Users will see browser warnings.",
                        "recommendation": "Renew your SSL certificate immediately. Consider Let's Encrypt for free auto-renewal.",
                        "references": ["https://letsencrypt.org/"],
                    })
                elif expiry_days and expiry_days < 30:
                    findings.append({
                        "check": "SSL/TLS Certificate",
                        "status": "warning",
                        "detail": f"SSL certificate expires in {expiry_days} days.",
                    })
                    vulns.append({
                        "name": "SSL Certificate Expiring Soon",
                        "severity": "medium",
                        "description": f"SSL certificate expires in {expiry_days} days. Site will become insecure.",
                        "recommendation": "Renew your SSL certificate before it expires.",
                        "references": [],
                    })
                else:
                    findings.append({
                        "check": "SSL/TLS Certificate",
                        "status": "pass",
                        "detail": f"Valid certificate. Expires in {expiry_days} days.",
                    })
            else:
                findings.append({
                    "check": "SSL/TLS Certificate",
                    "status": "warning",
                    "detail": "Could not retrieve SSL certificate details.",
                })

        except Exception as e:
            findings.append({
                "check": "SSL/TLS Certificate",
                "status": "warning",
                "detail": f"SSL check error: {str(e)[:100]}",
            })

        return findings, vulns, ssl_valid, expiry_days

    def _get_cert_info(self, hostname: str, port: int) -> Optional[Dict]:
        """Blocking SSL cert check (run in executor)."""
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    not_after = cert.get("notAfter")
                    if not_after:
                        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        expiry = expiry.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        days_remaining = (expiry - now).days
                        return {
                            "valid": days_remaining > 0,
                            "days_remaining": days_remaining,
                            "subject": dict(x[0] for x in cert.get("subject", [])),
                        }
        except ssl.SSLCertVerificationError:
            return {"valid": False, "days_remaining": None}
        except Exception:
            return None

    def _check_http_redirect(self, original_url: str, final_url: str) -> List:
        """Check if HTTP properly redirects to HTTPS."""
        findings = []
        if original_url.startswith("https://"):
            # Already HTTPS — check passes
            findings.append({
                "check": "HTTPS Redirect",
                "status": "pass",
                "detail": "Site is accessed over HTTPS.",
            })
        elif final_url.startswith("https://"):
            findings.append({
                "check": "HTTPS Redirect",
                "status": "pass",
                "detail": "HTTP redirects to HTTPS correctly.",
            })
        else:
            findings.append({
                "check": "HTTPS Redirect",
                "status": "fail",
                "detail": "HTTP does not redirect to HTTPS.",
            })
        return findings

    def _check_xss_patterns(self, html: str) -> Tuple[List, List]:
        """Scan HTML source for basic XSS-prone patterns."""
        findings = []
        vulns = []

        for pattern, description in XSS_PATTERNS:
            if pattern.lower() in html.lower():
                findings.append({
                    "check": f"XSS Pattern: {pattern}",
                    "status": "warning",
                    "detail": description,
                })
                vulns.append({
                    "name": f"Potential XSS Vector: {pattern}",
                    "severity": "medium",
                    "description": f"Found '{pattern}' in page source. {description}. If user input reaches this, XSS is possible.",
                    "recommendation": "Sanitize all user inputs before use in DOM operations. Use textContent instead of innerHTML. Avoid eval().",
                    "references": [
                        "https://owasp.org/www-community/attacks/xss/",
                        "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
                    ],
                })
            else:
                findings.append({
                    "check": f"XSS Pattern: {pattern}",
                    "status": "pass",
                    "detail": f"Pattern '{pattern}' not found",
                })

        return findings, vulns

    def _check_cookies(self, headers: Dict) -> Tuple[List, List]:
        """Check Set-Cookie headers for Secure and HttpOnly flags."""
        findings = []
        vulns = []
        header_keys_lower = {k.lower(): v for k, v in headers.items()}
        cookie_header = header_keys_lower.get("set-cookie", "")

        if not cookie_header:
            findings.append({
                "check": "Cookie Security",
                "status": "pass",
                "detail": "No cookies set on this response.",
            })
            return findings, vulns

        cookie_str = str(cookie_header).lower()

        # Check Secure flag
        if "secure" not in cookie_str:
            findings.append({
                "check": "Cookie: Secure Flag",
                "status": "fail",
                "detail": "Cookie missing 'Secure' flag — sent over HTTP too.",
            })
            vulns.append({
                "name": "Cookie Missing Secure Flag",
                "severity": "medium",
                "description": "Session cookies are set without the Secure flag, meaning they can be sent over unencrypted HTTP connections.",
                "recommendation": "Add the 'Secure' attribute to all sensitive cookies: Set-Cookie: session=abc; Secure; HttpOnly",
                "references": ["https://owasp.org/www-community/controls/SecureCookieAttribute"],
            })
        else:
            findings.append({"check": "Cookie: Secure Flag", "status": "pass", "detail": "Secure flag present"})

        # Check HttpOnly flag
        if "httponly" not in cookie_str:
            findings.append({
                "check": "Cookie: HttpOnly Flag",
                "status": "fail",
                "detail": "Cookie missing 'HttpOnly' flag — accessible via JavaScript.",
            })
            vulns.append({
                "name": "Cookie Missing HttpOnly Flag",
                "severity": "medium",
                "description": "Cookies without HttpOnly can be stolen by XSS attacks via document.cookie.",
                "recommendation": "Add 'HttpOnly' to all session cookies: Set-Cookie: session=abc; Secure; HttpOnly; SameSite=Strict",
                "references": ["https://owasp.org/www-community/HttpOnly"],
            })
        else:
            findings.append({"check": "Cookie: HttpOnly Flag", "status": "pass", "detail": "HttpOnly flag present"})

        return findings, vulns

    def _check_mixed_content(self, html: str, url: str) -> List:
        """Check for HTTP resources loaded on HTTPS pages."""
        findings = []
        if not url.startswith("https://"):
            return findings

        # Simple heuristic: look for http:// in src/href attributes
        import re
        http_resources = re.findall(r'(?:src|href)=["\']http://[^"\']+["\']', html, re.IGNORECASE)

        if http_resources:
            count = len(http_resources)
            findings.append({
                "check": "Mixed Content",
                "status": "fail",
                "detail": f"Found {count} HTTP resource(s) on HTTPS page. Mixed content degrades security.",
            })
        else:
            findings.append({
                "check": "Mixed Content",
                "status": "pass",
                "detail": "No obvious mixed content (HTTP on HTTPS) detected.",
            })

        return findings


def calculate_risk_score(vulnerabilities: List[Dict]) -> float:
    """
    Calculate a 0–100 risk score based on vulnerability severities.
    Higher = more risky.
    """
    if not vulnerabilities:
        return 5.0  # Baseline — no perfect score without audit

    severity_weights = {
        "critical": 25,
        "high": 15,
        "medium": 7,
        "low": 2,
    }

    total_score = sum(
        severity_weights.get(v.get("severity", "low"), 2)
        for v in vulnerabilities
    )

    # Cap at 100
    return min(round(total_score, 1), 100.0)


def get_overall_severity(risk_score: float) -> str:
    """Map risk score to overall severity label."""
    if risk_score >= 70:
        return "critical"
    elif risk_score >= 45:
        return "high"
    elif risk_score >= 20:
        return "medium"
    else:
        return "low"

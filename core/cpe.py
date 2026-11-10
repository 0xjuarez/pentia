import re
from typing import Optional


def _tokens(text: str) -> set[str]:
    """Lowercase alphanumeric tokens of a string (word match, not substring)."""
    return set(re.split(r"[^a-z0-9]+", text.lower()))


def version_to_cpe(software: str, name: str, version: str) -> str:
    """Build a simple CPE 2.3 string. This is heuristic and may need manual correction.

    Example: version_to_cpe("apache", "http_server", "2.4.49") ->
        cpe:2.3:a:apache:http_server:2.4.49
    """
    vendor = software.lower().replace(" ", "_")
    product = name.lower().replace(" ", "_")
    ver = version.strip()
    return f"cpe:2.3:a:{vendor}:{product}:{ver}"


def detect_cpe_from_service(service: str, version: Optional[str] = None) -> Optional[str]:
    """Basic mapping from common service strings to probable CPE product names.

    This function is intentionally simple; for production use integrate a CPE dictionary or use official CPE matching.
    """
    s = service.lower()
    if "apache" in s or "httpd" in s:
        product = "http_server"
    elif "nginx" in s:
        product = "nginx"
    elif "iis" in s or "microsoft-iis" in s:
        product = "iis"
    elif "wordpress" in s or "wp" in _tokens(s):
        product = "wordpress"
    else:
        # fallback: try to split first word as product
        product = s.split()[0] if s.split() else "unknown"

    # Build a CPE even when no version is known ("*" = any version).
    return version_to_cpe(service.split()[0] if service.split() else "unknown", product, version or "*")

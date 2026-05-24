from typing import Optional


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
    elif "wordpress" in s or "wp" in s:
        product = "wordpress"
    else:
        # fallback: try to split first word as product
        product = s.split()[0]

    if version:
        return version_to_cpe(service.split()[0], product, version)
    return None

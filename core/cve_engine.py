import requests
from typing import Dict, List, Optional

NVD_SEARCH_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def search_cves_by_cpe(cpe: str, api_key: Optional[str] = None) -> Dict:
    params = {"cpeName": cpe}
    headers = {"User-Agent": "pentia-cve-engine/1.0"}
    if api_key:
        headers["apiKey"] = api_key

    resp = requests.get(NVD_SEARCH_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_nvd_item(item: Dict) -> Dict:
    # Extract common fields with safety checks
    cve_meta = item.get("cve", {})
    cve_id = cve_meta.get("CVE_data_meta", {}).get("ID")

    description = ""
    for d in cve_meta.get("description", {}).get("description_data", []):
        if d.get("lang") == "en":
            description = d.get("value", "")
            break

    # CVSS extraction
    impact = item.get("impact", {})
    base = impact.get("baseMetricV3") or impact.get("baseMetricV2") or {}
    cvss = None
    severity = None
    if base:
        cvss = base.get("cvssV3", {}).get("baseScore") if isinstance(base.get("cvssV3"), dict) else base.get("baseScore")
        severity = base.get("cvssV3", {}).get("baseSeverity") if isinstance(base.get("cvssV3"), dict) else base.get("severity")

    references = [r.get("url") for r in cve_meta.get("references", {}).get("reference_data", []) if r.get("url")]

    return {
        "id": cve_id,
        "cvss": cvss,
        "severity": severity,
        "description": description,
        "references": references,
    }


def lookup_cves_for_cpe(cpe: str, api_key: Optional[str] = None) -> List[Dict]:
    data = search_cves_by_cpe(cpe, api_key=api_key)
    items = data.get("vulnerabilities") or data.get("CVE_Items") or []
    parsed = []
    # NVD v2 response uses 'vulnerabilities' top-level key
    for it in items:
        # item may be wrapped under 'cve' key
        candidate = it.get("cve") if isinstance(it, dict) and "cve" in it else it
        parsed.append(parse_nvd_item(candidate if candidate else it))
    return parsed

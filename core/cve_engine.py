import requests
from typing import Dict, List, Optional

NVD_SEARCH_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def search_cves_by_cpe(cpe: str, api_key: Optional[str] = None) -> Dict:
    params = {"cpeName": cpe, "resultsPerPage": 2000}
    headers = {"User-Agent": "pentia-cve-engine/1.0"}
    if api_key:
        headers["apiKey"] = api_key

    resp = requests.get(NVD_SEARCH_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _extract_cvss_v2(cve: Dict) -> tuple:
    """CVSS/severity from an NVD 2.0 ``metrics`` block (or None, None)."""
    metrics = cve.get("metrics") or {}
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key) or []
        if entries:
            data = entries[0].get("cvssData") or {}
            return data.get("baseScore"), data.get("baseSeverity")
    return None, None


def _extract_cvss_v1(item: Dict) -> tuple:
    """CVSS/severity from a legacy NVD 1.x ``impact`` block (or None, None)."""
    impact = item.get("impact") or {}
    base = impact.get("baseMetricV3") or impact.get("baseMetricV2") or {}
    if not base:
        return None, None
    cvss_v3 = base.get("cvssV3")
    if isinstance(cvss_v3, dict):
        return cvss_v3.get("baseScore"), cvss_v3.get("baseSeverity")
    return base.get("baseScore"), base.get("severity")


def parse_nvd_item(item: Dict) -> Dict:
    """Parse one NVD item, NVD 2.0 schema first, 1.x schema as fallback.

    NVD 2.0 items look like ``{"cve": {"id": ..., "descriptions": [...],
    "metrics": {...}, "references": [...]}}``. Legacy 1.x items carry
    ``CVE_data_meta`` / ``description_data`` / ``impact.baseMetricV3``.
    ``item`` may also be the bare ``cve`` dict itself.
    """
    if not isinstance(item, dict):
        return {"id": None, "cvss": None, "severity": None, "description": "", "references": []}

    # NVD 2.0 wraps the CVE object under "cve"; a bare cve dict has "id".
    cve = item.get("cve") if isinstance(item.get("cve"), dict) else item

    # --- ID: 2.0 first, then 1.x ---
    cve_id = cve.get("id")
    if not cve_id:
        cve_id = (cve.get("CVE_data_meta") or {}).get("ID")

    # --- Description: 2.0 "descriptions" list, then 1.x description_data ---
    description = ""
    descriptions = cve.get("descriptions")
    if isinstance(descriptions, list):
        for d in descriptions:
            if isinstance(d, dict) and d.get("lang") == "en":
                description = d.get("value", "")
                break
        if not description and descriptions:
            first = descriptions[0]
            if isinstance(first, dict):
                description = first.get("value", "")
    if not description:
        desc_block = cve.get("description") or {}
        for d in desc_block.get("description_data", []) or []:
            if isinstance(d, dict) and d.get("lang") == "en":
                description = d.get("value", "")
                break

    # --- CVSS/severity: 2.0 metrics first, then 1.x impact ---
    cvss, severity = _extract_cvss_v2(cve)
    if cvss is None:
        cvss, severity = _extract_cvss_v1(item if "cve" in item else cve)

    # --- References: 2.0 list of {"url": ...}, then 1.x reference_data ---
    references = []
    refs = cve.get("references")
    if isinstance(refs, list):
        references = [r.get("url") for r in refs if isinstance(r, dict) and r.get("url")]
    if not references:
        ref_block = cve.get("references") or {}
        references = [
            r.get("url")
            for r in ref_block.get("reference_data", []) or []
            if isinstance(r, dict) and r.get("url")
        ]

    return {
        "id": cve_id,
        "cvss": cvss,
        "severity": severity,
        "description": description,
        "references": references,
    }


def lookup_cves_for_cpe(cpe: str, api_key: Optional[str] = None) -> List[Dict]:
    data = search_cves_by_cpe(cpe, api_key=api_key)
    # NVD 2.0 uses "vulnerabilities"; legacy feeds use "CVE_Items".
    items = data.get("vulnerabilities") or data.get("CVE_Items") or []
    return [parse_nvd_item(it) for it in items if isinstance(it, dict)]

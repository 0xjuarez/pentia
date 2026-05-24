import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from .cpe import detect_cpe_from_service
from .cve_engine import lookup_cves_for_cpe
from .cache import load_nvd_cache, save_nvd_cache, save_findings


KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def load_kev(local_path: Optional[str] = None) -> Dict[str, Any]:
    if local_path and os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        import requests
        r = requests.get(KEV_URL, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def is_in_kev(cve_id: str, kev_data: Dict[str, Any]) -> bool:
    items = kev_data.get("vulnerabilities") or kev_data.get("vulnerabilities", [])
    for it in items:
        if it.get("cveID") == cve_id:
            return True
    return False


async def correlate_exploitdb(cve_id: str, exploitdb_dir: Optional[str] = None) -> bool:
    # Simple local search in datasets/exploits for lines containing the CVE
    base = exploitdb_dir or os.path.join(os.path.dirname(__file__), "..", "datasets", "exploits")
    found = False
    if not os.path.isdir(base):
        return False
    for root, _, files in os.walk(base):
        for f in files:
            try:
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    for line in handle:
                        if cve_id in line:
                            return True
            except Exception:
                continue
    return found


async def correlate_nuclei(cve_id: str, nuclei_dir: Optional[str] = None) -> Optional[str]:
    base = nuclei_dir or os.path.join(os.path.dirname(__file__), "..", "datasets", "nuclei")
    if not os.path.isdir(base):
        return None
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".yaml") or f.endswith(".yml"):
                try:
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                        content = handle.read()
                        if cve_id in content:
                            # return relative path
                            rel = os.path.relpath(path, os.path.join(os.path.dirname(__file__), ".."))
                            return rel
                except Exception:
                    continue
    return None


async def correlate_metasploit(cve_id: str) -> bool:
    # Placeholder: real integration would query local msf db or resources
    return False


async def enrich_service(target: str, service: str, version: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Given a detected service and optional version, return enriched findings and save them in cache."""
    findings: Dict[str, Any] = {
        "target": target,
        "service": service,
        "version": version,
        "port": None,
        "protocol": "tcp",
        "cpe": None,
        "cves": [],
    }

    cpe = detect_cpe_from_service(service, version)
    findings["cpe"] = cpe

    nvd_cache = load_nvd_cache()

    cves = []
    if cpe:
        if cpe in nvd_cache:
            cves = nvd_cache[cpe]
        else:
            try:
                cves = lookup_cves_for_cpe(cpe, api_key=api_key)
            except Exception:
                cves = []
            nvd_cache[cpe] = cves
            save_nvd_cache(nvd_cache)

    # KEV
    kev = load_kev()

    # Correlate per CVE
    for c in cves:
        cve_id = c.get("id")
        if not cve_id:
            continue
        kev_flag = is_in_kev(cve_id, kev)
        exploitdb_flag = await correlate_exploitdb(cve_id)
        nuclei_template = await correlate_nuclei(cve_id)
        metasploit_flag = await correlate_metasploit(cve_id)

        c_entry = {
            "id": cve_id,
            "cvss": c.get("cvss"),
            "severity": c.get("severity"),
            "description": c.get("description"),
            "kev": kev_flag,
            "exploit_available": exploitdb_flag,
            "metasploit": metasploit_flag,
            "nuclei_template": nuclei_template,
            "references": c.get("references", []),
        }
        findings["cves"].append(c_entry)

    # Save findings to cache
    save_path = save_findings(target.replace("/", "_"), findings)
    findings["_cache_path"] = save_path
    return findings

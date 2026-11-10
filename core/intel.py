import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from .cpe import detect_cpe_from_service
from .cve_engine import lookup_cves_for_cpe
from .cache import load_nvd_cache, save_nvd_cache, save_findings

logger = logging.getLogger("pentia.intel")

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")


KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

# In-memory KEV cache: the feed used to be re-fetched from the network on
# every enrich_service() call. TTL is 1 hour.
KEV_TTL_SECONDS = 3600
_KEV_CACHE: Dict[str, Any] = {"data": None, "fetched_at": 0.0, "ids": set()}


def load_kev(local_path: Optional[str] = None) -> Dict[str, Any]:
    if local_path and os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)

    now = time.monotonic()
    if _KEV_CACHE["data"] is not None and now - _KEV_CACHE["fetched_at"] < KEV_TTL_SECONDS:
        return _KEV_CACHE["data"]

    try:
        import requests
        r = requests.get(KEV_URL, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning(f"Could not load CISA KEV feed ({e}); continuing without KEV data")
        return _KEV_CACHE["data"] if _KEV_CACHE["data"] is not None else {}

    _KEV_CACHE["data"] = data
    _KEV_CACHE["fetched_at"] = now
    _KEV_CACHE["ids"] = {
        it.get("cveID")
        for it in (data.get("vulnerabilities") or [])
        if isinstance(it, dict) and it.get("cveID")
    }
    return data


def is_in_kev(cve_id: str, kev_data: Dict[str, Any]) -> bool:
    # O(1) lookup when kev_data is the cached feed; otherwise fall back to
    # building a set from the supplied dict (still O(n) once, not per CVE
    # scan of the raw list — the set is rebuilt only for a new dict object).
    if kev_data is _KEV_CACHE["data"] and _KEV_CACHE["ids"]:
        return cve_id in _KEV_CACHE["ids"]
    items = kev_data.get("vulnerabilities") or []
    return any(
        isinstance(it, dict) and it.get("cveID") == cve_id for it in items
    )


def _build_exploitdb_index(base: str) -> set:
    """Index the ExploitDB dataset dir once: set of CVE ids mentioned."""
    found = set()
    if not os.path.isdir(base):
        return found
    for root, _, files in os.walk(base):
        for f in files:
            try:
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                    for line in handle:
                        found.update(_CVE_RE.findall(line))
            except Exception:
                continue
    return found


def _build_nuclei_index(base: str) -> Dict[str, str]:
    """Index the Nuclei templates dir once: CVE id -> relative template path."""
    index: Dict[str, str] = {}
    if not os.path.isdir(base):
        return index
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".yaml") or f.endswith(".yml"):
                try:
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                        content = handle.read()
                    rel = os.path.relpath(path, os.path.join(os.path.dirname(__file__), ".."))
                    for cve_id in _CVE_RE.findall(content):
                        index.setdefault(cve_id, rel)
                except Exception:
                    continue
    return index


async def correlate_exploitdb(cve_id: str, exploitdb_dir: Optional[str] = None, _index: Optional[set] = None) -> bool:
    # Simple local search in datasets/exploits for the CVE id. Callers that
    # check many CVEs should build the index once via
    # _build_exploitdb_index() and pass it in; otherwise it is built here.
    base = exploitdb_dir or os.path.join(os.path.dirname(__file__), "..", "datasets", "exploits")
    if not os.path.isdir(base):
        return False
    index = _index if _index is not None else _build_exploitdb_index(base)
    return cve_id in index


async def correlate_nuclei(cve_id: str, nuclei_dir: Optional[str] = None, _index: Optional[Dict[str, str]] = None) -> Optional[str]:
    base = nuclei_dir or os.path.join(os.path.dirname(__file__), "..", "datasets", "nuclei")
    if not os.path.isdir(base):
        return None
    index = _index if _index is not None else _build_nuclei_index(base)
    return index.get(cve_id)


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
            except Exception as e:
                logger.warning(f"NVD lookup for {cpe} failed ({e}); continuing without CVEs")
                cves = []
            nvd_cache[cpe] = cves
            save_nvd_cache(nvd_cache)

    # KEV
    kev = load_kev()

    # Index each dataset dir once and reuse the indexes for all CVEs.
    exploitdb_base = os.path.join(os.path.dirname(__file__), "..", "datasets", "exploits")
    nuclei_base = os.path.join(os.path.dirname(__file__), "..", "datasets", "nuclei")
    exploitdb_index = _build_exploitdb_index(exploitdb_base)
    nuclei_index = _build_nuclei_index(nuclei_base)

    # Correlate per CVE
    for c in cves:
        cve_id = c.get("id")
        if not cve_id:
            continue
        kev_flag = is_in_kev(cve_id, kev)
        exploitdb_flag = await correlate_exploitdb(cve_id, _index=exploitdb_index)
        nuclei_template = await correlate_nuclei(cve_id, _index=nuclei_index)
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

    # Save findings to cache (filename is sanitized inside save_findings).
    save_path = save_findings(target, findings)
    findings["_cache_path"] = save_path
    return findings

import json
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_DIR = Path("/home/venus/ai/pentia/cache")
FINDINGS_DIR = CACHE_DIR / "findings"
NVD_CACHE = CACHE_DIR / "nvd_cache.json"


def ensure_dirs():
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_nvd_cache() -> Dict[str, Any]:
    ensure_dirs()
    if not NVD_CACHE.exists():
        NVD_CACHE.write_text(json.dumps({}), encoding="utf-8")
    return json.loads(NVD_CACHE.read_text(encoding="utf-8"))


def save_nvd_cache(cache: Dict[str, Any]):
    ensure_dirs()
    NVD_CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def save_findings(target: str, data: Dict[str, Any]):
    ensure_dirs()
    path = FINDINGS_DIR / f"{target}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)


def load_findings(target: str) -> Optional[Dict[str, Any]]:
    ensure_dirs()
    path = FINDINGS_DIR / f"{target}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .validation import sanitize_filename

logger = logging.getLogger("pentia.cache")

# Cache location is configurable via PENTIA_CACHE_DIR; the default lives
# under the current user's home directory (never a hardcoded /home/<user>).
CACHE_DIR = Path(os.environ.get("PENTIA_CACHE_DIR") or Path.home() / ".pentia" / "cache")
FINDINGS_DIR = CACHE_DIR / "findings"
NVD_CACHE = CACHE_DIR / "nvd_cache.json"


def ensure_dirs():
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write(path: Path, text: str) -> None:
    """Write via a temp file in the same directory + os.replace (atomic)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def load_nvd_cache() -> Dict[str, Any]:
    ensure_dirs()
    if not NVD_CACHE.exists():
        _atomic_write(NVD_CACHE, json.dumps({}))
    try:
        return json.loads(NVD_CACHE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        # A corrupt cache must not crash every CVE enrichment.
        logger.warning(f"Corrupt NVD cache at {NVD_CACHE} ({e}); starting with an empty cache")
        return {}


def save_nvd_cache(cache: Dict[str, Any]):
    ensure_dirs()
    _atomic_write(NVD_CACHE, json.dumps(cache, indent=2))


def save_findings(target: str, data: Dict[str, Any]):
    ensure_dirs()
    # The raw target used to become the filename (path traversal); sanitize it.
    path = FINDINGS_DIR / f"{sanitize_filename(target)}.json"
    _atomic_write(path, json.dumps(data, indent=2))
    return str(path)


def load_findings(target: str) -> Optional[Dict[str, Any]]:
    ensure_dirs()
    path = FINDINGS_DIR / f"{sanitize_filename(target)}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

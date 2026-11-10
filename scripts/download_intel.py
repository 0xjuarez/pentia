#!/usr/bin/env python3
"""Simple downloader for KEV and example NVD feed to datasets directory.

Security notes: --nvd-url only accepts http(s) URLs whose host is on an
explicit allowlist (NVD/CISA); downloads are streamed with a 500 MB cap;
--out must stay inside the project directory and the output filename is
sanitized, so neither the URL nor the output path can be abused for SSRF
or path traversal.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from core.validation import sanitize_filename, validate_output_dir, validate_url

DATA_DIR = BASE_DIR / "datasets"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

# Only these hosts may be fetched with --nvd-url.
ALLOWED_NVD_HOSTS = {
    "static.nvd.nist.gov",
    "services.nvd.nist.gov",
    "www.cisa.gov",
    "cisa.gov",
    "nvd.nist.gov",
}

MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024  # 500 MB


def _stream_download(url: str, dest: Path, timeout: int = 60) -> None:
    """Stream a download to dest, aborting above MAX_DOWNLOAD_BYTES."""
    print(f"Downloading from {url} to {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.tmp")
    downloaded = 0
    try:
        with requests.get(url, timeout=timeout, stream=True) as r:
            r.raise_for_status()
            with open(tmp, "wb") as handle:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_DOWNLOAD_BYTES:
                        raise ValueError(
                            f"Download exceeds the {MAX_DOWNLOAD_BYTES // (1024 * 1024)} MB limit; aborted"
                        )
                    handle.write(chunk)
        os.replace(tmp, dest)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def download_kev(dest: Path):
    print(f"Downloading KEV to {dest}")
    _stream_download(KEV_URL, dest, timeout=30)
    print("KEV downloaded")


def download_nvd(url: str, dest: Path):
    # Validate the URL (http/https, no credentials) and enforce the host
    # allowlist before any network access.
    url = validate_url(url)
    host = (urlparse(url).hostname or "").lower()
    if host not in ALLOWED_NVD_HOSTS:
        raise ValueError(
            f"Host no permitido para --nvd-url: {host}. "
            f"Hosts permitidos: {', '.join(sorted(ALLOWED_NVD_HOSTS))}"
        )
    _stream_download(url, dest, timeout=60)
    print("NVD feed downloaded")


def safe_nvd_filename(url: str) -> str:
    """Filename from a URL: basename without query/fragment, sanitized."""
    name = urlparse(url).path.rsplit("/", 1)[-1]
    if not name or name in (".", ".."):
        raise ValueError("No se pudo derivar un nombre de archivo válido de la URL")
    if "/" in name or "\\" in name:
        raise ValueError("Nombre de archivo no válido en la URL")
    return sanitize_filename(name)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kev", action="store_true", help="Download CISA KEV feed")
    p.add_argument("--nvd-url", help="NVD feed URL to download (e.g., https://static.nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-2024.json.gz)")
    p.add_argument("--out", help="Output directory", default=str(DATA_DIR))
    args = p.parse_args()

    # --out must stay inside the project directory (rejects ".." escapes).
    outdir = validate_output_dir(args.out, base=BASE_DIR)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.kev:
        download_kev(outdir / "kev" / "known_exploited_vulnerabilities.json")

    if args.nvd_url:
        # user should provide a downloadable JSON or gz link; we save raw response
        fname = safe_nvd_filename(args.nvd_url)
        download_nvd(args.nvd_url, outdir / "cves" / fname)

    if not args.kev and not args.nvd_url:
        print("Nothing to do. Use --kev or --nvd-url")

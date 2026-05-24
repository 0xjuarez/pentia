#!/usr/bin/env python3
"""Simple downloader for KEV and example NVD feed to datasets directory."""
import argparse
import json
import os
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datasets"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def download_kev(dest: Path):
    print(f"Downloading KEV to {dest}")
    r = requests.get(KEV_URL, timeout=30)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(r.text, encoding="utf-8")
    print("KEV downloaded")


def download_nvd(url: str, dest: Path):
    print(f"Downloading NVD from {url} to {dest}")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(r.text, encoding="utf-8")
    print("NVD feed downloaded")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kev", action="store_true", help="Download CISA KEV feed")
    p.add_argument("--nvd-url", help="NVD feed URL to download (e.g., https://static.nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-2024.json.gz)")
    p.add_argument("--out", help="Output directory", default=str(DATA_DIR))
    args = p.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.kev:
        download_kev(outdir / "kev" / "known_exploited_vulnerabilities.json")

    if args.nvd_url:
        # user should provide a downloadable JSON or gz link; we save raw response
        fname = os.path.basename(args.nvd_url)
        download_nvd(args.nvd_url, outdir / "cves" / fname)

    if not args.kev and not args.nvd_url:
        print("Nothing to do. Use --kev or --nvd-url")

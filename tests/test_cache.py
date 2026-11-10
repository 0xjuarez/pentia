"""Tests for core/cache.py — traversal-safe findings and corrupt cache (4.0.1).

In 4.0.0 the findings filename was the raw target (only "/" replaced)
under a hardcoded /home/venus/... path, and a corrupt nvd_cache.json
crashed every CVE enrichment.
"""
import json

import core.cache as cache


def test_findings_filename_cannot_traverse(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache, "FINDINGS_DIR", tmp_path / "findings")
    monkeypatch.setattr(cache, "NVD_CACHE", tmp_path / "nvd_cache.json")

    path = cache.save_findings("../../etc/passwd", {"cves": []})
    assert path.startswith(str((tmp_path / "findings").resolve()))
    assert (tmp_path / "findings").exists()
    # Nothing was written outside the findings dir.
    assert not (tmp_path / "etc").exists()
    assert cache.load_findings("../../etc/passwd") == {"cves": []}


def test_corrupt_nvd_cache_returns_empty_instead_of_crashing(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache, "FINDINGS_DIR", tmp_path / "findings")
    bad = tmp_path / "nvd_cache.json"
    bad.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(cache, "NVD_CACHE", bad)

    assert cache.load_nvd_cache() == {}


def test_nvd_cache_round_trip(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache, "FINDINGS_DIR", tmp_path / "findings")
    monkeypatch.setattr(cache, "NVD_CACHE", tmp_path / "nvd_cache.json")

    cache.save_nvd_cache({"cpe:2.3:a:apache:http_server": [{"id": "CVE-2021-44228"}]})
    loaded = cache.load_nvd_cache()
    assert loaded["cpe:2.3:a:apache:http_server"][0]["id"] == "CVE-2021-44228"

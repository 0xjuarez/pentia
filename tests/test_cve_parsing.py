"""Tests for NVD parsing — 2.0 schema first, 1.x as fallback (4.0.1).

In 4.0.0 parse_nvd_item only understood the NVD 1.x schema while the
code queries the NVD 2.0 API, so every CVE came back id=None/cvss=None
(engine) or raised AttributeError (intelligence ingest).
"""
from core.cve_engine import parse_nvd_item
from core.cve_intelligence import CVEIntelligence

V2_ITEM = {
    "cve": {
        "id": "CVE-2021-44228",
        "descriptions": [{"lang": "en", "value": "Log4Shell RCE in Log4j"}],
        "metrics": {
            "cvssMetricV31": [
                {"cvssData": {"baseScore": 10.0, "baseSeverity": "CRITICAL"}}
            ]
        },
        "references": [{"url": "https://example.com/log4shell"}],
    }
}

V1_ITEM = {
    "CVE_data_meta": {"ID": "CVE-2019-0001"},
    "description": {
        "description_data": [{"lang": "en", "value": "An old bug"}]
    },
    "impact": {
        "baseMetricV3": {"cvssV3": {"baseScore": 7.5, "baseSeverity": "HIGH"}}
    },
    "references": {"reference_data": [{"url": "https://example.com/old"}]},
}


def test_parse_nvd_2_0_item():
    parsed = parse_nvd_item(V2_ITEM)
    assert parsed["id"] == "CVE-2021-44228"
    assert parsed["cvss"] == 10.0
    assert parsed["severity"] == "CRITICAL"
    assert "Log4Shell" in parsed["description"]
    assert parsed["references"]


def test_parse_nvd_2_0_bare_cve_dict():
    # lookup_cves_for_cpe passes the inner cve dict directly.
    parsed = parse_nvd_item(V2_ITEM["cve"])
    assert parsed["id"] == "CVE-2021-44228"
    assert parsed["cvss"] == 10.0


def test_parse_nvd_1_x_fallback():
    parsed = parse_nvd_item(V1_ITEM)
    assert parsed["id"] == "CVE-2019-0001"
    assert parsed["cvss"] == 7.5
    assert parsed["severity"] == "HIGH"
    assert "old bug" in parsed["description"]


def test_parse_non_dict_returns_empty():
    parsed = parse_nvd_item(None)
    assert parsed["id"] is None
    assert parsed["cvss"] is None


def test_intelligence_parse_shares_engine():
    parsed = CVEIntelligence.parse_nvd_item(V2_ITEM)
    assert parsed["id"] == "CVE-2021-44228"
    assert parsed["source"] == "nvd"
    assert "Log4Shell" in parsed["summary"]
    assert parsed["cvss"] == 10.0

"""Tests for reports/generator.py — valid JSON and HTML escaping (4.0.1).

The 4.0.0 generator wrote the JSON report with str(dict) (Python repr,
not valid JSON) and interpolated findings raw into Markdown/HTML.
"""
import json

from reports.generator import build_html, build_json, build_markdown, write_reports

EVIL = '<script>alert("xss")</script><img src=x onerror=alert(1)>'


def test_json_report_is_valid_json():
    data = build_json("summary text", [{"title": "t", "description": "d"}])
    # Must round-trip through the JSON parser (4.0.0 wrote Python repr).
    text = json.dumps(data)
    parsed = json.loads(text)
    assert parsed["summary"] == "summary text"
    assert parsed["findings"][0]["title"] == "t"


def test_write_reports_produces_parseable_json_file(tmp_path, monkeypatch):
    # write_reports confines output to the CWD by design (validate_output_dir),
    # so run it with the CWD inside the temp dir.
    monkeypatch.chdir(tmp_path)
    paths = write_reports(
        "recon done",
        [{"title": "nmap scan", "description": "3 ports open"}],
        output_dir="out",
    )
    with open(paths["json"], encoding="utf-8") as fh:
        parsed = json.load(fh)
    assert parsed["summary"] == "recon done"
    assert parsed["findings"][0]["description"] == "3 ports open"
    assert (tmp_path / "out" / "report.md").exists()


def test_build_html_escapes_dynamic_content():
    html = build_html(EVIL, [{"title": EVIL, "description": EVIL}])
    # No real tags may survive: the payload is rendered as escaped text.
    # ("onerror=" as bare text inside an escaped tag is harmless.)
    assert "<script>" not in html
    assert "<img" not in html
    assert "&lt;script&gt;" in html


def test_build_markdown_keeps_content():
    md = build_markdown("summary", [{"title": "nmap scan", "description": "ok"}])
    assert "summary" in md
    assert "nmap scan" in md

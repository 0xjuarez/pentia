import html
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from core.validation import validate_output_dir


def build_markdown(summary: str, findings: Optional[List[Dict[str, str]]] = None) -> str:
    lines = ["# Pentia Findings", "", summary, ""]
    if findings:
        lines.append("## Findings")
        for finding in findings:
            lines.append(f"- **{finding.get('title', 'Finding')}**: {finding.get('description', '')}")
    return "\n".join(lines)


def build_json(summary: str, findings: Optional[List[Dict[str, str]]] = None) -> Dict[str, object]:
    return {"summary": summary, "findings": findings or []}


def build_html(summary: str, findings: Optional[List[Dict[str, str]]] = None) -> str:
    """Render the report as HTML with all dynamic content escaped."""
    parts = ["<h1>Pentia Findings</h1>", f"<p>{html.escape(summary)}</p>"]
    if findings:
        parts.append("<h2>Findings</h2><ul>")
        for finding in findings:
            title = html.escape(str(finding.get("title", "Finding")))
            description = html.escape(str(finding.get("description", "")))
            parts.append(f"<li><strong>{title}</strong>: {description}</li>")
        parts.append("</ul>")
    return "\n".join(parts)


def _atomic_write(path: Path, text: str) -> None:
    """Write via a temp file in the same directory + os.replace (atomic)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_reports(summary: str, findings: Optional[List[Dict[str, str]]] = None, output_dir: str = "reports") -> Dict[str, str]:
    out = validate_output_dir(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(summary, findings)
    json_data = build_json(summary, findings)
    report_paths = {
        "markdown": out / "report.md",
        "json": out / "report.json",
    }
    _atomic_write(report_paths["markdown"], markdown)
    _atomic_write(report_paths["json"], json.dumps(json_data, indent=2, ensure_ascii=False))
    return {"markdown": str(report_paths["markdown"]), "json": str(report_paths["json"])}

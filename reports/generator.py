from pathlib import Path
from typing import Dict, List, Optional


def build_markdown(summary: str, findings: Optional[List[Dict[str, str]]] = None) -> str:
    lines = ["# Pentia Findings", "", summary, ""]
    if findings:
        lines.append("## Findings")
        for finding in findings:
            lines.append(f"- **{finding.get('title', 'Finding')}**: {finding.get('description', '')}")
    return "\n".join(lines)


def build_json(summary: str, findings: Optional[List[Dict[str, str]]] = None) -> Dict[str, object]:
    return {"summary": summary, "findings": findings or []}


def write_reports(summary: str, findings: Optional[List[Dict[str, str]]] = None, output_dir: str = "reports") -> Dict[str, str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(summary, findings)
    json_data = build_json(summary, findings)
    report_paths = {
        "markdown": Path(output_dir) / "report.md",
        "json": Path(output_dir) / "report.json",
    }
    report_paths["markdown"].write_text(markdown, encoding="utf-8")
    report_paths["json"].write_text(str(json_data), encoding="utf-8")
    return {"markdown": str(report_paths["markdown"]), "json": str(report_paths["json"])}

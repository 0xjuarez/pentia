from typing import Dict, Any

try:
    from neural.exploit_ranker import ExploitRanker
except Exception:
    ExploitRanker = None


def score_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a score summary for a CVE finding using ExploitRanker if available, otherwise a heuristic."""
    features = {
        "cvss": finding.get("cvss") or 0.0,
        "exploit_exists": 1.0 if finding.get("exploit_available") else 0.0,
        "public_poc": 1.0 if finding.get("exploit_available") else 0.0,
        "metasploit_module": 1.0 if finding.get("metasploit") else 0.0,
        "service_exposure": 1.0,
        "internet_exposed": 1.0,
        "auth_required": 0.0,
    }

    if ExploitRanker is not None:
        ranker = ExploitRanker()
        pred = ranker.predict(features)
        return {"score": pred.get("score", 0.0), "label": pred.get("label")}

    # fallback heuristic
    base = features["cvss"] * (1.0 + features["exploit_exists"]) * (1.0 + features["public_poc"]) 
    normalized = min(1.0, base / 10.0) if base > 0 else 0.0
    label = "high" if normalized >= 0.7 else "medium" if normalized >= 0.4 else "low"
    return {"score": normalized, "label": label}

from typing import Dict, Any

try:
    from neural.exploit_ranker import ExploitRanker
except Exception:
    ExploitRanker = None

# Single module-level ranker: constructing one per finding is wasteful
# (each __init__ may load a model file from disk).
_RANKER = ExploitRanker() if ExploitRanker is not None else None


def score_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a score summary for a CVE finding using ExploitRanker if available, otherwise a heuristic."""
    # exploit_exists and public_poc describe the same fact (a public
    # exploit/PoC is known), so they are counted only once: the feature
    # dict keeps both keys for the model, but the heuristic below uses
    # just exploit_exists.
    exploit_known = 1.0 if finding.get("exploit_available") else 0.0
    features = {
        "cvss": finding.get("cvss") or 0.0,
        "exploit_exists": exploit_known,
        "public_poc": exploit_known,
        "metasploit_module": 1.0 if finding.get("metasploit") else 0.0,
        "service_exposure": 1.0,
        "internet_exposed": 1.0,
        "auth_required": 0.0,
    }

    if _RANKER is not None:
        pred = _RANKER.predict(features)
        return {"score": pred.get("score", 0.0), "label": pred.get("label")}

    # fallback heuristic (exploit factor counted once, not twice)
    base = features["cvss"] * (1.0 + features["exploit_exists"])
    normalized = min(1.0, base / 10.0) if base > 0 else 0.0
    label = "high" if normalized >= 0.7 else "medium" if normalized >= 0.4 else "low"
    return {"score": normalized, "label": label}

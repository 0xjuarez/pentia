import asyncio
from typing import Any, Dict

from core.memory import MemoryStore
from core.orchestrator import Orchestrator
from scanners import nmap, whatweb, nuclei, subdomains, web_enum


async def run_recon_pipeline(target: str, memory: MemoryStore, orchestrator: Orchestrator, fast: bool = False) -> Dict[str, Any]:
    tasks = [
        nmap.run_nmap(target),
        whatweb.run_whatweb(target),
        nuclei.run_nuclei(target),
        subdomains.run_subfinder(target),
    ]

    if not fast:
        tasks.append(web_enum.run_ffuf(target))

    scan_results = await asyncio.gather(*tasks, return_exceptions=True)
    report = {
        "nmap": scan_results[0],
        "whatweb": scan_results[1],
        "nuclei": scan_results[2],
        "subdomains": scan_results[3],
        "ffuf": scan_results[4] if not fast else None,
    }

    if isinstance(scan_results[0], dict):
        routing = await orchestrator.route(target, scan_results[0].get("output", ""))
        report["orchestrator"] = routing
    else:
        report["orchestrator"] = {"error": str(scan_results[0])}

    await memory.add_notes(
        notes=f"Recon results for {target}: {report}",
        metadata={"target": target, "pipeline": "recon"},
    )

    return report

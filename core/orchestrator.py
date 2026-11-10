import asyncio
from typing import Any, Dict, List, Optional

from scanners import nmap as nmap_scanner
from scanners import nuclei as nuclei_scanner
from scanners import web_enum
from scanners import ad as ad_scanner
from scanners import smb as smb_scanner
from pipelines import web as web_pipeline
from .decision_engine import DecisionEngine
from core.intel import enrich_service


class Orchestrator:
    def __init__(self):
        self.decisions = []

    @staticmethod
    def normalize_services(nmap_output: str) -> List[str]:
        services = []
        for line in nmap_output.splitlines():
            if "/tcp" in line and "open" in line:
                parts = line.split()
                # 3-part lines like "80/tcp open http" carry the service
                # in parts[2]; longer lines do too.
                if len(parts) >= 3:
                    services.append(parts[2].lower())
        return services

    async def route(self, target: str, nmap_output: str, skip: Optional[set] = None) -> Dict[str, Any]:
        decision = DecisionEngine.decide(nmap_output)
        services = decision["services"]
        actions = decision["actions"]
        skip = skip or set()

        # Run the selected scanners concurrently instead of sequentially.
        # Each scanner enforces its own per-tool timeout via
        # scanners/_common.py run_tool.
        coros: Dict[str, Any] = {}
        if "ffuf" in actions and "ffuf" not in skip:
            coros["ffuf"] = web_enum.run_ffuf(target)
        if "nuclei" in actions and "nuclei" not in skip:
            coros["nuclei"] = nuclei_scanner.run_nuclei(target)
        if "wpscan" in actions and "wpscan" not in skip:
            coros["wpscan"] = web_pipeline.run_wpscan(target)
        if "enum4linux" in actions and "enum4linux" not in skip:
            coros["enum4linux"] = smb_scanner.run_enum4linux(target)
        if "bloodhound" in actions and "bloodhound" not in skip:
            coros["bloodhound"] = ad_scanner.run_bloodhound(target)

        keys = list(coros)
        outputs = await asyncio.gather(*coros.values(), return_exceptions=True)
        results = dict(zip(keys, outputs))
        if "kerbrute" in actions and "kerbrute" not in skip:
            results["kerbrute"] = {"status": "pending", "note": "kerbrute tool execution placeholder"}

        self.decisions = actions
        return {
            "service_list": services,
            "actions": actions,
            "results": results,
        }

    async def run_all(self, target: str) -> Dict[str, Any]:
        tasks = [
            nmap_scanner.run_nmap(target),
            web_enum.run_web_enum(target),
            nuclei_scanner.run_nuclei(target),
            web_enum.run_ffuf(target),
            web_enum.run_subfinder(target),
        ]
        outputs = await asyncio.gather(*tasks, return_exceptions=True)
        report = {
            "nmap": outputs[0],
            "whatweb": outputs[1],
            "nuclei": outputs[2],
            "ffuf": outputs[3],
            "subfinder": outputs[4],
        }

        # Enrich findings from Nmap output (if available)
        try:
            nmap_out = outputs[0]
            if isinstance(nmap_out, dict) and nmap_out.get("output"):
                services = self.normalize_services(nmap_out.get("output", ""))
                # launch enrichment for detected services concurrently
                enrich_tasks = [enrich_service(target, svc, None) for svc in services]
                intel_results = await asyncio.gather(*enrich_tasks, return_exceptions=True)
                report["intel"] = intel_results
        except Exception:
            report["intel"] = {"error": "intel enrichment failed"}

        return report

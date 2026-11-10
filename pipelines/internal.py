import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners import smb, ad


async def run_internal_pipeline(network: str) -> Dict[str, Any]:
    # validate_target accepts a CIDR network as well as a single host/IP.
    network = validate_target(network)
    tasks = [
        smb.run_enum4linux(network),
        ad.run_bloodhound(network),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "enum4linux": results[0],
        "bloodhound": results[1],
    }

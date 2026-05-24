import asyncio
from typing import Any, Dict

from scanners import smb, ad


async def run_internal_pipeline(network: str) -> Dict[str, Any]:
    tasks = [
        smb.run_enum4linux(network),
        ad.run_bloodhound(network),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        "enum4linux": results[0],
        "bloodhound": results[1],
    }

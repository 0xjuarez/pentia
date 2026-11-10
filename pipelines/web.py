import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners import web_enum, whatweb
from scanners._common import run_tool


async def run_web_pipeline(target: str) -> Dict[str, Any]:
    results = await asyncio.gather(
        web_enum.run_web_enum(target),
        web_enum.run_ffuf(target),
        whatweb.run_whatweb(target),
        return_exceptions=True,
    )
    return {
        "web_enum": results[0],
        "ffuf": results[1],
        "whatweb": results[2],
    }


async def run_wpscan(target: str) -> Dict[str, Any]:
    target = validate_target(target)
    return await run_tool("wpscan", ["--url", target, "--no-banner"])

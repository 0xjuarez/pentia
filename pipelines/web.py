import asyncio
from typing import Any, Dict

from scanners import web_enum, whatweb


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
    process = await asyncio.create_subprocess_exec(
        "wpscan", "--url", target, "--no-banner",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }

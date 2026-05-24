import asyncio
from typing import Dict, Optional


async def run_shortname_scan(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-S", target]
    process = await asyncio.create_subprocess_exec(
        "rpcclient", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }


async def run_bloodhound(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-u", target]
    process = await asyncio.create_subprocess_exec(
        "bloodhound", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }

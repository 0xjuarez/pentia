import asyncio
from typing import Dict, Optional


async def run_nmap(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-sV", "-p-", "--open", target]
    process = await asyncio.create_subprocess_exec(
        "nmap", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }


async def run_nuclei(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-t", "-", "-target", target]
    process = await asyncio.create_subprocess_exec(
        "nuclei", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }

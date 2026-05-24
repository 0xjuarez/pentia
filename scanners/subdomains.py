import asyncio
from typing import Dict, Optional


async def run_subfinder(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-d", target, "-silent"]
    process = await asyncio.create_subprocess_exec(
        "subfinder", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }

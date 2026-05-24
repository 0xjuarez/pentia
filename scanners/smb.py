import asyncio
from typing import Dict, Optional


async def run_enum4linux(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-a", target]
    process = await asyncio.create_subprocess_exec(
        "enum4linux", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }

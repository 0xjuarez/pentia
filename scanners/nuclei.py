import asyncio
from typing import Dict, Optional


async def run_nuclei(target: str, template: Optional[str] = None) -> Dict[str, str]:
    args = ["-u", target]
    if template:
        args.extend(["-t", template])
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

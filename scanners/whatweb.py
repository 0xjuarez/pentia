import asyncio
from typing import Dict, Optional


async def run_whatweb(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or [target]
    process = await asyncio.create_subprocess_exec(
        "whatweb", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }

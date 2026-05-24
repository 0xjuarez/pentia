import asyncio
from typing import Any, Dict

from .base import Plugin


class RustScanPlugin(Plugin):
    name = "rustscan"

    async def run(self, target: str, **kwargs: Any) -> Dict[str, Any]:
        args = [target, "--ulimit", "5000"]
        process = await asyncio.create_subprocess_exec(
            "rustscan", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return {
            "returncode": process.returncode,
            "output": stdout.decode(errors="ignore"),
            "error": stderr.decode(errors="ignore"),
        }

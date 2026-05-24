import asyncio
from typing import Any, Dict

from .base import Plugin


class SQLMapPlugin(Plugin):
    name = "sqlmap"

    async def run(self, target: str, **kwargs: Any) -> Dict[str, Any]:
        args = ["-u", target, "--batch"]
        process = await asyncio.create_subprocess_exec(
            "sqlmap", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return {
            "returncode": process.returncode,
            "output": stdout.decode(errors="ignore"),
            "error": stderr.decode(errors="ignore"),
        }

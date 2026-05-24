import asyncio
from typing import Any, Dict, Optional

from .base import Plugin


class FFUFPlugin(Plugin):
    name = "ffuf"

    async def run(self, target: str, **kwargs: Any) -> Dict[str, Any]:
        args = kwargs.get("args") or ["-u", f"{target}/FUZZ", "-w", "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt", "-t", "20"]
        process = await asyncio.create_subprocess_exec(
            "ffuf", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return {
            "returncode": process.returncode,
            "output": stdout.decode(errors="ignore"),
            "error": stderr.decode(errors="ignore"),
        }

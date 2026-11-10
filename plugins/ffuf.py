import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool

from .base import Plugin


class FFUFPlugin(Plugin):
    name = "ffuf"

    async def run(self, target: str, **kwargs: Any) -> Dict[str, Any]:
        target = validate_target(target)
        caller_args = kwargs.get("args")
        if caller_args is None:
            return await run_tool("ffuf", [
                "-u", f"{target}/FUZZ",
                "-w", "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
                "-t", "20",
            ])
        # Caller-supplied args used to silently drop the target; always
        # append the validated target URL.
        return await run_tool("ffuf", list(caller_args) + ["-u", f"{target}/FUZZ"])

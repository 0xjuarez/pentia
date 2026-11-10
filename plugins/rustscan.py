import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool

from .base import Plugin


class RustScanPlugin(Plugin):
    name = "rustscan"

    async def run(self, target: str, **kwargs: Any) -> Dict[str, Any]:
        target = validate_target(target)
        # rustscan requires the target behind "-a"; the previous code passed
        # it as a bare positional argument, which rustscan rejects.
        caller_args = kwargs.get("args")
        base = list(caller_args) if caller_args is not None else ["--ulimit", "5000"]
        return await run_tool("rustscan", base + ["-a", target])

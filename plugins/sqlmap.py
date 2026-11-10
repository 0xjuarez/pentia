import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool

from .base import Plugin


class SQLMapPlugin(Plugin):
    name = "sqlmap"

    async def run(self, target: str, **kwargs: Any) -> Dict[str, Any]:
        target = validate_target(target)
        caller_args = kwargs.get("args")
        base = list(caller_args) if caller_args is not None else []
        # sqlmap supports "--": the validated target URL is passed via -u,
        # and validation rejects a leading "-" so it cannot become a flag.
        return await run_tool("sqlmap", base + ["-u", target, "--batch"])

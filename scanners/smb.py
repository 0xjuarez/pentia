import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool


async def run_enum4linux(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    target = validate_target(target)
    if args is None:
        return await run_tool("enum4linux", ["-a", target])
    return await run_tool("enum4linux", list(args) + ["-a", target])

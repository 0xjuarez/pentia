import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool


async def run_whatweb(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    target = validate_target(target)
    # whatweb supports "--": the validated target is always appended after
    # it so it can never be parsed as a flag.
    if args is None:
        return await run_tool("whatweb", ["--", target])
    return await run_tool("whatweb", list(args) + ["--", target])

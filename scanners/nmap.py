import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool


async def run_nmap(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    target = validate_target(target)
    # The validated target is always appended after "--" so it can never be
    # parsed as an nmap flag, even when the caller supplies custom args.
    if args is None:
        return await run_tool("nmap", ["-sV", "-p-", "--open", "--", target])
    return await run_tool("nmap", list(args) + ["--", target])

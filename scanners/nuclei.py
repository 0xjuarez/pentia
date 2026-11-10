import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool


async def run_nuclei(target: str, template: Optional[str] = None) -> Dict[str, str]:
    target = validate_target(target)
    args = ["-u", target]
    if template:
        args.extend(["-t", template])
    return await run_tool("nuclei", args)

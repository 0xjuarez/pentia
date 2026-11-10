import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool


async def run_shortname_scan(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    target = validate_target(target)
    if args is None:
        return await run_tool("rpcclient", ["-S", target])
    return await run_tool("rpcclient", list(args) + ["-S", target])


async def run_bloodhound(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    # There is no `bloodhound` CLI binary: the old code invoked
    # `bloodhound -u <target>`, which cannot work. BloodHound collection
    # needs bloodhound-python / SharpHound with domain credentials, run
    # out of band — do not invent an invocation here.
    return {
        "returncode": 1,
        "output": "",
        "error": (
            "BloodHound collection is not supported: no 'bloodhound' CLI exists; "
            "use bloodhound-python/SharpHound with domain credentials out of band."
        ),
    }

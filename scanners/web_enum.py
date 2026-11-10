import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.validation import validate_target
from scanners._common import run_tool
from scanners.subdomains import run_subfinder as _subdomains_run_subfinder


async def run_web_enum(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    # NOTE: this intentionally uses different whatweb defaults
    # ("-u <target> --random-agent") than scanners/whatweb.py's
    # run_whatweb; keep the two in sync only if the callers agree.
    target = validate_target(target)
    if args is None:
        return await run_tool("whatweb", ["-u", target, "--random-agent"])
    # Caller-supplied args used to silently drop the target; always append
    # the validated target (validation rejects a leading "-").
    return await run_tool("whatweb", list(args) + [target])


async def run_ffuf(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    target = validate_target(target)
    if args is None:
        return await run_tool("ffuf", [
            "-u", f"{target}/FUZZ",
            "-w", "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
            "-t", "20",
        ])
    return await run_tool("ffuf", list(args) + ["-u", f"{target}/FUZZ"])


async def run_subfinder(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    # Byte-identical to scanners.subdomains.run_subfinder: delegate so the
    # two cannot drift apart again.
    return await _subdomains_run_subfinder(target, args)

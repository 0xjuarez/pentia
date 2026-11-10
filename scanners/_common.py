"""Shared helper to run external scanner binaries safely.

Every scanner/plugin in the project should go through :func:`run_tool` so
that:

* a missing binary fails fast with a clear error instead of crashing the
  event loop with ``FileNotFoundError``;
* execution always uses an argument list (never a shell);
* a hung tool is killed after ``timeout`` seconds;
* runaway output cannot exhaust memory (stdout/stderr are truncated).
"""
from __future__ import annotations

import asyncio
import shutil
from typing import Dict, List, Optional

__all__ = ["run_tool", "MAX_OUTPUT_CHARS"]

MAX_OUTPUT_CHARS = 1_000_000


async def run_tool(binary: str, args: List[str], timeout: int = 120) -> Dict[str, object]:
    """Run ``binary`` with the given argument list.

    Returns ``{"returncode": int, "output": str, "error": str}``.
    Raises :class:`RuntimeError` with a clear message when the binary is
    not installed. On timeout the process is killed and a result with
    ``returncode == -1`` and a timeout message in ``error`` is returned.
    """
    binary_path = shutil.which(binary)
    if binary_path is None:
        raise RuntimeError(
            f"Required tool '{binary}' not found in PATH. "
            f"Install it (see ./install.sh tool check) before running this scan."
        )

    argv = [str(a) for a in args]
    process = await asyncio.create_subprocess_exec(
        binary_path,
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return {
            "returncode": -1,
            "output": "",
            "error": f"Timeout after {timeout}s running {binary}",
        }
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore")[:MAX_OUTPUT_CHARS],
        "error": stderr.decode(errors="ignore")[:MAX_OUTPUT_CHARS],
    }

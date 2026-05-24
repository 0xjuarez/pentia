import asyncio
from typing import Dict, Optional


async def run_web_enum(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-u", target, "--random-agent"]
    process = await asyncio.create_subprocess_exec(
        "whatweb", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }


async def run_ffuf(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-u", f"{target}/FUZZ", "-w", "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt", "-t", "20"]
    process = await asyncio.create_subprocess_exec(
        "ffuf", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }


async def run_subfinder(target: str, args: Optional[list[str]] = None) -> Dict[str, str]:
    args = args or ["-d", target, "-silent"]
    process = await asyncio.create_subprocess_exec(
        "subfinder", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "returncode": process.returncode,
        "output": stdout.decode(errors="ignore"),
        "error": stderr.decode(errors="ignore"),
    }

"""Tests for scanners/_common.py run_tool — timeouts and missing binaries (4.0.1).

In 4.0.0 every scanner awaited process.communicate() with no timeout and
no binary check, so a hung nmap -p- or a missing tool hung/crashed the CLI.
"""
import asyncio
import shutil
import sys

import pytest

from scanners._common import run_tool


def test_run_tool_success():
    result = asyncio.run(run_tool(sys.executable, ["-c", "print('hi')"]))
    assert result["returncode"] == 0
    assert result["output"].strip() == "hi"


def test_run_tool_missing_binary_raises_clear_error():
    with pytest.raises(RuntimeError, match="not found in PATH"):
        asyncio.run(run_tool("definitely-not-a-real-binary-xyz", []))


def test_run_tool_timeout_kills_process():
    if shutil.which("sleep") is None:
        pytest.skip("sleep binary not available")
    result = asyncio.run(run_tool("sleep", ["30"], timeout=1))
    assert result["returncode"] == -1
    assert "Timeout" in result["error"]


def test_run_tool_nonzero_returncode_is_reported():
    result = asyncio.run(
        run_tool(sys.executable, ["-c", "import sys; sys.exit(3)"])
    )
    assert result["returncode"] == 3

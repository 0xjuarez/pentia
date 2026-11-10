"""Tests for scanners/ad.py — missing run_tool import (F821) and bloodhound stub (4.0.1).

In 4.0.1 fixer #1's refactor, every scanner imports run_tool from
scanners._common except ad.py, so run_shortname_scan raised NameError.
run_bloodhound must return a clear unsupported-error dict instead of
invoking a `bloodhound` binary that does not exist.
"""
import asyncio
import shutil

import pytest

import scanners.ad as ad


def test_ad_imports_run_tool():
    # Regression guard for the F821: the name must exist at module level.
    assert hasattr(ad, "run_tool")


def test_shortname_scan_missing_binary_is_runtime_error_not_name_error():
    if shutil.which("rpcclient") is not None:
        pytest.skip("rpcclient is installed; missing-binary path not exercised")
    with pytest.raises(RuntimeError, match="not found in PATH"):
        asyncio.run(ad.run_shortname_scan("127.0.0.1"))


def test_bloodhound_returns_unsupported_error():
    result = asyncio.run(ad.run_bloodhound("127.0.0.1"))
    assert result["returncode"] == 1
    assert "not supported" in result["error"]
    assert "bloodhound-python" in result["error"]

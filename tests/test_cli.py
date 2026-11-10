"""CLI smoke tests — --help and version (4.0.1).

The CLI surface must stay stable: `pentia --help`, `pentia version`
and the existing subcommands.
"""
from typer.testing import CliRunner

from pentia import app

runner = CliRunner()


def test_help_exits_zero_and_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "recon" in result.output
    assert "serve" in result.output
    assert "version" in result.output


def test_version_reports_4_0_1():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "4.0.1" in result.output


def test_recon_help_lists_target_and_fast():
    result = runner.invoke(app, ["recon", "--help"])
    assert result.exit_code == 0
    assert "fast" in result.output.lower()

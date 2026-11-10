"""Pytest configuration for PENTIA 4.0.1 smoke tests.

Ensures the repository root (the pentia-updated tree) is importable
when pytest is run from anywhere, so `import pentia`, `core.*`,
`scanners.*` etc. resolve to the tree under test, not to an installed copy.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

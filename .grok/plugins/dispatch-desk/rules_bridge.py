#!/usr/bin/env python3
"""Start the kit rules_mcp.py so lookup_rule reads dispatch_rules.md."""
from pathlib import Path
import runpy

here = Path(__file__).resolve()
for parent in here.parents:
    candidate = parent / "rules_mcp.py"
    if candidate.exists():
        runpy.run_path(str(candidate), run_name="__main__")
        break
else:
    raise SystemExit("rules_mcp.py not found")

#!/usr/bin/env python3
"""Start the kit rules_mcp.py so lookup_rule reads dispatch_rules.md."""
from pathlib import Path
import runpy

here = Path(__file__).resolve()
candidate = None
for parent in here.parents:
    for path in (parent / "instructions" / "rules_mcp.py", parent / "rules_mcp.py"):
        if path.exists():
            candidate = path
            break
    if candidate is not None:
        break
if candidate is None:
    raise SystemExit("rules_mcp.py not found")
runpy.run_path(str(candidate), run_name="__main__")

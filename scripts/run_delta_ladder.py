#!/usr/bin/env python3
"""Plan or replay paired normal/selection_blind budgets without dropping missing cells."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.task_campaign import main

if __name__ == "__main__":
    raise SystemExit(main("delta_ladder"))

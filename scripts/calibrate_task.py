#!/usr/bin/env python3
"""Plan or replay independent first-draw calibration; --execute explicitly makes model calls."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.task_campaign import main

if __name__ == "__main__":
    raise SystemExit(main("calibration"))

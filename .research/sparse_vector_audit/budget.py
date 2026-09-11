"""Where the reference's budget goes: scan, screen, confirm, per world."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_both import ev, load, TASK  # noqa: E402

ref = load(TASK / "verification/reference_library_scan.py", "sva_ref")
for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
    world = ev._world(spec)
    problem = ev._public_problem(world)
    k, t = problem["n_queries"], problem["threshold"]
    scan = 0
    for side in ("up", "down"):
        for gap in range(ref.SCAN_STEP, 51, ref.SCAN_STEP):
            p = ref._dissent_probability(problem, gap, side)
            n = -(-8 // 1) if p <= 0 else int(-(-ref.SCAN_EXPECTED // p))
            if n <= ref.SCAN_MAX_RUNS:
                scan += n
    vecs = {tuple(v) for a, b in ref._library(k, t) for v in (a, b)}
    screen = len(vecs) * ref.SCREEN_RUNS
    left = problem["sample_budget"] - scan - screen
    print("%-24s scan %6d  screen %6d (%d vectors)  left for confirm %6d" % (spec["name"], scan, screen, len(vecs), left))

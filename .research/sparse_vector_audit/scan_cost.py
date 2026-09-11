"""What the headroom's positional scan spends per world, and what is left for the library."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_both import ev, load  # noqa: E402

hr = load(Path(__file__).parent / "headroom_positional.py", "sva_headroom")
for spec in ev.DEVELOPMENT_WORLDS + ev.HELDOUT_WORLDS:
    world = ev._world(spec)
    problem = ev._public_problem(world)
    inner = ev._Campaign(world).oracle()
    log = []

    def sample(q, n):
        log.append(n)
        return inner(q, n)

    # stop right after the scan: a budget of scan-only is emulated by counting calls before the first screen
    out = hr.audit(problem, sample)
    screen_at = next((i for i, n in enumerate(log) if n == hr.ref.SCREEN_RUNS), len(log))
    print("%-24s scan %6d  total %6d  verdict %s" % (spec["name"], sum(log[:screen_at]), sum(log), out["verdict"]))

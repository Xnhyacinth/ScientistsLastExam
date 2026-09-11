"""Why does the positional scan miss dev-branch-c?"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_both import ev, load  # noqa: E402

hr = load(Path(__file__).parent / "headroom_positional.py", "sva_headroom")
spec = next(s for s in ev.DEVELOPMENT_WORLDS if s["name"] == "dev-branch-c")
world = ev._world(spec)
problem = ev._public_problem(world)
inner = ev._Campaign(world).oracle()


def sample(q, n):
    out = inner(q, n)
    t = problem["threshold"]
    tpos = {}
    for o, v in out.items():
        j = o.find("T")
        if j >= 0:
            tpos[j] = tpos.get(j, 0) + v
    print("n=%6d q-t=%s T-at-position=%s" % (n, [x - t for x in q], dict(sorted(tpos.items()))))
    return out


print(hr.audit(problem, sample))

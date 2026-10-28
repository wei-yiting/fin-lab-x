import sys
from pathlib import Path
from backend.evals.experiments.reader_model_reasoning import grounding as g
raw, out, prior = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
g.FAITH_ARMS = ["luna_medium", "reader_luna_medium"]
gr = out / "grounding"
print(len(g.load_nuggets(gr / "nuggets")), "fresh nugget rows")
g.cmd_build_coverage(raw, gr / "nuggets", gr / "coverage", gr / "KEY_do_not_share")
kp = gr / "KEY_do_not_share" / "prior_checklist"
g.cmd_build_coverage(raw, prior, gr / "coverage_prior_checklist", kp)

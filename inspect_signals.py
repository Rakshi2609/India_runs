import json
import pprint

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

print("REDROB SIGNALS\n")
pprint.pp(candidates[0]["redrob_signals"])

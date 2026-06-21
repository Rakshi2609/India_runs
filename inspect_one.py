import json
import pprint

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

print("=" * 80)
print("CANDIDATE [0] FULL INSPECT")
print("=" * 80)
pprint.pp(candidates[0])

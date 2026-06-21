import json
import pprint

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

candidate = candidates[0]

for key, value in candidate.items():
    print("\n" + "=" * 80)
    print("FIELD:", key)
    print("TYPE :", type(value).__name__)
    pprint.pp(value)
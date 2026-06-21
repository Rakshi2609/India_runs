# explore.py

import json
from collections import Counter

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

print("Candidates:", len(candidates))

all_keys = Counter()

for c in candidates:
    all_keys.update(c.keys())

print("\nTop Level Fields:")
for k in all_keys:
    print(k)
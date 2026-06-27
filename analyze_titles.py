import json
from collections import Counter

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

titles = Counter()

for c in candidates:
    titles[c["profile"]["current_title"]] += 1

print("=" * 80)
print("TITLES DISTRIBUTION")
print("=" * 80)
for title,count in titles.most_common(50):
    print(count, title)

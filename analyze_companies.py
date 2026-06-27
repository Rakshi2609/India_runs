import json
from collections import Counter

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

companies = Counter()

for c in candidates:
    companies[c["profile"]["current_company"]] += 1

print("=" * 80)
print("COMPANIES DISTRIBUTION")
print("=" * 80)
for company,count in companies.most_common(50):
    print(count, company)

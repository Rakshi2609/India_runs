import json

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

print("=" * 80)
print("DESCRIPTIONS PREVIEW")
print("=" * 80)
for i,c in enumerate(candidates[:10]):
    print("="*80)
    print(f"CANDIDATE {i+1}:", c["profile"]["current_title"])

    for job in c["career_history"]:
        print(job["description"])

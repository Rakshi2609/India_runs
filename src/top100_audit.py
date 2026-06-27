import csv
import sys

def main():
    print("Loading submission_debug.csv...")
    try:
        with open("submission_debug.csv", "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except FileNotFoundError:
        print("submission_debug.csv not found. Please run rank.py first.")
        return

    print("=" * 140)
    print(f"{'Rank':<5} | {'Candidate Name':<25} | {'Title':<30} | {'Career':<8} | {'Prod':<8} | {'Behav':<8} | {'Avail':<8} | {'Sem':<8} | {'Final':<8}")
    print("=" * 140)

    for i, r in enumerate(rows[:100]):
        print(f"[{i+1:>3}] | {r.get('name', 'N/A')[:25]:<25} | {r.get('title', 'N/A')[:30]:<30} | {r['career_score']:<8} | {r['production_score']:<8} | {r['behavior_score']:<8} | {r['availability_score']:<8} | {r['semantic_score'][:6]:<8} | {r['final_score']:<8}")

if __name__ == "__main__":
    main()

import json
from career_evidence import score_career
from behavioral_score import score_behavioral
from availability_score import score_availability

def main():
    with open("data/sample_candidates.json") as f:
        candidates = json.load(f)

    results = []
    for c in candidates:
        career = score_career(c)
        behavioral = score_behavioral(c)
        availability = score_availability(c)
        
        total = career["score"] + behavioral + availability
        
        results.append({
            "name": career["name"],
            "title": career["title"],
            "career_score": career["score"],
            "behavioral_score": behavioral,
            "availability_score": availability,
            "total_score": total
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)

    print("=" * 100)
    print(f"{'Candidate':<25} | {'Career':<8} | {'Behavioral':<10} | {'Availability':<12} | {'Total'}")
    print("-" * 100)
    for r in results[:20]:
        print(f"{r['name']:<25} | {r['career_score']:>8.1f} | {r['behavioral_score']:>10.1f} | {r['availability_score']:>12.1f} | {r['total_score']:>8.1f}")

if __name__ == "__main__":
    main()

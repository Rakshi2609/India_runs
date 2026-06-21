import json
from career_evidence import score_career
from behavioral_score import score_behavioral
from availability_score import score_availability
from production_score import score_production

def main():
    with open("data/sample_candidates.json") as f:
        candidates = json.load(f)

    results = []
    for c in candidates:
        career = score_career(c)
        behavioral = score_behavioral(c)
        availability = score_availability(c)
        production = score_production(c)
        
        career_raw = career["score"]
        
        # Norms (basic scaling to make them comparable before weighting)
        career_norm = max(0, career_raw) # prevent negative career from contributing to weighted
        
        final_score = (
            0.60 * career_norm + 
            0.15 * production + 
            0.15 * behavioral + 
            0.10 * availability
        )
        
        # Penalize non-AI careers heavily
        if career_raw < 0:
            final_score *= 0.25
        elif career_raw < 20:
            final_score *= 0.5
        
        results.append({
            "name": career["name"],
            "title": career["title"],
            "career_score": career_raw,
            "production_score": production,
            "behavioral_score": behavioral,
            "availability_score": availability,
            "total_score": final_score
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)

    print("=" * 120)
    print(f"{'Candidate':<25} | {'Career':<8} | {'Prod':<8} | {'Behav':<8} | {'Avail':<8} | {'Total'}")
    print("-" * 120)
    for r in results[:20]:
        print(f"{r['name']:<25} | {r['career_score']:>8.1f} | {r['production_score']:>8.1f} | {r['behavioral_score']:>8.1f} | {r['availability_score']:>8.1f} | {r['total_score']:>8.1f}")

if __name__ == "__main__":
    main()

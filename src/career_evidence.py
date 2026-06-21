import json

STRONG_TITLES = [
    "recommendation", "search", "retrieval", "ranking", 
    "ml engineer", "machine learning", "ai engineer", 
    "applied scientist", "data scientist"
]

MEDIUM_TITLES = [
    "backend", "software engineer", "data engineer", "full stack", "cloud engineer"
]

NEGATIVE_TITLES = [
    "marketing", "operations", "accountant", "customer support", 
    "hr", "mechanical", "civil", "business analyst", "graphic designer", "sales"
]

PRODUCT_COMPANIES = [
    "swiggy", "zomato", "razorpay", "cred", "phonepe", "meesho", "ola"
]

CONSULTING_COMPANIES = [
    "tcs", "infosys", "wipro", "accenture", "capgemini", 
    "cognizant", "mindtree", "tech mahindra"
]

EVIDENCE_KEYWORDS = [
    "ranking", "retrieval", "recommendation", "search", 
    "matching", "relevance", "hybrid search", "ndcg", "mrr", "map",
    "ab testing", "a/b test", "evaluation", "vector db", "embeddings"
]

def score_career(candidate):
    score = 0.0
    reasons = []

    profile = candidate.get("profile", {})
    history = candidate.get("career_history", [])
    
    # 1. Experience Years (Ideal 5-9)
    yoe = profile.get("years_of_experience", 0)
    if 5 <= yoe <= 9:
        score += 20.0
        reasons.append("Ideal YoE (5-9)")
    elif 4 <= yoe < 5 or 9 < yoe <= 12:
        score += 10.0
        reasons.append("Acceptable YoE")
    elif yoe > 12:
        score += 5.0
        reasons.append("High YoE (Maybe overqualified/architecture)")
    else:
        score += 0.0
        reasons.append("Low YoE")

    # 2. Title Scoring
    def score_title(title, is_current=False):
        t = title.lower()
        if any(x in t for x in STRONG_TITLES):
            return 30.0 if is_current else 15.0
        if any(x in t for x in MEDIUM_TITLES):
            return 10.0 if is_current else 5.0
        if any(x in t for x in NEGATIVE_TITLES):
            return -20.0 if is_current else -10.0
        return 0.0
        
    curr_title_score = score_title(profile.get("current_title", ""), is_current=True)
    score += curr_title_score
    if curr_title_score > 0:
        reasons.append(f"Strong/Medium current title ({profile.get('current_title', '')})")
    elif curr_title_score < 0:
        reasons.append(f"Negative current title ({profile.get('current_title', '')})")

    for job in history:
        t_score = score_title(job.get("title", ""), is_current=False)
        score += t_score
        
    # 3 & 4. Company Scoring (Product vs Consulting)
    product_count = 0
    consulting_count = 0
    total_jobs = len(history)

    for job in history:
        comp = job.get("company", "").lower()
        if any(x in comp for x in PRODUCT_COMPANIES):
            product_count += 1
        if any(x in comp for x in CONSULTING_COMPANIES):
            consulting_count += 1
            
    if product_count > 0:
        score += (15.0 * product_count)
        reasons.append(f"Product company experience ({product_count} roles)")
        
    if total_jobs > 0 and consulting_count == total_jobs:
        score -= 30.0  # Penalty for entirely consulting
        reasons.append("Entirely consulting career")
    elif consulting_count > 0:
        score -= (5.0 * consulting_count)
        reasons.append(f"Some consulting experience ({consulting_count} roles)")

    # 5. Evidence Keywords in Descriptions
    keyword_hits = 0
    for job in history:
        desc = job.get("description", "").lower()
        for kw in EVIDENCE_KEYWORDS:
            if kw in desc:
                keyword_hits += 1
                
    if keyword_hits > 0:
        score += (10.0 * min(keyword_hits, 5)) # Cap at 50 pts
        reasons.append(f"Evidence keywords found ({keyword_hits} hits)")

    return {
        "candidate_id": candidate["candidate_id"],
        "name": profile.get("anonymized_name", ""),
        "title": profile.get("current_title", ""),
        "score": score,
        "reasons": reasons
    }

if __name__ == "__main__":
    with open("data/sample_candidates.json") as f:
        candidates = json.load(f)
        
    results = [score_career(c) for c in candidates]
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    print("=" * 80)
    print("CAREER EVIDENCE SCORING (TOP 10)")
    print("=" * 80)
    for r in results[:10]:
        print(f"[{r['score']:>5.1f}] {r['name']} - {r['title']}")
        for reason in r["reasons"]:
            print(f"  - {reason}")
        print()

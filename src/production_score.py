def score_production(candidate):
    PRODUCTION_KEYWORDS = [
        "production",
        "deployed",
        "real users",
        "latency",
        "throughput",
        "monitoring",
        "a/b",
        "ab test",
        "experimentation",
        "evaluation",
        "serving",
        "inference",
        "online metrics",
        "offline metrics",
        "ndcg",
        "mrr",
        "map",
    ]

    score = 0.0
    history = candidate.get("career_history", [])
    
    keyword_hits = 0
    for job in history:
        desc = job.get("description", "").lower()
        for kw in PRODUCTION_KEYWORDS:
            if kw in desc:
                keyword_hits += 1

    score += (15.0 * min(keyword_hits, 4)) # Cap at 60 points
    
    return score

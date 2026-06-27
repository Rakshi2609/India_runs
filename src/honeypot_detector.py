def detect_honeypot(candidate: dict) -> float:
    """
    Returns a fraud score 0-1. Higher = more suspicious.
    If > 0.5, apply heavy penalty to final score.
    """
    fraud_signals = 0
    max_signals = 10
    
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    sig = candidate.get("redrob_signals", {})
    
    # --- Impossible experience at company ---
    # e.g., 8 years at a company founded 3 years ago
    # We can't check founding dates, but we can check duration vs YOE
    yoe = profile.get("years_of_experience", 0)
    total_career_months = sum(j.get("duration_months", 0) for j in career)
    if total_career_months > 0 and yoe * 12 < total_career_months * 0.5:
        fraud_signals += 2  # timeline doesn't add up
    
    # --- Perfect assessment scores across many skills ---
    assessments = sig.get("skill_assessment_scores", {})
    if len(assessments) >= 4:
        perfect = sum(1 for v in assessments.values() if v >= 99)
        if perfect >= 3:
            fraud_signals += 2  # suspiciously perfect
    
    # --- All skills "expert" with 60 months ---
    expert_60_count = sum(
        1 for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) >= 60
    )
    if expert_60_count >= 6:
        fraud_signals += 2  # 6 expert skills all with 5 years = fishy
    
    # --- Too many jobs in too little time ---
    if len(career) >= 8 and yoe < 5:
        fraud_signals += 2  # 8+ jobs in 5 years is impossible
    
    # --- Contradictory seniority vs experience ---
    current_title = profile.get("current_title", "").lower()
    if yoe < 3 and any(t in current_title for t in ["principal", "staff", "head of", "director", "vp"]):
        fraud_signals += 2
    
    # --- All signals maxed out (too good to be true) ---
    rr = sig.get("recruiter_response_rate", 0)
    icr = sig.get("interview_completion_rate", 0)
    oar = sig.get("offer_acceptance_rate", -1)
    if rr >= 0.99 and icr >= 0.99 and oar >= 0.99:
        fraud_signals += 2
    
    return min(fraud_signals / max_signals, 1.0)

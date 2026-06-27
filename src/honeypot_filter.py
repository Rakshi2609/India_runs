def is_honeypot(candidate):
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0)
    sig = candidate.get("redrob_signals", {})
    skills = candidate.get("skills", [])
    history = candidate.get("career_history", [])
    
    # 1. Flag impossible years of experience
    if yoe > 45: 
        return True
        
    # 2. Expert in something they have used for 0 months
    for s in skills:
        prof = s.get("proficiency", "")
        duration = s.get("duration_months", 0)
        if prof == "expert" and duration == 0:
            return True
            
    # 3. Negative job duration
    for job in history:
        dur = job.get("duration_months", 0)
        if dur < 0:
            return True
            
    # 4. Perfect assessment scores across many skills (Suspicious)
    assessments = sig.get("skill_assessment_scores", {})
    if assessments and len(assessments) >= 4:
        perfect = sum(1 for v in assessments.values() if v is not None and v >= 99)
        if perfect >= 3:
            return True
            
    # 5. Expert skills inflation (e.g. 6 expert skills with 5+ years, but total YoE doesn't align)
    expert_60_count = sum(1 for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 0) >= 60)
    if expert_60_count >= 6:
        return True
        
    # 6. Too many jobs in too little time
    if len(history) >= 8 and yoe < 5:
        return True
        
    # 7. Contradictory seniority vs experience
    current_title = profile.get("current_title", "").lower()
    if yoe < 3 and any(t in current_title for t in ["principal", "staff", "head of", "director", "vp"]):
        return True
        
    # 8. All signals maxed out (Too good to be true)
    rr = sig.get("recruiter_response_rate", 0)
    icr = sig.get("interview_completion_rate", 0)
    oar = sig.get("offer_acceptance_rate", -1)
    if rr >= 0.99 and icr >= 0.99 and oar >= 0.99:
        return True

    # 9. Timeline anomalies (cumulative job durations exceed 2x the stated overall YoE)
    total_career_months = sum(j.get("duration_months", 0) for j in history)
    if yoe > 0 and total_career_months > yoe * 12 * 2.0:
        return True
        
    return False


def detect_honeypot(candidate):
    multiplier = 1.0
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0)
    
    # 1. Impossible YOE
    if yoe > 45:
        return 0.0
        
    skills = candidate.get("skills", [])
    for s in skills:
        prof = s.get("proficiency", "")
        duration = s.get("duration_months", 0)
        # 2. Expert with 0 duration
        if prof == "expert" and duration == 0:
            return 0.0
            
    history = candidate.get("career_history", [])
    for job in history:
        dur = job.get("duration_months", 0)
        # 3. Negative duration
        if dur < 0:
            return 0.0

    # 4. Seniority vs YOE contradiction
    title = profile.get("current_title", "").lower()
    if ("principal" in title or "staff" in title or "director" in title) and yoe <= 3:
        multiplier *= 0.1

    # 5. Short-tenure / title-chasing
    if len(history) >= 4:
        short_jobs = sum(1 for job in history if 0 < job.get("duration_months", 999) < 6)
        if short_jobs >= 3:
            multiplier *= 0.5
            
    # 6. Overlapping timeline / excessive experience sum
    total_months = sum(job.get("duration_months", 0) for job in history)
    if total_months > (yoe + 3) * 12 and len(history) >= 2:
        multiplier *= 0.5

    return multiplier

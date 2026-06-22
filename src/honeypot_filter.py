def is_honeypot(candidate):
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0)
    
    if yoe > 45: # Flag impossible years of experience
        return True
        
    skills = candidate.get("skills", [])
    for s in skills:
        prof = s.get("proficiency", "")
        duration = s.get("duration_months", 0)
        # Expert in something they have used for 0 months
        if prof == "expert" and duration == 0:
            return True
            
    history = candidate.get("career_history", [])
    for job in history:
        dur = job.get("duration_months", 0)
        if dur < 0:
            return True

    return False

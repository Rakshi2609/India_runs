def generate_reasoning(c, raw):
    profile = c.get("profile", {})
    signals = c.get("redrob_signals", {})
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Engineer")
    notice = signals.get("notice_period_days", 30)
    
    # JD Connection & Facts
    reasons = []
    
    # 1. Career/Product connection
    yoe_context = "Ideal" if 5 <= yoe <= 9 else "Extensive" if yoe > 9 else "Early-career"
    if raw["career_raw"] > 70:
        reasons.append(f"{yoe_context} experience ({yoe} years) as a {title} with a proven track record in relevant domains.")
    elif raw["career_raw"] > 40:
        reasons.append(f"Solid profile with {yoe} years of experience, currently working as a {title}.")
    else:
        reasons.append(f"Primarily an adjacent background (current title: {title}, {yoe} YOE).")

    # 2. Production evidence
    if raw["production_raw"] > 40:
        reasons.append("Shows clear production-level ML deployment experience, matching the 'shipper' over 'researcher' requirement.")
    elif raw["production_raw"] < 20:
        reasons.append("Lacks explicit evidence of large-scale production deployments.")

    # 3. Behavioral / Notice period concerns
    concerns = []
    if notice > 30:
        concerns.append(f"high notice period ({notice} days)")
    
    resp_rate = signals.get("recruiter_response_rate", 1.0)
    if resp_rate < 0.5:
        concerns.append(f"low recruiter response rate ({resp_rate:.0%})")
        
    if concerns:
        reasons.append(f"Noted concerns: {', '.join(concerns)}.")
    elif raw.get("behavior_raw", 1.0) > 1.0:
        reasons.append(f"Highly engaged candidate with {notice}-day notice period.")

    # 4. Semantic match
    if raw["semantic_raw"] > 0.6:
        reasons.append("Narrative aligns well with our specific requirement for building ranking and retrieval systems.")

    # Ensure variation
    skills = [s["name"] for s in c.get("skills", []) if "duration_months" in s and s["duration_months"] > 12]
    if skills:
        top_skills = skills[:3]
        reasons.append(f"Brings hands-on experience with {', '.join(top_skills)}.")
        
    return " ".join(reasons)

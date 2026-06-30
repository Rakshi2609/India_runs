import random

def generate_reasoning(c, raw):
    random.seed(c.get("candidate_id", 0))
    profile = c.get("profile", {})
    skills = [s.get("name", "") for s in c.get("skills", []) if "name" in s]
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "Engineer")
    notice = c.get("redrob_signals", {}).get("notice_period_days", 30)
    
    companies = [job.get("company", "") for job in c.get("career_history", []) if job.get("company")]
    last_company = companies[0] if companies else "their current employer"
    
    reasons = []
    
    # Career evaluation
    if raw["career_raw"] > 60:
        opts = [
            f"With {yoe} years in the industry, this candidate has built a robust foundation, notably at {last_company}.",
            f"Currently serving as a {title}, they possess deep domain expertise directly relevant to the JD.",
            f"The candidate's {yoe}-year tenure aligns strongly with our core ranking and retrieval requirements."
        ]
        reasons.append(random.choice(opts))
    elif raw["career_raw"] > 30:
        reasons.append(f"They offer a moderate {yoe}-year track record, primarily operating as a {title}.")
    else:
        reasons.append(f"Their background is somewhat adjacent, with {yoe} years of general engineering experience.")

    # Production capabilities
    if raw["production_raw"] > 40:
        tech_mention = f" utilizing {skills[0]} and {skills[1]}" if len(skills) >= 2 else ""
        opts = [
            f"Critically, they demonstrate concrete production deployment capabilities{tech_mention}, distinguishing them from purely academic profiles.",
            f"Their career history shows clear evidence of shipping real ML models to production environments.",
            f"Unlike many researchers, they have documented experience handling large-scale engineering systems and infrastructure."
        ]
        reasons.append(random.choice(opts))
    elif raw["production_raw"] < 20:
        reasons.append("There is a notable lack of explicit evidence regarding large-scale production deployments.")

    # Semantic JD match
    if raw["semantic_raw"] > 0.65:
        opts = [
            "The semantic density of their resume closely matches the JD's focus on search ecosystems.",
            "Analysis of their project descriptions reveals strong overlap with our specific machine learning needs.",
            "They speak the exact technical language outlined in the JD, particularly around retrieval and ranking."
        ]
        reasons.append(random.choice(opts))

    # Behavioral and Availability
    if notice <= 15:
        reasons.append(f"Their short {notice}-day notice period is a valuable logistical advantage for an immediate start.")
    
    if raw.get("behavior_raw", 1.0) > 1.0:
        reasons.append("Signals indicate excellent recruiter engagement and high responsiveness.")
        
    return " ".join(reasons).strip()

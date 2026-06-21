def build_candidate_text(candidate):
    profile = candidate.get("profile", {})
    parts = []

    parts.append(profile.get("headline", ""))
    parts.append(profile.get("summary", ""))
    parts.append(profile.get("current_title", ""))

    for skill in candidate.get("skills", []):
        parts.append(skill.get("name", ""))

    for job in candidate.get("career_history", []):
        parts.append(job.get("title", ""))
        parts.append(job.get("description", ""))

    # filter out any empty strings
    parts = [p for p in parts if p and p.strip()]
    return "\n".join(parts)

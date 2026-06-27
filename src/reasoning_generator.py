def generate_reasoning(candidate_scores):
    reasons = []

    career_raw = candidate_scores["career_raw"]
    production_raw = candidate_scores["production_raw"]
    behavior_raw = candidate_scores["behavior_raw"]
    availability_raw = candidate_scores["availability_raw"]

    if career_raw > 70:
        reasons.append("Strong experience in ranking, retrieval, or recommendation systems.")
    elif career_raw > 30:
        reasons.append("Solid technical background with relevant engineering experience.")
        
    if production_raw > 30:
        reasons.append("Demonstrated production ML deployment and evaluation experience.")

    if behavior_raw > 60:
        reasons.append("Strong recruiter engagement signals and activity.")

    if availability_raw > 50:
        reasons.append("Favorable hiring availability (short notice period/flexible).")

    if not reasons:
        reasons.append("Candidate matches baseline requirements but lacks strong signals in key areas.")

    return " ".join(reasons)

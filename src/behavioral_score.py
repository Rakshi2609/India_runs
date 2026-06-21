def score_behavioral(candidate):
    sig = candidate.get("redrob_signals", {})
    score = 0.0

    score += sig.get("recruiter_response_rate", 0) * 30.0
    score += sig.get("interview_completion_rate", 0) * 25.0

    offer_acc = sig.get("offer_acceptance_rate", -1)
    if offer_acc != -1:
        score += offer_acc * 15.0

    score += min(sig.get("saved_by_recruiters_30d", 0), 10) * 2.0
    score += min(sig.get("search_appearance_30d", 0) / 50.0, 10.0)
    score += min(sig.get("github_activity_score", 0), 10.0)

    if sig.get("open_to_work_flag"):
        score += 10.0

    return score

def score_availability(candidate):
    sig = candidate.get("redrob_signals", {})
    score = 0.0

    notice = sig.get("notice_period_days", 999)

    if notice <= 30:
        score += 50.0
    elif notice <= 60:
        score += 35.0
    elif notice <= 90:
        score += 20.0

    if sig.get("willing_to_relocate"):
        score += 20.0

    pref_mode = sig.get("preferred_work_mode", "").lower()
    if pref_mode in ["flexible", "hybrid", "onsite"]:
        score += 10.0

    return score

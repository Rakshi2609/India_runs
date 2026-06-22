def score_behavioral(candidate):
    sig = candidate.get("redrob_signals", {})
    multiplier = 1.0

    # Strong positive signals
    response_rate = sig.get("recruiter_response_rate", 0.5)
    if response_rate > 0.8:
        multiplier *= 1.1
    elif response_rate < 0.2:
        multiplier *= 0.5 # Severe penalty for ghosting

    offer_acc = sig.get("offer_acceptance_rate", -1)
    if offer_acc > 0.8:
        multiplier *= 1.1

    if sig.get("open_to_work_flag"):
        multiplier *= 1.05

    # Activity signals
    from datetime import datetime
    try:
        last_active = datetime.strptime(sig.get("last_active_date", "2020-01-01"), "%Y-%m-%d")
        if (datetime.now() - last_active).days > 180:
            multiplier *= 0.7 # Inactive penalty
    except:
        pass

    return multiplier

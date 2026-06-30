def calculate_buzzword_penalty(candidate, career_raw_score):
    penalty = 0.0
    skills = [s.get("name", "").lower() for s in candidate.get("skills", [])]
    
    buzzwords = ["langchain", "openai", "chatgpt", "generative ai"]
    
    has_buzzword = any(any(bw in s for bw in buzzwords) for s in skills)
    
    if has_buzzword and career_raw_score < 20.0:
        penalty += 100.0
        
    return penalty

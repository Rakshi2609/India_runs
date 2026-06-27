# technical_fit.py

MUST_HAVE_SKILLS = {
    # Core retrieval & search
    "embeddings", "vector search", "semantic search", "retrieval", "rag",
    "retrieval augmented generation", "hybrid search", "dense retrieval",
    "bm25", "information retrieval",
    
    # Vector databases
    "faiss", "pinecone", "weaviate", "qdrant", "milvus", "opensearch",
    "elasticsearch", "chroma", "pgvector",
    
    # ML/AI core
    "nlp", "natural language processing", "machine learning", "deep learning",
    "transformers", "bert", "sentence-transformers", "llm", "large language models",
    "pytorch", "tensorflow",
    
    # Ranking & evaluation
    "ranking", "learning to rank", "ndcg", "mrr", "reranking", "reranker",
    
    # Production ML
    "mlops", "model serving", "inference", "model deployment",
}

NICE_TO_HAVE_SKILLS = {
    "lora", "qlora", "peft", "fine-tuning", "fine tuning", "finetuning",
    "xgboost", "recommendation system", "recommender",
    "a/b testing", "feature engineering",
    "spark", "kafka", "airflow", "kubeflow",
}

ADJACENT_ONLY_SKILLS = {
    "langchain", "openai", "chatgpt", "prompt engineering",
    "computer vision", "image classification", "object detection",
    "speech recognition", "tts", "robotics",
}

def score_technical_fit(candidate: dict) -> float:
    """
    Score 0-100 based on how well skills match JD.
    Not pure keyword matching — weights by proficiency + duration + endorsements + assessments.
    """
    skills = candidate.get("skills", [])
    if not skills:
        return 0.0
    
    must_score = 0.0
    nice_score = 0.0
    adjacent_penalty = 0.0
    
    assessment_scores = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})
    # Lowercase assessment keys for case-insensitive lookup
    assessments_lower = {k.lower().strip(): v for k, v in assessment_scores.items() if v is not None}
    
    for skill in skills:
        name = skill.get("name", "").lower().strip()
        if not name:
            continue
        proficiency = skill.get("proficiency", "beginner")
        duration = skill.get("duration_months", 0)
        endorsements = skill.get("endorsements", 0)
        
        # 1. Proficiency multiplier
        prof_mult = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.85, "expert": 1.0}
        pm = prof_mult.get(proficiency, 0.3)
        
        # 2. Duration multiplier (cap at 36 months = 3 years)
        dm = min(duration / 36.0, 1.0)
        
        # 3. Endorsement boost (cap at 50)
        em = min(endorsements / 50.0, 1.0) * 0.2 + 0.8  # 0.8 to 1.0
        
        skill_weight = pm * (0.7 + 0.3 * dm) * em
        
        # 4. Assessment score lookup
        # Check if the skill matches any of the assessment names
        matched_assessment = False
        for k_lower, val in assessments_lower.items():
            if k_lower in name or name in k_lower:
                # Found a match, apply multiplier based on score (70+ is good, below 40 is bad)
                skill_weight *= (0.5 + val / 200.0)  # e.g., 100/200 + 0.5 = 1.0 multiplier
                matched_assessment = True
                break
        
        # Categorize skill
        is_must = False
        is_nice = False
        is_adj = False
        
        if any(must in name for must in MUST_HAVE_SKILLS) or name in MUST_HAVE_SKILLS:
            must_score += skill_weight
            is_must = True
        elif any(nice in name for nice in NICE_TO_HAVE_SKILLS) or name in NICE_TO_HAVE_SKILLS:
            nice_score += skill_weight * 0.5
            is_nice = True
        elif any(adj in name for adj in ADJACENT_ONLY_SKILLS) or name in ADJACENT_ONLY_SKILLS:
            adjacent_penalty += 0.05
            is_adj = True
            
    # Base score normalized (cap at matching ~6 must-have skills and ~3 nice-to-have skills)
    base = min(must_score / 6.0, 1.0) * 0.7 + min(nice_score / 3.0, 1.0) * 0.3
    
    # Penalty if profile is ONLY adjacent skills with zero core
    if must_score < 0.1 and adjacent_penalty > 0.2:
        base *= 0.3  # Heavy penalty for LangChain-only/cv-only profiles
        
    return min(base, 1.0) * 100.0

# HireIQ — India Runs Data & AI Challenge
## Complete Phase-Based Build Plan
> Deadline: July 2, 2026 | Solo | CPU-only | 5 min runtime | Top 100 from 100K candidates

---

## What You're Actually Building

A Python script (`rank.py`) that:
1. Reads `candidates.jsonl` (100K candidates, ~465MB)
2. Scores every candidate against the JD for **Senior AI Engineer – Founding Team at Redrob AI**
3. Outputs a `submission.csv` with the top 100, ranked best-to-worst, with reasoning

**Judged on:** NDCG@10 (50%) + NDCG@50 (30%) + MAP (15%) + P@10 (5%)
**Eliminated if:** honeypot rate > 10% in top 100 | can't reproduce in 5 min CPU | can't defend in interview

---

## The JD in Plain English (Read This Before Coding Anything)

The role is **Senior AI Engineer at an AI startup (Series A)**. They need someone who:

### MUST HAVE (hard requirements)
- Production embeddings/retrieval systems (not tutorials — real deployed systems)
- Vector DB experience (Pinecone, Weaviate, Qdrant, Milvus, FAISS, Elasticsearch)
- Strong Python
- Evaluation frameworks for ranking (NDCG, MRR, MAP, A/B testing)
- 5–9 years experience (flexible if signals are strong)
- **Product company experience** — NOT pure consulting (TCS, Infosys, Wipro = red flag)
- Has **written production code in last 18 months** (not just "architect")

### NICE TO HAVE (bonus)
- LLM fine-tuning (LoRA, QLoRA, PEFT)
- Learning-to-rank (XGBoost, neural LTR)
- HR-tech / marketplace background
- Open-source AI contributions
- Located in Pune/Noida/Hyderabad/Mumbai/Delhi NCR or willing to relocate

### HARD REJECTIONS (penalty in score)
| Red Flag | Why |
|---|---|
| Pure research / academic / PhD with no production | Explicitly disqualified |
| LangChain-only, OpenAI API wrapper engineers | Explicitly disqualified |
| "Architect" who hasn't coded in 18+ months | Explicitly disqualified |
| Entire career in TCS/Infosys/Wipro/Accenture/Cognizant | Bad fit signal |
| CV/Speech/Robotics only, no NLP/IR | Wrong domain |
| Job-hopper (1.5 yr avg, title-chasing) | Culture mismatch |

### The Hidden Trap (JD literally tells you)
> "A Tier 5 candidate may not use the words 'RAG' or 'Pinecone' but if they built a recommendation system at a product company, they fit. A candidate with all AI keywords but title 'Marketing Manager' is not a fit."

**Keyword matching will fail. You must score by understanding, not by counting.**

---

## Scoring Architecture

```
Final Score = 
  0.35 × Technical Fit Score
+ 0.25 × Career Fit Score  
+ 0.20 × Behavioral Signal Score
+ 0.12 × Production Experience Score
+ 0.08 × Availability Score
- honeypot_penalty (if fraud detected)
```

All components normalized to [0, 1].

---

## Phase 0 — Setup (Day 1, ~1 hour)

### What to do
```bash
# 1. Create project structure
mkdir hireiq && cd hireiq
mkdir -p src data output tests

# 2. Copy dataset files here
cp /path/to/candidates.jsonl data/
cp /path/to/sample_candidates.json data/
cp /path/to/job_description.docx data/

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 4. Install dependencies
pip install sentence-transformers numpy pandas tqdm
```

### `requirements.txt`
```
sentence-transformers==2.7.0
numpy>=1.24
pandas>=2.0
tqdm>=4.65
```

### Why these packages?
- `sentence-transformers` — for embedding the JD and candidates (CPU-friendly, all-MiniLM-L6-v2 is fast)
- `numpy` — score math
- `pandas` — CSV output
- `tqdm` — progress bar so you know it's not frozen

### Checkpoint ✅
Run `python -c "from sentence_transformers import SentenceTransformer; print('ok')"` — should print `ok`.

---

## Phase 1 — Explore the Data (Day 1, ~2 hours)

**Do NOT skip this. Every weight in your formula comes from this phase.**

### Step 1.1 — Run this exploration script

Create `src/explore.py`:

```python
import json
import random

with open("data/sample_candidates.json") as f:
    candidates = json.load(f)

print(f"Total sample: {len(candidates)}")

# Look at 5 random candidates carefully
for c in random.sample(candidates, 5):
    p = c["profile"]
    sig = c["redrob_signals"]
    
    print("="*60)
    print(f"ID: {c['candidate_id']}")
    print(f"Title: {p['current_title']} | YOE: {p['years_of_experience']}")
    print(f"Company: {p['current_company']} (size: {p['current_company_size']})")
    print(f"Headline: {p['headline']}")
    print(f"Skills: {[s['name'] for s in c['skills'][:8]]}")
    
    # Career history
    for job in c["career_history"][:2]:
        print(f"  - {job['title']} at {job['company']} ({job['duration_months']}mo)")
    
    # Signals
    print(f"Active: {sig['last_active_date']} | Open: {sig['open_to_work_flag']}")
    print(f"Recruiter response: {sig['recruiter_response_rate']}")
    print(f"Notice: {sig['notice_period_days']} days")
    print(f"GitHub score: {sig['github_activity_score']}")
```

Run it 3–4 times. Look at profiles. **Ask yourself: would a human recruiter call this person?**

### Step 1.2 — Understand the distribution

```python
# Add to explore.py
yoes = [c["profile"]["years_of_experience"] for c in candidates]
print(f"\nYOE: min={min(yoes):.1f}, max={max(yoes):.1f}, avg={sum(yoes)/len(yoes):.1f}")

all_skills = []
for c in candidates:
    all_skills.extend([s["name"] for s in c["skills"]])
from collections import Counter
print("\nTop 20 skills in pool:")
for skill, count in Counter(all_skills).most_common(20):
    print(f"  {skill}: {count}")
```

### What you'll learn
- What the typical candidate looks like
- How skills are named (exact strings matter for matching)
- How fresh/active profiles are
- Whether honeypots stand out visually

### Checkpoint ✅
Write down 3 candidates you'd personally shortlist and 3 you'd reject. This becomes your ground truth for testing.

---

## Phase 2 — Build the Scoring Components (Day 2, ~4 hours)

Build each component as a standalone function. Test each one before combining.

### Step 2.1 — Technical Fit Score

This is the most important component (35% weight).

Create `src/technical_fit.py`:

```python
# JD-derived skill lists — built from reading the JD carefully
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

# These skills alone are NOT disqualifiers but should not boost score much
ADJACENT_ONLY_SKILLS = {
    "langchain", "openai", "chatgpt", "prompt engineering",
    "computer vision", "image classification", "object detection",
    "speech recognition", "tts", "robotics",
}

def score_technical_fit(candidate: dict) -> float:
    """
    Score 0-1 based on how well skills match JD.
    NOT pure keyword matching — weights by proficiency + duration + endorsements.
    """
    skills = candidate.get("skills", [])
    if not skills:
        return 0.0
    
    must_score = 0.0
    nice_score = 0.0
    adjacent_penalty = 0.0
    
    for skill in skills:
        name = skill["name"].lower().strip()
        proficiency = skill.get("proficiency", "beginner")
        duration = skill.get("duration_months", 0)
        endorsements = skill.get("endorsements", 0)
        
        # Proficiency multiplier
        prof_mult = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.85, "expert": 1.0}
        pm = prof_mult.get(proficiency, 0.3)
        
        # Duration multiplier (cap at 36 months = 3 years)
        dm = min(duration / 36.0, 1.0)
        
        # Endorsement boost (cap at 50)
        em = min(endorsements / 50.0, 1.0) * 0.2 + 0.8  # 0.8 to 1.0
        
        skill_weight = pm * (0.7 + 0.3 * dm) * em
        
        # Check assessment scores (from redrob signals)
        assessment_scores = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})
        if name in [k.lower() for k in assessment_scores]:
            # Find the score
            for k, v in assessment_scores.items():
                if k.lower() == name:
                    # Assessment score above 70 is good, below 40 is concern
                    skill_weight *= (0.5 + v / 200.0)  # 0.5 to 1.0 multiplier
        
        # Categorize
        if any(must in name for must in MUST_HAVE_SKILLS) or name in MUST_HAVE_SKILLS:
            must_score += skill_weight
        elif any(nice in name for nice in NICE_TO_HAVE_SKILLS) or name in NICE_TO_HAVE_SKILLS:
            nice_score += skill_weight * 0.5
        elif any(adj in name for adj in ADJACENT_ONLY_SKILLS) or name in ADJACENT_ONLY_SKILLS:
            adjacent_penalty += 0.05
    
    # Normalize must_score (cap at ~10 matched skills = 1.0)
    base = min(must_score / 6.0, 1.0) * 0.7 + min(nice_score / 3.0, 1.0) * 0.3
    
    # Penalty if profile is ONLY adjacent skills with zero core
    if must_score < 0.1 and adjacent_penalty > 0.2:
        base *= 0.3  # Heavy penalty for LangChain-only profiles
    
    return min(base, 1.0)
```

**Why this works:** A "Marketing Manager" who keyword-stuffed 9 AI skills but has 0 duration months and 0 endorsements gets a low score. A real ML engineer with 36 months of "NLP" experience at advanced level gets a high score.

---

### Step 2.2 — Career Fit Score

Create `src/career_fit.py`:

```python
STRONG_TITLES = [
    "ai engineer", "ml engineer", "machine learning engineer",
    "applied scientist", "nlp engineer", "search engineer",
    "applied ml", "applied ai", "data scientist",
    "senior ai", "senior ml", "principal ai",
    "research engineer",  # OK if production work exists
]

ACCEPTABLE_TITLES = [
    "software engineer", "backend engineer", "data engineer",
    "platform engineer", "full stack", "software developer",
]

BAD_TITLES = [
    "marketing", "sales", "hr", "human resources", "content writer",
    "graphic designer", "accountant", "civil engineer", "mechanical engineer",
    "customer support", "operations manager",
]

CONSULTING_COMPANIES = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "mphasis", "tech mahindra",
]

def score_career_fit(candidate: dict) -> float:
    profile = candidate["profile"]
    career = candidate.get("career_history", [])
    
    score = 0.0
    
    # --- Current title fit ---
    current_title = profile.get("current_title", "").lower()
    
    if any(t in current_title for t in STRONG_TITLES):
        score += 0.40
    elif any(t in current_title for t in ACCEPTABLE_TITLES):
        score += 0.20
    elif any(t in current_title for t in BAD_TITLES):
        score -= 0.20  # penalty
    
    # --- Years of experience ---
    yoe = profile.get("years_of_experience", 0)
    if 5 <= yoe <= 9:
        score += 0.20   # ideal range
    elif 4 <= yoe < 5 or 9 < yoe <= 12:
        score += 0.12   # acceptable
    elif yoe < 2:
        score += 0.0    # too junior
    else:
        score += 0.06   # senior but possibly over-experienced
    
    # --- Career history analysis ---
    total_months = 0
    ai_months = 0
    startup_bonus = 0
    consulting_penalty = 0
    
    for job in career:
        dur = job.get("duration_months", 0)
        title = job.get("title", "").lower()
        company = job.get("company", "").lower()
        desc = job.get("description", "").lower()
        size = job.get("company_size", "")
        
        total_months += dur
        
        # Was this an AI/ML role?
        if any(t in title for t in STRONG_TITLES):
            ai_months += dur
        
        # Production signals in description
        production_words = ["deployed", "production", "serving", "latency",
                           "pipeline", "scale", "inference", "monitoring", "a/b"]
        if any(w in desc for w in production_words):
            ai_months += dur * 0.3  # extra credit for production context
        
        # Startup bonus (small companies = startup experience)
        if size in ["1-10", "11-50", "51-200"]:
            startup_bonus += min(dur / 24.0, 1.0) * 0.05
        
        # Consulting penalty (entire career consulting)
        if any(c in company for c in CONSULTING_COMPANIES):
            consulting_penalty += 0.05
    
    # AI career ratio
    if total_months > 0:
        ai_ratio = ai_months / total_months
        score += ai_ratio * 0.25
    
    # Startup bonus (cap at 0.10)
    score += min(startup_bonus, 0.10)
    
    # Consulting penalty
    # Only penalize if ALL or most career is consulting
    career_at_consulting = consulting_penalty / max(len(career), 1)
    if career_at_consulting > 0.6:
        score -= 0.15  # mostly consulting career
    
    # Job hopping penalty: avg tenure < 18 months
    if len(career) >= 3 and total_months > 0:
        avg_tenure = total_months / len(career)
        if avg_tenure < 18:
            score -= 0.10
    
    return max(0.0, min(score, 1.0))
```

---

### Step 2.3 — Production Experience Score

This is a **separate component** because the JD mentions "production" 8+ times.

Create `src/production_score.py`:

```python
PRODUCTION_SIGNALS = [
    "deployed", "deployment", "production", "prod", "serving", "served",
    "latency", "throughput", "sla", "uptime", "real users", "at scale",
    "a/b test", "monitoring", "observability", "model drift",
    "inference pipeline", "model serving", "online", "live",
    "millions", "billion", "qps", "requests per second",
]

RESEARCH_ONLY_SIGNALS = [
    "published", "publication", "paper", "arxiv", "thesis", "dissertation",
    "research lab", "academic", "university research", "phd research",
    "conference paper", "workshop", "ieee", "neurips", "icml", "iclr",
]

RECENT_CODE_SIGNALS = [
    "built", "implemented", "developed", "shipped", "launched", "owned",
    "designed and built", "end-to-end",
]

def score_production_experience(candidate: dict) -> float:
    career = candidate.get("career_history", [])
    
    prod_score = 0.0
    research_penalty = 0.0
    total_jobs = len(career)
    
    if total_jobs == 0:
        return 0.0
    
    for job in career:
        desc = job.get("description", "").lower()
        title = job.get("title", "").lower()
        is_current = job.get("is_current", False)
        dur = job.get("duration_months", 0)
        
        job_prod_score = 0.0
        job_research_score = 0.0
        
        for word in PRODUCTION_SIGNALS:
            if word in desc:
                job_prod_score += 1
        
        for word in RESEARCH_ONLY_SIGNALS:
            if word in desc or word in title:
                job_research_score += 1
        
        # Normalize per-job (cap at 5 signals each)
        job_prod_score = min(job_prod_score / 5.0, 1.0)
        job_research_score = min(job_research_score / 3.0, 1.0)
        
        # Current job weighted more (have they coded recently?)
        weight = 2.0 if is_current else 1.0
        prod_score += job_prod_score * weight * (dur / 12.0)
        
        # Pure research without production = penalty
        if job_research_score > 0.5 and job_prod_score < 0.2:
            research_penalty += 0.15
    
    # GitHub activity — real engineers commit
    github = candidate.get("redrob_signals", {}).get("github_activity_score", -1)
    if github > 60:
        prod_score += 0.20
    elif github > 30:
        prod_score += 0.10
    elif github == -1:
        prod_score -= 0.05  # no github linked
    
    # Normalize
    final = prod_score / (total_jobs * 2.0 + 1.0)
    final = max(0.0, final - research_penalty)
    
    return min(final, 1.0)
```

---

### Step 2.4 — Behavioral Signal Score

Create `src/behavioral_score.py`:

```python
from datetime import date, datetime

def score_behavioral_signals(candidate: dict) -> float:
    sig = candidate.get("redrob_signals", {})
    score = 0.0
    
    # --- Recruiter response rate (most predictive signal) ---
    rr = sig.get("recruiter_response_rate", 0)
    score += rr * 0.25  # up to 0.25
    
    # --- Interview completion rate ---
    icr = sig.get("interview_completion_rate", 0)
    score += icr * 0.15
    
    # --- Offer acceptance rate ---
    oar = sig.get("offer_acceptance_rate", -1)
    if oar >= 0:
        score += oar * 0.10
    # -1 means no history — neutral
    
    # --- Recency (last active) ---
    try:
        last_active = datetime.strptime(sig.get("last_active_date", "2020-01-01"), "%Y-%m-%d").date()
        today = date.today()
        days_ago = (today - last_active).days
        if days_ago <= 30:
            score += 0.15
        elif days_ago <= 90:
            score += 0.10
        elif days_ago <= 180:
            score += 0.05
        else:
            score -= 0.10  # 6+ months inactive
    except:
        pass
    
    # --- Saved by recruiters (market validation) ---
    saved = sig.get("saved_by_recruiters_30d", 0)
    score += min(saved / 10.0, 1.0) * 0.10
    
    # --- Profile completeness ---
    completeness = sig.get("profile_completeness_score", 0)
    score += (completeness / 100.0) * 0.10
    
    # --- Open to work ---
    if sig.get("open_to_work_flag", False):
        score += 0.10
    
    # --- Quick responder (< 24 hrs avg response time) ---
    avg_response = sig.get("avg_response_time_hours", 999)
    if avg_response < 12:
        score += 0.05
    elif avg_response < 48:
        score += 0.02
    
    # --- Verified contact (trustworthiness) ---
    if sig.get("verified_email", False) and sig.get("verified_phone", False):
        score += 0.05
    
    return min(score, 1.0)
```

---

### Step 2.5 — Availability Score

Create `src/availability_score.py`:

```python
def score_availability(candidate: dict) -> float:
    sig = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})
    score = 0.5  # start neutral
    
    # --- Notice period (JD loves < 30 days) ---
    notice = sig.get("notice_period_days", 90)
    if notice == 0:
        score += 0.30  # immediately available
    elif notice <= 30:
        score += 0.25  # great
    elif notice <= 60:
        score += 0.10  # okay
    elif notice <= 90:
        score += 0.0   # neutral
    else:
        score -= 0.15  # 90+ days is a concern
    
    # --- Location (JD: Pune/Noida, open to Hyd/Mumbai/Delhi NCR) ---
    location = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    
    PREFERRED_CITIES = ["pune", "noida", "delhi", "ncr", "gurgaon", "gurugram",
                        "hyderabad", "mumbai", "bangalore", "bengaluru"]
    
    if country == "india":
        if any(city in location for city in PREFERRED_CITIES):
            score += 0.15
        else:
            score += 0.05  # India but not preferred city
    else:
        # Outside India — case by case, no visa sponsorship
        score -= 0.10
    
    # --- Willing to relocate ---
    if sig.get("willing_to_relocate", False):
        score += 0.10
    
    # --- Work mode (JD says hybrid, flexible cadence) ---
    work_mode = sig.get("preferred_work_mode", "")
    if work_mode in ["hybrid", "flexible"]:
        score += 0.05
    elif work_mode == "onsite":
        score += 0.05
    elif work_mode == "remote":
        score -= 0.05  # JD is hybrid-first
    
    # --- Salary check (ballpark — don't over-filter) ---
    salary = sig.get("expected_salary_range_inr_lpa", {})
    sal_min = salary.get("min", 0)
    if sal_min > 80:  # > 80 LPA min expectation is probably too high for Series A
        score -= 0.10
    
    return max(0.0, min(score, 1.0))
```

---

### Step 2.6 — Honeypot Detector

Create `src/honeypot_detector.py`:

```python
def detect_honeypot(candidate: dict) -> float:
    """
    Returns a fraud score 0-1. Higher = more suspicious.
    If > 0.5, apply heavy penalty to final score.
    """
    fraud_signals = 0
    max_signals = 10
    
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    sig = candidate.get("redrob_signals", {})
    
    # --- Impossible experience at company ---
    # e.g., 8 years at a company founded 3 years ago
    # We can't check founding dates, but we can check duration vs YOE
    yoe = profile.get("years_of_experience", 0)
    total_career_months = sum(j.get("duration_months", 0) for j in career)
    if total_career_months > 0 and yoe * 12 < total_career_months * 0.5:
        fraud_signals += 2  # timeline doesn't add up
    
    # --- Perfect assessment scores across many skills ---
    assessments = sig.get("skill_assessment_scores", {})
    if len(assessments) >= 4:
        perfect = sum(1 for v in assessments.values() if v >= 99)
        if perfect >= 3:
            fraud_signals += 2  # suspiciously perfect
    
    # --- All skills "expert" with 60 months ---
    expert_60_count = sum(
        1 for s in skills
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) >= 60
    )
    if expert_60_count >= 6:
        fraud_signals += 2  # 6 expert skills all with 5 years = fishy
    
    # --- Too many jobs in too little time ---
    if len(career) >= 8 and yoe < 5:
        fraud_signals += 2  # 8+ jobs in 5 years is impossible
    
    # --- Contradictory seniority vs experience ---
    current_title = profile.get("current_title", "").lower()
    if yoe < 3 and any(t in current_title for t in ["principal", "staff", "head of", "director", "vp"]):
        fraud_signals += 2
    
    # --- All signals maxed out (too good to be true) ---
    rr = sig.get("recruiter_response_rate", 0)
    icr = sig.get("interview_completion_rate", 0)
    oar = sig.get("offer_acceptance_rate", -1)
    if rr >= 0.99 and icr >= 0.99 and oar >= 0.99:
        fraud_signals += 2
    
    return min(fraud_signals / max_signals, 1.0)
```

---

## Phase 3 — Build the Main Ranker (Day 3, ~3 hours)

Now combine everything into `rank.py`:

```python
#!/usr/bin/env python3
"""
HireIQ — Redrob Hackathon Ranker
Usage: python rank.py --candidates data/candidates.jsonl --out submission.csv
"""

import json
import argparse
import csv
from tqdm import tqdm

from src.technical_fit import score_technical_fit
from src.career_fit import score_career_fit
from src.production_score import score_production_experience
from src.behavioral_score import score_behavioral_signals
from src.availability_score import score_availability
from src.honeypot_detector import detect_honeypot

# Component weights — derived from JD analysis
WEIGHTS = {
    "technical":    0.35,
    "career":       0.25,
    "behavioral":   0.20,
    "production":   0.12,
    "availability": 0.08,
}

def score_candidate(candidate: dict) -> dict:
    tech    = score_technical_fit(candidate)
    career  = score_career_fit(candidate)
    prod    = score_production_experience(candidate)
    behav   = score_behavioral_signals(candidate)
    avail   = score_availability(candidate)
    
    base_score = (
        tech    * WEIGHTS["technical"] +
        career  * WEIGHTS["career"] +
        prod    * WEIGHTS["production"] +
        behav   * WEIGHTS["behavioral"] +
        avail   * WEIGHTS["availability"]
    )
    
    # Honeypot check
    fraud = detect_honeypot(candidate)
    if fraud > 0.5:
        base_score *= 0.1  # 90% penalty — virtually removes from top 100
    elif fraud > 0.3:
        base_score *= 0.5
    
    return {
        "candidate_id": candidate["candidate_id"],
        "score": round(base_score, 6),
        "components": {
            "technical": round(tech, 3),
            "career": round(career, 3),
            "production": round(prod, 3),
            "behavioral": round(behav, 3),
            "availability": round(avail, 3),
            "fraud": round(fraud, 3),
        },
        "_candidate": candidate,  # keep for reasoning generation
    }

def generate_reasoning(result: dict) -> str:
    c = result["_candidate"]
    comp = result["components"]
    p = c["profile"]
    sig = c["redrob_signals"]
    
    title = p.get("current_title", "Unknown")
    yoe = p.get("years_of_experience", 0)
    notice = sig.get("notice_period_days", "?")
    rr = sig.get("recruiter_response_rate", 0)
    
    # Build specific reasoning from actual profile data
    strengths = []
    concerns = []
    
    if comp["technical"] > 0.6:
        top_skills = [s["name"] for s in c.get("skills", [])
                      if s.get("proficiency") in ["advanced", "expert"]][:3]
        strengths.append(f"strong technical fit ({', '.join(top_skills)})")
    
    if comp["production"] > 0.5:
        strengths.append("demonstrated production ML experience")
    
    if comp["career"] > 0.5:
        strengths.append(f"{yoe:.1f}yrs in relevant roles")
    
    if sig.get("open_to_work_flag"):
        strengths.append("actively seeking")
    
    if rr > 0.7:
        strengths.append(f"high recruiter response rate ({rr:.0%})")
    
    if notice > 60:
        concerns.append(f"notice period {notice}d")
    
    if comp["behavioral"] < 0.3:
        concerns.append("low platform engagement")
    
    if comp["technical"] < 0.3:
        concerns.append("limited core AI/ML skills")
    
    parts = []
    if strengths:
        parts.append(f"{title} with {yoe:.1f}yrs: " + "; ".join(strengths))
    if concerns:
        parts.append("Concerns: " + ", ".join(concerns))
    
    return ". ".join(parts) if parts else f"{title} with {yoe:.1f}yrs experience."

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="data/candidates.jsonl")
    parser.add_argument("--out", default="submission.csv")
    parser.add_argument("--top", type=int, default=100)
    args = parser.parse_args()
    
    print(f"Loading candidates from {args.candidates}...")
    
    results = []
    with open(args.candidates, "r") as f:
        for line in tqdm(f):
            line = line.strip()
            if not line:
                continue
            candidate = json.loads(line)
            result = score_candidate(candidate)
            results.append(result)
    
    print(f"Scored {len(results)} candidates. Sorting...")
    
    # Sort: score descending, then candidate_id ascending for ties
    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    top_100 = results[:args.top]
    
    print(f"Writing top {args.top} to {args.out}...")
    
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank, result in enumerate(top_100, 1):
            reasoning = generate_reasoning(result)
            writer.writerow([
                result["candidate_id"],
                rank,
                f"{result['score']:.4f}",
                reasoning,
            ])
    
    print(f"Done! Validate with: python validate_submission.py {args.out}")

if __name__ == "__main__":
    main()
```

---

## Phase 4 — Test & Tune (Day 3 evening, ~2 hours)

### Step 4.1 — Test on sample first

```bash
# Test on 50-candidate sample
python rank.py --candidates data/sample_candidates.json --out test_output.csv
```

**But wait** — sample_candidates.json is a JSON list, not JSONL. Add this to rank.py:

```python
# Auto-detect format
if args.candidates.endswith(".json"):
    with open(args.candidates) as f:
        candidates_list = json.load(f)
    for c in tqdm(candidates_list):
        results.append(score_candidate(c))
else:
    # JSONL processing (the full dataset)
    with open(args.candidates) as f:
        for line in tqdm(f):
            ...
```

### Step 4.2 — Validate format

```bash
python validate_submission.py test_output.csv
# Should print: "Submission is valid."
```

### Step 4.3 — Inspect your top 10 manually

```python
# src/inspect_results.py
import csv, json

with open("test_output.csv") as f:
    rows = list(csv.DictReader(f))

for row in rows[:10]:
    print(f"Rank {row['rank']}: {row['candidate_id']}")
    print(f"  Score: {row['score']}")
    print(f"  Reasoning: {row['reasoning']}")
    print()
```

**Ask yourself:**
- Does rank 1 look like a genuinely great candidate?
- Does rank 10 look noticeably weaker than rank 1?
- Is anyone obviously wrong (Marketing Manager in top 5)?
- Are the reasonings specific and honest?

### Step 4.4 — Tune weights if needed

If Marketing Managers keep appearing top 10 → increase career_fit weight.
If all top 10 are inactive profiles → increase behavioral weight.
If production engineers rank too low → increase production weight.

---

## Phase 5 — Run on Full Dataset (Day 4, ~2 hours)

```bash
# Time it first on a subset
time head -1000 data/candidates.jsonl > data/test_1000.jsonl
python rank.py --candidates data/test_1000.jsonl --out test_1000.csv

# If under 30s for 1000 → full run will be ~50min
# Optimize if needed (see below)
```

### If it's too slow:

```python
# Batch process with early exit after scoring
# You don't need to sort until the end
# Use multiprocessing for CPU speedup

from multiprocessing import Pool, cpu_count

def score_line(line: str):
    line = line.strip()
    if not line:
        return None
    return score_candidate(json.loads(line))

with open(args.candidates) as f:
    lines = f.readlines()

with Pool(cpu_count()) as pool:
    results = list(tqdm(pool.imap(score_line, lines, chunksize=500),
                        total=len(lines)))

results = [r for r in results if r is not None]
```

### Final run:

```bash
time python rank.py --candidates data/candidates.jsonl --out submission.csv
python validate_submission.py submission.csv
```

Should print: **"Submission is valid."**

---

## Phase 6 — Build the Sandbox (Day 4, ~1 hour)

You need a working demo hosted online (HuggingFace Spaces / Streamlit Cloud).

### Option: Streamlit app (`app.py`)

```python
import streamlit as st
import json
import csv
import io
from rank import score_candidate, generate_reasoning

st.title("HireIQ — Senior AI Engineer Ranker")
st.write("Upload candidates JSON to rank them against the Redrob AI JD.")

uploaded = st.file_uploader("Upload candidates (JSON or JSONL)", type=["json", "jsonl"])

if uploaded:
    content = uploaded.read().decode("utf-8")
    
    if uploaded.name.endswith(".json"):
        candidates = json.loads(content)
    else:
        candidates = [json.loads(l) for l in content.strip().split("\n") if l]
    
    st.write(f"Loaded {len(candidates)} candidates")
    
    if st.button("Rank Candidates"):
        results = [score_candidate(c) for c in candidates]
        results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
        top = results[:min(100, len(results))]
        
        output = []
        for rank, r in enumerate(top, 1):
            output.append({
                "rank": rank,
                "candidate_id": r["candidate_id"],
                "score": f"{r['score']:.4f}",
                "reasoning": generate_reasoning(r),
            })
        
        st.dataframe(output)
        
        # Download button
        csv_str = "candidate_id,rank,score,reasoning\n"
        for row in output:
            csv_str += f"{row['candidate_id']},{row['rank']},{row['score']},\"{row['reasoning']}\"\n"
        
        st.download_button("Download CSV", csv_str, "submission.csv")
```

Deploy to Streamlit Cloud (free) in 10 minutes.

---

## Phase 7 — PDF Deck (Day 5, ~2 hours)

### Slides structure (8 slides max)

| Slide | Content |
|---|---|
| 1 | Title + team + problem statement |
| 2 | JD Analysis — what the role ACTUALLY needs (not just keywords) |
| 3 | Architecture diagram — 5-component scoring pipeline |
| 4 | Technical Fit — how you score skills (not keyword matching) |
| 5 | Behavioral Signals — which 6 signals matter and why |
| 6 | Honeypot Detection — how you avoid traps |
| 7 | Results — top 5 candidates with reasoning, score breakdown |
| 8 | Compute stats — runtime, memory, why it's production-ready |

**Key message:** "We didn't match keywords. We modeled recruiter judgment."

---

## Phase 8 — Submit (Day 5)

### Checklist before submitting

- [ ] `python validate_submission.py submission.csv` → "Submission is valid."
- [ ] Exactly 100 rows, ranks 1-100, no duplicates
- [ ] Scores are non-increasing
- [ ] No candidate_id that doesn't exist in candidates.jsonl
- [ ] GitHub repo has: README, rank.py, src/, requirements.txt, submission_metadata.yaml
- [ ] Sandbox link works and can rank sample_candidates.json
- [ ] PDF deck ready
- [ ] submission_metadata.yaml filled in

### Repo structure to commit
```
India_runs/
├── README.md          ← setup + reproduce_command
├── rank.py            ← main ranker
├── app.py             ← streamlit demo
├── requirements.txt
├── submission_metadata.yaml
├── src/
│   ├── technical_fit.py
│   ├── career_fit.py
│   ├── production_score.py
│   ├── behavioral_score.py
│   ├── availability_score.py
│   └── honeypot_detector.py
├── data/
│   └── sample_candidates.json
└── output/
    └── submission.csv
```

---

## Key Things That Separate Top 5 from Everyone Else

| Thing | Most teams | You |
|---|---|---|
| Skill scoring | keyword count | weighted by proficiency × duration × endorsements × assessment |
| Career fit | title matching | title + AI-months ratio + startup bonus + consulting penalty |
| Behavioral | ignored | 6 signals combined as hireability multiplier |
| Honeypots | caught by them | detected by timeline + perfection anomalies |
| Reasoning | templated | profile-specific facts + honest concerns |
| Reproducibility | API calls | pure CPU, no network, runs in < 5 min |

---

## Daily Schedule

| Day | Goal | Output |
|---|---|---|
| Day 1 | Setup + Phase 0 + Phase 1 (explore) | Working Python env, know the data |
| Day 2 | Phase 2 (all 6 scoring components) | 6 files in src/, each tested standalone |
| Day 3 | Phase 3 (rank.py) + Phase 4 (test + tune) | Valid test_output.csv on sample |
| Day 4 | Phase 5 (full run) + Phase 6 (sandbox) | Valid submission.csv + working demo URL |
| Day 5 | Phase 7 (deck) + Phase 8 (submit) | Submitted ✅ |
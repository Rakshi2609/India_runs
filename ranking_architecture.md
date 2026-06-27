# Intelligent Candidate Ranking System: Architecture & Formulas

This document outlines the complete workflow and mathematical formulas used to rank 100,000 candidates for the Senior AI Engineer role at Redrob.

> [!NOTE]
> The system is explicitly designed to model **Recruiter Judgment** rather than pure keyword matching. It prioritizes production experience, behavioral signals, and logical career progressions while actively penalizing "keyword-stuffed" or fraudulent profiles.

---

## 1. High-Level Workflow

The pipeline (`src/rank.py`) processes candidates through a multi-stage funnel:

1. **Text Serialization**: Each candidate's JSON profile (headline, summary, titles, skills, and past job descriptions) is flattened into a single, cohesive text block.
2. **Semantic Embedding**: The candidate text and the Job Description (JD) text are passed through the `all-MiniLM-L6-v2` transformer model to generate dense vectors.
3. **Heuristic Extraction**: Independent modules calculate raw scores for Career, Production, Behavior, Availability, and Fraud.
4. **Normalization**: All raw sub-scores are normalized to a scale of `0` to `100` across the entire candidate pool.
5. **Weighted Aggregation**: The normalized scores are combined using a fixed weighting formula.
6. **Penalty Application**: Multiplicative penalties are applied for lack of core domain experience, lack of production evidence, or triggering honeypot fraud rules.
7. **Reasoning Generation**: A dynamic text explanation is generated justifying the final score.

---

## 2. Core Scoring Formulas

### A. Semantic Match Score (Weight: 20%)
Calculates the conceptual alignment between the candidate's entire career text and the JD.
```math
Semantic\_Score = Cosine\_Similarity(Embed_{JD}, Embed_{Candidate})
```

### B. Career Evidence Score (Weight: 35%)
Evaluates domain relevance and career stability.
- **Title Match**: Strong titles (AI/ML Engineer) add heavily; weak titles (HR, Marketing) apply negative points.
- **Tenure Math**: High bonus for 5-9 years of experience.
- **Production Context**: Extra points if job descriptions contain words like "latency", "deployed", "serving".
- **Startup Bonus**: Bonus for working in companies sized 1-200.
- **Consulting Penalty**: Penalty if >60% of the career is spent at pure IT service firms (TCS, Wipro, etc.).
- **Job Hopping**: Penalty if the average tenure across all jobs is < 18 months.

### C. Production Experience Score (Weight: 20%)
Differentiates between builders and pure researchers.
- **Production Signals**: Counts frequency of words like "deployed", "QPS", "inference pipeline".
- **Research Signals**: Counts frequency of words like "publication", "academic lab", "arxiv".
- **Formula**: `(Production\_Count / 5.0) - (Research\_Count > threshold ? penalty : 0)`
- **GitHub Bonus**: If `github_activity_score > 60`, adds a flat bonus to the production score.

### D. Behavioral Signals Score (Weight: 15%)
Measures if the candidate is actually hireable based on platform engagement.
```text
Behavior\_Score = 
    (Recruiter_Response_Rate * 0.25) + 
    (Interview_Completion_Rate * 0.15) + 
    (Offer_Acceptance_Rate * 0.10) +
    (Recent_Login_Bonus) + 
    (Saved_By_Recruiters_Bonus) + 
    (Profile_Completeness)
```

### E. Availability Score (Weight: 10%)
Checks logistics and willingness to join.
- **Notice Period**: `0 days` = Max points. `> 90 days` = Penalty.
- **Location**: Bonus for residing in Pune/Noida or willing to relocate.
- **Work Mode**: Bonus for Hybrid/Onsite preference.

---

## 3. The Final Aggregation Formula

Before aggregation, all raw scores (except Semantic, which is inherently `0-1`) are normalized across the entire dataset to `0-100`:
```python
Norm_Score = ((Raw_Score - Min_Score) / (Max_Score - Min_Score)) * 100
```

The Base Final Score is calculated as:
```python
Base_Score = (
    0.35 * Career_Norm +
    0.20 * Production_Norm +
    0.15 * Behavioral_Norm +
    0.10 * Availability_Norm +
    0.20 * Semantic_Norm
)
```

---

## 4. Penalty Multipliers (The Elimination Rules)

Once the `Base_Score` is calculated, severe multiplicative penalties are applied to effectively remove bad fits from the Top 100.

> [!WARNING]
> These penalties stack multiplicatively. A candidate triggering multiple rules will see their score drop to near zero.

### Rule 1: Buzzword Stuffing
- Subtract flat penalty points if a candidate has massive skill lists but a very low `Career_Score` (meaning they have the keywords but no actual career history to back it up).

### Rule 2: Wrong Domain
- If `Career_Score < 0` (e.g., they work in Sales/HR): `Final_Score = Base_Score * 0.25`
- If `Career_Score < 20`: `Final_Score = Base_Score * 0.50`

### Rule 3: No Production Evidence
- If `Career_Score < 20` AND `Production_Score == 0`: 
  `Final_Score = Base_Score * 0.25`

### Rule 4: Honeypot Fraud Detection
The `detect_honeypot` module calculates a `fraud_score` (0.0 to 1.0) based on impossible timeline math (e.g., total job durations wildly exceed stated years of experience), suspiciously perfect assessments, or contradictory seniority.
- If `fraud_score > 0.5` (Extreme Fraud): `Final_Score = Base_Score * 0.10`
- If `fraud_score > 0.3` (Suspicious): `Final_Score = Base_Score * 0.50`

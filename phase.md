# HireIQ — Redrob AI Candidate Discovery Challenge

## Complete End-to-End Build Plan (Leaderboard-Oriented)

> Goal: Build a CPU-only candidate ranking system that identifies the best Senior AI Engineers from a large candidate pool by modeling recruiter judgment rather than keyword matching.

---

# 1. Problem Understanding

You are NOT building:

* Keyword matching
* Resume filtering
* Skill counting

You ARE building:

* Candidate understanding
* Recruiter-style ranking
* Behavioral-aware matching
* Career-aware matching

The JD explicitly warns:

> Candidates with AI buzzwords are not necessarily good matches.

and

> Candidates with recommendation, ranking, retrieval, search experience may be excellent matches even without RAG or Pinecone keywords.

---

# 2. Core Philosophy

## Bad Approach

```text
RAG found = +10
Pinecone found = +10
LLM found = +10
```

## Good Approach

```text
What has this candidate actually built?

Search?
Retrieval?
Ranking?
Recommendation?
Matching systems?
Production ML?

Would a recruiter actually call them?
```

---

# 3. Final Architecture

```text
Final Score =
0.35 Career Evidence Score
+ 0.25 Semantic JD Match
+ 0.15 Production Systems Score
+ 0.15 Behavioral Signal Score
+ 0.10 Availability Score
- Honeypot Penalty
```

---

# 4. Project Structure

```text
hireiq/
│
├── data/
│   ├── candidates.jsonl
│   ├── sample_candidates.json
│   ├── job_description.docx
│
├── src/
│   ├── feature_builder.py
│   ├── semantic_match.py
│   ├── career_evidence.py
│   ├── technical_fit.py
│   ├── production_score.py
│   ├── behavioral_score.py
│   ├── availability_score.py
│   ├── honeypot_detector.py
│   └── reasoning_generator.py
│
├── rank.py
├── requirements.txt
├── README.md
└── submission.csv
```

---

# 5. Setup

```bash
python -m venv venv
source venv/bin/activate

pip install sentence-transformers
pip install pandas
pip install numpy
pip install tqdm
```

## requirements.txt

```text
sentence-transformers
numpy
pandas
tqdm
```

---

# 6. Explore Dataset First

Before building anything:

```python
import json

with open("sample_candidates.json") as f:
    data = json.load(f)

print(data[0].keys())
```

Inspect:

* profile
* career_history
* skills
* redrob_signals

Questions:

* What does a strong candidate look like?
* What does a weak candidate look like?
* What fields are reliable?
* Which fields are noisy?

---

# 7. Build Candidate Text

Create a unified text representation.

```python
candidate_text = f"""
Headline:
{headline}

Summary:
{summary}

Current Title:
{current_title}

Skills:
{skills}

Career History:
{job_titles}

Descriptions:
{job_descriptions}
"""
```

This text becomes the input for semantic matching.

---

# 8. Build JD Text

Extract the entire JD into plain text.

```python
jd_text
```

Store once.

Reuse for all candidates.

---

# 9. Semantic Matching Layer

## Model

```python
all-MiniLM-L6-v2
```

CPU friendly.

Fast.

Good enough.

---

## Generate Embeddings

```python
jd_embedding
candidate_embedding
```

---

## Calculate Similarity

```python
semantic_score =
cosine_similarity(
    jd_embedding,
    candidate_embedding
)
```

Normalize:

```text
0 → 1
```

Weight:

```text
25%
```

Purpose:

Captures:

* Search
* Ranking
* Retrieval
* Recommendation
* Matching

even when keywords differ.

---

# 10. Career Evidence Score

Most important component.

Weight:

```text
35%
```

---

## Current Role

### Strong

```text
AI Engineer
ML Engineer
Machine Learning Engineer
Applied Scientist
NLP Engineer
Search Engineer
```

### Acceptable

```text
Software Engineer
Backend Engineer
Data Engineer
```

### Weak

```text
Marketing
Sales
HR
Customer Support
Operations
Accountant
```

---

## Experience Range

### Ideal

```text
5–9 years
```

### Acceptable

```text
4–12 years
```

---

## Startup Bonus

Reward company sizes:

```text
1-10
11-50
51-200
```

---

## Product Company Bonus

Examples:

```text
Swiggy
Flipkart
PhonePe
Meesho
Zomato
Razorpay
Freshworks
```

Reward similar companies.

---

## Consulting Penalty

Penalize if majority of career is:

```text
TCS
Infosys
Wipro
Capgemini
Accenture
Cognizant
```

---

## Domain Relevance Bonus

Search job descriptions for:

```text
retrieval
ranking
recommendation
matching
search
relevance
personalization
candidate discovery
```

This is extremely important.

Someone who built recommendation systems is likely a better fit than someone who only fine-tuned LLMs.

---

# 11. Technical Fit Score

Weight:

```text
10-15%
```

Do NOT over-weight.

---

## Strong Skills

```text
Embeddings
Retrieval
Vector Search
Ranking
NLP
Transformers
PyTorch
LLMs
Sentence Transformers
FAISS
Milvus
Qdrant
Pinecone
Elasticsearch
```

---

## Bonus Skills

```text
LoRA
QLoRA
PEFT
Fine-Tuning
Learning-to-Rank
XGBoost
Recommendation Systems
```

---

## Weak Signals

Do not heavily reward:

```text
LangChain
Prompt Engineering
OpenAI API
ChatGPT
```

The JD explicitly warns about this.

---

# 12. Production Systems Score

Weight:

```text
15%
```

Look for:

```text
deployed
production
serving
inference
latency
throughput
monitoring
A/B testing
real users
scale
```

Reward heavily.

---

## Research Penalty

Penalize:

```text
publication
research lab
academic
PhD research
conference paper
```

ONLY when no production evidence exists.

---

# 13. Behavioral Signals Score

Weight:

```text
15%
```

---

## High Importance

```text
recruiter_response_rate
interview_completion_rate
saved_by_recruiters_30d
```

---

## Medium Importance

```text
profile_views_received_30d
search_appearance_30d
offer_acceptance_rate
```

---

## Low Importance

```text
verified_email
verified_phone
linkedin_connected
```

---

## Activity Score

Use:

```text
last_active_date
```

Penalty:

```text
Inactive > 180 days
```

---

# 14. Availability Score

Weight:

```text
10%
```

---

## Notice Period

```text
0-30 days = best
31-60 days = good
61-90 days = neutral
90+ days = penalty
```

---

## Preferred Cities

```text
Pune
Noida
Delhi NCR
Hyderabad
Mumbai
Bangalore
```

---

## Relocation

Bonus:

```text
willing_to_relocate = true
```

---

# 15. Honeypot Detection

Apply soft penalties.

---

## Contradictory Profiles

Example:

```text
Marketing Manager
+
Milvus
+
LoRA
+
RAG
```

Suspicious.

---

## Impossible Seniority

Example:

```text
2 years experience
Principal AI Architect
```

Suspicious.

---

## Perfect Everything

Example:

```text
99% assessments
99% response rate
99% offer acceptance
```

Suspicious.

---

# 16. Final Score

```python
final_score = (
    0.35 * career_score
    + 0.25 * semantic_score
    + 0.15 * production_score
    + 0.15 * behavioral_score
    + 0.10 * availability_score
)

final_score *= honeypot_modifier
```

---

# 17. Generate Reasoning

Use real profile information.

Example:

```text
Senior ML Engineer with 7.2 years experience building recommendation and ranking systems. Strong recruiter engagement signals and active job-search behavior. Demonstrated production deployment experience with low notice period.
```

Never hallucinate.

---

# 18. Ranking

Sort:

```python
results.sort(
    key=lambda x: (
        -x["score"],
        x["candidate_id"]
    )
)
```

Output:

```csv
candidate_id,rank,score,reasoning
```

Exactly:

```text
100 rows
```

---

# 19. Validation

```bash
python validate_submission.py submission.csv
```

Must pass.

---

# 20. Streamlit Demo

Features:

* Upload candidate file
* Run ranker
* Show top candidates
* Download CSV

---

# 21. PPT Structure

### Slide 1

Problem Statement

### Slide 2

JD Analysis

### Slide 3

Architecture

### Slide 4

Semantic Matching Layer

### Slide 5

Career Evidence Engine

### Slide 6

Behavioral Signal Modeling

### Slide 7

Results & Top Candidates

### Slide 8

Runtime, Scalability, Reproducibility

---

# 22. Timeline

## Day 1

Dataset exploration

## Day 2

Feature engineering

## Day 3

Semantic matching + ranking pipeline

## Day 4

Testing + tuning

## Day 5

Submission + PPT + Demo

---

# Final Winning Insight

The JD is not asking:

> Who knows RAG?

The JD is asking:

> Who has successfully built retrieval, ranking, recommendation, matching, and production ML systems and is actually available to hire today?

Build your ranking system around that principle and you'll outperform most keyword-based solutions.

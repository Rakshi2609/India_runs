# Redrob Challenge: Intelligent Candidate Discovery & Ranking Engine

## Slide 1: The AI Trap (The Problem)
* **Keyword Matching is Broken:** Simple vector search over-rewards "AI buzzword stuffers" (e.g. Frontend Engineers who took a LangChain tutorial) over deep infrastructure engineers.
* **The JD Reality:** True recommendation systems require robust backend knowledge, production ML deployment, and offline-to-online evaluation experience, not just taking online courses on "LLMs".
* **The Solution:** A multi-stage deterministic scoring engine fused with semantic context, designed specifically to capture the nuance of a candidate's actual engineering depth.

## Slide 2: Pipeline Architecture (The Solution)
* **Data Ingestion:** 100K candidates (Profile, Career History, Redrob Signals).
* **Career Evidence Engine (35%):** Penalizes consulting traps, rewards product companies (if AI relevant), and looks for specific infrastructure keywords (e.g. *Elasticsearch*, *Vector DB*).
* **Production Evidence Engine (20%):** Filters out generic "production" terms. Scans for *inference*, *latency*, *ab testing*, *offline metrics* (NDCG/MRR/MAP).
* **Behavioral Signals Engine (15%):** Rewards active candidates (high recruiter response rate, profile completeness, recent logins).
* **Availability Engine (10%):** Normalizes and rewards notice periods and work preferences.
* **Semantic Matching (20%):** MiniLM-L6-v2 embeddings to align candidate career descriptions natively with the provided JD.

## Slide 3: The "Zero AI" Gate (Adversarial Defense)
* **The Challenge:** How do we stop a high-performing active Cloud Engineer from outranking a passive Recommendation Engineer?
* **The Gate Logic:** If a candidate lacks ML production signals (`production_score = 0`) AND lacks a deep relevant career history (`career_score < 20`), their final score is slashed by 75%.
* **The Result:** Complete elimination of irrelevant high-activity candidates (Marketing, Operations, generic Frontend/DevOps) from the Top 50.

## Slide 4: Reasoning Generator (Explainability)
* **Black Box vs Glass Box:** We don't just output a score; we output a human-readable *Why*.
* **Mapping Signals to Text:** The pipeline deterministically builds an explanation string based on the exact thresholds the candidate passed.
* **Recruiter Ready:** Generates clear, concise justifications (e.g., *"Demonstrated production ML deployment and evaluation experience. Strong recruiter engagement signals."*)

## Slide 5: Performance & Scalability
* **Efficiency:** 100K candidate vectors embedded using `MiniLM-L6-v2` with `batch_size=256` running natively on CPU in ~75 minutes.
* **Deterministic Traceability:** Every rank can be traced back to its raw `career_score`, `production_score`, etc., via the `submission_debug.csv`.
* **The Outcome:** The Top 25 candidates are exclusively deep-tech Recommendation, Search, and ML Engineers from top-tier product companies (Swiggy, Zomato, CRED, etc.).

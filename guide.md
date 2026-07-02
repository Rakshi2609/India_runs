# Redrob Challenge: System Execution Guide

This guide explains how to set up the environment, where to place the datasets, and how to execute the intelligent candidate ranking pipeline from start to finish.

## 1. Prerequisites & Environment Setup

Before running the system, ensure you have Python 3.8+ installed. You must install the required dependencies:

```bash
pip install sentence-transformers python-docx
```

The system uses `SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")` to compute semantic similarities between the Job Description and the candidates.

## 2. Dataset Placement

For the system to work correctly, your data files must be placed in the `data/` directory relative to the root folder:

1. **Candidates Dataset**: Place the full 487MB dataset file inside the `data/` directory and ensure it is named **`candidates.jsonl`**. 
   - *Path:* `data/candidates.jsonl`
   - *Note:* If you are testing, you can place a smaller sample file here, but it must be named `candidates.jsonl` (or modify `src/rank.py` to point to a different filename).

2. **Job Description**: Place the Word document containing the job description in the `data/` directory.
   - *Path:* `data/job_description.docx`

## 3. Running the Pipeline

Once the data is in place, you can execute the main ranking engine from the project root directory.

Run the following command:

```bash
python3 src/rank.py
```

### What Happens During Execution?

1. **Model Loading:** The system initializes the `all-MiniLM-L6-v2` transformer model.
2. **JD Extraction:** It reads `data/job_description.docx` and generates a dense vector embedding representing the semantic meaning of the job description.
3. **Data Ingestion:** The script streams `data/candidates.jsonl` (100,000 candidate profiles) into memory.
4. **Candidate Text Building:** It compiles a rich text representation of each candidate based on their experiences, titles, and skills.
5. **Embedding Generation (The Longest Step):** The system encodes all 100,000 candidate profiles into dense vectors.
   - *Note:* This step batches processing (size=256). On a standard CPU, this phase takes approximately **55-60 minutes**. On a GPU-enabled machine, it takes significantly less time.
6. **Heuristic Scoring:** Parallel to semantic matching, the system calculates specialized signals:
   - **Career Relevance:** Evaluates alignment with Machine Learning / Search / Retrieval roles.
   - **Production Score:** Detects evidence of actual production deployment vs. academic/toy projects.
   - **Behavioral & Availability Scores:** Analyzes stability and readiness to join.
   - **Buzzword Penalties:** Penalizes profiles that keyword-stuff without tangible proof.
7. **Final Aggregation & Ranking:** Combines semantic similarity scores with heuristic scores to produce a definitive, normalized final ranking.

## 4. Final Outputs

Upon completion, the script generates two files in the project root directory:

- **`submission.csv`**: The final required output containing the **Top 100 ranked candidates**. It includes the `candidate_id`, the final `score`, and a generated `reasoning` string explaining why the candidate was selected.
- **`submission_debug.csv`**: A detailed breakdown for the same Top 100 candidates, exposing the exact heuristic scores (career, production, semantic, etc.) to help debug why they were ranked highly.

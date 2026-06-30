# Candidate Ranking System (Team Vibecoderzz)

This repository contains an automated pipeline to evaluate and rank 100,000 candidate profiles against a target Job Description. The system uses a combination of semantic embeddings and heuristic scoring to identify candidates with verifiable production experience in Search, Ranking, and Recommendation Systems, while explicitly filtering keyword-stuffed resumes.

## System Architecture

The pipeline processes candidates through a multi-stage funnel consisting of strict exclusion filters and weighted scoring modules.

```mermaid
graph TD
    A[Raw Candidates JSONL] --> B{Honeypot Filter}
    B -- Honeypot Detected --> Z[Discard Candidate]
    B -- Clean --> C[Feature Engineering]
    
    C --> D[Semantic Matching]
    C --> E[Career Evidence Score]
    C --> F[Production Capability]
    C --> G[Behavioral & Availability]
    
    D --> H[Base Aggregation]
    E --> H
    F --> H
    G --> H
    
    H --> I{Buzzword Check}
    I -- Keyword stuffed + low exp --> J[Apply Buzzword Penalty]
    I -- Genuine / No buzzwords --> K[Final Score Computation]
    J --> K
    
    K --> L[Sort Top 100 Candidates]
    L --> M[Generate Reasoning String]
    M --> N[Output CSV]
    
    classDef process fill:#f9f,stroke:#333,stroke-width:2px;
    classDef discard fill:#f66,stroke:#333,stroke-width:2px;
    classDef output fill:#6f6,stroke:#333,stroke-width:2px;
    class Z discard;
    class N output;
```

## Setup and Execution

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Place the dataset (`candidates.jsonl`) and the target JD (`job_description.docx`) inside the `isnt/` directory.

3. Execute the pipeline:
```bash
python src/rank.py --candidates isnt/candidates.jsonl --out team_vibecoderzz.csv
```

## Scoring Methodology

The final score is a weighted aggregation of normalized sub-scores.

| Scoring Module | Weight | Metric Measured | Penalty Condition |
| :--- | :---: | :--- | :--- |
| **Semantic Alignment** | 20% | Cosine similarity between candidate history and JD | N/A |
| **Career Relevance** | 35% | Exact matching of domain (Search, Ranking, RecSys) | Low relevance caps score |
| **Production Experience** | 20% | Scale, tools, and production environment terms | N/A |
| **Behavioral Signals** | 15% | Evidence of continuous contribution (e.g. GitHub) | N/A |
| **Availability** | 10% | Notice period and immediate start viability | N/A |
| **Buzzword Penalty** | Variable | Flags GenAI keyword stuffing | -100 if Career Score < 20 |

## Repository Structure

```mermaid
erDiagram
    REPOSITORY {
        file README "Documentation"
        file requirements "Dependencies"
        file submission_metadata "Hackathon config"
    }
    src {
        file rank "Main Entrypoint"
        file semantic_match "BERT Embeddings"
        file career_evidence "Rule-based scoring"
        file production_score "Experience rules"
        file buzzword_penalty "Spam filters"
        file behavioral_score "Signal analysis"
        file honeypot_filter "Bad actor detection"
        file reasoning_generator "Explainability module"
    }
    REPOSITORY ||--o{ src : contains
```

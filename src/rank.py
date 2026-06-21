import json
import csv
import os
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from career_evidence import score_career
from behavioral_score import score_behavioral
from availability_score import score_availability
from production_score import score_production
from candidate_text_builder import build_candidate_text
from buzzword_penalty import calculate_buzzword_penalty
from reasoning_generator import generate_reasoning

def extract_jd_text(jd_path):
    from docx import Document
    doc = Document(jd_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def normalize(values):
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [0.0] * len(values)
    return [((v - min_val) / (max_val - min_val)) * 100.0 for v in values]

def main():
    print("Loading model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    print("Loading JD...")
    jd_text = extract_jd_text("data/job_description.docx")
    jd_embedding = model.encode(jd_text, normalize_embeddings=True)

    candidates_file = "data/sample_candidates.json"
    if not os.path.exists(candidates_file):
        print(f"{candidates_file} not found.")

    print("Loading candidates...")
    candidates = []
    if candidates_file.endswith(".jsonl"):
        with open(candidates_file) as f:
            for line in f:
                candidates.append(json.loads(line))
    else:
        with open(candidates_file) as f:
            candidates = json.load(f)

    print(f"Loaded {len(candidates)} candidates.")

    print("Building candidate texts...")
    candidate_texts = [build_candidate_text(c) for c in candidates]
    
    print("Encoding candidates...")
    candidate_embeddings = model.encode(candidate_texts, batch_size=256, show_progress_bar=True, normalize_embeddings=True)

    print("Calculating raw scores...")
    raw_scores = []

    for i, c in enumerate(candidates):
        career_info = score_career(c)
        career_raw = career_info["score"]
        prod_raw = score_production(c)
        behav_raw = score_behavioral(c)
        avail_raw = score_availability(c)
        
        sem_raw = float(cos_sim(jd_embedding, candidate_embeddings[i]))
        
        penalty = calculate_buzzword_penalty(c, career_raw)
        
        raw_scores.append({
            "candidate_id": c["candidate_id"],
            "name": c.get("profile", {}).get("anonymized_name", "Unknown"),
            "title": c.get("profile", {}).get("current_title", "Unknown"),
            "career_raw": career_raw,
            "production_raw": prod_raw,
            "behavior_raw": behav_raw,
            "availability_raw": avail_raw,
            "semantic_raw": sem_raw,
            "penalty": penalty
        })

    # Normalize
    career_norms = normalize([x["career_raw"] for x in raw_scores])
    prod_norms = normalize([x["production_raw"] for x in raw_scores])
    behav_norms = normalize([x["behavior_raw"] for x in raw_scores])
    avail_norms = normalize([x["availability_raw"] for x in raw_scores])
    sem_norms = normalize([x["semantic_raw"] for x in raw_scores])

    print("Calculating final scores and reasoning...")
    final_results = []
    
    for i, raw in enumerate(raw_scores):
        final_score = (
            0.35 * career_norms[i] +
            0.20 * prod_norms[i] +
            0.15 * behav_norms[i] +
            0.10 * avail_norms[i] +
            0.20 * sem_norms[i]
        )
        
        final_score -= raw["penalty"]
        
        if raw["career_raw"] < 0:
            final_score *= 0.25
        elif raw["career_raw"] < 20:
            final_score *= 0.5
            
        # Severe penalty for no AI/production evidence
        if raw["production_raw"] == 0 and raw["career_raw"] < 40:
            final_score *= 0.1
            
        reasoning = generate_reasoning(raw)
        
        final_results.append({
            "candidate_id": raw["candidate_id"],
            "name": raw["name"],
            "title": raw["title"],
            "career_raw": raw["career_raw"],
            "semantic_raw": raw["semantic_raw"],
            "score": final_score,
            "reasoning": reasoning
        })

    final_results.sort(key=lambda x: x["score"], reverse=True)

    print("=" * 120)
    print("TOP 20 CANDIDATES")
    print("=" * 120)
    for r in final_results[:20]:
        print(f"[{r['score']:>6.1f}] {r['name']:<25} | {r['title'][:30]:<30} | CR: {r['career_raw']:>5.1f} | SM: {r['semantic_raw']:>4.2f}")
        print(f"         Reason: {r['reasoning']}")

    # Write CSV
    print("Writing submission.csv...")
    with open("submission.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "score", "reasoning"])
        for r in final_results:
            writer.writerow([r["candidate_id"], f"{r['score']:.4f}", r["reasoning"]])
            
    print("Writing submission_debug.csv...")
    with open("submission_debug.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "career_score", "production_score", "behavior_score", "availability_score", "semantic_score", "final_score", "reasoning"])
        for r in final_results:
            writer.writerow([
                r["candidate_id"], 
                f"{r['career_raw']:.1f}", 
                f"{next(x['production_raw'] for x in raw_scores if x['candidate_id'] == r['candidate_id']):.1f}",
                f"{next(x['behavior_raw'] for x in raw_scores if x['candidate_id'] == r['candidate_id']):.1f}",
                f"{next(x['availability_raw'] for x in raw_scores if x['candidate_id'] == r['candidate_id']):.1f}",
                f"{r['semantic_raw']:.4f}", 
                f"{r['score']:.4f}", 
                r["reasoning"]
            ])

    print("Done! submission.csv and submission_debug.csv generated.")

if __name__ == "__main__":
    main()

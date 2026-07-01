import json
import csv
import os
import argparse
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from career_evidence import score_career
from behavioral_score import score_behavioral
from availability_score import score_availability
from production_score import score_production
from candidate_text_builder import build_candidate_text
from buzzword_penalty import calculate_buzzword_penalty
from reasoning_generator import generate_reasoning
from honeypot_filter import detect_honeypot

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="isnt/candidates.jsonl")
    parser.add_argument("--jd", default="isnt/job_description.docx")
    parser.add_argument("--validator", default="isnt/validate_submission.py")
    parser.add_argument("--out", default="tanushbhootra576.csv")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()

    print("Loading model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    print("Loading JD...")
    jd_text = extract_jd_text(args.jd)
    jd_embedding = model.encode(jd_text, normalize_embeddings=True)

    print(f"Loading up to {args.limit} candidates from {args.candidates}...")
    candidates = []
    honeypot_count = 0
    with open(args.candidates, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            
            # 1. HONEYPOT FILTERING
            hp_mult = detect_honeypot(c)
            if hp_mult == 0.0:
                honeypot_count += 1
                continue
                
            c["hp_mult"] = hp_mult
            candidates.append(c)
            if args.limit > 0 and len(candidates) >= args.limit:
                break

    print(f"Loaded {len(candidates)} valid candidates. Filtered {honeypot_count} honeypots.")

    print("Calculating heuristic scores...")
    heuristic_scores = []
    for c in candidates:
        career_raw = score_career(c)["score"]
        prod_raw = score_production(c)
        behav_multiplier = score_behavioral(c)
        avail_raw = score_availability(c)
        penalty = calculate_buzzword_penalty(c, career_raw)
        
        heuristic_scores.append({
            "candidate": c,
            "career_raw": career_raw,
            "production_raw": prod_raw,
            "behavior_raw": behav_multiplier,
            "availability_raw": avail_raw,
            "penalty": penalty,
            "hp_mult": c.get("hp_mult", 1.0)
        })
        
    print("Pre-filtering top candidates for semantic matching...")
    # Normalize heuristic scores
    c_norms = normalize([x["career_raw"] for x in heuristic_scores])
    p_norms = normalize([x["production_raw"] for x in heuristic_scores])
    a_norms = normalize([x["availability_raw"] for x in heuristic_scores])
    
    for i, item in enumerate(heuristic_scores):
        base_h = (0.40 * c_norms[i] + 0.20 * p_norms[i] + 0.10 * a_norms[i]) * item["behavior_raw"] * item["hp_mult"] - item["penalty"]
        
        if item["career_raw"] < 0:
            base_h -= 50
        elif item["career_raw"] < 20:
            base_h -= 20
            
        if item["production_raw"] < 20:
            base_h -= 30  # JD says production experience is absolutely required
            
        yoe = item["candidate"].get("profile", {}).get("years_of_experience", 0)
        if yoe > 12:
            base_h -= 10  # Heavy penalty for being too senior (likely architect)
        elif yoe < 4:
            base_h -= 10  # Heavy penalty for being too junior
            
        item["pre_score"] = base_h
        
    heuristic_scores.sort(key=lambda x: x["pre_score"], reverse=True)
    
    # Take top 5000 candidates for semantic matching
    top_candidates = heuristic_scores[:5000]
    
    print(f"Building texts for {len(top_candidates)} candidates...")
    skills_texts = []
    exp_texts = []
    for item in top_candidates:
        c = item["candidate"]
        skills_texts.append(" ".join([s.get("name", "") for s in c.get("skills", [])]))
        e_text = []
        for job in c.get("career_history", []):
            e_text.append(job.get("title", ""))
            e_text.append(job.get("description", ""))
        exp_texts.append("\n".join(e_text))
    
    print("Encoding candidates skills and experience...")
    skills_embeddings = model.encode(skills_texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)
    exp_embeddings = model.encode(exp_texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)
    
    print("Calculating final scores and reasoning...")
    final_results = []
    
    sem_raw_values = []
    for i, item in enumerate(top_candidates):
        sem_skills = float(cos_sim(jd_embedding, skills_embeddings[i]))
        sem_exp = float(cos_sim(jd_embedding, exp_embeddings[i]))
        sem_raw = (sem_skills + sem_exp) / 2.0
        sem_raw_values.append(sem_raw)
        
    sem_norms = normalize(sem_raw_values)
    
    # We also need to re-normalize the other scores for the top 5000 candidates to combine correctly with semantic
    c_norms_top = normalize([x["career_raw"] for x in top_candidates])
    p_norms_top = normalize([x["production_raw"] for x in top_candidates])
    a_norms_top = normalize([x["availability_raw"] for x in top_candidates])
    
    for i, item in enumerate(top_candidates):
        base_score = (
            0.40 * c_norms_top[i] +
            0.20 * p_norms_top[i] +
            0.10 * a_norms_top[i] +
            0.30 * sem_norms[i]
        )
        
        final_score = base_score * item["behavior_raw"] * item["hp_mult"]
        final_score -= item["penalty"]
        
        if item["career_raw"] < 0:
            final_score -= 50
        elif item["career_raw"] < 20:
            final_score -= 20
            
        if item["production_raw"] < 20:
            final_score -= 30
            
        yoe = item["candidate"].get("profile", {}).get("years_of_experience", 0)
        if yoe > 12:
            final_score -= 10
        elif yoe < 4:
            final_score -= 10
            
        raw = {
            "candidate_id": item["candidate"]["candidate_id"],
            "career_raw": item["career_raw"],
            "production_raw": item["production_raw"],
            "behavior_raw": item["behavior_raw"],
            "availability_raw": item["availability_raw"],
            "semantic_raw": sem_raw_values[i],
            "penalty": item["penalty"]
        }
        
        reasoning = generate_reasoning(item["candidate"], raw)
        
        final_results.append({
            "candidate_id": raw["candidate_id"],
            "score": final_score,
            "reasoning": reasoning
        })

    # 3. DETERMINISTIC SORTING & NORMALIZATION
    if final_results:
        max_score = max(r["score"] for r in final_results)
        min_score = min(r["score"] for r in final_results)
        for r in final_results:
            if max_score > min_score:
                r["score"] = (r["score"] - min_score) / (max_score - min_score)
            else:
                r["score"] = 0.5

    final_results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    top_100 = final_results[:100]

    # Write CSV with exact format
    print(f"Writing {args.out}...")
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank_idx, r in enumerate(top_100, start=1):
            writer.writerow([r["candidate_id"], rank_idx, f"{r['score']:.4f}", r["reasoning"]])
            
    print("Done! Validating submission...")
    os.system(f"python {args.validator} {args.out}")

if __name__ == "__main__":
    main()

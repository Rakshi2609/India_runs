import json
import csv
import os
import argparse
from multiprocessing import Pool, cpu_count
from tqdm import tqdm


from career_evidence import score_career
from technical_fit import score_technical_fit
from behavioral_score import score_behavioral
from availability_score import score_availability
from production_score import score_production
from candidate_text_builder import build_candidate_text
from buzzword_penalty import calculate_buzzword_penalty
from reasoning_generator import generate_reasoning
from honeypot_filter import is_honeypot

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

def process_line(line):
    line = line.strip()
    if not line:
        return None
    try:
        c = json.loads(line)
    except Exception:
        return None
        
    if is_honeypot(c):
        return None
        
    career_raw = score_career(c)["score"]
    tech_raw = score_technical_fit(c)
    prod_raw = score_production(c)
    behav_multiplier = score_behavioral(c)
    avail_raw = score_availability(c)
    penalty = calculate_buzzword_penalty(c, career_raw)
    
    return {
        "candidate": c,
        "career_raw": career_raw,
        "technical_raw": tech_raw,
        "production_raw": prod_raw,
        "behavior_raw": behav_multiplier,
        "availability_raw": avail_raw,
        "penalty": penalty
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="isnt/candidates.jsonl")
    parser.add_argument("--out", default="submission.csv")
    parser.add_argument("--limit", type=int, default=-1)
    args = parser.parse_args()

    print("Loading model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    print("Loading JD...")
    jd_text = extract_jd_text("isnt/job_description.docx")
    jd_embedding = model.encode(jd_text, normalize_embeddings=True)

    print(f"Reading candidates from {args.candidates}...")
    lines = []
    
    # Auto-detect if file is JSON list or JSONL
    is_json_list = args.candidates.lower().endswith(".json")
    
    if is_json_list:
        with open(args.candidates, "r", encoding="utf-8") as f:
            candidates_list = json.load(f)
            # Serialize each to JSON string to unify interface
            lines = [json.dumps(c) for c in candidates_list]
    else:
        with open(args.candidates, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    lines.append(line)
                    if args.limit > 0 and len(lines) >= args.limit:
                        break

    if args.limit > 0 and len(lines) > args.limit:
        lines = lines[:args.limit]

    print(f"Scoring {len(lines)} candidates in parallel...")
    heuristic_scores = []
    honeypot_count = 0
    
    # Run multiprocessing on Windows safely
    chunksize = max(1, len(lines) // (cpu_count() * 4)) if len(lines) > 100 else 1
    with Pool(cpu_count()) as pool:
        results = list(tqdm(pool.imap(process_line, lines, chunksize=chunksize), total=len(lines), desc="Scoring candidates"))
        
    for r in results:
        if r is None:
            honeypot_count += 1
        else:
            heuristic_scores.append(r)
            
    print(f"Loaded {len(heuristic_scores)} valid candidates. Filtered {honeypot_count} honeypots.")
    
    if not heuristic_scores:
        print("No valid candidates found!")
        return

    print("Pre-filtering top candidates for semantic matching...")
    # Normalize heuristic scores
    c_norms = normalize([x["career_raw"] for x in heuristic_scores])
    t_norms = normalize([x["technical_raw"] for x in heuristic_scores])
    p_norms = normalize([x["production_raw"] for x in heuristic_scores])
    a_norms = normalize([x["availability_raw"] for x in heuristic_scores])
    
    for i, item in enumerate(heuristic_scores):
        base_h = (
            0.30 * c_norms[i] +
            0.30 * t_norms[i] +
            0.25 * p_norms[i] +
            0.15 * a_norms[i]
        ) * item["behavior_raw"] - item["penalty"]
        
        if item["career_raw"] < 0:
            base_h -= 500
        elif item["career_raw"] < 20:
            base_h -= 200
            
        if item["production_raw"] < 20:
            base_h -= 300  # JD says production experience is absolutely required
            
        yoe = item["candidate"].get("profile", {}).get("years_of_experience", 0)
        if yoe > 12:
            base_h -= 100  # Heavy penalty for being too senior (likely architect)
        elif yoe < 4:
            base_h -= 100  # Heavy penalty for being too junior
            
        item["pre_score"] = base_h
        
    heuristic_scores.sort(key=lambda x: x["pre_score"], reverse=True)
    
    # Take top 5000 candidates for semantic matching (or all if we have fewer)
    top_n = min(5000, len(heuristic_scores))
    top_candidates = heuristic_scores[:top_n]
    
    print(f"Building texts for {len(top_candidates)} candidates...")
    candidate_texts = [build_candidate_text(item["candidate"]) for item in top_candidates]
    
    print("Encoding candidates...")
    candidate_embeddings = model.encode(candidate_texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)
    
    print("Calculating final scores and reasoning...")
    final_results = []
    
    sem_raw_values = []
    for i, item in enumerate(top_candidates):
        sem_raw = float(cos_sim(jd_embedding, candidate_embeddings[i]))
        sem_raw_values.append(sem_raw)
        
    sem_norms = normalize(sem_raw_values)
    
    # We also need to re-normalize the other scores for the top candidates to combine correctly with semantic
    c_norms_top = normalize([x["career_raw"] for x in top_candidates])
    t_norms_top = normalize([x["technical_raw"] for x in top_candidates])
    p_norms_top = normalize([x["production_raw"] for x in top_candidates])
    a_norms_top = normalize([x["availability_raw"] for x in top_candidates])
    
    for i, item in enumerate(top_candidates):
        base_score = (
            0.25 * c_norms_top[i] +
            0.25 * t_norms_top[i] +
            0.15 * p_norms_top[i] +
            0.10 * a_norms_top[i] +
            0.25 * sem_norms[i]
        )
        
        final_score = base_score * item["behavior_raw"]
        final_score -= item["penalty"]
        
        if item["career_raw"] < 0:
            final_score -= 500
        elif item["career_raw"] < 20:
            final_score -= 200
            
        if item["production_raw"] < 20:
            final_score -= 300
            
        yoe = item["candidate"].get("profile", {}).get("years_of_experience", 0)
        if yoe > 12:
            final_score -= 100
        elif yoe < 4:
            final_score -= 100
            
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
        
        # Round the score to 4 decimal places before appending for deterministic tie-breaker sorting
        rounded_score = round(final_score, 4)
        
        final_results.append({
            "candidate_id": raw["candidate_id"],
            "score": rounded_score,
            "reasoning": reasoning
        })

    # DETERMINISTIC SORTING & TIE-BREAKING
    # Sort: score descending, then candidate_id ascending for ties (crucial for validator check!)
    final_results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    top_100 = final_results[:100]

    # Write CSV with exact format required by spec
    print(f"Writing {args.out}...")
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank_idx, r in enumerate(top_100, start=1):
            writer.writerow([r["candidate_id"], rank_idx, f"{r['score']:.4f}", r["reasoning"]])
            
    print("Done! Validating submission...")
    # Execute validator python script
    os.system(f"python isnt/validate_submission.py {args.out}")

if __name__ == "__main__":
    main()

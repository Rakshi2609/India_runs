import json
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from career_evidence import score_career
from behavioral_score import score_behavioral
from availability_score import score_availability
from production_score import score_production
from candidate_text_builder import build_candidate_text
from buzzword_penalty import calculate_buzzword_penalty

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

    print("Loading candidates...")
    with open("data/sample_candidates.json") as f:
        candidates = json.load(f)

    print("Building candidate texts...")
    candidate_texts = [build_candidate_text(c) for c in candidates]
    
    print("Encoding candidates...")
    candidate_embeddings = model.encode(candidate_texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)

    results = []
    
    # Calculate raw scores
    career_raws = []
    prod_raws = []
    behav_raws = []
    avail_raws = []
    sem_raws = []
    penalties = []

    for i, c in enumerate(candidates):
        career_info = score_career(c)
        career_raw = career_info["score"]
        prod_raw = score_production(c)
        behav_raw = score_behavioral(c)
        avail_raw = score_availability(c)
        
        sem_raw = float(cos_sim(jd_embedding, candidate_embeddings[i]))
        
        penalty = calculate_buzzword_penalty(c, career_raw)

        career_raws.append(career_raw)
        prod_raws.append(prod_raw)
        behav_raws.append(behav_raw)
        avail_raws.append(avail_raw)
        sem_raws.append(sem_raw)
        penalties.append(penalty)

    # Normalize
    career_norms = normalize(career_raws)
    prod_norms = normalize(prod_raws)
    behav_norms = normalize(behav_raws)
    avail_norms = normalize(avail_raws)
    sem_norms = normalize(sem_raws)

    for i, c in enumerate(candidates):
        final_score = (
            0.35 * career_norms[i] +
            0.20 * prod_norms[i] +
            0.15 * behav_norms[i] +
            0.10 * avail_norms[i] +
            0.20 * sem_norms[i]
        )
        
        final_score -= penalties[i]
        
        # JD Trap Penalties
        if career_raws[i] < 0:
            final_score *= 0.25
        elif career_raws[i] < 20:
            final_score *= 0.5

        results.append({
            "name": c["profile"]["anonymized_name"],
            "title": c["profile"]["current_title"],
            "career_raw": career_raws[i],
            "semantic_raw": sem_raws[i],
            "penalty": penalties[i],
            "total_score": final_score
        })

    results.sort(key=lambda x: x["total_score"], reverse=True)

    print("=" * 100)
    print(f"{'Candidate':<25} | {'Title':<30} | {'Career':<8} | {'Semantic':<8} | {'Penalty':<8} | {'Total'}")
    print("-" * 100)
    for r in results[:20]:
        print(f"{r['name']:<25} | {r['title'][:30]:<30} | {r['career_raw']:>8.1f} | {r['semantic_raw']:>8.2f} | {r['penalty']:>8.1f} | {r['total_score']:>8.1f}")

if __name__ == "__main__":
    main()

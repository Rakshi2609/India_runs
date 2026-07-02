import json
import numpy as np
from sentence_transformers import SentenceTransformer

def main():
    print("Loading model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    print("Loading candidates...")
    candidates = []
    with open(r"D:\isnt\candidates.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            candidates.append(json.loads(line))
            
    print(f"Loaded {len(candidates)} candidates.")
    
    print("Building texts...")
    candidate_ids = []
    skills_texts = []
    exp_texts = []
    
    for c in candidates:
        candidate_ids.append(c["candidate_id"])
        skills_texts.append(" ".join([s.get("name", "") for s in c.get("skills", [])]))
        e_text = []
        for job in c.get("career_history", []):
            e_text.append(job.get("title", ""))
            e_text.append(job.get("description", ""))
        exp_texts.append("\n".join(e_text))
        
    print("Encoding skills...")
    skills_embeddings = model.encode(skills_texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)
    
    print("Encoding experience...")
    exp_embeddings = model.encode(exp_texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)
    
    print("Saving to embeddings.npy...")
    np.save("embeddings.npy", {
        "candidate_ids": np.array(candidate_ids),
        "skills_embeddings": skills_embeddings,
        "exp_embeddings": exp_embeddings
    }, allow_pickle=True)
    print("Done!")

if __name__ == "__main__":
    main()

# app.py

import streamlit as st
import json
import csv
import io
import sys
import os

# Set page configuration for layout and title
st.set_page_config(
    page_title="HireIQ — Candidate Discovery Portal",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Append src folder to path for relative imports
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from career_evidence import score_career
from technical_fit import score_technical_fit
from behavioral_score import score_behavioral
from availability_score import score_availability
from production_score import score_production
from buzzword_penalty import calculate_buzzword_penalty
from reasoning_generator import generate_reasoning
from honeypot_filter import is_honeypot

# Premium Custom Styling with Glassmorphism and Custom Fonts
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0e121a 0%, #151b26 100%);
        color: #e2e8f0;
    }
    
    .main-title {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0.2rem;
        font-weight: 800;
    }
    
    .subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .metric-card {
        flex: 1;
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #818cf8;
        margin-bottom: 4px;
        font-family: 'Outfit', sans-serif;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Highlight the run button */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.4);
        transition: all 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #4f46e5 0%, #9333ea 100%);
        box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.6);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Main UI layout
st.markdown("<h1 class='main-title'>HireIQ Discover</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Heuristic-Semantic Engine for Senior AI Engineer Matching</p>", unsafe_allow_html=True)

# Helpers for file handling
def extract_jd_text(doc_bytes):
    from docx import Document
    doc = Document(io.BytesIO(doc_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

def normalize(values):
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [0.0] * len(values)
    return [((v - min_val) / (max_val - min_val)) * 100.0 for v in values]

# Sidebar configurations
with st.sidebar:
    st.markdown("### Model Config")
    st.info("Uses SentenceTransformer `all-MiniLM-L6-v2` for semantic indexing.")
    
    # Load model cache
    @st.cache_resource
    def load_model():
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    try:
        model = load_model()
        st.success("Model cached successfully!")
    except Exception as e:
        st.error(f"Error loading model: {e}")

# Upload section in cards
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("📁 Input Materials")

col1, col2 = st.columns(2)

with col1:
    jd_file = st.file_uploader("Upload Job Description (.docx)", type=["docx"])
    # Auto-load default if present
    default_jd_path = "isnt/job_description.docx"
    if not jd_file and os.path.exists(default_jd_path):
        with open(default_jd_path, "rb") as f:
            jd_bytes = f.read()
        jd_file_name = "job_description.docx (Default)"
        st.caption("Using default `isnt/job_description.docx`")
    elif jd_file:
        jd_bytes = jd_file.read()
        jd_file_name = jd_file.name
    else:
        jd_bytes = None
        jd_file_name = None

with col2:
    candidates_file = st.file_uploader("Upload Candidates (.json, .jsonl)", type=["json", "jsonl"])
    default_candidates_path = "isnt/sample_candidates.json"
    if not candidates_file and os.path.exists(default_candidates_path):
        with open(default_candidates_path, "rb") as f:
            cand_bytes = f.read()
        cand_file_name = "sample_candidates.json (Default)"
        st.caption("Using default `isnt/sample_candidates.json`")
    elif candidates_file:
        cand_bytes = candidates_file.read()
        cand_file_name = candidates_file.name
    else:
        cand_bytes = None
        cand_file_name = None

st.markdown("</div>", unsafe_allow_html=True)

# Run process button
if st.button("🚀 Process & Rank Candidates"):
    if not jd_bytes:
        st.error("Please upload or provide a Job Description document.")
    elif not cand_bytes:
        st.error("Please upload or provide a Candidates file.")
    else:
        with st.spinner("Extracting JD & embedding context..."):
            jd_text = extract_jd_text(jd_bytes)
            jd_embedding = model.encode(jd_text, normalize_embeddings=True)
            
        with st.spinner("Reading and parsing candidate profiles..."):
            # Determine list or lines
            content_str = cand_bytes.decode("utf-8")
            candidates = []
            
            if cand_file_name.endswith(".json") and not cand_file_name.endswith(".jsonl"):
                try:
                    candidates = json.loads(content_str)
                except Exception as e:
                    # Fallback to line-by-line if standard JSON parse fails
                    candidates = [json.loads(l) for l in content_str.strip().split("\n") if l.strip()]
            else:
                candidates = [json.loads(l) for l in content_str.strip().split("\n") if l.strip()]

        st.info(f"Loaded {len(candidates)} candidate profiles from file.")

        with st.spinner("Calculating technical, career, and availability metrics..."):
            results = []
            honeypots = 0
            
            for c in candidates:
                if is_honeypot(c):
                    honeypots += 1
                    continue
                career_raw = score_career(c)["score"]
                tech_raw = score_technical_fit(c)
                prod_raw = score_production(c)
                behav_multiplier = score_behavioral(c)
                avail_raw = score_availability(c)
                penalty = calculate_buzzword_penalty(c, career_raw)
                
                results.append({
                    "candidate": c,
                    "career_raw": career_raw,
                    "technical_raw": tech_raw,
                    "production_raw": prod_raw,
                    "behavior_raw": behav_multiplier,
                    "availability_raw": avail_raw,
                    "penalty": penalty
                })

        if not results:
            st.warning("All candidates were filtered out as honeypots or no candidates found.")
        else:
            with st.spinner("Encoding semantic narratives and building rankings..."):
                from sentence_transformers.util import cos_sim
                from candidate_text_builder import build_candidate_text
                
                # Fetch text representations
                texts = [build_candidate_text(r["candidate"]) for r in results]
                embeddings = model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
                
                # Compute semantic matching values
                sem_raw_values = []
                for i in range(len(results)):
                    sem_raw = float(cos_sim(jd_embedding, embeddings[i]))
                    sem_raw_values.append(sem_raw)
                    
                sem_norms = normalize(sem_raw_values)
                c_norms = normalize([r["career_raw"] for r in results])
                t_norms = normalize([r["technical_raw"] for r in results])
                p_norms = normalize([r["production_raw"] for r in results])
                a_norms = normalize([r["availability_raw"] for r in results])
                
                final_list = []
                for i, r in enumerate(results):
                    base_score = (
                        0.25 * c_norms[i] +
                        0.25 * t_norms[i] +
                        0.15 * p_norms[i] +
                        0.10 * a_norms[i] +
                        0.25 * sem_norms[i]
                    )
                    
                    final_score = base_score * r["behavior_raw"]
                    final_score -= r["penalty"]
                    
                    if r["career_raw"] < 0:
                        final_score -= 500
                    elif r["career_raw"] < 20:
                        final_score -= 200
                        
                    if r["production_raw"] < 20:
                        final_score -= 300
                        
                    yoe = r["candidate"].get("profile", {}).get("years_of_experience", 0)
                    if yoe > 12:
                        final_score -= 100
                    elif yoe < 4:
                        final_score -= 100
                        
                    raw = {
                        "candidate_id": r["candidate"]["candidate_id"],
                        "career_raw": r["career_raw"],
                        "production_raw": r["production_raw"],
                        "behavior_raw": r["behavior_raw"],
                        "availability_raw": r["availability_raw"],
                        "semantic_raw": sem_raw_values[i],
                        "penalty": r["penalty"]
                    }
                    
                    reasoning = generate_reasoning(r["candidate"], raw)
                    
                    final_list.append({
                        "candidate_id": raw["candidate_id"],
                        "score": round(final_score, 4),
                        "reasoning": reasoning
                    })
                    
                final_list.sort(key=lambda x: (-x["score"], x["candidate_id"]))
                top_100 = final_list[:100]

            # Render key stats
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class='metric-container'>
                <div class='metric-card'>
                    <div class='metric-value'>{len(candidates)}</div>
                    <div class='metric-label'>Total Loaded</div>
                </div>
                <div class='metric-card'>
                    <div class='metric-value'>{len(results)}</div>
                    <div class='metric-label'>Valid Profiles</div>
                </div>
                <div class='metric-card' style='border-color: rgba(239, 68, 68, 0.3)'>
                    <div class='metric-value' style='color: #ef4444'>{honeypots}</div>
                    <div class='metric-label'>Filtered Honeypots</div>
                </div>
                <div class='metric-card'>
                    <div class='metric-value'>{len(top_100)}</div>
                    <div class='metric-label'>Ranked Output</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Display ranking list
            st.subheader("🏆 Top Ranked Candidates")
            
            display_rows = []
            for rank_idx, r in enumerate(top_100, start=1):
                display_rows.append({
                    "Rank": rank_idx,
                    "Candidate ID": r["candidate_id"],
                    "Match Score": f"{r['score']:.4f}",
                    "Shortlist Reasoning": r["reasoning"]
                })
                
            st.dataframe(display_rows, use_container_width=True)
            
            # Export CSV
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for rank_idx, r in enumerate(top_100, start=1):
                writer.writerow([r["candidate_id"], rank_idx, f"{r['score']:.4f}", r["reasoning"]])
                
            st.download_button(
                label="📥 Download Submission CSV",
                data=csv_buffer.getvalue(),
                file_name="submission.csv",
                mime="text/csv"
            )

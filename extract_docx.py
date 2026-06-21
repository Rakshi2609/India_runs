from docx import Document
import sys

def extract(file_path):
    print("=" * 80)
    print(f"EXTRACTING: {file_path}")
    print("=" * 80)
    doc = Document(file_path)
    for p in doc.paragraphs:
        if p.text.strip():
            print(p.text)
    print("\n")

if __name__ == "__main__":
    extract("data/job_description.docx")
    extract("data/redrob_signals_doc.docx")

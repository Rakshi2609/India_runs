import docx

def docx_to_txt(docx_path, txt_path):
    d = docx.Document(docx_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join([p.text for p in d.paragraphs]))

docx_to_txt(r'D:\India_runs_data_and_ai_challenge\submission_spec.docx', r'D:\India_runs\spec.txt')
docx_to_txt(r'D:\India_runs_data_and_ai_challenge\redrob_signals_doc.docx', r'D:\India_runs\signals.txt')
print("Done")

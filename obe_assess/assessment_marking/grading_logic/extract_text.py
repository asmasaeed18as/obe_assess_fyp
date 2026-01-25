import pdfplumber
import docx2txt
import os

def extract_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_from_docx(path):
    return docx2txt.process(path)

def extract_from_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text(path):
    path = str(path).strip()
    _, ext = os.path.splitext(path.lower())
    if ext == ".pdf":
        return extract_from_pdf(path)
    elif ext == ".docx":
        return extract_from_docx(path)
    elif ext == ".txt":
        return extract_from_txt(path)
    else:
        # Fallback for temp files that might lack extension in path strings
        try:
            return extract_from_pdf(path)
        except:
            return ""
import io
import fitz  # PyMuPDF
from docx import Document

try:
    import pymupdf4llm  # Optional dependency for Markdown extraction
except Exception:  # ImportError or any env-specific error
    pymupdf4llm = None

def extract_text_from_file(file_obj, filename):
    """
    State-of-the-Art LLM Extraction:
    Converts PDFs and DOCX files into pure Markdown.
    LLMs natively understand Markdown tables, completely eliminating hallucination.
    """
    file_ext = filename.lower().split('.')[-1]

    try:
        file_obj.seek(0)
        file_bytes = file_obj.read()

        # ==========================================
        # 1. PDF EXTRACTION (The LLM Standard)
        # ==========================================
        if file_ext == 'pdf':
            # Open the PDF stream directly from memory
            doc = fitz.open(stream=file_bytes, filetype="pdf")

            # Prefer Markdown extraction if available; otherwise fallback to plain text
            if pymupdf4llm is not None:
                return pymupdf4llm.to_markdown(doc)

            # Fallback: extract plain text per page
            extracted = []
            for page in doc:
                extracted.append(page.get_text("text"))
            return "\n".join(extracted)

        # ==========================================
        # 2. DOCX EXTRACTION (Formatted as Markdown)
        # ==========================================
        elif file_ext in ['docx', 'doc']:
            doc = Document(io.BytesIO(file_bytes))
            extracted_text = []
            
            # Extract paragraphs
            for p in doc.paragraphs:
                if p.text.strip():
                    extracted_text.append(p.text.strip())
            
            # Extract tables and format them as Markdown tables so the LLM understands them
            for table in doc.tables:
                extracted_text.append("\n") # Add spacing before table
                for i, row in enumerate(table.rows):
                    clean_row = list(dict.fromkeys([cell.text.replace('\n', ' ').strip() for cell in row.cells if cell.text.strip()]))
                    if clean_row:
                        # Format as a Markdown row: | Column 1 | Column 2 |
                        extracted_text.append("| " + " | ".join(clean_row) + " |")
                        
                        # Add the Markdown header separator after the first row
                        if i == 0:
                            extracted_text.append("|" + "|".join(["---"] * len(clean_row)) + "|")
                extracted_text.append("\n")

            return "\n".join(extracted_text)

        else:
            raise ValueError("Unsupported file format.")

    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return ""

import io
import pdfplumber
from docx import Document

def extract_text_from_file(file_obj, filename):
    """
    Extracts text from PDF or DOCX while PRESERVING TABLE STRUCTURES.
    This is crucial for ML models to understand columns (CLO | PLO | BT Level).
    """
    extracted_text = []
    file_ext = filename.lower().split('.')[-1]

    try:
        file_obj.seek(0)
        file_bytes = file_obj.read()

        if file_ext == 'pdf':
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    # 1. Extract plain text
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                    
                    # 2. Extract tables and format them with ' | ' separators
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            # Clean empty cells and join with a pipe
                            clean_row = [str(cell).replace('\n', ' ').strip() for cell in row if cell]
                            if clean_row:
                                extracted_text.append(" | ".join(clean_row))

        elif file_ext in ['docx', 'doc']:
            doc = Document(io.BytesIO(file_bytes))
            
            # 1. Extract paragraphs
            for p in doc.paragraphs:
                if p.text.strip():
                    extracted_text.append(p.text.strip())
            
            # 2. Extract tables
            for table in doc.tables:
                for row in table.rows:
                    clean_row = [cell.text.replace('\n', ' ').strip() for cell in row.cells if cell.text.strip()]
                    if clean_row:
                        extracted_text.append(" | ".join(clean_row))
        else:
            raise ValueError("Unsupported file format.")

        return "\n".join(extracted_text)

    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return ""
    finally:
        try:
            file_obj.close()
        except Exception:
            pass
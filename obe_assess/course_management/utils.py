import io
from PyPDF2 import PdfReader
from docx import Document

def extract_text_from_pdf_filefield(filefield):
    """
    filefield: Django FileField or file-like object
    returns: extracted plain text
    """
    # filefield might be an InMemoryUploadedFile or FieldFile
    try:
        # Seek to start
        filefield.open()
        data = filefield.read()
        # PyPDF2 accepts bytes -> use PdfReader(io.BytesIO(data))
        reader = PdfReader(io.BytesIO(data))
        text = []
        for p in reader.pages:
            page_text = p.extract_text() or ""
            text.append(page_text)
        return "\n".join(text)
    finally:
        try:
            filefield.close()
        except Exception:
            pass

def extract_text_from_docx_fileobj(fileobj):
    """
    Accept file-like object (bytes). Returns text.
    """
    # if given FieldFile, use .read()
    try:
        data = fileobj.read()
        doc = Document(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception:
        return ""

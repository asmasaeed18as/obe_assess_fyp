# assessment_creation/utils.py
import fitz   # PyMuPDF
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.core.files.base import ContentFile

def extract_text_from_pdf_filefield(django_file) -> str:
    """
    django_file is an UploadedFile or FileField instance.
    We'll read its bytes and use PyMuPDF.
    """
    # read bytes
    file_bytes = django_file.read()
    # open with fitz using stream
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def render_assessment_pdf(assessment_title: str, questions_data: list) -> ContentFile:
    """
    Build a simple PDF from the questions_data (list of dicts with keys: question, answer, rubric).
    Returns a Django ContentFile you can assign to a FileField.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(assessment_title, styles['Title']))
    story.append(Spacer(1, 12))

    for i, q in enumerate(questions_data, start=1):
        story.append(Paragraph(f"Q{i}. {q.get('question')}", styles['Heading3']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Model Answer: {q.get('answer')}", styles['Normal']))
        story.append(Spacer(1, 6))
        rubric = q.get("rubric", {})
        story.append(Paragraph("Rubric:", styles['Italic']))
        story.append(Paragraph(f"• Excellent: {rubric.get('Excellent', '')}", styles['Normal']))
        story.append(Paragraph(f"• Average: {rubric.get('Average', '')}", styles['Normal']))
        story.append(Paragraph(f"• Poor: {rubric.get('Poor', '')}", styles['Normal']))
        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return ContentFile(buffer.read())

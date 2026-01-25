import re

def clean_raw_text(text):
    if not text:
        return ""
    # Remove common page headings/footers
    text = re.sub(r"\n?\s*Page\s*\d+(?:\s*of\s*\d+)?\s*\n?", "\n", text, flags=re.IGNORECASE)
    # Remove multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Fix broken hyphenated words
    text = re.sub(r"-\n\s*", "", text)
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    # Remove consecutive blank lines
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()
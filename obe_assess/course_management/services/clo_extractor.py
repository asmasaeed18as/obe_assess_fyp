import re
import nltk

# Ensure NLTK data is available for the fallback logic
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Common regex patterns to catch CLOs lines
CLO_PATTERNS = [
    r'(CLO[-\s]?(\d+))[:\.\-\s]+(.+)',    # "CLO-1: Students will..."
    r'^(Outcome|CLO)[:\s]+(.+)$',        # "Outcome: ..."
    r'^(PLO[:\s]+.*)$',                 # sometimes PLOs labeled
]

# Bloom keywords mapping (simple)
BLOOM_KEYWORDS = {
    "C1": ["define", "list", "identify", "name", "recall", "remember"],
    "C2": ["explain", "describe", "summarize", "interpret", "classify"],
    "C3": ["apply", "use", "demonstrate", "solve", "implement"],
    "C4": ["analyze", "differentiate", "compare", "contrast"],
    "C5": ["evaluate", "judge", "critique", "assess"],
    "C6": ["create", "design", "construct", "develop", "formulate"],
}

def map_bloom_from_text(text):
    t = text.lower()
    for level, keywords in BLOOM_KEYWORDS.items():
        for k in keywords:
            if re.search(r'\b' + re.escape(k) + r'\b', t):
                return level
    return None

def extract_clos_from_text(text):
    """
    Return list of dicts: {"code": "CLO-1", "text": "...", "bloom": "C3"}
    """
    clos = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    # First pass: look for explicit CLO lines
    for line in lines:
        m = re.search(r'(CLO[-\s]?(\d+))[:\.\-\s]+(.+)', line, re.IGNORECASE)
        if m:
            code = m.group(1).upper().replace(" ", "-")
            txt = m.group(3).strip()
            bloom = map_bloom_from_text(txt)
            clos.append({"code": code, "text": txt, "bloom": bloom})
            
    # Fallback: look for numbered list items like "1. ...", "2) ..."
    if not clos:
        for line in lines:
            m = re.match(r'^\d+[\.\)]\s*(.+)', line)
            if m:
                txt = m.group(1).strip()
                bloom = map_bloom_from_text(txt)
                # Assign a generic code if none found
                clos.append({"code": f"CLO-{len(clos)+1}", "text": txt, "bloom": bloom})
                
    # Final fallback: chunk long paragraphs into sentences and pick top N
    if not clos:
        try:
            from nltk.tokenize import sent_tokenize
            sents = sent_tokenize(text)
        except Exception:
            # Simple split as fallback
            sents = re.split(r'(?<=[.!?])\s+', text)
            
        for i, s in enumerate(sents[:10]):
            bloom = map_bloom_from_text(s)
            clos.append({"code": f"CLO-{i+1}", "text": s.strip(), "bloom": bloom})
            
    return clos
import re
from collections import OrderedDict

def _find_question_starts(text):
    starts = []
    for m in re.finditer(r"(?:Q(?:uestion)?\s*\d+[:.)]?)|(?:^\d+\.\s+)", text, flags=re.IGNORECASE | re.MULTILINE):
        starts.append((m.start(), m.group(0).strip()))
    return starts

def segment_questions(text):
    text = text.strip()
    q_starts = _find_question_starts(text)
    
    if not q_starts:
        # Fallback: split by double newline
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        questions = OrderedDict()
        for i, b in enumerate(blocks, start=1):
            questions[f"Q{i}"] = {"question": b, "answer": ""}
        return questions

    positions = [pos for pos, _ in q_starts] + [len(text)]
    questions = OrderedDict()
    
    for idx in range(len(q_starts)):
        start_pos = positions[idx]
        end_pos = positions[idx+1]
        block = text[start_pos:end_pos].strip()

        qid_match = re.search(r"(?:Q(?:uestion)?\s*(\d+))|^(\d+)\.", block, flags=re.IGNORECASE)
        if qid_match:
            num = qid_match.group(1) or qid_match.group(2)
            qid = f"Q{num}"
        else:
            qid = f"Q{idx+1}"

        content_only = re.sub(r"^(?:Q(?:uestion)?\s*\d+[:.)]?)", "", block, flags=re.IGNORECASE).strip()
        
        # Split Question from Answer
        split_marker = re.split(r"\n(?:(?:Answer|Student Answer|Model Answer|Solution)\s*[:\-])", content_only, flags=re.IGNORECASE)
        
        if len(split_marker) >= 2:
            q_text = split_marker[0].strip()
            a_text = "\n".join(s.strip() for s in split_marker[1:]).strip()
        else:
            lines = content_only.splitlines()
            if len(lines) > 1 and lines[0].strip():
                q_text = lines[0].strip()
                a_text = "\n".join(lines[1:]).strip()
            else:
                q_text = content_only
                a_text = ""
        
        questions[qid] = {"question": q_text, "answer": a_text}

    return questions

def segment_rubric(text):
    m = re.search(r"(Rubric|Marking Scheme|Marking Criteria|Marking Scheme:|Scheme:)", text, flags=re.IGNORECASE)
    if not m:
        return text # If no header found, assume whole text is rubric
    return text[m.start():].strip()
import re

def extract_marks_from_rubric(rubric_text):
    criteria = []
    lines = [ln.strip() for ln in rubric_text.splitlines() if ln.strip()]
    for line in lines:
        # Patter: Q1 - Accuracy: 3 marks
        m = re.search(r"(Q(?:uestion)?\s*\d+|\b\d+\b)?\s*[:,.\-]?\s*([A-Za-z0-9 \-()\/&]+?)\s*(?:\(|:|\-)?\s*(\d+)\s*marks?", line, flags=re.IGNORECASE)
        if m:
            qid_raw = m.group(1)
            criterion = m.group(2).strip()
            marks = int(m.group(3))
            qid = None
            if qid_raw:
                qid_m = re.search(r"\d+", qid_raw)
                if qid_m:
                    qid = f"Q{qid_m.group(0)}"
            criteria.append({"qid": qid, "criterion": criterion, "marks": marks})
            continue
        
        # Pattern: Accuracy - 3 marks
        m2 = re.search(r"(.+?)\s*[–\-:]\s*(\d+)\s*marks?", line, flags=re.IGNORECASE)
        if m2:
            criteria.append({"qid": None, "criterion": m2.group(1).strip(), "marks": int(m2.group(2))})

    return criteria

def extract_total_marks(criteria_list):
    for c in criteria_list:
        if c["criterion"].lower() == "total":
            return c["marks"]
    return sum(c["marks"] for c in criteria_list if c.get("marks"))

def map_criteria_to_questions(criteria_list, questions):
    qids = list(questions.keys())
    mapping = {qid: [] for qid in qids}
    
    # 1. Direct Mapping
    direct_found = any(c.get("qid") for c in criteria_list)
    if direct_found:
        for c in criteria_list:
            if c.get("qid") and c["qid"] in mapping:
                mapping[c["qid"]].append(c)
            else:
                for q in qids: mapping[q].append(c)
        return mapping

    # 2. 1-to-1 Mapping if counts match
    if len(criteria_list) == len(qids) and len(qids) > 0:
        for i, q in enumerate(qids):
            mapping[q].append(criteria_list[i])
        return mapping

    # 3. Fallback: Assign all criteria to all questions
    for q in qids:
        mapping[q] = list(criteria_list)
    return mapping
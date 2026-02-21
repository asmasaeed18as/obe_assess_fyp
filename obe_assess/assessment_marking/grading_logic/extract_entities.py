import re

def extract_student_info(text):
    """Extracts Name and CMS ID from the first part of the document."""
    header = text[:1000]
    
    # CMS ID: More flexible pattern for IDs (supports spaces, colons, or just the number)
    cms_id = "Not Found"
    cms_match = re.search(r"(?:CMS\s*ID|CMS|ID|Reg\s*(?:No|#)?)\s*[:\-]?\s*([A-Z0-9\-]+)", header, re.I)
    if cms_match:
        cms_id = cms_match.group(1).strip()

    # Name: Updated to catch names even if they aren't perfectly capitalized
    name = "Unknown"
    name_match = re.search(r"(?:Name|Student\s*Name)\s*[:\-]?\s*([A-Za-z\s]{3,50})", header, re.I)
    if name_match:
        name = name_match.group(1).strip().split('\n')[0] # Ensure we only get the first line
        # Remove trailing identifiers if they appear on the same line (e.g., "CMS ID")
        name = re.split(r"\bCMS\b|\bID\b|\bReg\b", name, maxsplit=1, flags=re.I)[0].strip()
        
    return {"student_name": name, "cms_id": cms_id}

def extract_marks_from_rubric(rubric_text):
    criteria = []
    # Split into lines and ignore empty ones
    lines = [ln.strip() for ln in rubric_text.splitlines() if ln.strip()]
    
    for line in lines:
        # Pattern 1: Look for Question ID, Criterion, and a Number at the end
        # Matches: "Q1 - Accuracy: 10 marks" or "1. Content 5"
        m = re.search(r"(?:Q(?:uestion)?\s*(\d+))?[:.\-]?\s*(.*?)\s*[:\-\(\[]?\s*(\d+)\s*(?:marks?|pts|points)?[\)\]]?$", line, re.I)
        
        if m:
            qid_num = m.group(1)
            criterion = m.group(2).strip()
            marks = int(m.group(3))
            
            # Clean up criterion name (remove trailing punctuation)
            criterion = re.sub(r"[:\-\s]+$", "", criterion)
            
            qid = f"Q{qid_num}" if qid_num else None
            criteria.append({"qid": qid, "criterion": criterion, "marks": marks})

    return criteria

def extract_total_marks(criteria_list):
    # Check if 'Total' is explicitly defined
    for c in criteria_list:
        if c["criterion"].lower() == "total":
            return c["marks"]
    # No explicit total found
    return 0

def map_criteria_to_questions(criteria_list, questions):
    qids = list(questions.keys())
    mapping = {qid: [] for qid in qids}
    
    # Filter out any "Total" rows from the mapping
    actual_criteria = [c for c in criteria_list if c["criterion"].lower() != "total"]

    # 1. Direct QID Mapping (If Q1 is in the rubric)
    direct_mapping_exists = any(c.get("qid") for c in actual_criteria)
    if direct_mapping_exists:
        for c in actual_criteria:
            if c.get("qid") in mapping:
                mapping[c["qid"]].append(c)
        return mapping

    # 2. Sequential Mapping (If number of rubric lines = number of questions)
    if len(actual_criteria) == len(qids):
        for i, qid in enumerate(qids):
            mapping[qid].append(actual_criteria[i])
        return mapping

    # 3. Global Mapping (Assign all criteria to every question)
    for qid in qids:
        mapping[qid] = actual_criteria
    return mapping

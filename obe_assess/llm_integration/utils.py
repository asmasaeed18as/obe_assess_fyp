import json
import re


def _safe_json_loads(text):
    """Try multiple safe normalizations before giving up on JSON parsing."""
    base = (text or "").strip()
    if not base:
        return None

    candidates = [
        base,
        re.sub(r',\s*([\]}])', r'\1', base),
        re.sub(r'[\u201c\u201d]', '"', re.sub(r"[\u2018\u2019]", "'", base)),
    ]

    no_comments = re.sub(r'//.*?$', '', base, flags=re.MULTILINE)
    no_comments = re.sub(r'/\*[\s\S]*?\*/', '', no_comments)
    candidates.append(no_comments)
    candidates.append(re.sub(r',\s*([\]}])', r'\1', no_comments))

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return None


def _extract_balanced_json_chunks(text):
    """
    Extract top-level balanced JSON chunks from mixed prose + JSON responses.
    """
    chunks = []
    stack = []
    start = None
    in_str = False
    escape = False

    for idx, ch in enumerate(text or ""):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue

        if ch in "{[":
            if not stack:
                start = idx
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                continue
            open_ch = stack[-1]
            if (open_ch == "{" and ch == "}") or (open_ch == "[" and ch == "]"):
                stack.pop()
                if not stack and start is not None:
                    chunks.append(text[start : idx + 1])
                    start = None
            else:
                stack = []
                start = None

    return chunks


def clean_and_extract_json(raw_text):
    """Aggressively hunts for JSON boundaries and removes trailing commas."""
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(code_block_pattern, raw_text or "", re.IGNORECASE)
    if match:
        raw_text = match.group(1)

    start_idx = -1
    for i, char in enumerate(raw_text or ""):
        if char in ["{", "["]:
            start_idx = i
            break

    end_idx = -1
    text = raw_text or ""
    for i in range(len(text) - 1, -1, -1):
        if text[i] in ["}", "]"]:
            end_idx = i
            break

    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        extracted_json = text[start_idx : end_idx + 1]
        extracted_json = re.sub(r',\s*([\]}])', r'\1', extracted_json)
        return extracted_json

    return raw_text


def extract_questions_from_any_structure(parsed_data):
    """Digs through nested lists/dicts to find question objects."""
    extracted = []

    def walk(node):
        if isinstance(node, dict):
            if "questions" in node and isinstance(node.get("questions"), list):
                for q in node["questions"]:
                    if isinstance(q, dict):
                        extracted.append(q)
                for v in node.values():
                    walk(v)
                return
            if "question" in node:
                extracted.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(parsed_data)

    # Deduplicate by normalized question text if possible
    unique = []
    seen = set()
    for item in extracted:
        key = str(item.get("question", "")).strip().lower()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        unique.append(item)
    return unique


def parse_and_clean_assessment(result_text, questions_config, strategy):
    """Parses, validates, and forcefully recovers malformed model data without crashing."""
    raw_questions_data = []

    # 1) Parse fenced JSON blocks first
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(code_block_pattern, result_text or "", re.IGNORECASE)
    json_strings_to_try = matches if matches else [result_text or ""]

    for raw_text in json_strings_to_try:
        cleaned_text = clean_and_extract_json(raw_text)
        # Fix escaped quote edge case around array elements
        cleaned_text = re.sub(r'([\[, ]\s*)\\"', r'\1"', cleaned_text)
        cleaned_text = re.sub(r'\\"(\s*[\],])', r'"\1', cleaned_text)

        parsed = _safe_json_loads(cleaned_text)
        if parsed is None:
            continue
        raw_questions_data.extend(extract_questions_from_any_structure(parsed))

    # 2) Balanced JSON chunk recovery from mixed prose output
    if not raw_questions_data:
        for chunk in _extract_balanced_json_chunks(result_text or ""):
            parsed = _safe_json_loads(chunk)
            if parsed is None:
                continue
            raw_questions_data.extend(extract_questions_from_any_structure(parsed))

    # 3) Regex salvage for question/answer pairs when JSON is badly broken
    if not raw_questions_data:
        qa_pattern = re.compile(
            r'"question"\s*:\s*"(?P<question>.*?)"[\s\S]*?"answer"\s*:\s*"(?P<answer>.*?)"',
            re.IGNORECASE,
        )
        for m in qa_pattern.finditer(result_text or ""):
            raw_questions_data.append(
                {
                    "question": m.group("question").strip(),
                    "answer": m.group("answer").strip(),
                }
            )

    final_questions = []

    for i, config in enumerate(questions_config):
        q_data = {}

        if i < len(raw_questions_data):
            q_data = raw_questions_data[i]
        if not isinstance(q_data, dict):
            q_data = {"question": str(q_data)}

        expected_type = config.get("question_type") or strategy.get("structure", "Standard")

        # Normalize question first
        if "question" in q_data and q_data["question"] is not None:
            q_data["question"] = str(q_data["question"]).strip()

        # Ensure answer exists
        if "answer" not in q_data or not str(q_data["answer"]).strip():
            if expected_type in ["Multiple Choice", "MCQ"]:
                q_data["answer"] = "Option A"
            else:
                q_data["answer"] = "Detailed model solution expected."
        else:
            q_data["answer"] = str(q_data["answer"]).strip()

        # Ensure rubric exists
        if "rubric" not in q_data or not isinstance(q_data["rubric"], dict):
            q_data["rubric"] = {
                "Excellent": "100% correct.",
                "Average": "Partially correct.",
                "Poor": "0% correct.",
            }

        # MCQ options normalization
        if expected_type in ["Multiple Choice", "MCQ"]:
            raw_options = q_data.get("options", [])
            if isinstance(raw_options, str):
                raw_options = [opt.strip() for opt in raw_options.split(",")]
            elif isinstance(raw_options, list) and len(raw_options) == 1 and "," in str(raw_options[0]):
                raw_options = [opt.strip() for opt in str(raw_options[0]).split(",")]
            elif not isinstance(raw_options, list):
                raw_options = []

            while len(raw_options) < 4:
                raw_options.append("Option not generated")
            raw_options = raw_options[:4]

            prefixes = ["A) ", "B) ", "C) ", "D) "]
            clean_options = []
            for j in range(4):
                opt = re.sub(r'^[A-D][\.\)]\s*', '', str(raw_options[j]))
                clean_options.append(f"{prefixes[j]}{opt}")
            q_data["options"] = clean_options
        else:
            q_data["options"] = None

        # Rubric text cleanup
        for level in ["Excellent", "Average", "Poor"]:
            rubric_text = q_data["rubric"].get(level, "N/A")
            clean_rubric = re.sub(r'^\d+/\d+\s*[-:]\s*', '', str(rubric_text))
            q_data["rubric"][level] = clean_rubric

        # Force metadata correctness
        q_data["id"] = config.get("id")
        q_data["marks"] = config.get("weightage")
        q_data["meta"] = {
            "clo": config.get("clo"),
            "bloom": config.get("bloom_level"),
            "difficulty": config.get("difficulty"),
            "type": expected_type,
        }

        # Ultimate safe fallback so frontend never sees a blank question
        if "question" not in q_data or not q_data["question"]:
            q_data["question"] = f"Error: JSON formatting crashed for {config.get('id')}."
            q_data["answer"] = "N/A"
            q_data["options"] = None
            q_data["rubric"] = {"Excellent": "N/A", "Average": "N/A", "Poor": "N/A"}

        final_questions.append(q_data)

    return final_questions

import json
import re

def clean_and_extract_json(raw_text):
    """Aggressively hunts for a JSON object or array, ignores markdown garbage, and fixes trailing commas."""
    # 1. Strip markdown
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(code_block_pattern, raw_text, re.IGNORECASE)
    if match:
        raw_text = match.group(1)
    
    # 2. Find the JSON boundaries
    start_idx = -1
    for i, char in enumerate(raw_text):
        if char in ['{', '[']:
            start_idx = i
            break
            
    end_idx = -1
    for i in range(len(raw_text) - 1, -1, -1):
        if raw_text[i] in ['}', ']']:
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        extracted_json = raw_text[start_idx:end_idx+1]
        
        #THE TRAILING COMMA FIX
        # This regex looks for a comma followed by any amount of whitespace, 
        # immediately followed by a closing bracket } or ]
        extracted_json = re.sub(r',\s*([\]}])', r'\1', extracted_json)
        
        return extracted_json
    
    return raw_text

def extract_questions_from_any_structure(parsed_data):
    """The Ultimate Crawler: Digs through nested lists/dicts to find the actual questions."""
    extracted = []
    if isinstance(parsed_data, dict):
        if "questions" in parsed_data and isinstance(parsed_data["questions"], list):
            extracted.extend(parsed_data["questions"])
        elif "question" in parsed_data:
            extracted.append(parsed_data)
    elif isinstance(parsed_data, list):
        for item in parsed_data:
            if isinstance(item, dict):
                if "questions" in item and isinstance(item["questions"], list):
                    extracted.extend(item["questions"])
                elif "question" in item:
                    extracted.append(item)
    return extracted

def parse_and_clean_assessment(result_text, questions_config, strategy):
    """The Bulletproof Janitor: Parses, validates, and forcefully fixes LLM data."""
    
    raw_questions_data = []
    
    # 1. 🛡️ NEW MULTI-BLOCK EXTRACTOR: Find ALL json blocks!
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    matches = re.findall(code_block_pattern, result_text, re.IGNORECASE)
    
    json_strings_to_try = []
    if matches:
        json_strings_to_try.extend(matches)
    else:
        json_strings_to_try.append(result_text)

    # 2. Parse every block we found
    for raw_text in json_strings_to_try:
        # Clean boundaries and trailing commas
        start_idx = -1
        for i, char in enumerate(raw_text):
            if char in ['{', '[']:
                start_idx = i
                break
        end_idx = -1
        for i in range(len(raw_text) - 1, -1, -1):
            if raw_text[i] in ['}', ']']:
                end_idx = i
                break
        
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            cleaned_text = raw_text[start_idx:end_idx+1]
            # Trailing comma fix
            cleaned_text = re.sub(r',\s*([\]}])', r'\1', cleaned_text) 
            
            try:
                parsed = json.loads(cleaned_text)
                extracted = extract_questions_from_any_structure(parsed)
                raw_questions_data.extend(extracted)
            except json.JSONDecodeError as e:
                print(f"❌ JSON Decode Error in block: {str(e)}")
                continue

    # 3. Validation & The "Bulletproof Janitor" Loop
    final_questions = []
    
    for i, config in enumerate(questions_config):
        q_data = {}
        
        # Merge AI data if it exists
        if i < len(raw_questions_data):
            q_data = raw_questions_data[i]
            
        expected_type = config.question_type or strategy.get("structure", "Standard")
        
        # --- BULLETPROOF MISSING FIELD REBUILDER ---
        if "answer" not in q_data or not q_data["answer"]:
            if expected_type in ["Multiple Choice", "MCQ"]:
                q_data["answer"] = "Option A" 
            else:
                q_data["answer"] = "Detailed model solution expected."

        if "rubric" not in q_data or not isinstance(q_data["rubric"], dict):
            q_data["rubric"] = {
                "Full_Marks": "100% correct.",
                "Partial_Marks": "Partially correct.",
                "Zero_Marks": "0% correct."
            }

        # 🧹 JANITOR TASK 1: Force perfect Options formatting
        if expected_type in ["Multiple Choice", "MCQ"]:
            raw_options = q_data.get("options", [])
            
            if isinstance(raw_options, str):
                raw_options = [opt.strip() for opt in raw_options.split(",")]
            elif isinstance(raw_options, list) and len(raw_options) == 1 and "," in str(raw_options[0]):
                raw_options = [opt.strip() for opt in str(raw_options[0]).split(",")]
                
            if not isinstance(raw_options, list):
                raw_options = []

            while len(raw_options) < 4:
                raw_options.append("Option not generated")
            raw_options = raw_options[:4]

            prefixes = ["A) ", "B) ", "C) ", "D) "]
            clean_options = []
            for j in range(4):
                opt = raw_options[j]
                opt = re.sub(r'^[A-D][\.\)]\s*', '', str(opt))
                clean_options.append(f"{prefixes[j]}{opt}")
                
            q_data["options"] = clean_options
        else:
            q_data["options"] = None

        # 🧹 JANITOR TASK 2: Clean Rubric Hallucinations
        for level in ["Full_Marks", "Partial_Marks", "Zero_Marks"]:
            rubric_text = q_data["rubric"].get(level, "N/A")
            clean_rubric = re.sub(r'^\d+/\d+\s*[-:]\s*', '', str(rubric_text))
            q_data["rubric"][level] = clean_rubric

        # Force metadata correctness
        q_data["id"] = config.id
        q_data["marks"] = config.weightage
        q_data["meta"] = {
            "clo": config.clo,
            "bloom": config.bloom_level,
            "difficulty": config.difficulty,
            "type": expected_type
        }

        # Safe fallback for total failures
        if "question" not in q_data or not q_data["question"]:
            q_data["question"] = f"Error: The AI model failed to generate Item {config.id} correctly."
            q_data["answer"] = "N/A"
            q_data["options"] = None
            q_data["rubric"] = {"Full_Marks": "N/A", "Partial_Marks": "N/A", "Zero_Marks": "N/A"}

        final_questions.append(q_data)

    return final_questions
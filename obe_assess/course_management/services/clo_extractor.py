import json
import requests
import re
from course_management.utils import extract_text_from_file

class OBECourseExtractor:
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.filename = file_obj.name

    def clean_and_extract_json(self, raw_text):
        """Safely extracts JSON list from LLM output, preventing crashes."""
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text, re.IGNORECASE)
        if match:
            raw_text = match.group(1)
        
        start = raw_text.find('[')
        end = raw_text.rfind(']')
        if start != -1 and end != -1:
            raw_text = raw_text[start:end+1]
            
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            print("Failed to decode LLM JSON:", raw_text)
            return []

    def extract(self):
        # 1. Get structured text (with tables)
        text_content = extract_text_from_file(self.file_obj, self.filename)
        
        if not text_content:
            raise Exception("Could not read any text from the file.")

        # 2. Ultra-Strict Prompt with Anti-Loop and Anti-Duplication Rules
        prompt = f"""
        You are an expert academic data extractor. Your ONLY job is to extract the Course Learning Outcomes (CLOs) from the text.

        🛑 CRITICAL RULE: DO NOT GUESS SEQUENTIAL NUMBERS! 🛑
        Do NOT assume CLO-4 maps to PLO-4, or CLO-5 maps to PLO-5. You MUST read the actual table columns. The mapping is often randomized!

        ✅ GOOD EXAMPLE (Reading the actual text):
        Text: "CLO 5 | Collaboratively design the pipeline | PLO-9 | C-6 (Create)"
        Output:
        {{
            "code": "CLO-5",
            "text": "Collaboratively design the pipeline.",
            "bloom": "C-6",
            "mapped_plos": ["PLO-9"]
        }}

        ❌ BAD EXAMPLE (Guessing the next number):
        Output:
        {{
            "code": "CLO-5",
            "text": "Collaboratively design the pipeline.",
            "bloom": "C-5",
            "mapped_plos": ["PLO-5"] 
        }}

        CONTEXT MATERIAL (Syllabus Text):
        {text_content[:10000]}

        STRICT JSON OUTPUT SCHEMA:
        Return ONLY a JSON array. Extract EVERY CLO present in the text.
        [
            {{
                "code": "CLO-1",
                "text": "<Write the full CLO description here>",
                "bloom": "<Extract EXACT BT Level, e.g. C-2>",
                "mapped_plos": ["<Extract EXACTLY ONE PLO. DO NOT add more than one>"]
            }}
        ]
        """
        print("--- PDF EXTRACTED TEXT ---")
        print(text_content[:10000]) 
        print("--------------------------")
        # 3. Call your lightweight local model with Anti-Repetition logic
        try:
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:1b", 
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "top_k": 10,
                        "num_predict": 1500,
                        "repeat_penalty": 1.2  # 🛑 THIS PREVENTS THE AI FROM LOOPING REPEATED TEXT!
                    } 
                },
                timeout=300
            )
            resp.raise_for_status()
            llm_response = resp.json().get("response", "")
            
        except Exception as e:
            raise Exception(f"LLM Connection Error: {str(e)}")

        # 4. Parse JSON
        clos_data = self.clean_and_extract_json(llm_response)

        # 5. 🛡️ PYTHON DEDUPLICATION & ARRAY SLICING (The Ironclad Fallback) 🛡️
        unique_clos = []
        seen_texts = set()
        
        for clo in clos_data:
            text = clo.get("text", "").strip().lower()
            
            # Clean up the PLO array
            plos = clo.get("mapped_plos", [])
            if isinstance(plos, str):
                plos = [plos] # Catch if the model forgot the array brackets
                
            clean_plos = [p for p in plos if "CLO" not in str(p).upper() and "PLO" in str(p).upper()]
            
            # 🛑 THE ARRAY HALLUCINATION FIX 🛑
            # Gemma 1B puts the correct PLO first, then starts hallucinating numbers.
            # We strictly slice the array to keep ONLY the very first PLO it found!
            if clean_plos:
                clo["mapped_plos"] = [clean_plos[0]] 
            else:
                clo["mapped_plos"] = []
            
            # Remove any weird numbering the AI added to the start of the text
            clean_desc = re.sub(r'^(CLO[- ]?\d+[:\.\-]?\s*)+', '', clo.get("text", ""), flags=re.IGNORECASE).strip()
            clo["text"] = clean_desc

            # Keep only unique CLOs
            if text and text not in seen_texts:
                seen_texts.add(text)
                unique_clos.append(clo)
                
        return unique_clos[:6]
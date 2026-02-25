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
        match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_text)
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

        # 2. Optimized Prompt for Zero-Shot Extraction
        # We use placeholders so the LLM cannot copy the prompt example.
        # 2. Universal Prompt for Any Course Outline
        prompt = f"""
        You are an expert academic data extraction AI.
        Your sole task is to find and extract the "Course Learning Outcomes" (CLOs) from the provided university syllabus.

        WHAT TO LOOK FOR (THE TARGET):
        1. CLOs are typically a short list (usually 4 to 8 items) stating what a student will achieve by the end of the course.
        2. Look for explicit labels like "Course Learning Outcomes", "CLOs", "COs", or "Course Objectives".
        3. CLOs always start with an action verb (e.g., Describe, Analyze, Design, Implement, Evaluate).
        4. Extract their mapped Program Learning Outcomes (often labeled PLO, PO, or WA) and Bloom's Taxonomy levels (often labeled BT, Cognitive Level, C1, C2, C3, P1, P2, etc.).

        WHAT TO IGNORE (STRICT NEGATIVE RULES):
        - IGNORE Instructor details, office hours, and contact information.
        - IGNORE Weekly Schedules, Lecture Topics, and Lab Experiments (e.g., if it says "Week 1" or "Lab 2", skip it).
        - IGNORE Assessment Methods, Grading Policies, Quizzes, and Rubrics.
        - IGNORE Course Synopsis or general descriptions.
        
        COURSE OUTLINE TEXT:
        {text_content[:10000]}

        STRICT JSON OUTPUT FORMAT:
        Extract the data into this exact JSON array format. If a PLO or Bloom level is missing for a CLO, output an empty array [] or null. Replace the placeholder values with actual extracted data.
        [
            {{
                "code": "CLO-1",
                "text": "Extract the full text of the learning outcome here.",
                "mapped_plos": ["PLO-1", "PLO-2"],
                "bloom": "C2"
            }}
        ]

        Return ONLY the valid JSON array. Do not output any conversational text, markdown formatting, or explanations.
        """

        # 3. Call your lightweight local model
        try:
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:1b", # Change if using a different model like phi3 or llama3
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0, # Set to exactly 0 to force strict extraction and stop creativity
                        "top_k": 10
                    } 
                },
                timeout=300
            )
            resp.raise_for_status()
            llm_response = resp.json().get("response", "")
        except Exception as e:
            raise Exception(f"LLM Connection Error: {str(e)}")

        # 4. Parse and return crash-proof JSON
        clos_data = self.clean_and_extract_json(llm_response)
        return clos_data
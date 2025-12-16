# llm_service/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import requests
import json
import random
import re
from fastapi.responses import JSONResponse

app = FastAPI(title="LLM Service with Gemma 3 (Ollama)")

# -------------------------
# 1. Input Models
# -------------------------

class QuestionConfig(BaseModel):
    id: int
    clo: str
    bloom_level: str
    difficulty: str
    weightage: str

class LLMRequest(BaseModel):
    text: str
    assessment_type: str
    questions_config: List[QuestionConfig]

# -------------------------
# 2. Helper: Robust JSON Extractor
# -------------------------
def clean_and_extract_json(raw_text):
    """
    Attempts to extract valid JSON from the LLM's raw output.
    Handles markdown code blocks and conversational filler.
    """
    # 1. Try to find content inside ```json ... ``` blocks
    code_block_pattern = r"```json\s*([\s\S]*?)\s*```"
    match = re.search(code_block_pattern, raw_text)
    if match:
        return match.group(1)
    
    # 2. Fallback: finding the first '{' and last '}'
    start = raw_text.find('{')
    end = raw_text.rfind('}')
    if start != -1 and end != -1:
        return raw_text[start:end+1]
    
    # 3. If no markers found, return raw text and hope it's clean
    return raw_text

# -------------------------
# 3. Generate Assessment Route
# -------------------------
@app.post("/generate")
def generate_assessment(req: LLMRequest):
    """
    Generates assessment questions where each question follows 
    specific CLO, Bloom, and Difficulty requirements.
    """

    # 1️⃣ Build requirements string
    requirements_list = ""
    for q in req.questions_config:
        requirements_list += (
            f"- Question {q.id}: {q.weightage} Marks, "
            f"CLO: {q.clo}, "
            f"Bloom Level: {q.bloom_level}, "
            f"Difficulty: {q.difficulty}\n"
        )

    num_questions = len(req.questions_config)

    # 2️⃣ Prepare the Prompt (Stricter JSON enforcement)
    prompt = f"""
    You are an expert academic AI. Generate an assessment based on the provided text.
    
    CONTEXT MATERIAL:
    {req.text[:30000]}... (truncated)

    TASK:
    Generate exactly {num_questions} questions for a {req.assessment_type}.
    
    CONSTRAINTS:
    {requirements_list}

    OUTPUT FORMAT:
    Return ONLY valid JSON. Do not include markdown formatting, preambles, or explanations.
    The output must match this schema exactly:
    {{
        "questions": [
            {{
                "id": 1,
                "question": "The question text...",
                "answer": "The model answer...",
                "marks": "5",
                "rubric": {{
                    "Excellent": "Criteria for full marks...",
                    "Average": "Criteria for partial marks...",
                    "Poor": "Criteria for low marks..."
                }}
            }}
        ]
    }}
    """

    # 3️⃣ Call local Ollama
    print(f"--> Sending request to Ollama for {num_questions} questions...")
    
    try:
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma3:1b",  # Make sure this matches your installed model (e.g., gemma2:2b)
                "prompt": prompt, 
                "stream": False,
                "options": {
                    "temperature": 0.2, # Lower temperature for more structured output
                    "num_ctx": 8192 ,
                    "num_predict": 3000,   # NEW: Forces longer output (prevents stopping at Q1)
                    "top_k": 40,
                    "top_p": 0.9
                }
            },
            timeout=5000
        )
        ollama_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama Connection Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to reach Ollama: {str(e)}"}
        )

    result_text = ollama_response.json().get("response", "").strip()
    
    # Debug: Print raw output to console (helps with troubleshooting)
    # print(f"DEBUG RAW LLM OUTPUT:\n{result_text[:200]}...") 

    # 4️⃣ Clean and Extract JSON
    clean_json_str = clean_and_extract_json(result_text)
    
    questions_data = []
    try:
        parsed = json.loads(clean_json_str)
        questions_data = parsed.get("questions", [])
    except json.JSONDecodeError:
        print("❌ JSON Decode Error. The LLM output was not valid JSON.")
        questions_data = []

    # 5️⃣ Validation & Fallback (Merge with Config)
    final_questions = []
    
    for i, config in enumerate(req.questions_config):
        q_data = {}
        
        # Try to use LLM data if available for this index
        if i < len(questions_data):
            q_data = questions_data[i]
        
        # Force metadata correctness from config
        q_data["id"] = config.id
        q_data["marks"] = config.weightage
        q_data["meta"] = {
            "clo": config.clo,
            "bloom": config.bloom_level,
            "difficulty": config.difficulty
        }

        # Fallback if specific fields are missing in LLM output
        if "question" not in q_data:
            q_data["question"] = f"Error: Could not generate question {config.id}."
            q_data["answer"] = "N/A"
            q_data["rubric"] = {}

        final_questions.append(q_data)

    # 6️⃣ Return Structured Response
    return JSONResponse(
        content={
            "job_id": f"job_{random.randint(1000,9999)}",
            "metadata": {
                "assessment_type": req.assessment_type,
                "total_questions": num_questions,
                "model": "gemma (local)"
            },
            "questions": final_questions
        },
        status_code=200
    )
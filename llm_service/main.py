from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import json
import random
import re
from fastapi.responses import JSONResponse

app = FastAPI(title="LLM Service with Gemma 3 (Ollama)")

# ==========================================
# 1. SHARED HELPERS
# ==========================================

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

def call_ollama(prompt, model="gemma3:1b", options=None):
    """
    Centralized function to call the local Ollama instance.
    """
    if options is None:
        options = {
            "temperature": 0.2,
            "num_ctx": 8192,
            "num_predict": 3000,
            "top_k": 40,
            "top_p": 0.9
        }

    print(f"--> Sending request to Ollama ({model})...")
    
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model, 
                "prompt": prompt, 
                "stream": False,
                "options": options
            },
            timeout=180 # Extended timeout for long generations
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama Connection Error: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama Error: {str(e)}")

# ==========================================
# 2. FEATURE: ASSESSMENT GENERATION
# ==========================================

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

@app.post("/generate")
def generate_assessment(req: LLMRequest):
    """
    Generates assessment questions based on text context and configuration.
    """
    
    # 1. Build requirements string
    requirements_list = ""
    for q in req.questions_config:
        requirements_list += (
            f"- Question {q.id}: {q.weightage} Marks, "
            f"CLO: {q.clo}, "
            f"Bloom Level: {q.bloom_level}, "
            f"Difficulty: {q.difficulty}\n"
        )

    num_questions = len(req.questions_config)

    # 2. Prepare the Prompt
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

    # 3. Call Ollama
    result_text = call_ollama(prompt)

    # 4. Clean and Extract JSON
    clean_json_str = clean_and_extract_json(result_text)
    
    questions_data = []
    try:
        parsed = json.loads(clean_json_str)
        questions_data = parsed.get("questions", [])
    except json.JSONDecodeError:
        print("❌ JSON Decode Error. The LLM output was not valid JSON.")
        # We return empty list here, fallback logic below handles it
        questions_data = []

    # 5. Validation & Fallback (Merge with Config)
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

        # Fallback if specific fields are missing
        if "question" not in q_data:
            q_data["question"] = f"Error: Could not generate question {config.id}."
            q_data["answer"] = "N/A"
            q_data["rubric"] = {}

        final_questions.append(q_data)

    # 6. Return Structured Response
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


# ==========================================
# 3. FEATURE: ASSESSMENT MARKING (NEW)
# ==========================================

class GradingCriterion(BaseModel):
    criterion: str
    marks: int

class MarkingRequest(BaseModel):
    question_text: str
    student_answer: str
    max_marks: int
    criteria: List[GradingCriterion] = []

@app.post("/mark")
def mark_question(req: MarkingRequest):
    """
    Marks a single question based on criteria and student answer.
    """
    
    # 1. Build Criteria Text
    criteria_text = "\n".join([f"- {c.criterion} ({c.marks} marks)" for c in req.criteria]) \
        if req.criteria else "NO SPECIFIC CRITERIA. Use general academic judgement based on the question."

    # 2. Build Prompt
    prompt = f"""
You are a fair and objective academic assessor. Your task is to accurately mark the student's submission against the provided criteria.

**STRICT RULE:** Respond with a single, complete JSON object. DO NOT include any conversational text or markdown outside the JSON.

---
### ASSESSMENT DETAILS
**Question:** {req.question_text}
**Student Answer:** {req.student_answer}

**Marking Criteria (Total: {req.max_marks} Marks):**
{criteria_text}
---

Calculate the 'marks_awarded' out of 'max_marks'. Provide specific, actionable 'feedback' justifying the mark.

**REQUIRED JSON OUTPUT FORMAT:**
{{
    "marks_awarded": 0,
    "max_marks": {req.max_marks},
    "feedback": "Detailed justification..."
}}
"""

    # 3. Call Ollama
    raw_response = call_ollama(prompt)

    # 4. Parse JSON
    cleaned_json = clean_and_extract_json(raw_response)
    
    try:
        result_data = json.loads(cleaned_json)
        
        # Validate and return
        return {
            "marks_awarded": int(result_data.get("marks_awarded", 0)),
            "max_marks": int(result_data.get("max_marks", req.max_marks)),
            "feedback": str(result_data.get("feedback", "No feedback provided."))
        }
    except (json.JSONDecodeError, ValueError):
        # Fallback if AI fails to give valid JSON
        print(f"❌ JSON Error in Marking. Raw output: {raw_response[:100]}...")
        return {
            "marks_awarded": 0,
            "max_marks": req.max_marks,
            "feedback": "Error: AI response was not valid JSON. Manual review recommended."
        }
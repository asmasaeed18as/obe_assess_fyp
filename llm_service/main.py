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

# Defines the settings for a single question
class QuestionConfig(BaseModel):
    id: int
    clo: str
    bloom_level: str
    difficulty: str
    weightage: str  # e.g. "5", "10"

# Defines the overall payload coming from the Backend
class LLMRequest(BaseModel):
    text: str # The course outline/material content
    assessment_type: str
    questions_config: List[QuestionConfig] # List of specific configurations

# -------------------------
# 2. Generate Assessment Route
# -------------------------
@app.post("/generate")
def generate_assessment(req: LLMRequest):
    """
    Generates assessment questions where each question follows 
    specific CLO, Bloom, and Difficulty requirements.
    """

    # 1️⃣ Build a specific requirement string for the prompt
    # This tells the LLM: "Q1 needs to be Easy, Q2 needs to be Hard", etc.
    requirements_list = ""
    for q in req.questions_config:
        requirements_list += (
            f"- Question {q.id}: {q.weightage} Marks, "
            f"CLO: {q.clo}, "
            f"Bloom Level: {q.bloom_level}, "
            f"Difficulty: {q.difficulty}\n"
        )

    num_questions = len(req.questions_config)

    # 2️⃣ Prepare the Prompt
    prompt = f"""
    You are an expert academic AI. Generate an assessment based on the provided text.
    
    {req.text[:10000]}... (truncated for brevity)

    Type: {req.assessment_type}
    Total Questions: {num_questions}
    
    You must generate exactly {num_questions} questions. 
    Each question MUST strictly follow these specific constraints:
    
    {requirements_list}

    Return ONLY valid JSON. No markdown, no conversational text.
    Structure:
    {{
        "questions": [
            {{
                "id": 1,
                "question": "The question text...",
                "answer": "The model answer...",
                "marks": "5",
                "meta": {{ "clo": "CLO-1", "bloom": "C1", "difficulty": "easy" }},
                "rubric": {{
                    "Excellent": "...",
                    "Average": "...",
                    "Poor": "..."
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
                "model": "gemma3:1b",  # Adjusted to 2b or keep gemma3:1b depending on what you have installed
                "prompt": prompt, 
                "stream": False,
                "options": {
                    "temperature": 0.7, # Creative enough for questions
                    "num_ctx": 4096     # Ensure context window is large enough for material
                }
            },
            timeout=180
        )
        ollama_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama Connection Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to reach Ollama: {str(e)}"}
        )

    result_text = ollama_response.json().get("response", "").strip()
    
    # Debug print to see what LLM actually sent
    # print("=== Raw LLM Output ===")
    # print(result_text)
    # print("======================")

    # 4️⃣ Extract JSON safely
    # This regex looks for the first '{' and the last '}'
    json_str_match = re.search(r"\{[\s\S]*\}", result_text)
    
    questions_data = []
    
    if json_str_match:
        json_str = json_str_match.group(0)
        try:
            parsed = json.loads(json_str)
            questions_data = parsed.get("questions", [])
        except json.JSONDecodeError:
            print("❌ JSON Decode Error on LLM output")
            questions_data = []
    else:
        print("❌ No JSON found in LLM output")

    # 5️⃣ Validation & Fallback (Crucial for Arrays)
    # If LLM returns fewer questions than requested or fails completely, fill gaps.
    final_questions = []
    
    for i, config in enumerate(req.questions_config):
        # Try to find a question from LLM output that matches this ID or Index
        if i < len(questions_data):
            q_data = questions_data[i]
            # Enforce metadata correctness based on config, not just LLM output
            q_data["id"] = config.id
            q_data["meta"] = {
                "clo": config.clo,
                "bloom": config.bloom_level,
                "difficulty": config.difficulty
            }
            q_data["marks"] = config.weightage
            final_questions.append(q_data)
        else:
            # Fallback if LLM missed this question
            final_questions.append({
                "id": config.id,
                "question": f"Generated Placeholder: Discuss concepts related to {config.clo} ({config.bloom_level}).",
                "answer": "Model answer not generated due to processing limit.",
                "marks": config.weightage,
                "meta": {
                    "clo": config.clo,
                    "bloom": config.bloom_level,
                    "difficulty": config.difficulty
                },
                "rubric": {
                    "Excellent": "Full understanding shown.",
                    "Average": "Partial understanding.",
                    "Poor": "Little to no understanding."
                }
            })

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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import json
import random
from response_parser import parse_and_clean_assessment, clean_and_extract_json
import re
from fastapi.responses import JSONResponse

app = FastAPI(title="LLM Service with Gemma 3 (Ollama)")

# ==========================================
# 1. SHARED HELPERS
# ==========================================

import re

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
            timeout=500 # Extended timeout for long generations
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
    # ✅ NEW: Field to track if it's an MCQ, Short Question, or Standard
    question_type: Optional[str] = "Standard" 

class LLMRequest(BaseModel):
    text: str
    assessment_type: str
    questions_config: List[QuestionConfig]

@app.post("/generate")
def generate_assessment(req: LLMRequest):
    """
    Generates assessment questions TAILORED to specific types (Quiz/MCQs, Lab, Project)
    and enforces strict mathematical constraints to prevent LLM hallucination.
    """
    num_questions = len(req.questions_config)

    # 1. Build the dynamic Requirements List
    requirements_list = ""
    for q in req.questions_config:
        q_type = q.question_type or "Standard"
        
        # Add a specific nudge for the mixed MCQ/Short Question type
        if req.assessment_type == "Quiz/MCQs":
            if q_type in ["Multiple Choice", "MCQ"]:
                rule_nudge = "FORMAT: Multiple Choice. TOPIC: Extract a concept from the text."
            else:
                rule_nudge = "FORMAT: Detailed Essay/Short Answer. TOPIC: Extract a concept from the text."
        else:
            rule_nudge = ""
            
        requirements_list += f"- Item ID {q.id}: {rule_nudge} {q.weightage} Marks, CLO: {q.clo}, Bloom Level: {q.bloom_level}, Difficulty: {q.difficulty}\n"

    # 2. 🚦 THE 5-WAY PROMPT ROUTER 🚦
    
    if req.assessment_type == "Quiz/MCQs":
        prompt = f"""
You are an expert academic data extraction and content creation AI.
You are a precise university quiz master.
CONTEXT MATERIAL: {req.text[:20000]}

YOUR TASK: Generate Multiple Choice Questions (MCQs) and Short Questions strictly following the rules.
Generate exactly {num_questions} items.

REQUIREMENTS LIST:
{requirements_list}

STRICT JSON OUTPUT SCHEMA:
You MUST return a raw JSON array of exactly {num_questions} objects. DO NOT use markdown code blocks.
Even for short questions, you MUST keep the "options" array in the JSON to avoid breaking the format (just fill it with dummy text if it's a short question).

{{
    "questions": [
        {{
            "id": <Match ITEM ID exactly>,
            "question": "<Write the question text here>",
            "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
            "answer": "<Write the full correct answer or detailed explanation here>",
            "marks": "<Marks>",
            "rubric": {{
                "Excellent": "<Criteria for 90-100% marks>",
                "Average": "<Criteria for 30-50% marks>",
                "Poor": "<Criteria for 0% marks>"
            }}
        }}
    ]
}}
🛑 CRITICAL WARNING: YOU MUST GENERATE EXACTLY {num_questions} ITEMS.DO NOT LEAVE RUBRICS EMPTY. DO NOT STOP EARLY. YOUR LAST ITEM MUST HAVE "id": {num_questions}. 🛑
"""
    elif req.assessment_type == "Lab Manual":
        prompt = f"""
You are an expert academic data extraction and content creation AI.
You are a senior computer science lab instructor.
CONTEXT MATERIAL: {req.text[:20000]}

YOUR TASK: Generate hands-on, practical Lab Tasks. Students need to write code, run commands, or analyze output.
Generate exactly {num_questions} items.

REQUIREMENTS LIST:
{requirements_list}

STRICT JSON OUTPUT SCHEMA:
You MUST return a raw JSON array of exactly {num_questions} objects. DO NOT use markdown code blocks.
The 'question' field MUST contain the Lab Task Scenario. The 'answer' field MUST contain the expected output or code solution. 'options' MUST be exactly null.

{{
    "questions": [
        {{
            "id": <Match ITEM ID exactly>,
            "question": "<Write the Lab Task Scenario here>",
            "options": null,
            "answer": "<Write the expected output or code solution here>",
            "marks": "<Marks>",
            "rubric": {{
                "Excellent": "<Criteria for full marks>",
                "Average": "<Criteria for partial marks>",
                "Poor": "<Criteria for zero marks>"
            }}
        }}
    ]
}}
"""
    elif req.assessment_type == "Project Report":
        prompt = f"""
You are an expert academic data extraction and content creation AI.
You are a university project supervisor.
CONTEXT MATERIAL: {req.text[:20000]}

YOUR TASK: Generate comprehensive Project Proposals/Milestones based on the material.
Generate exactly {num_questions} items.

REQUIREMENTS LIST:
{requirements_list}

STRICT JSON OUTPUT SCHEMA:
You MUST return a raw JSON array of exactly {num_questions} objects. DO NOT use markdown code blocks.
The 'question' field MUST contain the Problem Statement. The 'answer' field MUST contain the Evaluation Methodology. 'options' MUST be exactly null.

{{
    "questions": [
        {{
            "id": <Match ITEM ID exactly>,
            "question": "<Write the Problem Statement here>",
            "options": null,
            "answer": "<Write the Evaluation Methodology here>",
            "marks": "<Marks>",
            "rubric": {{
                "Excellent": "<Criteria for full marks>",
                "Average": "<Criteria for partial marks>",
                "Poor": "<Criteria for zero marks>"
            }}
        }}
    ]
}}
"""
    elif req.assessment_type == "Assignment":
        prompt = f"""
You are an expert academic data extraction and content creation AI.
You are an academic professor.
CONTEXT MATERIAL: {req.text[:20000]}

YOUR TASK: Generate high-level analytical, mathematical, or theoretical assignment questions.
Generate exactly {num_questions} items.

REQUIREMENTS LIST:
{requirements_list}

STRICT JSON OUTPUT SCHEMA:
You MUST return a raw JSON array of exactly {num_questions} objects. DO NOT use markdown code blocks.
Questions must be open-ended requiring detailed work. The 'answer' should contain the model solution. 'options' MUST be exactly null.

{{
    "questions": [
        {{
            "id": <Match ITEM ID exactly>,
            "question": "<Write the open-ended analytical question here>",
            "options": null,
            "answer": "<Write the detailed model solution here>",
            "marks": "<Marks>",
            "rubric": {{
                "Excellent": "<Criteria for full marks>",
                "Average": "<Criteria for partial marks>",
                "Poor": "<Criteria for zero marks>"
            }}
        }}
    ]
}}
"""
    else:  # Exam
        prompt = f"""
You are an expert academic data extraction and content creation AI.
You are a strict academic examiner.
CONTEXT MATERIAL: {req.text[:20000]}

YOUR TASK: Generate standard academic exam questions.
Generate exactly {num_questions} items.

REQUIREMENTS LIST:
{requirements_list}

STRICT JSON OUTPUT SCHEMA:
You MUST return a raw JSON array of exactly {num_questions} objects. DO NOT use markdown code blocks.
Standard question and detailed model answer format. 'options' MUST be exactly null.

{{
    "questions": [
        {{
            "id": <Match ITEM ID exactly>,
            "question": "<Write the standard exam question here>",
            "options": null,
            "answer": "<Write the detailed model answer here>",
            "marks": "<Marks>",
            "rubric": {{
                "Excellent": "<Criteria for full marks>",
                "Average": "<Criteria for partial marks>",
                "Poor": "<Criteria for zero marks>"
            }}
        }}
    ]
}}
"""

    # 3. Call Ollama with strict hyperparameter tuning
    ollama_options = {
        "temperature": 0.1,   
        "top_k": 10,          
        "num_predict": 10000, 
        "num_ctx": 8192       
    }
    
    result_text = call_ollama(prompt, model="gemma3:1b", options=ollama_options)

    print("\n" + "="*50)
    print(f"🤖 RAW LLM OUTPUT ({req.assessment_type}):")
    print(result_text)
    print("="*50 + "\n")

    # 4. Delegate JSON parsing to the external janitor file
    # (Passing a generic strategy dict because the logic is already handled in the prompt)
    final_questions = parse_and_clean_assessment(result_text, req.questions_config, {"structure": "Standard"})

    # 5. Return Structured Response
    return JSONResponse(
        content={
            "metadata": {
                "assessment_type": req.assessment_type,
                "total_questions": num_questions
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

**REQUIRED JSON OUTPUT FORMAT:**
{{
    "marks_awarded": <REPLACE_WITH_CALCULATED_INTEGER>,
    "max_marks": {req.max_marks},
    "feedback": "Detailed justification based on criteria..."
}}

STRICT: Ensure 'marks_awarded' is an integer between 0 and {req.max_marks}.
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
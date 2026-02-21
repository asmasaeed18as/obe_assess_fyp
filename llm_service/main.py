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
    and supports sub-options (e.g., mixing MCQs and Short Questions).
    """
    
    # --- STRATEGY PATTERN FOR PROMPTS ---
    # This dictionary defines how the LLM should behave for each main assessment category
    strategies = {
        "Quiz/MCQs": {
            "role": "You are a quiz master.",
            "task": "Generate a mix of Multiple Choice Questions (MCQs) and Short Questions based on the requirements.",
            "format_instruction": "Check individual item types. For MCQs, provide 4 options. For Short Questions, options must be null.",
            "structure": "Mixed"
        },
        "Lab Manual": {
            "role": "You are a senior lab instructor.",
            "task": "Generate practical Lab Tasks. These should be hands-on activities.",
            "format_instruction": "Rename 'question' to 'Task Description'. Use 'answer' for the 'Procedure & Expected Output'. Options=null.",
            "structure": "Practical Task"
        },
        "Project Report": {
            "role": "You are a project supervisor.",
            "task": "Generate distinct Project Topics/Proposals based on the material.",
            "format_instruction": "Rename 'question' to 'Project Title & Problem Statement'. Use 'answer' for 'Implementation Steps & Methodology'. Options=null.",
            "structure": "Project Proposal"
        },
        "Assignment": {
            "role": "You are an academic professor.",
            "task": "Generate high-level analytical and theoretical questions.",
            "format_instruction": "Questions must be open-ended. 'answer' should contain a detailed model solution/key points. Options=null.",
            "structure": "Analytical Question"
        },
        "Exam": {
            "role": "You are an examiner.",
            "task": "Generate standard academic exam questions.",
            "format_instruction": "Standard question and detailed answer format.",
            "structure": "Exam Question"
        }
    }

    # Select strategy (Default to Exam if unknown)
    strategy = strategies.get(req.assessment_type, strategies["Exam"])

    # 1. Build requirements string with SPECIFIC TYPES
    requirements_list = ""
    for q in req.questions_config:
        # If frontend didn't send a specific type (e.g., for Assignment), fallback to strategy default
        q_type = q.question_type if q.question_type else strategy.get("structure", "Standard")
        
        requirements_list += (
            f"- Item {q.id}: Type={q_type}, {q.weightage} Marks, CLO: {q.clo}, Bloom: {q.bloom_level}, Difficulty: {q.difficulty}\n"
        )

    num_questions = len(req.questions_config)

    # 2. Prepare the Dynamic Prompt
    prompt = f"""
{strategy['role']}
CONTEXT MATERIAL:
{req.text[:40000]}... (truncated)

YOUR TASK:
{strategy['task']}
Generate exactly {num_questions} items based on the list below.

IMPORTANT - ITEM TYPES CONFIGURATION:
- If Type="MCQ": Provide a question and exactly 4 options ["A", "B", "C", "D"]. Answer must be the correct option text.
- If Type="Short Question" (or other): Provide question and model answer. Options must be null.

REQUIREMENTS LIST:
{requirements_list}

STRICT JSON OUTPUT FORMAT:
{strategy['format_instruction']}
Return ONLY valid JSON matching this schema exactly:
{{
    "questions": [
        {{
            "id": 1,
            "question": "Question text...",
            "options": ["Option A", "Option B", "Option C", "Option D"] OR null, 
            "answer": "Correct Answer",
            "marks": "5",
            "rubric": {{
                "Criteria 1": "Description..."
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
        
        # Force metadata correctness from config (overwrites LLM hallucinations)
        q_data["id"] = config.id
        q_data["marks"] = config.weightage
        q_data["meta"] = {
            "clo": config.clo,
            "bloom": config.bloom_level,
            "difficulty": config.difficulty,
            # Store the final type used so frontend knows how to display it
            "type": config.question_type or strategy["structure"]
        }

        # Fallback if specific fields are missing
        if "question" not in q_data:
            q_data["question"] = f"Error: Generation failed for Item {config.id}."
            q_data["answer"] = "N/A"
            q_data["rubric"] = {}

        final_questions.append(q_data)

    # 6. Return Structured Response
    return JSONResponse(
        content={
            "metadata": {
                "assessment_type": req.assessment_type,
                "strategy_used": strategy["task"],
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
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
            timeout=300 # Extended timeout for long generations
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
    
    # --- STRATEGY PATTERN FOR PROMPTS (OPTIMIZED) ---
    strategies = {
        "Quiz/MCQs": {
            "role": "You are a quiz master.",
            "task": "Generate a mix of Multiple Choice Questions (MCQs) and Short Questions.",
            "format_instruction": "For MCQs, 'options' MUST be a list of 4 choices [\"A\", \"B\", \"C\", \"D\"]. For Short Questions, 'options' MUST be null.",
            "structure": "Mixed"
        },
        "Lab Manual": {
            "role": "You are a senior computer science lab instructor.",
            "task": "Generate hands-on, practical Lab Tasks. Students need to write code, run commands, or analyze output.",
            "format_instruction": "The 'question' field MUST contain the Lab Task Scenario. The 'answer' field MUST contain the expected output or code solution. 'options' MUST be null.",
            "structure": "Practical Task"
        },
        "Project Report": {
            "role": "You are a university project supervisor.",
            "task": "Generate comprehensive Project Proposals/Milestones based on the material.",
            "format_instruction": "The 'question' field MUST contain the Problem Statement. The 'answer' field MUST contain the Evaluation Methodology. 'options' MUST be null.",
            "structure": "Project Proposal"
        },
        "Assignment": {
            "role": "You are an academic professor.",
            "task": "Generate high-level analytical, mathematical, or theoretical assignment questions.",
            "format_instruction": "Questions must be open-ended requiring detailed work. 'answer' should contain the model solution. 'options' MUST be null.",
            "structure": "Analytical Question"
        },
        "Exam": {
            "role": "You are a strict examiner.",
            "task": "Generate standard academic exam questions.",
            "format_instruction": "Standard question and detailed model answer format. 'options' MUST be null.",
            "structure": "Exam Question"
        }
    }

    # Select strategy (Default to Exam if unknown)
    strategy = strategies.get(req.assessment_type, strategies["Exam"])

    # 1. Build requirements string with SPECIFIC TYPES
    requirements_list = ""
    for q in req.questions_config:
        q_type = q.question_type if q.question_type else strategy.get("structure", "Standard")
        requirements_list += (
            f"- Item {q.id}: Type={q_type}, {q.weightage} Marks, CLO: {q.clo}, Bloom: {q.bloom_level}, Difficulty: {q.difficulty}\n"
        )

    num_questions = len(req.questions_config)

    # 2. Prepare the Highly Restrictive Dynamic Prompt
    prompt = f"""
    You are an expert academic content creator.
    {strategy['role']}

    CONTEXT MATERIAL:
    {req.text[:8000]}

    YOUR TASK:
    {strategy['task']}
    
    CRITICAL INSTRUCTION: You MUST generate EXACTLY {num_questions} items based on the Requirements List below. DO NOT STOP EARLY. If there are {num_questions} items required, your JSON array MUST contain exactly {num_questions} objects.

    REQUIREMENTS LIST:
    {requirements_list}

    STRICT JSON OUTPUT INSTRUCTIONS:
    {strategy['format_instruction']}
    - For the 'rubric', you MUST write a specific, context-aware 1-sentence grading criterion for "Excellent", "Average", and "Poor" tailored specifically to the generated question. Do not leave them blank.

    You MUST return ONLY valid JSON matching this schema exactly. DO NOT rename the JSON keys:
    {{
        "questions": [
            {{
                "id": 1,
                "question": "<Write the detailed task, scenario, or question here>",
                "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"] OR null, 
                "answer": "<Write the expected output, code, model solution, or correct option here>",
                "marks": "5",
                "rubric": {{
                    "Excellent": "<Write exactly what the student must include to get full marks>",
                    "Average": "<Write exactly what a partial or half-correct answer looks like>",
                    "Poor": "<Write exactly what a failing or incorrect answer looks like>"
                }}
            }}
        ]
    }}
    """

    # 3. Call Ollama with SPECIFIC hyperparameter options to prevent early cut-offs
    ollama_options = {
        "temperature": 0.3,   # Slight creativity for question generation
        "top_k": 40,
        "num_predict": 4000,  # CRITICAL: Forces Ollama to allow long outputs (fixes missing questions)
        "num_ctx": 8192       # CRITICAL: Gives it enough memory to read the document context
    }
    
    # ✅ USING GEMMA 3 (1B)
    result_text = call_ollama(prompt, model="gemma3:1b", options=ollama_options)

    # 4. Clean and Extract JSON
    clean_json_str = clean_and_extract_json(result_text)
    
    questions_data = []
    try:
        parsed = json.loads(clean_json_str)
        questions_data = parsed.get("questions", [])
    except json.JSONDecodeError:
        print("❌ JSON Decode Error. The LLM output was not valid JSON.")
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
            "type": config.question_type or strategy["structure"]
        }

        # Fallback if specific fields are missing or if generation stopped early
        if "question" not in q_data:
            q_data["question"] = f"Error: Generation failed for Item {config.id}. The AI model stopped early."
            q_data["answer"] = "N/A"
            q_data["options"] = None
            q_data["rubric"] = {
                "Excellent": "N/A",
                "Average": "N/A",
                "Poor": "N/A"
            }

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
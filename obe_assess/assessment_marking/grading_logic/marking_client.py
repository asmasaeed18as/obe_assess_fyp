import requests
from django.conf import settings
from .preprocesspipeline import preprocess, extract_total_marks

# LLM Service URL
LLM_URL = getattr(settings, "LLM_SERVICE_URL", "http://127.0.0.1:8001")

def call_mark_api(q_text, student_ans, criteria, max_marks):
    """Call the LLM Service /mark endpoint"""
    payload = {
        "question_text": q_text,
        "student_answer": student_ans,
        "max_marks": max_marks,
        "criteria": criteria
    }
    try:
        resp = requests.post(f"{LLM_URL}/mark", json=payload, timeout=40)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"LLM API Error: {e}")
        return {"marks_awarded": 0, "max_marks": max_marks, "feedback": f"AI Error: {str(e)}"}

def mark_assessment_logic(student_doc_path, rubric_doc_path):
    # 1. Preprocess
    student_data = preprocess(student_doc_path)
    rubric_data = preprocess(rubric_doc_path)

    questions = student_data.get("questions", {})
    criteria_map = rubric_data.get("criteria_map", {})
    total_marks = rubric_data.get("total_marks") or 10

    results = {}

    # 2. Mark Each Question
    for qid, qdata in questions.items():
        q_text = qdata.get("question", "")
        student_ans = qdata.get("answer", "")
        
        # Prepare criteria for this specific question
        q_criteria_raw = criteria_map.get(qid, [])
        api_criteria = [{"criterion": c["criterion"], "marks": c["marks"]} for c in q_criteria_raw]
        
        q_max = sum(c["marks"] for c in api_criteria)
        if q_max == 0: q_max = 5 # Default if no marks found

        # Call AI
        ai_res = call_mark_api(q_text, student_ans, api_criteria, q_max)

        results[qid] = {
            "question": q_text,
            "student_answer": student_ans,
            "marks_awarded": ai_res.get("marks_awarded", 0),
            "max_marks": ai_res.get("max_marks", q_max),
            "feedback": ai_res.get("feedback", "")
        }

    return {
        "total_marks": total_marks,
        "per_question": results
    }
import requests
from django.conf import settings
from .preprocesspipeline import preprocess
import os
import csv

def call_mark_api(q_text, student_ans, criteria, max_marks):
    """Call the LLM Service /mark endpoint"""
    llm_url = (getattr(settings, "LLM_SERVICE_URL", "") or "http://127.0.0.1:8001").rstrip('/')
    payload = {
        "question_text": q_text,
        "student_answer": student_ans,
        "max_marks": max_marks,
        "criteria": criteria
    }
    try:
        resp = requests.post(f"{llm_url}/mark", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # LOGIC FIX: Don't trust the AI to use the exact key "marks_awarded"
        # We check all common possibilities
        score = data.get("marks_awarded")
        if score is None:
            score = data.get("marks") or data.get("score") or 0

        # Ensure the score is an actual number (int or float)
        try:
            score = int(float(score))
        except (ValueError, TypeError):
            score = 0

        return {
            "marks_awarded": score,
            "max_marks": max_marks,
            "feedback": data.get("feedback", "")
        }
    except Exception as e:
        print(f"LLM API Error: {e}")
        return {"marks_awarded": 0, "max_marks": max_marks, "feedback": f"AI Error: {str(e)}"}

def mark_assessment_logic(student_doc_path, rubric_doc_path):
    # 1. Preprocess documents
    # student_data now contains 'student_info' (Name/CMS ID)
    student_data = preprocess(student_doc_path)
    rubric_data = preprocess(rubric_doc_path)

    questions = student_data.get("questions", {})
    criteria_map = rubric_data.get("criteria_map", {})
    total_rubric_marks = rubric_data.get("total_marks") or 0

    # Extract Metadata (Ajwa Sibtain / 411885)
    student_info = student_data.get("student_info", {"student_name": "Unknown", "cms_id": "Unknown"})

    results = {}
    clo_summary = {}
    obtained_total = 0
    computed_total_possible = 0

    # Detect "global" criteria mapping (same list for every question)
    global_map = False
    if criteria_map:
        values = list(criteria_map.values())
        if values:
            first_sig = [(c.get("criterion"), c.get("marks")) for c in values[0]]
            if all([(c.get("criterion"), c.get("marks")) for c in v] == first_sig for v in values[1:]):
                global_map = True

    # 2. Mark Each Question
    for qid, qdata in questions.items():
        if qid == "Q1":
            print("Q1 question:", qdata.get("question"))
            print("Q1 answer:", qdata.get("answer"))
            print("Q1 criteria:", criteria_map.get(qid, []))
        q_text = qdata.get("question", "")
        student_ans = qdata.get("answer", "")

        q_criteria_raw = criteria_map.get(qid, [])
        api_criteria = [{"criterion": c["criterion"], "marks": c["marks"]} for c in q_criteria_raw]

        # Calculate max marks for this specific question
        q_max = sum(c["marks"] for c in api_criteria)
        if q_max == 0:
            q_max = 10
        computed_total_possible += q_max

        # Call AI Grading Service
        ai_res = call_mark_api(q_text, student_ans, api_criteria, q_max)

        marks_awarded = ai_res.get("marks_awarded", 0)
        obtained_total += marks_awarded

        # Store result in dictionary for frontend display
        clo = qdata.get("clo")
        results[qid] = {
            "question": q_text,
            "student_answer": student_ans,
            "marks_awarded": marks_awarded,
            "max_marks": ai_res.get("max_marks", q_max),
            "feedback": ai_res.get("feedback", ""),
            "clo": clo
        }

        clo_key = clo or "UNMAPPED"
        agg = clo_summary.setdefault(clo_key, {"obtained": 0, "possible": 0})
        agg["obtained"] += marks_awarded
        agg["possible"] += q_max

    # --- NEW: GENERATE DOWNLOADABLE CSV ---

    # 1. Setup File Path
    # Ensure filename is unique using CMS ID
    cms_safe = str(student_info["cms_id"]).replace("/", "_")
    csv_filename = f"Grading_Report_{cms_safe}.csv"

    # Build directory path in MEDIA_ROOT
    report_dir = os.path.join(settings.MEDIA_ROOT, 'grading_reports')
    os.makedirs(report_dir, exist_ok=True)
    csv_path = os.path.join(report_dir, csv_filename)

    # 2. Write CSV Data
    # We explicitly include Name and ID in every row for data portability
    headers = ['Student Name', 'CMS ID', 'Question ID', 'Question', 'Marks Obtained', 'Max Marks', 'Feedback']

    with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        for qid, data in results.items():
            writer.writerow([
                student_info["student_name"],
                student_info["cms_id"],
                qid,
                data["question"],
                data["marks_awarded"],
                data["max_marks"],
                data["feedback"]
            ])

    # 3. Personalized Final Return
    # Added 'download_url' so the frontend can provide a download link
    # Prefer computed total; fall back to rubric if computed is unavailable.
    if computed_total_possible > 0:
        total_possible = computed_total_possible
    elif total_rubric_marks > 0:
        total_possible = total_rubric_marks
    elif global_map and criteria_map:
        total_possible = sum(c.get("marks", 0) for c in list(criteria_map.values())[0])
    else:
        total_possible = 0

    return {
        "student_name": student_info["student_name"],
        "cms_id": student_info["cms_id"],
        "download_url": f"{settings.MEDIA_URL}grading_reports/{csv_filename}",
        "summary": {
            "total_obtained": obtained_total,
            "total_possible": total_possible,
            "percentage": round((obtained_total / total_possible * 100), 2) if total_possible > 0 else 0
        },
        "clo_summary": clo_summary,
        "per_question": results
    }

from .extract_text import extract_text
from .clean_text import clean_raw_text
from .segment import segment_questions, segment_rubric
from .extract_entities import (
    extract_marks_from_rubric, 
    extract_total_marks, 
    map_criteria_to_questions,
    extract_student_info
)

def preprocess(path):
    raw_text = extract_text(path)
    cleaned = clean_raw_text(raw_text)

    # Extract student details
    student_meta = extract_student_info(cleaned)

    questions = segment_questions(cleaned)
    rubric_text = segment_rubric(cleaned)
    criteria = extract_marks_from_rubric(rubric_text)
    total_marks = extract_total_marks(criteria)
    criteria_map = map_criteria_to_questions(criteria, questions)

    return {
        "path": path,
        "student_info": student_meta,
        "questions": questions,
        "criteria": criteria,
        "criteria_map": criteria_map,
        "total_marks": total_marks
    }

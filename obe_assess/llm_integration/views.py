import os
import json
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from openai import OpenAI
from .serializers import GenerateAssessmentSerializer, MarkingRequestSerializer
from .utils import parse_and_clean_assessment, clean_and_extract_json


def _get_groq_client():
    """Initialize Groq client with API key and base URL"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables")
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def call_groq(prompt, model=None, options=None):
    """
    Call Groq API via OpenAI-compatible endpoint.
    """
    if options is None:
        options = {
            "temperature": 0.2,
            "top_p": 0.9
        }

    model = model or os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    print(f"--> Sending request to Groq ({model})...")
    try:
        client = _get_groq_client()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.get("temperature", 0.2),
            top_p=options.get("top_p", 0.9),
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: Groq API Error: {e}")
        raise


class GenerateAssessmentView(APIView):
    """
    POST /api/llm/generate/
    Generate assessment questions using Groq LLM.
    """

    def post(self, request):
        try:
            serializer = GenerateAssessmentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            num_questions = len(data["questions_config"])

            # 1. Build dynamic requirements list
            requirements_list = ""
            for q in data["questions_config"]:
                q_type = q.get("question_type", "Standard")

                if data["assessment_type"] == "Quiz/MCQs":
                    if q_type in ["Multiple Choice", "MCQ"]:
                        rule_nudge = "FORMAT: Multiple Choice. TOPIC: Extract a concept from the text."
                    else:
                        rule_nudge = "FORMAT: Detailed Essay/Short Answer. TOPIC: Extract a concept from the text."
                else:
                    rule_nudge = ""

                requirements_list += f"- Item ID {q['id']}: {rule_nudge} {q['weightage']} Marks, CLO: {q['clo']}, Bloom Level: {q['bloom_level']}, Difficulty: {q['difficulty']}\n"

            # 2. Router based on assessment type
            assessment_type = data["assessment_type"]

            if assessment_type == "Quiz/MCQs":
                prompt = f"""
You are an expert academic data extraction and content creation AI.
You are a precise university quiz master.
CONTEXT MATERIAL: {data['text'][:20000]}

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
CRITICAL WARNING: YOU MUST GENERATE EXACTLY {num_questions} ITEMS. DO NOT LEAVE RUBRICS EMPTY. DO NOT STOP EARLY. YOUR LAST ITEM MUST HAVE "id": {num_questions}.
"""
            elif assessment_type == "Lab Manual":
                prompt = f"""
You are an expert academic data extraction and content creation AI.
You are a senior computer science lab instructor.
CONTEXT MATERIAL: {data['text'][:20000]}

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
            elif assessment_type == "Project Report":
                prompt = f"""
You are an expert academic data extraction and content creation AI.
You are a university project supervisor.
CONTEXT MATERIAL: {data['text'][:20000]}

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
            elif assessment_type == "Assignment":
                prompt = f"""
You are an expert academic data extraction and content creation AI.
You are an academic professor.
CONTEXT MATERIAL: {data['text'][:20000]}

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
CONTEXT MATERIAL: {data['text'][:20000]}

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

            # 3. Call Groq with parameters
            groq_options = {
                "temperature": 0.1,
                "top_p": 0.9,
            }

            result_text = call_groq(prompt, model=os.getenv("GROQ_MODEL"), options=groq_options)

            print("\n" + "="*50)
            print(f"LLM OUTPUT ({assessment_type}):")
            print(result_text[:500])
            print("="*50 + "\n")

            # 4. Parse and clean assessment
            final_questions = parse_and_clean_assessment(result_text, data["questions_config"], {"structure": "Standard"})

            # 5. Return structured response
            return Response({
                "metadata": {
                    "assessment_type": assessment_type,
                    "total_questions": num_questions
                },
                "questions": final_questions
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in GenerateAssessmentView: {str(e)}")
            return Response(
                {"error": f"Failed to generate assessment: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MarkQuestionView(APIView):
    """
    POST /api/llm/mark/
    Mark a student's answer using Groq LLM.
    """

    def post(self, request):
        try:
            serializer = MarkingRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data

            # 1. Build criteria text
            criteria_list = data.get("criteria", [])
            criteria_text = "\n".join([f"- {c['criterion']} ({c['marks']} marks)" for c in criteria_list]) \
                if criteria_list else "NO SPECIFIC CRITERIA. Use general academic judgement based on the question."

            # 2. Build prompt
            prompt = f"""
You are a fair and objective academic assessor. Your task is to accurately mark the student's submission against the provided criteria.

STRICT RULE: Respond with a single, complete JSON object. DO NOT include any conversational text or markdown outside the JSON.

---
### ASSESSMENT DETAILS
**Question:** {data['question_text']}
**Student Answer:** {data['student_answer']}

**Marking Criteria (Total: {data['max_marks']} Marks):**
{criteria_text}
---

**REQUIRED JSON OUTPUT FORMAT:**
{{
    "marks_awarded": <REPLACE_WITH_CALCULATED_INTEGER>,
    "max_marks": {data['max_marks']},
    "feedback": "Detailed justification based on criteria..."
}}

STRICT: Ensure 'marks_awarded' is an integer between 0 and {data['max_marks']}.
"""

            # 3. Call Groq
            raw_response = call_groq(prompt)

            # 4. Parse JSON
            cleaned_json = clean_and_extract_json(raw_response)

            try:
                result_data = json.loads(cleaned_json)

                return Response({
                    "marks_awarded": int(result_data.get("marks_awarded", 0)),
                    "max_marks": int(result_data.get("max_marks", data['max_marks'])),
                    "feedback": str(result_data.get("feedback", "No feedback provided."))
                }, status=status.HTTP_200_OK)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON Error in Marking. Raw output: {raw_response[:100]}...")
                return Response({
                    "marks_awarded": 0,
                    "max_marks": data['max_marks'],
                    "feedback": "Error: AI response was not valid JSON. Manual review recommended."
                }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in MarkQuestionView: {str(e)}")
            return Response(
                {"error": f"Failed to mark question: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

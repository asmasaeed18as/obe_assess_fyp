# assessment_creation/views.py
import requests, json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import LectureMaterial, Assessment
from .serializers import LectureMaterialSerializer, AssessmentSerializer
from .utils import extract_text_from_pdf_filefield, render_assessment_pdf
from django.conf import settings

# Configure your LLM service URL (change if different)
LLM_SERVICE_URL = getattr(settings, "LLM_SERVICE_URL", "http://127.0.0.1:8001/generate")

class UploadMaterialAndGenerateAssessment(APIView):
    permission_classes = [permissions.IsAuthenticated]  # change as needed

    def post(self, request):
        """
        Accepts multipart/form-data with:
         - file (pdf)
         - clo
         - bloom_level
         - assessment_type (optional)
        This view:
         1) saves the uploaded PDF as LectureMaterial
         2) extracts text
         3) calls LLM service with text + clo + bloom
         4) saves Assessment (result_json) and generated PDF
         5) returns Assessment data
        """
        uploaded_file = request.FILES.get("file")
        clo = request.data.get("clo")
        bloom = request.data.get("bloom_level", "C3")
        assessment_type = request.data.get("assessment_type", "quiz")

        if not uploaded_file or not clo:
            return Response({"error": "file and clo are required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1) save lecture material
        lecture = LectureMaterial.objects.create(title=uploaded_file.name, file=uploaded_file)

        # 2) extract text
        try:
            text = extract_text_from_pdf_filefield(lecture.file)
            lecture.extracted_text = text[:100000]  # optional truncate for DB
            lecture.save()
        except Exception as e:
            return Response({"error": f"Failed to extract PDF text: {str(e)}"}, status=500)

        # 3) call LLM microservice
        payload = {
            "text": text[:30000],
            "clo": clo,
    "bloom_level": bloom,
    "assessment_type": assessment_type,
    "num_questions": int(request.data.get("num_questions", 3)),
    "difficulty": request.data.get("difficulty", "medium"),
}

        try:
            resp = requests.post(LLM_SERVICE_URL, json=payload, timeout=180)
            resp.raise_for_status()
            llm_result = resp.json()  # expected: {"job_id": "...", "questions": [{...}, ...]}
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Error connecting to LLM service: {str(e)}"}, status=500)
        except ValueError:
            return Response({"error": "LLM service returned non-JSON response."}, status=500)

        # Validate result
        questions = llm_result.get("questions")
        if not questions or not isinstance(questions, list):
            return Response({"error": "Invalid response from LLM service"}, status=500)

        # 4) Save Assessment object
        assessment = Assessment.objects.create(
            material=lecture,
            clo=clo,
            bloom_level=bloom,
            assessment_type=assessment_type,
            result_json=llm_result
        )

        # 5) Generate PDF and save to assessment.pdf
        try:
            pdf_content = render_assessment_pdf(f"Assessment - {lecture.title}", questions)
            filename = f"assessment_{assessment.id}.pdf"
            assessment.pdf.save(filename, pdf_content)
            assessment.save()
        except Exception as e:
            # If pdf generation fails, still return the JSON result
            return Response({
                "warning": f"Failed to generate PDF: {str(e)}",
                "result_json": llm_result
            }, status=200)

        serializer = AssessmentSerializer(assessment)
        return Response(serializer.data, status=201)

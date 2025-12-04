# assessment_creation/views.py
import requests, json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import LectureMaterial, Assessment
from .serializers import AssessmentSerializer
from .utils import extract_text_from_pdf_filefield, render_assessment_pdf
from django.conf import settings

# Configure your LLM service URL (change if different)
LLM_SERVICE_URL = getattr(settings, "LLM_SERVICE_URL", "http://127.0.0.1:8001/generate")

class UploadMaterialAndGenerateAssessment(APIView):
    permission_classes = [AllowAny]  # change as needed

    def post(self, request):
        """
        Accepts multipart/form-data with:
         - file (pdf)
         - outline (pdf, optional)
         - assessment_type (string)
         - questions_config (JSON stringified list of objects)
        
        This view:
         1) Saves the uploaded PDF as LectureMaterial
         2) Extracts text from material (and outline if provided)
         3) Calls LLM service with text + detailed question config
         4) Saves Assessment (result_json) and generated PDF
         5) Returns Assessment data
        """
        # 1. Extract Files and Data
        uploaded_file = request.FILES.get("file")
        outline_file = request.FILES.get("outline")  # Optional
        
        assessment_type = request.data.get("assessment_type", "Assignment")
        config_str = request.data.get("questions_config")

        # Basic Validation
        if not uploaded_file:
            return Response({"error": "Material file is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not config_str:
            return Response({"error": "Questions configuration is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Parse the JSON string from FormData
        try:
            questions_config = json.loads(config_str)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format for questions_config"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Save Lecture Material
        lecture = LectureMaterial.objects.create(title=uploaded_file.name, file=uploaded_file)

        # 3. Extract Text (Material + Optional Outline)
        try:
            text_content = extract_text_from_pdf_filefield(lecture.file)
            
            # If outline exists, append it to text context
            if outline_file:
                outline_text = extract_text_from_pdf_filefield(outline_file)
                # Combine texts: Outline gives context, Material gives specifics
                text_content = f"=== COURSE OUTLINE ===\n{outline_text}\n\n=== LECTURE MATERIAL ===\n{text_content}"
            
            lecture.extracted_text = text_content[:100000]  # Truncate for DB storage
            lecture.save()
        except Exception as e:
            return Response({"error": f"Failed to extract PDF text: {str(e)}"}, status=500)

        # 4. Call LLM Microservice
        # Payload matches the new structure expected by the modified LLM Service
        payload = {
            "text": text_content[:30000],  # Send a reasonable chunk to LLM
            "assessment_type": assessment_type,
            "questions_config": questions_config  # Sending the list of configs
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

        # 5. Save Assessment object
        # Generate a simple summary string for the legacy 'clo' field if needed
        # (e.g., "CLO-1, CLO-2")
        clo_summary = ", ".join(sorted(list(set([q.get('clo', '') for q in questions_config if q.get('clo')]))))
        
        assessment = Assessment.objects.create(
            material=lecture,
            assessment_type=assessment_type,
            questions_config=questions_config,  # Store the input settings
            clo=clo_summary,                    # Store summary
            result_json=llm_result
        )

        # 6. Generate PDF and save to assessment.pdf
        try:
            # Render PDF with the new question list
            pdf_content = render_assessment_pdf(f"{assessment_type} - {lecture.title}", questions)
            filename = f"assessment_{assessment.id}.pdf"
            assessment.pdf.save(filename, pdf_content)
            assessment.save()
        except Exception as e:
            # If PDF generation fails, still return the JSON result with a warning
            return Response({
                "warning": f"Assessment generated but PDF failed: {str(e)}",
                "assessment": AssessmentSerializer(assessment).data
            }, status=201)

        serializer = AssessmentSerializer(assessment)
        return Response(serializer.data, status=201)
# assessment_creation/views.py
import requests, json
import zipfile
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsInstructor  # ✅ Import your new custom permissio
from django.http import FileResponse, Http404
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from .models import LectureMaterial, Assessment
from course_management.models import Course, CourseSection  # ✅ Import Course to link assessment
from .serializers import AssessmentSerializer
from .utils import (
    extract_text_from_pdf_filefield, 
    generate_docx_assessment, 
    generate_pdf_assessment,
    generate_zip_bundle
)

# ✅ SMART URL CONFIGURATION
# 1. Grab the base URL (defaults to 127.0.0.1:8001) and strip any accidental trailing slashes
BASE_LLM_URL = getattr(settings, "LLM_SERVICE_URL", "http://127.0.0.1:8001").rstrip('/')
# 2. Append the specific endpoint for THIS app
LLM_GENERATE_URL = f"{BASE_LLM_URL}/generate"


class UploadMaterialAndGenerateAssessment(APIView):
    # DELETED comment out this line so Django uses your default JWT authentication
    # authentication_classes = [] 
    
    # APPLY the strict permissions
    permission_classes = [IsAuthenticated, IsInstructor]

    def post(self, request):
        # 1. Extract Files and Data
        uploaded_file = request.FILES.get("file")
        outline_file = request.FILES.get("outline")
        
        # Get Topic Input from frontend
        topic_input = request.data.get("topic_input", "").strip()
        
        assessment_type = request.data.get("assessment_type", "Assignment")
        config_str = request.data.get("questions_config")
        course_id = request.data.get("course_id") 

        # 2. Smart Validation: Require File OR Topic
        if not uploaded_file and not topic_input:
            return Response({"error": "Please upload a material file OR provide a topic description."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not config_str:
            return Response({"error": "Questions configuration is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate Course Linking
        course_obj = None
        if course_id:
            course_obj = get_object_or_404(Course, id=course_id)
        else:
            return Response({"error": "Course ID is required to link assessment"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            questions_config = json.loads(config_str)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format for questions_config"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Determine Context Content (Topic vs File)
        text_content = ""
        lecture = None

        if topic_input:
            # OPTION A: TOPIC MODE
            text_content = f"TOPIC/INSTRUCTIONS PROVIDED BY INSTRUCTOR:\n{topic_input}"
            # Create a placeholder lecture record to track this generation
            lecture = LectureMaterial.objects.create(
                title=f"Topic: {topic_input[:40]}...", 
                extracted_text=text_content
            )
        else:
            # OPTION B: FILE MODE
            lecture = LectureMaterial.objects.create(title=uploaded_file.name, file=uploaded_file)
            try:
                text_content = extract_text_from_pdf_filefield(lecture.file)
                lecture.extracted_text = text_content[:100000]
                lecture.save()
            except Exception as e:
                return Response({"error": f"Failed to extract PDF text: {str(e)}"}, status=500)

        # 4. Append Course Outline (Optional Context)
        if outline_file:
            try:
                outline_text = extract_text_from_pdf_filefield(outline_file)
                text_content = f"=== COURSE OUTLINE ===\n{outline_text}\n\n=== CONTENT ===\n{text_content}"
            except Exception:
                pass # Continue even if outline fails

        # 5. Call LLM Microservice
        payload = {
            "text": text_content[:40000], # Truncate to avoid token limits
            "assessment_type": assessment_type,
            "questions_config": questions_config
        }

        try:
            # ✅ Uses the correctly built LLM_GENERATE_URL 
            resp = requests.post(LLM_GENERATE_URL, json=payload, timeout=500)
            resp.raise_for_status()
            llm_result = resp.json()
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Error connecting to LLM service: {str(e)}"}, status=500)
        except ValueError:
            return Response({"error": "LLM service returned non-JSON response."}, status=500)

        questions = llm_result.get("questions")
        if not questions or not isinstance(questions, list):
            return Response({"error": "Invalid response from LLM service"}, status=500)

        # 6. Save Assessment object linked to the Course
        clo_summary = ", ".join(sorted(list(set([q.get('clo', '') for q in questions_config if q.get('clo')]))))
        
        assessment = Assessment.objects.create(
            course=course_obj,
            material=lecture,
            assessment_type=assessment_type,
            questions_config=questions_config,
            clo=clo_summary,
            result_json=llm_result
        )

        # 7. Generate and Save Default "Full" PDF to Database (Optional Backup)
        try:
            pdf_buffer = generate_pdf_assessment(questions, f"{assessment_type} - {lecture.title}", "full")
            filename = f"assessment_{assessment.id}.pdf"
            assessment.pdf.save(filename, ContentFile(pdf_buffer.read()))
            assessment.save()
        except Exception as e:
            pass

        serializer = AssessmentSerializer(assessment)
        return Response(serializer.data, status=201)

# ==========================================
# View for Downloading Single Format (Legacy)
# ==========================================
class DownloadSpecificAssessment(APIView):
    # now only instructor can download specific formats, students will use the ZIP bundle which has more options
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, assessment_id, content_type, file_format):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            raise Http404("Assessment not found")

        data = assessment.result_json
        questions = data.get('questions', []) if isinstance(data, dict) else []
        
        if not questions:
            return Response({"error": "No questions found"}, status=404)

        title = f"{assessment.assessment_type} - {assessment.material.title}"
        filename = f"Assessment_{assessment_id}_{content_type}.{file_format}"
        
        if file_format == 'docx':
            buffer = generate_docx_assessment(questions, title, content_type)
            content_type_header = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_format == 'pdf':
            buffer = generate_pdf_assessment(questions, title, content_type)
            content_type_header = 'application/pdf'
        else:
            return Response({"error": "Invalid file format"}, status=400)

        response = FileResponse(buffer, content_type=content_type_header)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ==========================================
# View for ZIP Bundle Download
# ==========================================
class DownloadAssessmentZip(APIView):
    # Only instructors can download the ZIP bundle, students can only access individual formats if we choose to allow that in the future. This keeps the bundle as a premium feature for instructors.
    permission_classes = [IsAuthenticated, IsInstructor]

    def get(self, request, assessment_id, file_format='docx'):
        try:
            assessment = Assessment.objects.get(id=assessment_id)
        except Assessment.DoesNotExist:
            raise Http404("Assessment not found")

        if not assessment.result_json or 'questions' not in assessment.result_json:
             return Response({"error": "Assessment data incomplete"}, status=404)

        try:
            # Generate the ZIP containing 3 separate files
            zip_buffer = generate_zip_bundle(assessment, file_format)
        except Exception as e:
            return Response({"error": f"Zip generation failed: {str(e)}"}, status=500)

        filename = f"Assessment_Bundle_{assessment_id}.zip"
        
        response = FileResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ==========================================
# View to List Assessments for a Course
# ==========================================
class CourseAssessmentListView(generics.ListAPIView):
    """
    Returns a list of assessments for a specific course_id.
    """
    serializer_class = AssessmentSerializer
    # Only authenticated instructors can view the list of assessments for a course. Students will not have access to this endpoint, as they should only interact with assessments through the course interface where we can control what they see.
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        # Return assessments for this course, newest first
        return Assessment.objects.filter(course_id=course_id).order_by('-created_at')

class SectionAssessmentListView(generics.ListAPIView):
    """
    Returns a list of assessments for a course using CourseSection UUID.
    """
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_queryset(self):
        section_id = self.kwargs['section_id']
        section = get_object_or_404(CourseSection, id=section_id)
        return Assessment.objects.filter(course=section.course).order_by('-created_at')

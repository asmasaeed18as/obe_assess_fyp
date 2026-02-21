import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import GradedSubmission
from .serializers import GradedSubmissionSerializer
from .grading_logic.marking_client import mark_assessment_logic # Import logic

class GradeAssessmentView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = GradedSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            # 1. Save Files
            submission = serializer.save()
            
            try:
                # 2. Get Absolute Paths
                s_path = os.path.join(settings.MEDIA_ROOT, str(submission.student_file))
                r_path = os.path.join(settings.MEDIA_ROOT, str(submission.rubric_file))

                # 3. Run Logic
                result = mark_assessment_logic(s_path, r_path)

                # 4. Save & Return
                submission.ai_result_json = result
                submission.save()
                
                return Response({"status": "success", "data": GradedSubmissionSerializer(submission).data})
            except Exception as e:
                print(f"Grading Error: {e}")
                return Response({"status": "error", "details": str(e)}, status=500)
        
        return Response(serializer.errors, status=400)


class GradedSubmissionDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, submission_id, *args, **kwargs):
        submission = get_object_or_404(GradedSubmission, id=submission_id)
        return Response(GradedSubmissionSerializer(submission).data)

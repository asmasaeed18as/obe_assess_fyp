from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GenerateAssessmentSerializer, MarkingRequestSerializer
from .utils import generate_questions_via_groq, mark_question_via_groq


class GenerateAssessmentView(APIView):
    """POST /api/llm/generate/ — Generate assessment questions using Groq."""

    def post(self, request):
        serializer = GenerateAssessmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = serializer.validated_data
            result = generate_questions_via_groq(
                data["text"], data["assessment_type"], data["questions_config"]
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to generate assessment: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MarkQuestionView(APIView):
    """POST /api/llm/mark/ — Mark a student answer using Groq."""

    def post(self, request):
        serializer = MarkingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = serializer.validated_data
            result = mark_question_via_groq(
                data["question_text"],
                data["student_answer"],
                data["max_marks"],
                data.get("criteria", []),
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to mark question: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

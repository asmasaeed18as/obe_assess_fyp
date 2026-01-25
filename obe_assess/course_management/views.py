from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Course, CourseEnrollment, CourseOutline, CLO
from .serializers import (
    CourseSerializer, 
    CourseEnrollmentSerializer, 
    CourseOutlineSerializer, 
    CLOSerializer
)
from .utils import extract_text_from_pdf_filefield, extract_text_from_docx_fileobj
# ✅ Import the real extractor service
from .services.clo_extractor import extract_clos_from_text

User = get_user_model()

# --- Helper to get Mock User if not logged in ---
def get_user_or_mock(request):
    if request.user.is_authenticated:
        return request.user
    return User.objects.first()

class CourseCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()

class CourseListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()

class CourseDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()

class EnrollSelfView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = get_user_or_mock(request)
        if not user: 
            return Response({"error": "No user found"}, status=400)

        role = request.data.get("role", "student")
        CourseEnrollment.objects.get_or_create(course=course, user=user, role=role)
        
        return Response({"message": f"Enrolled in {course.code}"}, status=200)

class UploadOutlineView(APIView):
    """
    Uploads outline, extracts text, and generates CLOs using REAL logic.
    """
    permission_classes = [AllowAny]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = get_user_or_mock(request)
        
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "File is required"}, status=400)

        # 1. Save Outline
        outline = CourseOutline.objects.create(course=course, file=file_obj, uploaded_by=user)

        # 2. Extract Text from PDF/Docx
        text = ""
        try:
            name = file_obj.name.lower()
            if name.endswith('.pdf'):
                text = extract_text_from_pdf_filefield(outline.file)
            elif name.endswith('.docx'):
                text = extract_text_from_docx_fileobj(outline.file)
            
            outline.extracted_text = text[:200000] 
            outline.save()
        except Exception as e:
            print(f"Extraction error: {e}")
            return Response({
                "message": "Outline uploaded but text extraction failed", 
                "error": str(e)
            }, status=200)

        # ✅ 3. Generate CLOs using REAL FUNCTION
        clos_data = extract_clos_from_text(text)

        # 4. Save CLOs to DB
        saved_clos = []
        
        # Optional: Uncomment if you want to clear old CLOs when uploading a new outline
        # CLO.objects.filter(course=course).delete()

        for item in clos_data:
            # Provide defaults/fallbacks
            code = item.get('code') or f"CLO-{len(saved_clos)+1}"
            bloom = item.get('bloom')
            
            clo, created = CLO.objects.get_or_create(
                course=course,
                code=code,
                defaults={
                    'text': item.get('text', ''), 
                    'bloom_level': bloom
                }
            )
            
            # If CLO existed but had no bloom level, update it
            if not created and bloom and not clo.bloom_level:
                clo.bloom_level = bloom
                clo.save()
                
            saved_clos.append(clo)

        return Response({
            "message": "Outline uploaded & CLOs extracted",
            "clos": CLOSerializer(saved_clos, many=True).data
        }, status=201)

class ListCourseCLOsView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    pagination_class = None  # ✅ FORCE DISABLE PAGINATION
    
    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        return CLO.objects.filter(course__id=course_id).order_by("code")

class CLOUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    queryset = CLO.objects.all()
    lookup_field = 'pk' # Expects UUID
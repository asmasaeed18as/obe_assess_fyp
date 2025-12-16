from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Course, CourseEnrollment, CourseOutline, CLO
from .serializers import CourseSerializer, CourseEnrollmentSerializer, CourseOutlineSerializer, CLOSerializer
from .utils import extract_text_from_pdf_filefield, extract_text_from_docx_fileobj
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model

User = get_user_model()

# --- Mock Service for Extraction (Replace with real AI call later) ---
def mock_extract_clos(text):
    """
    Simulates extracting CLOs from text. 
    """
    return [
        {"code": "CLO-1", "text": "Analyze complex engineering problems.", "bloom": "C4"},
        {"code": "CLO-2", "text": "Design solutions for specific requirements.", "bloom": "C6"},
        {"code": "CLO-3", "text": "Apply ethical principles in engineering practice.", "bloom": "A3"},
    ]

# --- Helper to get Mock User if not logged in ---
def get_user_or_mock(request):
    if request.user.is_authenticated:
        return request.user
    return User.objects.first()

class CourseCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny] # Changed for easier testing
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
        if not user: return Response({"error": "No user found"}, status=400)

        role = request.data.get("role", "student")
        CourseEnrollment.objects.get_or_create(course=course, user=user, role=role)
        
        return Response({"message": f"Enrolled in {course.code}"}, status=200)

class UploadOutlineView(APIView):
    """
    Uploads outline, extracts text, and generates CLOs.
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

        # 2. Extract Text
        text = ""
        try:
            name = file_obj.name.lower()
            if name.endswith('.pdf'):
                text = extract_text_from_pdf_filefield(outline.file)
            elif name.endswith('.docx'):
                text = extract_text_from_docx_fileobj(outline.file)
            
            outline.extracted_text = text[:100000] # Save first 100k chars
            outline.save()
        except Exception as e:
            print(f"Extraction error: {e}")

        # 3. Generate CLOs (Using Mock Service)
        # In the future, pass 'text' to your AI model here
        clos_data = mock_extract_clos(text)

        # 4. Save CLOs to DB
        saved_clos = []
        for item in clos_data:
            clo, _ = CLO.objects.get_or_create(
                course=course,
                code=item['code'],
                defaults={'text': item['text'], 'bloom_level': item['bloom']}
            )
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

# ✅ NEW VIEW: Edit/Delete CLOs
class CLOUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    queryset = CLO.objects.all()
    lookup_field = 'pk' # Expects UUID
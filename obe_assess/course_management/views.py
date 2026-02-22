from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny

# Import Models
from .models import (
    Department, Program, StudentBatch, Semester, 
    Course, CourseSection, CourseEnrollment, 
    CourseOutline, CLO
)

# Import Serializers
from .serializers import (
    DepartmentSerializer, ProgramSerializer, StudentBatchSerializer,
    CourseSectionSerializer, CourseSerializer, 
    CourseEnrollmentSerializer,  # ✅ FIXED NAME HERE
    CourseOutlineSerializer, CLOSerializer
)

# Import Service
from .services.clo_extractor import OBECourseExtractor 

User = get_user_model()

# --- Helper ---
def get_user_or_mock(request):
    if request.user.is_authenticated:
        return request.user
    return User.objects.first()

# ==========================================
# 1. ADMIN DASHBOARD APIs (Hierarchy & Sections)
# ==========================================

class LMSHierarchyView(APIView):
    """
    Returns the full tree: Dept -> Program -> Batch -> Semester -> Sections
    """
    permission_classes = [AllowAny] 

    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

class ResourceListView(APIView):
    """
    Returns Dropdown Data: Generic Courses and Instructors.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        courses = Course.objects.all().values('id', 'code', 'title')
        instructors = User.objects.filter(role='instructor').values('id', 'email', 'first_name', 'last_name')
        return Response({'courses': courses, 'instructors': instructors})

class SectionCreateView(generics.CreateAPIView):
    """
    Admin creates a specific Class (Section) in a Semester.
    """
    queryset = CourseSection.objects.all()
    serializer_class = CourseSectionSerializer
    permission_classes = [AllowAny] 

class CourseCreateView(APIView):
    """Allows Admin to create a new base Course in the catalog"""
    def post(self, request):
        try:
            course = Course.objects.create(
                code=request.data.get('code'),
                title=request.data.get('title'),
                # ❌ REMOVED the 'description' line that was crashing everything!
                
                # Note: If your model doesn't have 'credit_hours' either, 
                # you can delete the line below as well!
                credit_hours=request.data.get('credit_hours', 3) 
            )
            return Response(
                {"id": course.id, "code": course.code, "title": course.title}, 
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
# ==========================================
# 2. STUDENT APIs (Enrollment)
# ==========================================

class JoinSectionView(APIView):
    """
    Student enters 'Enrollment Code' to join a specific Class/Section.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("enrollment_code", "").strip()
        
        # 1. Validate Code
        section = get_object_or_404(CourseSection, enrollment_code=code)

        # 2. Check if already enrolled
        if CourseEnrollment.objects.filter(user=request.user, section=section).exists():
            return Response({"error": "You are already enrolled in this class."}, status=400)

        # 3. Create Enrollment
        CourseEnrollment.objects.create(user=request.user, section=section, role="student")
        
        return Response({
            "message": f"Successfully joined {section.course.code} ({section.section_name})",
            "section_id": section.id
        }, status=200)

class MyEnrollmentsView(generics.ListAPIView):
    """
    Returns list of active classes for the logged-in student/instructor.
    """
    serializer_class = CourseEnrollmentSerializer # ✅ FIXED USAGE HERE
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CourseEnrollment.objects.filter(user=self.request.user).order_by('-enrolled_at')

# ==========================================
# 3. COURSE CONTENT APIs (CLOs & Outlines)
# ==========================================

class CourseListView(generics.ListAPIView):
    """List all Generic Courses (Catalog)"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

# ✅ ADD THIS NEW VIEW
class CourseDetailView(generics.RetrieveAPIView):
    """Get details for a SINGLE course"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
class UploadOutlineView(APIView):
    """
    Uploads outline to a GENERIC COURSE, extracts CLOs, saves them.
    """
    permission_classes = [AllowAny]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = get_user_or_mock(request)
        
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "File is required"}, status=400)

        # 1. Save Outline Record
        outline = CourseOutline.objects.create(course=course, file=file_obj, uploaded_by=user)

        # 2. Reset file pointer for reading
        file_obj.seek(0)

        # 3. Run Intelligent Extraction
        try:
            extractor = OBECourseExtractor(file_obj)
            clos_data = extractor.extract()
            print(f"DEBUG: Extracted {len(clos_data)} CLOs")
        except Exception as e:
             return Response({"error": f"Extraction failed: {str(e)}"}, status=500)

        # 4. Save CLOs to DB
        saved_clos = []
        for item in clos_data:
            code = item.get('code') or f"CLO-{len(saved_clos)+1}"
            
            clo, created = CLO.objects.update_or_create(
                course=course,
                code=code,
                defaults={
                    'text': item.get('text', ''), 
                    'bloom_level': item.get('bloom'),
                    'mapped_plos': item.get('mapped_plos', [])
                }
            )
            saved_clos.append(clo)

        return Response({
            "message": f"Outline uploaded. {len(saved_clos)} CLOs extracted.",
            "clos": CLOSerializer(saved_clos, many=True).data
        }, status=201)

class ListCourseCLOsView(generics.ListAPIView):
    """Returns CLOs for a specific Generic Course"""
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    pagination_class = None 
    
    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        return CLO.objects.filter(course__id=course_id).order_by("code")

class CLOUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """Edit a single CLO"""
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    queryset = CLO.objects.all()
    lookup_field = 'pk'
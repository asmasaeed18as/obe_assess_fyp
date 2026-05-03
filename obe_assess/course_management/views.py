from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, AllowAny
import re

# Import Models
from .models import (
    Department, Program, StudentBatch, Semester, 
    Course, CourseSection, CourseEnrollment, 
    CourseOutline, CLO
)
from assessment_creation.models import Assessment
from assessment_marking.models import GradedSubmission
from assessment_marking.utils import remap_course_submissions

# Import Serializers
from .serializers import (
    DepartmentSerializer, ProgramSerializer, StudentBatchSerializer,
    CourseSectionSerializer, CourseSerializer, CourseSectionDetailSerializer,
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


def _normalize_clo_code(raw_code, fallback_index):
    value = " ".join(str(raw_code or "").split()).upper()
    if not value:
        return f"CLO-{fallback_index}"

    num_match = re.search(r"\bCLO\b\s*[-:]?\s*(\d+)", value, flags=re.IGNORECASE)
    if num_match:
        return f"CLO-{num_match.group(1)}"[:64]

    just_num = re.fullmatch(r"\d+", value)
    if just_num:
        return f"CLO-{just_num.group(0)}"[:64]

    return value[:64]


def _normalize_bloom_level(raw_bloom):
    value = " ".join(str(raw_bloom or "").split())
    if not value:
        return ""

    bt_match = re.search(r"\b([CPA])\s*-?\s*(\d+)\b", value, flags=re.IGNORECASE)
    if bt_match:
        return f"{bt_match.group(1).upper()}-{bt_match.group(2)}"

    return value[:20]


def _normalize_mapped_plos(raw_plos):
    if isinstance(raw_plos, str):
        candidates = [raw_plos]
    elif isinstance(raw_plos, list):
        candidates = raw_plos
    else:
        candidates = []

    clean = []
    seen = set()
    for candidate in candidates:
        text = str(candidate or "")
        se_matches = re.findall(r"\bPLO\s*\(\s*SE\s*\)\s*-?\s*(\d+)\b", text, flags=re.IGNORECASE)
        cs_matches = re.findall(
            r"\b(?:PLO\s*\(\s*CS\s*\)|SO\s*\(\s*PLO\s*\)\s*(?:\(\s*CS\s*\))?)\s*-?\s*(\d+)\b",
            text,
            flags=re.IGNORECASE,
        )
        generic_matches = re.findall(r"\bPLO\s*-?\s*(\d+)\b", text, flags=re.IGNORECASE)

        if se_matches or cs_matches or generic_matches:
            for m in se_matches:
                plo = f"PLO(SE)-{m}"
                if plo not in seen:
                    seen.add(plo)
                    clean.append(plo)
            for m in cs_matches:
                plo = f"PLO(CS)-{m}"
                if plo not in seen:
                    seen.add(plo)
                    clean.append(plo)
            for m in generic_matches:
                plo = f"PLO-{m}"
                if plo not in seen:
                    seen.add(plo)
                    clean.append(plo)
        else:
            compact = " ".join(text.split()).upper()
            if compact.startswith("PLO") and compact not in seen:
                seen.add(compact)
                clean.append(compact[:20])
            elif re.fullmatch(r"\d{1,2}", compact):
                plo = f"PLO-{compact}"
                if plo not in seen:
                    seen.add(plo)
                    clean.append(plo)

    return clean

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
    """
    List all Generic Courses.
    - If authenticated as instructor: returns only courses where instructor has active sections
    - If not authenticated: returns all courses
    """
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'instructor':
            # Get courses where this instructor has active course sections
            from django.db.models import Q
            return Course.objects.filter(
                sections__instructor=self.request.user
            ).distinct()
        # For non-instructors, return all courses
        return Course.objects.all()

# ✅ ADD THIS NEW VIEW
class CourseDetailView(generics.RetrieveAPIView):
    """Get details for a SINGLE course"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

class CourseDetailBySectionView(APIView):
    """Get course details using a CourseSection UUID."""
    permission_classes = [AllowAny]

    def get(self, request, section_id, *args, **kwargs):
        section = get_object_or_404(CourseSection, id=section_id)
        serializer = CourseSectionDetailSerializer(section)
        return Response(serializer.data)


class CourseCLOAnalyticsView(APIView):
    """Compute CLO attainment stats for a course based on graded submissions.

    Returns per-CLO: total students, average attainment, passed, failed, distribution.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk, *args, **kwargs):
        course = get_object_or_404(Course, pk=pk)
        # Ensure CLO mapping is up to date for this course before computing analytics
        remap_course_submissions(course)

        # Threshold (default 60%) - can be overridden by query param ?threshold=70
        try:
            threshold = float(request.query_params.get('threshold', 60))
        except Exception:
            threshold = 60.0

        # Build question -> CLO mapping from saved Assessments for this course
        question_map = []  # list of dicts: {'text':..., 'clo':..., 'possible': int}
        assessments = Assessment.objects.filter(course=course)
        latest_assessment = assessments.order_by('-created_at').first()
        clo_by_index = []
        for a in assessments:
            r = a.result_json or {}
            qs = r.get('questions', []) if isinstance(r, dict) else []
            for q in qs:
                qtext = (q.get('question') or '').strip()
                meta = q.get('meta', {}) if isinstance(q.get('meta', {}), dict) else {}
                clo = meta.get('clo') or q.get('clo') or 'UNMAPPED'
                try:
                    possible = int(q.get('marks') or 0)
                except Exception:
                    possible = 0
                question_map.append({'text': qtext, 'clo': clo, 'possible': possible})

        if latest_assessment:
            r = latest_assessment.result_json or {}
            qs = r.get('questions', []) if isinstance(r, dict) else []
            try:
                ordered = sorted(qs, key=lambda x: int(x.get('id')))
            except Exception:
                ordered = qs
            clo_by_index = [
                ((q.get('meta', {}) if isinstance(q.get('meta', {}), dict) else {}).get('clo') or q.get('clo') or 'UNMAPPED')
                for q in ordered
            ]

        # Gather graded submissions for this course
        submissions = GradedSubmission.objects.filter(course=course)

        # Accumulate per-CLO per-student percentages
        clo_students = {}  # clo -> list of {'cms_id':..., 'student_name':..., 'percent': float}

        for s in submissions:
            ai = s.ai_result_json or {}
            per_q = ai.get('per_question', {}) if isinstance(ai, dict) else {}

            # Per student totals per CLO
            student_totals = {}  # clo -> {'obtained': int, 'possible': int}

            for qid, qdata in per_q.items():
                qtext = (qdata.get('question') or '').strip()
                try:
                    obtained = int(qdata.get('marks_awarded', 0))
                except Exception:
                    try:
                        obtained = int(float(qdata.get('marks_awarded', 0)))
                    except Exception:
                        obtained = 0
                try:
                    possible = int(qdata.get('max_marks', 0))
                except Exception:
                    possible = 0

                # Prefer mapped_clo from grading; fallback to question text matching
                mapped_clo = qdata.get('mapped_clo') or qdata.get('clo')
                norm_qtext = qtext.lower()
                if not mapped_clo:
                    for m in question_map:
                        mq = (m['text'] or '').lower()
                        if not mq:
                            continue
                        if norm_qtext == mq or norm_qtext in mq or mq in norm_qtext:
                            mapped_clo = m['clo']
                            # prefer mapping's possible if available
                            if m.get('possible'):
                                possible = m.get('possible')
                            break

                # Final fallback: map by question order (Q1 -> first CLO)
                if not mapped_clo and clo_by_index:
                    try:
                        qnum = int(''.join([c for c in str(qid) if c.isdigit()])) - 1
                    except Exception:
                        qnum = None
                    if qnum is not None and 0 <= qnum < len(clo_by_index):
                        mapped_clo = clo_by_index[qnum]

                if not mapped_clo:
                    mapped_clo = 'UNMAPPED'

                agg = student_totals.setdefault(mapped_clo, {'obtained': 0, 'possible': 0})
                agg['obtained'] += obtained
                agg['possible'] += possible

            # finalize per-clo percentages for this student
            student_name = ai.get('student_name') or ai.get('student', {}).get('name') if isinstance(ai, dict) else None
            cms_id = ai.get('cms_id') or ai.get('student', {}).get('cms_id') if isinstance(ai, dict) else None

            for clo, totals in student_totals.items():
                possible = totals.get('possible', 0)
                obtained = totals.get('obtained', 0)
                percent = None
                if possible > 0:
                    try:
                        percent = round((obtained / possible * 100), 2)
                    except Exception:
                        percent = None

                clo_students.setdefault(clo, []).append({
                    'cms_id': cms_id,
                    'student_name': student_name,
                    'percent': percent
                })

        # Build analytics per CLO
        result = {}
        for clo, students in clo_students.items():
            # filter out None percentages when computing averages
            percents = [s['percent'] for s in students if isinstance(s.get('percent'), (int, float))]
            total = len(students)
            avg = round(sum(percents) / len(percents), 2) if percents else None
            passed = len([p for p in percents if p >= threshold])
            failed = len([p for p in percents if p < threshold])

            # distribution buckets
            buckets = {"0-50": 0, "50-60": 0, "60-70": 0, "70-80": 0, "80-90": 0, "90-100": 0}
            for p in percents:
                if p < 50:
                    buckets["0-50"] += 1
                elif p < 60:
                    buckets["50-60"] += 1
                elif p < 70:
                    buckets["60-70"] += 1
                elif p < 80:
                    buckets["70-80"] += 1
                elif p < 90:
                    buckets["80-90"] += 1
                else:
                    buckets["90-100"] += 1

            # above average: compare to avg
            above_avg = len([p for p in percents if avg is not None and p > avg])

            result[clo] = {
                'total_students': total,
                'students_with_score': len(percents),
                'average_percent': avg,
                'passed': passed,
                'failed': failed,
                'above_average': above_avg,
                'distribution': buckets,
                'students': students
            }

        # Build chart-friendly list for frontend
        clo_chart = []
        avg_values = []
        for clo, stats in sorted(result.items(), key=lambda x: x[0]):
            avg = stats.get('average_percent')
            if isinstance(avg, (int, float)):
                avg_values.append(avg)
                clo_chart.append({
                    'clo': clo,
                    'obtained': avg,
                    'possible': 100,
                    'percent': avg
                })
            else:
                clo_chart.append({
                    'clo': clo,
                    'obtained': 0,
                    'possible': 100,
                    'percent': 0
                })

        total_obtained = round(sum(avg_values) / len(avg_values), 2) if avg_values else 0
        total_possible = 100 if avg_values else 0

        return Response({
            'course': {'id': course.id, 'code': course.code, 'title': course.title},
            'threshold': threshold,
            'clo_attainment': result,
            'clo_chart': clo_chart,
            'total_obtained': total_obtained,
            'total_possible': total_possible
        })
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

        # Replace existing CLOs for this course with newly extracted ones
        CLO.objects.filter(course=course).delete()

        # 4. Save CLOs to DB
        saved_clos = []
        for item in clos_data:
            text = " ".join(str(item.get('text', '')).split()).strip()
            if not text:
                continue
            code = _normalize_clo_code(item.get('code'), len(saved_clos) + 1)
            bloom = _normalize_bloom_level(item.get('bloom'))
            mapped_plos = _normalize_mapped_plos(item.get('mapped_plos', []))
            
            clo, created = CLO.objects.update_or_create(
                course=course,
                code=code,
                defaults={
                    'text': text,
                    'bloom_level': bloom,
                    'mapped_plos': mapped_plos
                }
            )
            saved_clos.append(clo)

        return Response({
            "message": f"Outline uploaded. {len(saved_clos)} CLOs extracted.",
            "clos": CLOSerializer(saved_clos, many=True).data
        }, status=201)

class UploadOutlineBySectionView(APIView):
    """
    Uploads outline using a CourseSection UUID, extracts CLOs, saves them.
    """
    permission_classes = [AllowAny]

    def post(self, request, section_id):
        section = get_object_or_404(CourseSection, id=section_id)
        course = section.course
        user = get_user_or_mock(request)

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"error": "File is required"}, status=400)

        outline = CourseOutline.objects.create(course=course, file=file_obj, uploaded_by=user)
        file_obj.seek(0)

        try:
            extractor = OBECourseExtractor(file_obj)
            clos_data = extractor.extract()
            print(f"DEBUG: Extracted {len(clos_data)} CLOs")
        except Exception as e:
            return Response({"error": f"Extraction failed: {str(e)}"}, status=500)

        # Replace existing CLOs for this course with newly extracted ones
        CLO.objects.filter(course=course).delete()

        saved_clos = []
        for item in clos_data:
            text = " ".join(str(item.get('text', '')).split()).strip()
            if not text:
                continue
            code = _normalize_clo_code(item.get('code'), len(saved_clos) + 1)
            bloom = _normalize_bloom_level(item.get('bloom'))
            mapped_plos = _normalize_mapped_plos(item.get('mapped_plos', []))
            clo, created = CLO.objects.update_or_create(
                course=course,
                code=code,
                defaults={
                    'text': text,
                    'bloom_level': bloom,
                    'mapped_plos': mapped_plos
                }
            )
            saved_clos.append(clo)

        return Response({
            "message": f"Outline uploaded. {len(saved_clos)} CLOs extracted.",
            "clos": CLOSerializer(saved_clos, many=True).data,
            "outline_id": str(outline.id)
        }, status=201)

class ListCourseCLOsView(generics.ListAPIView):
    """Returns CLOs for a specific Generic Course"""
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    pagination_class = None 
    
    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        return CLO.objects.filter(course__id=course_id).order_by("code")

class ListSectionCLOsView(generics.ListAPIView):
    """Returns CLOs using a CourseSection UUID."""
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    pagination_class = None

    def get_queryset(self):
        section_id = self.kwargs.get("section_id")
        section = get_object_or_404(CourseSection, id=section_id)
        return CLO.objects.filter(course=section.course).order_by("code")

class CLOUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """Edit a single CLO"""
    permission_classes = [AllowAny]
    serializer_class = CLOSerializer
    queryset = CLO.objects.all()
    lookup_field = 'pk'


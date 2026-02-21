from rest_framework import serializers
from .models import (
    Department, Program, StudentBatch, Semester, 
    Course, CourseSection, CourseEnrollment, 
    CourseOutline, CLO
)
from users.serializers import UserSerializer

# ==========================================
# 1. HIERARCHY SERIALIZERS (New Scalable Structure)
# ==========================================

class CourseSectionSerializer(serializers.ModelSerializer):
    """
    Serializes the specific class instance (e.g. 'CS-102 Section A').
    Includes details about the generic course and instructor.
    """
    course_title = serializers.ReadOnlyField(source='course.title')
    course_code = serializers.ReadOnlyField(source='course.code')
    instructor_name = serializers.ReadOnlyField(source='instructor.email') # or full_name

    class Meta:
        model = CourseSection
        fields = [
            "id", "semester", "course", "course_code", "course_title", 
            "section_name", "instructor", "instructor_name", 
            "enrollment_code", "created_at"
        ]
        read_only_fields = ["enrollment_code", "created_at"]

class SemesterSerializer(serializers.ModelSerializer):
    """
    Shows a semester (e.g. '8th Semester') and its active sections.
    """
    sections = CourseSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Semester
        fields = ["id", "name", "is_active", "sections"]

class StudentBatchSerializer(serializers.ModelSerializer):
    """
    Shows a batch (e.g. 'BESE-13') and its semesters.
    """
    semesters = SemesterSerializer(many=True, read_only=True)
    
    class Meta:
        model = StudentBatch
        fields = ["id", "name", "start_year", "semesters"]

class ProgramSerializer(serializers.ModelSerializer):
    """
    Shows a program (e.g. 'Software Engineering') and its batches.
    """
    batches = StudentBatchSerializer(many=True, read_only=True)
    
    class Meta:
        model = Program
        fields = ["id", "name", "full_name", "batches"]

class DepartmentSerializer(serializers.ModelSerializer):
    """
    The root level (e.g. 'SEECS'). Shows programs.
    """
    programs = ProgramSerializer(many=True, read_only=True)
    
    class Meta:
        model = Department
        fields = ["id", "name", "full_name", "programs"]


# ==========================================
# 2. COURSE CONTENT SERIALIZERS (Preserving Your Logic)
# ==========================================

class CourseSerializer(serializers.ModelSerializer):
    """
    The Generic Subject (e.g. 'CS-101'). 
    CLOs and Outlines are attached here.
    """
    class Meta:
        model = Course
        fields = ["id", "code", "title", "credit_hours"]

class CLOSerializer(serializers.ModelSerializer):
    class Meta:
        model = CLO
        # ✅ Preserved your mapped_plos field
        fields = ["id", "course", "code", "text", "bloom_level", "mapped_plos", "created_at"]

class CourseOutlineSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CourseOutline
        fields = ["id", "course", "file", "uploaded_by", "uploaded_at", "extracted_text"]


# ==========================================
# 3. ENROLLMENT SERIALIZER (Updated for Hierarchy)
# ==========================================

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Links a User to a specific SECTION (not just the generic course).
    """
    user = UserSerializer(read_only=True)
    section_details = CourseSectionSerializer(source='section', read_only=True)

    class Meta:
        model = CourseEnrollment
        # ✅ Changed 'course' to 'section' because students join a specific Section
        fields = ["id", "section", "section_details", "user", "role", "enrolled_at"]
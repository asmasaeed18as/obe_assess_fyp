from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.apps import apps

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username", "first_name", "last_name", "role", "is_staff", "date_joined")

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "role", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # ✅ Add custom claims to the token payload
        token['role'] = user.role
        token['email'] = user.email
        token['first_name'] = user.first_name

        return token

    # Keep your existing validate method as is
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({"user": UserSerializer(self.user).data})
        return data

from rest_framework import serializers
from django.apps import apps
from .models import User

class DashboardDataSerializer(serializers.ModelSerializer):
    """
    Returns user profile + list of SECTIONS they are involved in.
    Smartly handles both Instructors and Students.
    """
    courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "courses"]

    def get_courses(self, obj):
        # 1. Lazy load models
        CourseSection = apps.get_model('course_management', 'CourseSection')
        CourseEnrollment = apps.get_model('course_management', 'CourseEnrollment')
        
        course_list = []
        user_role = obj.role.lower() if obj.role else 'student'

        # ==========================================
        # SCENARIO A: The user is an INSTRUCTOR
        # ==========================================
        if user_role == 'instructor':
            # Find sections where this user is the assigned instructor
            sections = CourseSection.objects.filter(instructor=obj)
            
            for section in sections:
                # Count how many students have enrolled in this section
                student_count = CourseEnrollment.objects.filter(section=section).count()
                
                course_list.append({
                    "id": section.id,               # Section ID
                    "course_id": section.course.id, # Base Course ID
                    "title": section.course.title,
                    "code": section.course.code,
                    "section_name": section.section_name,
                    "semester": section.semester.name if section.semester else "N/A",
                    "enrollment_code": section.enrollment_code,
                    "role_in_course": "instructor", # They are the boss here
                    "students_count": student_count,
                })

        # ==========================================
        # SCENARIO B: The user is a STUDENT
        # ==========================================
        else:
            # Find sections the student has officially enrolled in
            enrollments = CourseEnrollment.objects.filter(user=obj)
            
            for enrollment in enrollments:
                section = enrollment.section 
                course = section.course
                
                # Count students in this specific class
                student_count = CourseEnrollment.objects.filter(section=section).count()
                
                course_list.append({
                    "id": section.id,
                    "course_id": course.id,
                    "title": course.title,
                    "code": course.code,
                    "section_name": section.section_name,
                    "semester": section.semester.name if section.semester else "N/A",
                    "enrollment_code": section.enrollment_code,
                    "role_in_course": "student",
                    "students_count": student_count,
                })
                
        return course_list
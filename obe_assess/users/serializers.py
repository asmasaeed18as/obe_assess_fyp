# users/serializers.py
from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.apps import apps
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id","email","username","first_name","last_name","role","is_staff","date_joined")

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

# Extend token serializer to return user data with token
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({"user": UserSerializer(self.user).data})
        return data
class DashboardDataSerializer(serializers.ModelSerializer):
    """
    Returns user profile + list of courses they are enrolled in.
    """
    courses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "courses"]

    def get_courses(self, obj):
        # 1. Lazy load the model to prevent Circular Import errors (500 Error Fix)
        CourseEnrollment = apps.get_model('course_management', 'CourseEnrollment')
        
        # 2. Fetch enrollments
        enrollments = CourseEnrollment.objects.filter(user=obj)
        course_list = []
        
        for enrollment in enrollments:
            course = enrollment.course
            # Count students in this course
            student_count = CourseEnrollment.objects.filter(course=course, role='student').count()
            
            course_list.append({
                "id": course.id,
                "title": course.title,
                "code": course.code,
                "role_in_course": enrollment.role,
                "students_count": student_count,
                "lessons_count": 0 # Placeholder
            })
        return course_list
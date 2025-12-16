from rest_framework import serializers
from .models import Course, CourseEnrollment, CourseOutline, CLO
from users.serializers import UserSerializer  # uses your project's user serializer

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "title", "description", "created_at"]

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = CourseEnrollment
        fields = ["id", "course", "user", "role", "enrolled_at"]

class CourseOutlineSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    class Meta:
        model = CourseOutline
        fields = ["id", "course", "file", "uploaded_by", "uploaded_at", "extracted_text"]

class CLOSerializer(serializers.ModelSerializer):
    class Meta:
        model = CLO
        fields = ["id", "course", "code", "text", "bloom_level", "created_at"]

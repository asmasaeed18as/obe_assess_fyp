# course_management/tests/test_models.py
from django.test import TestCase
from course_management.models import Course
from django.contrib.auth import get_user_model

User = get_user_model()

class CourseModelTests(TestCase):
    def test_course_creation(self):
        """Ensure a course can be created in the database."""
        course = Course.objects.create(
            name="Large Language Models",
            code="CS-416",
            # Add any other required fields for your Course model here
        )
        
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(course.name, "Large Language Models")
        self.assertEqual(course.code, "CS-416")
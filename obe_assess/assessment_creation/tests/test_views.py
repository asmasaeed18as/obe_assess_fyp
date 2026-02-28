# assessment_creation/tests/test_views.py
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from course_management.models import Course

User = get_user_model()

class AssessmentGenerationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Change this URL to match your exact urls.py path for generating assessments!
        self.generate_url = '/api/assessments/generate/' 

        # Create an Instructor
        self.instructor = User.objects.create_user(username='prof', password='pwd')
        self.instructor.role = 'instructor'
        self.instructor.save()

        # Create a Student
        self.student = User.objects.create_user(username='student', password='pwd')
        self.student.role = 'student'
        self.student.save()
        
        # Create a Course
        self.course = Course.objects.create(name="Test Course", code="CS-101")

    def test_student_access_blocked(self):
        """Ensure students get a 403 Forbidden error when trying to generate an assessment."""
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.generate_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('assessment_creation.views.requests.post') # Fakes the FastAPI call
    def test_instructor_can_generate_assessment(self, mock_requests_post):
        """Ensure an instructor can successfully generate an assessment."""
        
        # 1. Fake the response from your FastAPI LLM service
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = {
            "questions": [{"id": 1, "question": "Mock?", "marks": 5}]
        }

        # 2. Authenticate as the instructor
        self.client.force_authenticate(user=self.instructor)

        # 3. Send the payload (mimicking the React frontend)
        payload = {
            "topic_input": "Test Topic",
            "assessment_type": "Quiz/MCQs",
            "course_id": self.course.id,
            "questions_config": '[{"id": 1, "weightage": 5, "clo": "CLO-1", "bloom_level": "C1", "difficulty": "Easy"}]'
        }

        response = self.client.post(self.generate_url, payload, format='multipart')
        
        # 4. Assert the backend succeeded and saved to the DB
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(mock_requests_post.called) # Proves we "fake" called the LLM
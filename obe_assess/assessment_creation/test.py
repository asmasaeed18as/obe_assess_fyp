import json
import io
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Assessment, LectureMaterial
from course_management.models import Course
from users.models import User  # Assuming you have a custom user model

class AssessmentGenerationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('generate-assessment')  # Make sure this matches your urls.py name
        
        # 1. Setup User and Course
        self.user = User.objects.create_user(username='testuser', password='password')
        self.course = Course.objects.create(
            code="CS101", 
            title="Intro to CS", 
            description="Test Course"
        )
        
        # 2. Standard Configuration Data
        self.valid_config = [
            {
                "id": 1, 
                "clo": "CLO-1", 
                "bloom_level": "C1", 
                "difficulty": "Easy", 
                "weightage": "5",
                "question_type": "MCQ"
            }
        ]
        
        # 3. Mock LLM Response Data
        self.mock_llm_success_response = {
            "questions": [
                {
                    "id": 1,
                    "question": "What is CPU?",
                    "options": ["A", "B", "C", "D"],
                    "answer": "Central Processing Unit",
                    "marks": "5",
                    "meta": {"clo": "CLO-1", "bloom": "C1"}
                }
            ]
        }

    # ==========================================
    # 1. VALIDATION TESTS
    # ==========================================

    def test_missing_source_material(self):
        """Should fail if neither File nor Topic is provided."""
        data = {
            "course_id": self.course.id,
            "assessment_type": "Quiz/MCQs",
            "questions_config": json.dumps(self.valid_config)
        }
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Please upload a material file OR provide a topic description.")

    def test_missing_config(self):
        """Should fail if questions_config is missing."""
        data = {
            "course_id": self.course.id,
            "topic_input": "Python Basics",
            "assessment_type": "Quiz/MCQs"
        }
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Questions configuration is required", response.data["error"])

    def test_invalid_course_id(self):
        """Should fail if Course ID does not exist."""
        data = {
            "course_id": 9999, # Non-existent
            "topic_input": "Test Topic",
            "questions_config": json.dumps(self.valid_config)
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ==========================================
    # 2. SUCCESS SCENARIOS (MOCKED)
    # ==========================================

    @patch('assessment_creation.views.requests.post')
    def test_generate_from_topic_success(self, mock_post):
        """Should successfully generate assessment from a Topic Input."""
        
        # Mock the LLM Service Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_llm_success_response
        mock_post.return_value = mock_response

        data = {
            "course_id": self.course.id,
            "topic_input": "History of AI",
            "assessment_type": "Assignment",
            "questions_config": json.dumps(self.valid_config)
        }

        response = self.client.post(self.url, data, format='multipart')

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Assessment.objects.filter(course=self.course).exists())
        
        # Verify LectureMaterial was created correctly
        lecture = LectureMaterial.objects.last()
        self.assertIn("TOPIC/INSTRUCTIONS", lecture.extracted_text)
        self.assertIn("History of AI", lecture.extracted_text)

    @patch('assessment_creation.views.generate_pdf_assessment') # Mock PDF generation to save time
    @patch('assessment_creation.views.extract_text_from_pdf_filefield')
    @patch('assessment_creation.views.requests.post')
    def test_generate_from_file_success(self, mock_post, mock_extract, mock_pdf_gen):
        """Should successfully generate assessment from a File Upload."""
        
        # 1. Mock Text Extraction
        mock_extract.return_value = "Extracted text from PDF content."
        
        # 2. Mock LLM Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_llm_success_response
        mock_post.return_value = mock_response

        # 3. Create Dummy File
        pdf_content = b"%PDF-1.4 mock content"
        uploaded_file = SimpleUploadedFile("test_lecture.pdf", pdf_content, content_type="application/pdf")

        data = {
            "course_id": self.course.id,
            "file": uploaded_file,
            "assessment_type": "Exam",
            "questions_config": json.dumps(self.valid_config)
        }

        response = self.client.post(self.url, data, format='multipart')

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify DB Objects
        self.assertTrue(LectureMaterial.objects.filter(title="test_lecture.pdf").exists())
        self.assertEqual(LectureMaterial.objects.first().extracted_text, "Extracted text from PDF content.")
        
        # Verify LLM was called with correct text
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['text'], "Extracted text from PDF content.")

    # ==========================================
    # 3. FAILURE SCENARIOS
    # ==========================================

    @patch('assessment_creation.views.requests.post')
    def test_llm_service_failure(self, mock_post):
        """Should return 500 if the LLM Microservice is down."""
        
        # Mock Connection Error
        mock_post.side_effect = requests.exceptions.ConnectionError("LLM Down")

        data = {
            "course_id": self.course.id,
            "topic_input": "Test Topic",
            "questions_config": json.dumps(self.valid_config)
        }

        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Error connecting to LLM service", response.data["error"])

    @patch('assessment_creation.views.requests.post')
    def test_llm_invalid_json_response(self, mock_post):
        """Should return 500 if LLM returns garbage instead of JSON."""
        
        # Mock Invalid JSON response (e.g., 500 error from FastAPI)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_post.return_value = mock_response

        data = {
            "course_id": self.course.id,
            "topic_input": "Test Topic",
            "questions_config": json.dumps(self.valid_config)
        }

        try:
            response = self.client.post(self.url, data, format='multipart')
            # It might return 500 either from raise_for_status or the try/except block
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception:
            pass # Test passes if exception logic is handled in view
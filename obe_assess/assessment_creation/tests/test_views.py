import io
import json
import zipfile
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.test import APIClient

from assessment_creation.models import Assessment, LectureMaterial
from course_management.models import (
    Course,
    CourseSection,
    Department,
    Program,
    Semester,
    StudentBatch,
)


User = get_user_model()


class AssessmentCreationViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.generate_url = reverse("generate_assessment")
        self.course = Course.objects.create(code="CS-404", title="Software Testing")
        self.instructor = User.objects.create_user(
            email="prof@test.com",
            password="pwd12345",
            role="instructor",
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            password="pwd12345",
            role="student",
        )
        self.valid_config = json.dumps(
            [
                {
                    "id": 1,
                    "weightage": 5,
                    "clo": "CLO-1",
                    "bloom_level": "C2",
                    "difficulty": "Easy",
                },
                {
                    "id": 2,
                    "weightage": 10,
                    "clo": "CLO-2",
                    "bloom_level": "C3",
                    "difficulty": "Medium",
                },
            ]
        )
        self.valid_llm_response = {
            "questions": [
                {
                    "id": 1,
                    "question": "Explain unit testing.",
                    "marks": 5,
                    "answer": "It tests isolated units of code.",
                }
            ]
        }

    def authenticate_instructor(self):
        self.client.force_authenticate(user=self.instructor)

    def test_unauthenticated_user_cannot_generate_assessment(self):
        response = self.client.post(self.generate_url, {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_access_blocked(self):
        self.client.force_authenticate(user=self.student)

        response = self.client.post(self.generate_url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_generation_requires_topic_or_file(self):
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "assessment_type": "Quiz",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("material file OR provide a topic", response.data["error"])

    def test_generation_requires_questions_config(self):
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Testing basics",
                "assessment_type": "Quiz",
                "course_id": self.course.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Questions configuration is required")

    def test_generation_requires_course_id(self):
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Testing basics",
                "assessment_type": "Quiz",
                "questions_config": self.valid_config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Course ID is required to link assessment")

    def test_generation_rejects_invalid_questions_config_json(self):
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Testing basics",
                "assessment_type": "Quiz",
                "course_id": self.course.id,
                "questions_config": "{bad json}",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid JSON format for questions_config")

    @patch("assessment_creation.views.generate_pdf_assessment")
    @patch("assessment_creation.views.requests.post")
    def test_instructor_can_generate_assessment_from_topic(
        self,
        mock_requests_post,
        mock_generate_pdf,
    ):
        mock_requests_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value=self.valid_llm_response),
        )
        mock_generate_pdf.return_value = io.BytesIO(b"pdf-content")
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Unit testing and mocking",
                "assessment_type": "Quiz",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Assessment.objects.count(), 1)
        assessment = Assessment.objects.get()
        self.assertEqual(assessment.course, self.course)
        self.assertEqual(assessment.material.extracted_text, "TOPIC/INSTRUCTIONS PROVIDED BY INSTRUCTOR:\nUnit testing and mocking")
        self.assertEqual(assessment.clo, "CLO-1, CLO-2")
        self.assertEqual(assessment.result_json, self.valid_llm_response)
        self.assertTrue(mock_requests_post.called)
        self.assertTrue(assessment.pdf.name.endswith(".pdf"))

    @patch("assessment_creation.views.generate_pdf_assessment")
    @patch("assessment_creation.views.requests.post")
    @patch("assessment_creation.views.extract_text_from_pdf_filefield")
    def test_generation_from_uploaded_file_includes_outline_text(
        self,
        mock_extract_text,
        mock_requests_post,
        mock_generate_pdf,
    ):
        mock_extract_text.side_effect = ["Lecture content", "Outline content"]
        mock_requests_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value=self.valid_llm_response),
        )
        mock_generate_pdf.return_value = io.BytesIO(b"pdf-content")
        self.authenticate_instructor()

        material_file = SimpleUploadedFile(
            "lecture.pdf",
            b"%PDF-1.4 lecture",
            content_type="application/pdf",
        )
        outline_file = SimpleUploadedFile(
            "outline.pdf",
            b"%PDF-1.4 outline",
            content_type="application/pdf",
        )

        response = self.client.post(
            self.generate_url,
            {
                "file": material_file,
                "outline": outline_file,
                "assessment_type": "Assignment",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        called_payload = mock_requests_post.call_args.kwargs["json"]
        self.assertIn("=== COURSE OUTLINE ===\nOutline content", called_payload["text"])
        self.assertIn("=== CONTENT ===\nLecture content", called_payload["text"])
        self.assertEqual(LectureMaterial.objects.get().title, "lecture.pdf")

    @patch("assessment_creation.views.extract_text_from_pdf_filefield", side_effect=Exception("parse failed"))
    def test_generation_returns_500_when_uploaded_material_extraction_fails(self, _mock_extract_text):
        self.authenticate_instructor()

        material_file = SimpleUploadedFile(
            "lecture.pdf",
            b"%PDF-1.4 lecture",
            content_type="application/pdf",
        )

        response = self.client.post(
            self.generate_url,
            {
                "file": material_file,
                "assessment_type": "Assignment",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Failed to extract PDF text", response.data["error"])

    @patch(
        "assessment_creation.views.requests.post",
        side_effect=RequestException("service unavailable"),
    )
    def test_generation_returns_500_when_llm_request_crashes(self, _mock_requests_post):
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Testing basics",
                "assessment_type": "Quiz",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Error connecting to LLM service", response.data["error"])

    @patch("assessment_creation.views.requests.post")
    def test_generation_returns_500_for_non_json_llm_response(self, mock_requests_post):
        mock_requests_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(side_effect=ValueError("not json")),
        )
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Testing basics",
                "assessment_type": "Quiz",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "LLM service returned non-JSON response.")

    @patch("assessment_creation.views.requests.post")
    def test_generation_returns_500_for_invalid_llm_questions_payload(self, mock_requests_post):
        mock_requests_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"questions": "bad-data"}),
        )
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Testing basics",
                "assessment_type": "Quiz",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"], "Invalid response from LLM service")

    @patch("assessment_creation.views.generate_pdf_assessment", side_effect=Exception("pdf failed"))
    @patch("assessment_creation.views.requests.post")
    def test_generation_still_succeeds_when_pdf_backup_generation_fails(
        self,
        mock_requests_post,
        _mock_generate_pdf,
    ):
        mock_requests_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value=self.valid_llm_response),
        )
        self.authenticate_instructor()

        response = self.client.post(
            self.generate_url,
            {
                "topic_input": "Testing basics",
                "assessment_type": "Quiz",
                "course_id": self.course.id,
                "questions_config": self.valid_config,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Assessment.objects.count(), 1)


class AssessmentDownloadAndListingViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="pwd12345",
            role="instructor",
        )
        self.student = User.objects.create_user(
            email="student2@test.com",
            password="pwd12345",
            role="student",
        )
        self.course = Course.objects.create(code="CS-405", title="QA Engineering")
        self.department = Department.objects.create(name="SEECS", full_name="School of EECS")
        self.program = Program.objects.create(
            department=self.department,
            name="BSCS",
            full_name="BS Computer Science",
        )
        self.batch = StudentBatch.objects.create(
            program=self.program,
            name="BSCS-13",
            start_year=2022,
        )
        self.semester = Semester.objects.create(batch=self.batch, name="Spring 2026")
        self.section = CourseSection.objects.create(
            semester=self.semester,
            course=self.course,
            section_name="A",
            instructor=self.instructor,
        )
        self.material = LectureMaterial.objects.create(title="Week 4")
        self.assessment = Assessment.objects.create(
            course=self.course,
            material=self.material,
            assessment_type="Quiz",
            result_json={
                "questions": [
                    {
                        "question": "What is integration testing?",
                        "answer": "It tests component interactions.",
                        "rubric": {"Definition": "5"},
                        "meta": {"clo": "CLO-1", "bloom": "C2"},
                    }
                ]
            },
        )

    def authenticate_instructor(self):
        self.client.force_authenticate(user=self.instructor)

    def test_student_cannot_download_specific_assessment(self):
        self.client.force_authenticate(user=self.student)

        response = self.client.get(
            reverse(
                "download_specific",
                args=[self.assessment.id, "full", "pdf"],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("assessment_creation.views.generate_docx_assessment")
    def test_download_specific_docx_returns_file_response(self, mock_generate_docx):
        mock_generate_docx.return_value = io.BytesIO(b"docx-content")
        self.authenticate_instructor()

        response = self.client.get(
            reverse(
                "download_specific",
                args=[self.assessment.id, "questions_only", "docx"],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="Assessment_{self.assessment.id}_questions_only.docx"',
        )

    def test_download_specific_rejects_invalid_format(self):
        self.authenticate_instructor()

        response = self.client.get(
            reverse(
                "download_specific",
                args=[self.assessment.id, "full", "txt"],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid file format")

    def test_download_specific_returns_404_when_questions_missing(self):
        self.authenticate_instructor()
        self.assessment.result_json = {}
        self.assessment.save()

        response = self.client.get(
            reverse(
                "download_specific",
                args=[self.assessment.id, "full", "pdf"],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "No questions found")

    @patch("assessment_creation.views.generate_zip_bundle")
    def test_download_zip_returns_bundle(self, mock_generate_zip):
        mock_generate_zip.return_value = io.BytesIO(self.build_zip_bytes())
        self.authenticate_instructor()

        response = self.client.get(
            reverse("download_zip", args=[self.assessment.id, "docx"])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="Assessment_Bundle_{self.assessment.id}.zip"',
        )

    @patch("assessment_creation.views.generate_zip_bundle", side_effect=Exception("zip failed"))
    def test_download_zip_returns_500_when_generation_fails(self, _mock_generate_zip):
        self.authenticate_instructor()

        response = self.client.get(
            reverse("download_zip", args=[self.assessment.id, "pdf"])
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Zip generation failed", response.data["error"])

    def test_download_zip_returns_404_when_result_json_is_incomplete(self):
        self.authenticate_instructor()
        self.assessment.result_json = None
        self.assessment.save()

        response = self.client.get(
            reverse("download_zip", args=[self.assessment.id, "pdf"])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Assessment data incomplete")

    def test_course_assessment_list_returns_only_requested_course(self):
        other_course = Course.objects.create(code="CS-406", title="Another Course")
        other_material = LectureMaterial.objects.create(title="Other")
        Assessment.objects.create(
            course=other_course,
            material=other_material,
            assessment_type="Assignment",
            result_json={"questions": [{"question": "Other"}]},
        )
        self.authenticate_instructor()

        response = self.client.get(reverse("course_assessments", args=[self.course.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.assessment.id))

    def test_section_assessment_list_returns_assessments_for_section_course(self):
        self.authenticate_instructor()

        response = self.client.get(
            reverse("section_course_assessments", args=[self.section.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["assessment_type"], "Quiz")

    def test_student_cannot_access_course_assessment_list(self):
        self.client.force_authenticate(user=self.student)

        response = self.client.get(reverse("course_assessments", args=[self.course.id]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def build_zip_bytes():
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("Question_Paper.docx", b"content")
        return buffer.getvalue()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from assessment_marking.models import GradedSubmission, grading_upload_to
from assessment_marking.serializers import GradedSubmissionSerializer
from course_management.models import Course


class GradedSubmissionModelTests(TestCase):
    def test_grading_upload_to_uses_submission_id(self):
        submission = GradedSubmission()

        path = grading_upload_to(submission, "answer.pdf")

        self.assertEqual(path, f"grading/{submission.id}/answer.pdf")

    def test_string_representation_includes_id(self):
        submission = GradedSubmission.objects.create(
            student_file=SimpleUploadedFile("student.txt", b"student"),
            rubric_file=SimpleUploadedFile("rubric.txt", b"rubric"),
        )

        self.assertEqual(str(submission), f"Grading {submission.id}")


class GradedSubmissionSerializerTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code="CS101", title="Intro")

    def test_serializer_creates_submission_and_ignores_read_only_ai_result(self):
        serializer = GradedSubmissionSerializer(
            data={
                "course": self.course.id,
                "title": "Serializer Test",
                "student_file": SimpleUploadedFile("student.txt", b"student"),
                "rubric_file": SimpleUploadedFile("rubric.txt", b"rubric"),
                "ai_result_json": {"should": "be ignored"},
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        submission = serializer.save()

        self.assertEqual(submission.course, self.course)
        self.assertEqual(submission.title, "Serializer Test")
        self.assertIsNone(submission.ai_result_json)

    def test_serializer_requires_both_files(self):
        serializer = GradedSubmissionSerializer(
            data={
                "course": self.course.id,
                "title": "Missing Files",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("student_file", serializer.errors)
        self.assertIn("rubric_file", serializer.errors)

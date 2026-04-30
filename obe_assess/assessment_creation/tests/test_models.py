import uuid

from django.test import TestCase

from assessment_creation.models import (
    Assessment,
    LectureMaterial,
    assessment_upload_to,
)
from course_management.models import Course


class LectureMaterialModelTests(TestCase):
    def test_string_representation_returns_title(self):
        lecture = LectureMaterial(title="Week 1 Slides")

        self.assertEqual(str(lecture), "Week 1 Slides")


class AssessmentModelTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code="CS-101", title="Intro to Computing")
        self.material = LectureMaterial.objects.create(title="Lecture 1")

    def test_upload_path_uses_assessment_id(self):
        assessment_id = uuid.uuid4()
        assessment = Assessment(
            id=assessment_id,
            material=self.material,
            assessment_type="Quiz",
        )

        path = assessment_upload_to(assessment, "quiz.pdf")

        self.assertEqual(path, f"assessments/{assessment_id}/quiz.pdf")

    def test_assessment_defaults_questions_config_to_empty_list(self):
        assessment = Assessment.objects.create(
            course=self.course,
            material=self.material,
            assessment_type="Assignment",
        )

        self.assertEqual(assessment.questions_config, [])

    def test_string_representation_includes_type(self):
        assessment = Assessment.objects.create(
            course=self.course,
            material=self.material,
            assessment_type="Midterm",
        )

        self.assertIn("Midterm", str(assessment))
        self.assertIn(str(assessment.id), str(assessment))

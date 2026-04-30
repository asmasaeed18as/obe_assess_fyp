from django.test import TestCase

from assessment_creation.models import Assessment, LectureMaterial
from assessment_creation.serializers import (
    AssessmentSerializer,
    LectureMaterialSerializer,
)
from course_management.models import Course


class LectureMaterialSerializerTests(TestCase):
    def test_serializer_exposes_expected_fields(self):
        lecture = LectureMaterial.objects.create(
            title="Lecture Notes",
            extracted_text="Topic coverage",
        )

        data = LectureMaterialSerializer(lecture).data

        self.assertEqual(
            set(data.keys()),
            {"id", "title", "file", "uploaded_at", "extracted_text"},
        )
        self.assertEqual(data["title"], "Lecture Notes")


class AssessmentSerializerTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code="CS-202", title="Data Structures")
        self.material = LectureMaterial.objects.create(title="Trees")
        self.assessment = Assessment.objects.create(
            course=self.course,
            material=self.material,
            assessment_type="Quiz",
            questions_config=[{"id": 1, "clo": "CLO-1", "weightage": 5}],
            result_json={"questions": [{"question": "Define a tree."}]},
        )

    def test_serializer_exposes_expected_fields(self):
        data = AssessmentSerializer(self.assessment).data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "material",
                "assessment_type",
                "questions_config",
                "clo",
                "bloom_level",
                "created_at",
                "result_json",
                "pdf",
            },
        )
        self.assertEqual(data["assessment_type"], "Quiz")

    def test_read_only_fields_are_not_accepted_from_input(self):
        serializer = AssessmentSerializer(
            data={
                "material": self.material.id,
                "assessment_type": "Final",
                "questions_config": [{"id": 2, "clo": "CLO-2", "weightage": 10}],
                "created_at": "2026-01-01T00:00:00Z",
                "result_json": {"questions": []},
                "pdf": "should-be-ignored",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("created_at", serializer.validated_data)
        self.assertNotIn("result_json", serializer.validated_data)
        self.assertNotIn("pdf", serializer.validated_data)

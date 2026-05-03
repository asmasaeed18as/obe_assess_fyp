from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from assessment_creation.models import Assessment, LectureMaterial
from assessment_marking.models import GradedSubmission
from assessment_marking.utils import map_submission_clos, remap_course_submissions
from course_management.models import Course


def text_file(name):
    return SimpleUploadedFile(name, b"content", content_type="text/plain")


class AssessmentMarkingUtilsTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(code="CS101", title="Intro")
        self.material = LectureMaterial.objects.create(
            title="Material",
            file=text_file("material.txt"),
            extracted_text="content",
        )

    def _create_assessment(self, questions):
        return Assessment.objects.create(
            course=self.course,
            material=self.material,
            assessment_type="Quiz",
            result_json={"questions": questions},
        )

    def test_map_submission_clos_matches_by_question_text(self):
        self._create_assessment(
            [
                {"id": 1, "question": "Define abstraction.", "meta": {"clo": "CLO-1"}},
                {"id": 2, "question": "Explain polymorphism.", "meta": {"clo": "CLO-2"}},
            ]
        )
        submission = GradedSubmission.objects.create(
            course=self.course,
            student_file=text_file("student.txt"),
            rubric_file=text_file("rubric.txt"),
            ai_result_json={
                "summary": {},
                "per_question": {
                    "first": {
                        "question": "Define abstraction.",
                        "marks_awarded": 5,
                        "max_marks": 5,
                    },
                    "second": {
                        "question": "Explain polymorphism.",
                        "marks_awarded": 3,
                        "max_marks": 5,
                    },
                },
            },
        )

        map_submission_clos(submission)
        submission.refresh_from_db()

        self.assertEqual(submission.ai_result_json["per_question"]["first"]["mapped_clo"], "CLO-1")
        self.assertEqual(submission.ai_result_json["per_question"]["second"]["mapped_clo"], "CLO-2")
        self.assertEqual(
            submission.ai_result_json["clo_summary"],
            {
                "CLO-1": {"obtained": 5, "possible": 5},
                "CLO-2": {"obtained": 3, "possible": 5},
            },
        )
        self.assertEqual(submission.ai_result_json["summary"]["total_obtained"], 8)
        self.assertEqual(submission.ai_result_json["summary"]["total_possible"], 10)
        self.assertEqual(submission.ai_result_json["summary"]["percentage"], 80.0)

    def test_map_submission_clos_falls_back_to_question_number_and_bad_marks(self):
        self._create_assessment(
            [
                {"id": 1, "question": "Generated one", "meta": {"clo": "CLO-1"}},
                {"id": 2, "question": "Generated two", "meta": {"clo": "CLO-2"}},
            ]
        )
        submission = GradedSubmission.objects.create(
            course=self.course,
            student_file=text_file("student.txt"),
            rubric_file=text_file("rubric.txt"),
            ai_result_json={
                "per_question": {
                    "Q1": {"question": "Different text", "marks_awarded": "bad", "max_marks": "5"},
                    "Q2": {"question": "Different text", "marks_awarded": "2.7", "max_marks": "bad"},
                },
            },
        )

        map_submission_clos(submission)
        submission.refresh_from_db()

        self.assertEqual(submission.ai_result_json["per_question"]["Q1"]["mapped_clo"], "CLO-1")
        self.assertEqual(submission.ai_result_json["per_question"]["Q2"]["mapped_clo"], "CLO-2")
        self.assertEqual(submission.ai_result_json["clo_summary"]["CLO-1"], {"obtained": 0, "possible": 5})
        self.assertEqual(submission.ai_result_json["clo_summary"]["CLO-2"], {"obtained": 2, "possible": 0})

    def test_remap_course_submissions_updates_only_course_submissions(self):
        self._create_assessment(
            [{"id": 1, "question": "Question one", "meta": {"clo": "CLO-1"}}]
        )
        other_course = Course.objects.create(code="CS102", title="Other")
        first = GradedSubmission.objects.create(
            course=self.course,
            student_file=text_file("student1.txt"),
            rubric_file=text_file("rubric1.txt"),
            ai_result_json={
                "per_question": {
                    "Q1": {"question": "Question one", "marks_awarded": 4, "max_marks": 5}
                }
            },
        )
        second = GradedSubmission.objects.create(
            course=self.course,
            student_file=text_file("student2.txt"),
            rubric_file=text_file("rubric2.txt"),
            ai_result_json={
                "per_question": {
                    "Q1": {"question": "Question one", "marks_awarded": 3, "max_marks": 5}
                }
            },
        )
        other = GradedSubmission.objects.create(
            course=other_course,
            student_file=text_file("student3.txt"),
            rubric_file=text_file("rubric3.txt"),
            ai_result_json={
                "per_question": {
                    "Q1": {"question": "Question one", "marks_awarded": 1, "max_marks": 5}
                }
            },
        )

        count = remap_course_submissions(self.course)

        self.assertEqual(count, 2)
        first.refresh_from_db()
        second.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(first.ai_result_json["per_question"]["Q1"]["mapped_clo"], "CLO-1")
        self.assertEqual(second.ai_result_json["per_question"]["Q1"]["mapped_clo"], "CLO-1")
        self.assertNotIn("mapped_clo", other.ai_result_json["per_question"]["Q1"])

    def test_remap_course_submissions_returns_zero_for_missing_course(self):
        self.assertEqual(remap_course_submissions(None), 0)

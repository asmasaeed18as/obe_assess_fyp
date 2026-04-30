import io
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from assessment_creation.models import Assessment, LectureMaterial
from assessment_marking.models import GradedSubmission
from course_management.models import (
    CLO,
    Course,
    CourseEnrollment,
    CourseOutline,
    CourseSection,
    Department,
    Program,
    Semester,
    StudentBatch,
)


User = get_user_model()


class CourseManagementViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="secret123",
            role="admin",
        )
        self.instructor = User.objects.create_user(
            email="teacher@test.com",
            password="secret123",
            role="instructor",
            first_name="Ayesha",
            last_name="Khan",
        )
        self.other_instructor = User.objects.create_user(
            email="other@test.com",
            password="secret123",
            role="instructor",
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            password="secret123",
            role="student",
        )
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
        self.course = Course.objects.create(code="CS-301", title="Software QA", credit_hours=3)
        self.other_course = Course.objects.create(code="CS-302", title="Networks", credit_hours=4)
        self.section = CourseSection.objects.create(
            semester=self.semester,
            course=self.course,
            section_name="A",
            instructor=self.instructor,
        )
        self.other_section = CourseSection.objects.create(
            semester=self.semester,
            course=self.other_course,
            section_name="B",
            instructor=self.other_instructor,
        )
        self.enrollment = CourseEnrollment.objects.create(
            section=self.section,
            user=self.student,
            role="student",
        )
        self.material = LectureMaterial.objects.create(title="Testing lecture")
        self.assessment = Assessment.objects.create(
            course=self.course,
            material=self.material,
            assessment_type="Quiz",
            result_json={
                "questions": [
                    {
                        "id": 1,
                        "question": "Define unit testing",
                        "marks": 10,
                        "meta": {"clo": "CLO-1"},
                    },
                    {
                        "id": 2,
                        "question": "Define integration testing",
                        "marks": 20,
                        "meta": {"clo": "CLO-2"},
                    },
                ]
            },
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_lms_hierarchy_returns_nested_data(self):
        response = self.client.get(reverse("lms-hierarchy"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "SEECS")
        self.assertEqual(response.data[0]["programs"][0]["batches"][0]["semesters"][0]["sections"][0]["course_code"], "CS-301")

    def test_resource_list_returns_courses_and_instructors(self):
        response = self.client.get(reverse("lms-resources"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["courses"]), 2)
        self.assertEqual(len(response.data["instructors"]), 2)

    def test_section_create_view_creates_section(self):
        response = self.client.post(
            reverse("section-create"),
            {
                "semester": self.semester.id,
                "course": self.course.id,
                "section_name": "C",
                "instructor": self.instructor.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CourseSection.objects.filter(section_name="C").exists())

    def test_course_create_view_creates_course(self):
        response = self.client.post(
            reverse("course-create-admin"),
            {"code": "CS-450", "title": "Compiler Design", "credit_hours": 2},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(code="CS-450", title="Compiler Design").exists())

    def test_course_create_view_returns_400_for_duplicate_code(self):
        response = self.client.post(
            reverse("course-create-admin"),
            {"code": "CS-301", "title": "Duplicate"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_join_section_requires_authentication(self):
        response = self.client.post(reverse("student-join"), {"enrollment_code": self.section.enrollment_code})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_can_join_section(self):
        new_student = User.objects.create_user(
            email="newstudent@test.com",
            password="secret123",
            role="student",
        )
        self.authenticate(new_student)

        response = self.client.post(
            reverse("student-join"),
            {"enrollment_code": self.section.enrollment_code},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CourseEnrollment.objects.filter(user=new_student, section=self.section).exists())

    def test_join_section_rejects_duplicate_enrollment(self):
        self.authenticate(self.student)

        response = self.client.post(
            reverse("student-join"),
            {"enrollment_code": self.section.enrollment_code},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "You are already enrolled in this class.")

    def test_my_enrollments_returns_current_user_records(self):
        self.authenticate(self.student)

        response = self.client.get(reverse("my-enrollments"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["section_details"]["course_code"], "CS-301")

    def test_course_list_filters_for_instructor_sections(self):
        self.authenticate(self.instructor)

        response = self.client.get(reverse("course-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "CS-301")

    def test_course_list_returns_all_courses_for_anonymous_user(self):
        response = self.client.get(reverse("course-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_course_detail_returns_selected_course(self):
        response = self.client.get(reverse("course-detail", args=[self.course.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Software QA")

    def test_course_detail_by_section_returns_section_course(self):
        response = self.client.get(reverse("course-detail-by-section", args=[self.section.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "CS-301")

    @patch("course_management.views.OBECourseExtractor")
    def test_upload_outline_requires_file(self, _mock_extractor):
        response = self.client.post(reverse("upload-outline", args=[self.course.id]), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "File is required")

    @patch("course_management.views.OBECourseExtractor")
    def test_upload_outline_saves_and_normalizes_clos(self, mock_extractor):
        existing = CLO.objects.create(
            course=self.course,
            code="OLD",
            text="Old CLO",
        )
        mock_extractor.return_value.extract.return_value = [
            {"code": "clo 1", "text": "  Explain testing basics  ", "bloom": "c 2", "mapped_plos": ["PLO(SE)-1"]},
            {"code": "", "text": "Design test plans", "bloom": "", "mapped_plos": ["3"]},
            {"code": "skip", "text": "   ", "bloom": "c1", "mapped_plos": []},
        ]
        upload = SimpleUploadedFile("outline.pdf", b"%PDF-1.4", content_type="application/pdf")
        self.authenticate(self.instructor)

        response = self.client.post(
            reverse("upload-outline", args=[self.course.id]),
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(CLO.objects.filter(id=existing.id).exists())
        self.assertEqual(CLO.objects.filter(course=self.course).count(), 2)
        self.assertEqual(response.data["clos"][0]["code"], "CLO-1")
        self.assertEqual(response.data["clos"][0]["bloom_level"], "C-2")
        self.assertEqual(response.data["clos"][1]["mapped_plos"], ["PLO-3"])
        self.assertTrue(CourseOutline.objects.filter(course=self.course).exists())

    @patch("course_management.views.OBECourseExtractor", side_effect=Exception("extractor failed"))
    def test_upload_outline_returns_500_when_extraction_fails(self, _mock_extractor):
        upload = SimpleUploadedFile("outline.pdf", b"%PDF-1.4", content_type="application/pdf")

        response = self.client.post(
            reverse("upload-outline", args=[self.course.id]),
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Extraction failed", response.data["error"])

    @patch("course_management.views.OBECourseExtractor")
    def test_upload_outline_by_section_returns_outline_id(self, mock_extractor):
        mock_extractor.return_value.extract.return_value = [
            {"code": "1", "text": "Understand QA", "bloom": "A1", "mapped_plos": ["PLO-1"]}
        ]
        upload = SimpleUploadedFile("outline.pdf", b"%PDF-1.4", content_type="application/pdf")
        self.authenticate(self.instructor)

        response = self.client.post(
            reverse("upload-outline-by-section", args=[self.section.id]),
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("outline_id", response.data)
        self.assertEqual(response.data["clos"][0]["code"], "CLO-1")

    def test_list_course_clos_returns_course_clos(self):
        CLO.objects.create(course=self.course, code="CLO-1", text="Understand testing")
        CLO.objects.create(course=self.course, code="CLO-2", text="Write cases")

        response = self.client.get(reverse("course-clos", args=[self.course.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_section_clos_returns_section_course_clos(self):
        CLO.objects.create(course=self.course, code="CLO-1", text="Understand testing")

        response = self.client.get(reverse("section-clos", args=[self.section.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["code"], "CLO-1")

    def test_clo_update_view_updates_clo(self):
        clo = CLO.objects.create(course=self.course, code="CLO-1", text="Old text")

        response = self.client.patch(
            reverse("clo-update", args=[clo.id]),
            {"text": "Updated text", "bloom_level": "C-2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        clo.refresh_from_db()
        self.assertEqual(clo.text, "Updated text")
        self.assertEqual(clo.bloom_level, "C-2")

    def test_clo_update_view_deletes_clo(self):
        clo = CLO.objects.create(course=self.course, code="CLO-1", text="Delete me")

        response = self.client.delete(reverse("clo-update", args=[clo.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CLO.objects.filter(id=clo.id).exists())

    @patch("course_management.views.remap_course_submissions")
    def test_course_clo_analytics_returns_aggregated_stats(self, mock_remap):
        GradedSubmission.objects.create(
            course=self.course,
            title="Quiz 1",
            student_file=SimpleUploadedFile("student1.pdf", b"student", content_type="application/pdf"),
            rubric_file=SimpleUploadedFile("rubric1.pdf", b"rubric", content_type="application/pdf"),
            ai_result_json={
                "student_name": "Ali",
                "cms_id": "001",
                "per_question": {
                    "Q1": {
                        "question": "Define unit testing",
                        "marks_awarded": 8,
                        "max_marks": 10,
                        "mapped_clo": "CLO-1",
                    },
                    "Q2": {
                        "question": "Define integration testing",
                        "marks_awarded": 12,
                        "max_marks": 20,
                    },
                },
            },
        )
        GradedSubmission.objects.create(
            course=self.course,
            title="Quiz 1",
            student_file=SimpleUploadedFile("student2.pdf", b"student", content_type="application/pdf"),
            rubric_file=SimpleUploadedFile("rubric2.pdf", b"rubric", content_type="application/pdf"),
            ai_result_json={
                "student": {"name": "Sara", "cms_id": "002"},
                "per_question": {
                    "Q1": {
                        "question": "Define unit testing",
                        "marks_awarded": 4,
                        "max_marks": 10,
                    },
                    "Q2": {
                        "question": "Define integration testing",
                        "marks_awarded": 18,
                        "max_marks": 20,
                    },
                },
            },
        )

        response = self.client.get(
            reverse("course-clo-analytics", args=[self.course.id]),
            {"threshold": "70"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_remap.called)
        self.assertEqual(response.data["course"]["code"], "CS-301")
        self.assertEqual(response.data["threshold"], 70.0)
        self.assertEqual(response.data["clo_attainment"]["CLO-1"]["average_percent"], 60.0)
        self.assertEqual(response.data["clo_attainment"]["CLO-2"]["average_percent"], 75.0)
        self.assertEqual(response.data["clo_attainment"]["CLO-2"]["passed"], 1)
        self.assertEqual(len(response.data["clo_chart"]), 2)

    @patch("course_management.views.remap_course_submissions")
    def test_course_clo_analytics_uses_default_threshold_for_invalid_query_param(self, _mock_remap):
        response = self.client.get(
            reverse("course-clo-analytics", args=[self.course.id]),
            {"threshold": "bad-value"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["threshold"], 60.0)
        self.assertEqual(response.data["total_obtained"], 0)

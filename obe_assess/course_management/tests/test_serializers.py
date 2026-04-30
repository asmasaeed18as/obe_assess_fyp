from django.contrib.auth import get_user_model
from django.test import TestCase

from course_management.models import (
    CLO,
    Course,
    CourseEnrollment,
    CourseSection,
    Department,
    Program,
    Semester,
    StudentBatch,
)
from course_management.serializers import (
    CLOSerializer,
    CourseEnrollmentSerializer,
    CourseSectionSerializer,
    DepartmentSerializer,
)


User = get_user_model()


class CourseManagementSerializerTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            email="teacher@test.com",
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
        self.course = Course.objects.create(code="CS-402", title="Software Design")
        self.section = CourseSection.objects.create(
            semester=self.semester,
            course=self.course,
            section_name="A",
            instructor=self.instructor,
        )
        self.enrollment = CourseEnrollment.objects.create(
            section=self.section,
            user=self.student,
            role="student",
        )
        self.clo = CLO.objects.create(
            course=self.course,
            code="CLO-1",
            text="Design maintainable systems",
            bloom_level="C-3",
            mapped_plos=["PLO-1"],
        )

    def test_course_section_serializer_includes_derived_fields(self):
        data = CourseSectionSerializer(self.section).data

        self.assertEqual(data["course_code"], "CS-402")
        self.assertEqual(data["course_title"], "Software Design")
        self.assertEqual(data["instructor_name"], "teacher@test.com")

    def test_department_serializer_includes_nested_program_tree(self):
        data = DepartmentSerializer(self.department).data

        self.assertEqual(data["name"], "SEECS")
        self.assertEqual(len(data["programs"]), 1)
        self.assertEqual(data["programs"][0]["name"], "BSCS")
        self.assertEqual(data["programs"][0]["batches"][0]["name"], "BSCS-13")

    def test_course_enrollment_serializer_includes_section_details_and_user(self):
        data = CourseEnrollmentSerializer(self.enrollment).data

        self.assertEqual(data["role"], "student")
        self.assertEqual(data["user"]["email"], "student@test.com")
        self.assertEqual(data["section_details"]["course_code"], "CS-402")

    def test_clo_serializer_exposes_expected_fields(self):
        data = CLOSerializer(self.clo).data

        self.assertEqual(data["code"], "CLO-1")
        self.assertEqual(data["bloom_level"], "C-3")
        self.assertEqual(data["mapped_plos"], ["PLO-1"])

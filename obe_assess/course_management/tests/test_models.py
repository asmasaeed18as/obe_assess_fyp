from django.contrib.auth import get_user_model
from django.test import TestCase

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
    generate_enrollment_code,
)


User = get_user_model()


class CourseManagementModelTests(TestCase):
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
        self.course = Course.objects.create(code="CS-416", title="Large Language Models")

    def test_generate_enrollment_code_returns_six_character_code(self):
        code = generate_enrollment_code()

        self.assertEqual(len(code), 6)
        self.assertTrue(code.isalnum())

    def test_department_string_representation(self):
        self.assertEqual(str(self.department), "SEECS")

    def test_program_string_representation(self):
        self.assertEqual(str(self.program), "BSCS (SEECS)")

    def test_student_batch_string_representation(self):
        self.assertEqual(str(self.batch), "BSCS-13")

    def test_semester_string_representation(self):
        self.assertEqual(str(self.semester), "Spring 2026 - BSCS-13")

    def test_course_string_representation(self):
        self.assertEqual(str(self.course), "CS-416 Large Language Models")

    def test_course_section_defaults_and_string_representation(self):
        section = CourseSection.objects.create(
            semester=self.semester,
            course=self.course,
            section_name="Section A",
            instructor=self.instructor,
        )

        self.assertEqual(len(section.enrollment_code), 6)
        self.assertIn("CS-416-Section A", str(section))

    def test_course_enrollment_unique_pair(self):
        section = CourseSection.objects.create(
            semester=self.semester,
            course=self.course,
            section_name="Section A",
            instructor=self.instructor,
        )
        enrollment = CourseEnrollment.objects.create(
            section=section,
            user=self.student,
            role="student",
        )

        self.assertEqual(enrollment.role, "student")
        self.assertEqual(CourseEnrollment.objects.count(), 1)

    def test_course_outline_string_representation(self):
        outline = CourseOutline(course=self.course)

        self.assertEqual(str(outline), "Outline for CS-416")

    def test_clo_string_representation(self):
        clo = CLO.objects.create(
            course=self.course,
            code="CLO-1",
            text="Apply testing techniques",
        )

        self.assertEqual(str(clo), "CS-416 - CLO-1")

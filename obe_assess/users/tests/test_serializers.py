from django.contrib.auth import get_user_model
from django.test import TestCase

from course_management.models import (
    Course,
    CourseEnrollment,
    CourseSection,
    Department,
    Program,
    Semester,
    StudentBatch,
)
from users.serializers import (
    AdminRegisterSerializer,
    DashboardDataSerializer,
    RegisterSerializer,
    UserSerializer,
)


User = get_user_model()


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com",
            password="secret123",
            username="user1",
            first_name="Ali",
            last_name="Khan",
            role="student",
        )

    def test_user_serializer_exposes_expected_fields(self):
        data = UserSerializer(self.user).data

        self.assertEqual(
            set(data.keys()),
            {"id", "email", "username", "first_name", "last_name", "role", "is_staff", "date_joined"},
        )
        self.assertEqual(data["email"], "user@test.com")

    def test_register_serializer_creates_user_with_hashed_password(self):
        serializer = RegisterSerializer(
            data={
                "email": "new@test.com",
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "role": "instructor",
                "password": "secret123",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.role, "instructor")
        self.assertTrue(user.check_password("secret123"))

    def test_admin_register_serializer_creates_admin_user(self):
        serializer = AdminRegisterSerializer(
            data={
                "email": "admin2@test.com",
                "username": "admin2",
                "first_name": "Admin",
                "last_name": "User",
                "password": "secret123",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class DashboardDataSerializerTests(TestCase):
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
        self.course = Course.objects.create(code="CS-201", title="OOP")
        self.section = CourseSection.objects.create(
            semester=self.semester,
            course=self.course,
            section_name="A",
            instructor=self.instructor,
        )
        CourseEnrollment.objects.create(section=self.section, user=self.student, role="student")

    def test_dashboard_serializer_returns_instructor_courses(self):
        data = DashboardDataSerializer(self.instructor).data

        self.assertEqual(data["role"], "instructor")
        self.assertEqual(len(data["courses"]), 1)
        self.assertEqual(data["courses"][0]["role_in_course"], "instructor")
        self.assertEqual(data["courses"][0]["students_count"], 1)

    def test_dashboard_serializer_returns_student_courses(self):
        data = DashboardDataSerializer(self.student).data

        self.assertEqual(data["role"], "student")
        self.assertEqual(len(data["courses"]), 1)
        self.assertEqual(data["courses"][0]["role_in_course"], "student")
        self.assertEqual(data["courses"][0]["code"], "CS-201")

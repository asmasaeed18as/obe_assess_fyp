from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from course_management.models import (
    Course,
    CourseEnrollment,
    CourseSection,
    Department,
    Program,
    Semester,
    StudentBatch,
)


User = get_user_model()


class UserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="secret123",
            role="admin",
            is_staff=True,
        )
        self.instructor = User.objects.create_user(
            email="teacher@test.com",
            password="secret123",
            role="instructor",
            first_name="Ayesha",
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            password="secret123",
            role="student",
            first_name="Ali",
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
        self.course = Course.objects.create(code="CS-305", title="Software Testing")
        self.section = CourseSection.objects.create(
            semester=self.semester,
            course=self.course,
            section_name="A",
            instructor=self.instructor,
        )
        CourseEnrollment.objects.create(
            section=self.section,
            user=self.student,
            role="student",
        )
        self.register_payload = {
            "email": "new_instructor@test.com",
            "password": "securepass123",
            "first_name": "New",
            "last_name": "Teacher",
            "role": "instructor",
        }

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_public_register_creates_user(self):
        response = self.client.post(reverse("register"), self.register_payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new_instructor@test.com").exists())
        self.assertIn("account created successfully", response.data["message"])

    def test_register_rejects_duplicate_email(self):
        payload = self.register_payload.copy()
        payload["email"] = "student@test.com"

        response = self.client.post(reverse("register"), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_admin_creates_admin(self):
        response = self.client.post(
            reverse("register-admin"),
            {
                "email": "newadmin@test.com",
                "password": "securepass123",
                "first_name": "Root",
                "last_name": "User",
                "username": "root1",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(email="newadmin@test.com")
        self.assertEqual(created.role, "admin")
        self.assertTrue(created.is_staff)

    def test_login_returns_tokens_and_user_payload(self):
        response = self.client.post(
            reverse("login"),
            {"email": "teacher@test.com", "password": "secret123"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["role"], "instructor")
        self.assertEqual(response.data["user"]["email"], "teacher@test.com")

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {"email": "teacher@test.com", "password": "wrong-pass"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(reverse("logout"), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_refresh_token(self):
        self.authenticate(self.student)

        response = self.client.post(reverse("logout"), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Refresh token required.")

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post(
            reverse("login"),
            {"email": "student@test.com", "password": "secret123"},
        )
        refresh = login.data["refresh"]
        self.authenticate(self.student)

        response = self.client.post(reverse("logout"), {"refresh": refresh})

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_profile_view_returns_current_user(self):
        self.authenticate(self.student)

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "student@test.com")

    def test_profile_view_updates_current_user(self):
        self.authenticate(self.student)

        response = self.client.patch(
            reverse("me"),
            {"first_name": "Updated", "last_name": "Name"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, "Updated")

    def test_change_password_rejects_wrong_old_password(self):
        self.authenticate(self.student)

        response = self.client.post(
            reverse("change-password"),
            {"old_password": "wrong", "new_password": "newsecret123"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Current password is incorrect.")

    def test_change_password_rejects_short_new_password(self):
        self.authenticate(self.student)

        response = self.client.post(
            reverse("change-password"),
            {"old_password": "secret123", "new_password": "123"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "New password must be at least 6 characters.")

    def test_change_password_updates_password(self):
        self.authenticate(self.student)

        response = self.client.post(
            reverse("change-password"),
            {"old_password": "secret123", "new_password": "newsecret123"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("newsecret123"))

    def test_user_list_requires_admin_role(self):
        self.authenticate(self.student)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.authenticate(self.admin)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_dashboard_data_requires_authentication(self):
        response = self.client.get(reverse("dashboard_data"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_data_returns_student_courses(self):
        self.authenticate(self.student)

        response = self.client.get(reverse("dashboard_data"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "student")
        self.assertEqual(len(response.data["courses"]), 1)
        self.assertEqual(response.data["courses"][0]["code"], "CS-305")

    def test_dashboard_data_returns_instructor_courses(self):
        self.authenticate(self.instructor)

        response = self.client.get(reverse("dashboard_data"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "instructor")
        self.assertEqual(len(response.data["courses"]), 1)
        self.assertEqual(response.data["courses"][0]["role_in_course"], "instructor")

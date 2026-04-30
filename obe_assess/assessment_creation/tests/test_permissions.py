from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from assessment_creation.permissions import IsInstructor


User = get_user_model()


class IsInstructorPermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsInstructor()
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="secret123",
            role="instructor",
        )
        self.student = User.objects.create_user(
            email="student@test.com",
            password="secret123",
            role="student",
        )

    def test_permission_allows_authenticated_instructor(self):
        request = self.factory.get("/api/assessment/generate/")
        request.user = self.instructor

        self.assertTrue(self.permission.has_permission(request, None))

    def test_permission_denies_authenticated_non_instructor(self):
        request = self.factory.get("/api/assessment/generate/")
        request.user = self.student

        self.assertFalse(self.permission.has_permission(request, None))

    def test_permission_denies_anonymous_user(self):
        request = self.factory.get("/api/assessment/generate/")
        request.user = AnonymousUser()

        self.assertFalse(self.permission.has_permission(request, None))

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from course_management.views import (
    _normalize_bloom_level,
    _normalize_clo_code,
    _normalize_mapped_plos,
    get_user_or_mock,
)


User = get_user_model()


class CourseManagementHelperTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email="first@test.com",
            password="secret123",
            role="student",
        )

    def test_get_user_or_mock_returns_authenticated_user(self):
        request = self.factory.get("/api/courses/")
        request.user = self.user

        self.assertEqual(get_user_or_mock(request), self.user)

    def test_get_user_or_mock_returns_first_user_for_anonymous_request(self):
        request = self.factory.get("/api/courses/")
        request.user = AnonymousUser()

        self.assertEqual(get_user_or_mock(request), self.user)

    def test_normalize_clo_code_handles_standard_patterns(self):
        self.assertEqual(_normalize_clo_code("clo 3", 1), "CLO-3")
        self.assertEqual(_normalize_clo_code("4", 1), "CLO-4")
        self.assertEqual(_normalize_clo_code("", 2), "CLO-2")

    def test_normalize_bloom_level_handles_prefixed_and_blank_values(self):
        self.assertEqual(_normalize_bloom_level("c 2"), "C-2")
        self.assertEqual(_normalize_bloom_level("  "), "")
        self.assertEqual(_normalize_bloom_level("Remembering"), "Remembering")

    def test_normalize_mapped_plos_normalizes_and_deduplicates_values(self):
        result = _normalize_mapped_plos(
            ["PLO(SE)-1", "PLO(CS)-2", "PLO-3", "plo(se)-1", "4", "Random PLO"]
        )

        self.assertEqual(result, ["PLO(SE)-1", "PLO(CS)-2", "PLO-3", "PLO-4"])

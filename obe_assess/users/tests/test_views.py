from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterViewSecurityTests(APITestCase):
    def setUp(self):
        """Set up the testing environment with different user roles."""
        # 1. Create an Admin User (The one who SHOULD have access)
        self.admin_user = User.objects.create_user(
            email='admin@seecs.edu.pk',
            password='adminpassword123',
            role='admin'
        )
        
        # 2. Create a Student User (The one who SHOULD be blocked)
        self.student_user = User.objects.create_user(
            email='student@seecs.edu.pk',
            password='studentpassword123',
            role='student'
        )
        
        # 3. The exact payload we want to send to create a new instructor
        self.valid_payload = {
            "email": "new_instructor@seecs.edu.pk",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "Teacher",
            "role": "instructor"
        }
        
        # This matches the name="register" you set in users/urls.py
        self.register_url = reverse('register')

    def test_unauthenticated_user_cannot_register(self):
        """Ensure an anonymous user gets a 401/403 when trying to register someone."""
        # We DO NOT authenticate the client here
        response = self.client.post(self.register_url, self.valid_payload)
        
        # Should be Forbidden (403) or Unauthorized (401)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_register_users(self):
        """Ensure a logged-in student gets a 403 Forbidden when trying to access the endpoint."""
        # Force authenticate as the student
        self.client.force_authenticate(user=self.student_user)
        
        response = self.client.post(self.register_url, self.valid_payload)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Verify the specific error message your custom IsAdminRole throws
        self.assertIn("You do not have permission", str(response.data))

    def test_admin_can_register_users(self):
        """Ensure a logged-in admin successfully creates a user and gets a 201 response."""
        # Force authenticate as the Admin
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(self.register_url, self.valid_payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3) # Admin, Student, and the newly created user
        
        # Verify the success message we coded into your views.py earlier
        self.assertIn("account created successfully!", response.data.get("message", ""))

    def test_admin_cannot_register_duplicate_email(self):
        """Ensure the API catches validation errors (like duplicate emails) even for admins."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Try to register a user with an email that already exists (the student's email)
        bad_payload = self.valid_payload.copy()
        bad_payload["email"] = "student@seecs.edu.pk"
        
        response = self.client.post(self.register_url, bad_payload)
        
        # Should throw a 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data) # The error should mention the email field
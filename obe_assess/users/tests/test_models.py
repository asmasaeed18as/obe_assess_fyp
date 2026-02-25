# users/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserTests(TestCase):
    def test_create_instructor(self):
        """Ensure instructors are created successfully with hashed passwords."""
        user = User.objects.create_user(
            username='dr_faisal',
            email='faisal@test.com',
            password='securepassword123'
        )
        user.role = 'instructor'
        user.save()

        # Check basic fields
        self.assertEqual(user.username, 'dr_faisal')
        self.assertEqual(user.role, 'instructor')
        self.assertTrue(user.is_active)
        
        # Security Check: Ensure password is NOT stored in plain text
        self.assertNotEqual(user.password, 'securepassword123')
        self.assertTrue(user.check_password('securepassword123'))
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserTests(TestCase):

    def test_create_standard_user(self):
        """Test creating a standard user (defaults to student role)."""
        user = User.objects.create_user(
            email='student@seecs.edu.pk',
            password='securepassword123',
            first_name='Ali',
            last_name='Khan'
        )
        
        # Check basic fields
        self.assertEqual(user.email, 'student@seecs.edu.pk')
        self.assertEqual(user.first_name, 'Ali')
        self.assertEqual(user.role, 'student') # Should default to student
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        
        # Security Check: Ensure password is hashed
        self.assertNotEqual(user.password, 'securepassword123')
        self.assertTrue(user.check_password('securepassword123'))

    def test_create_instructor(self):
        """Test creating an instructor by passing extra fields."""
        # Because your UserManager accepts **extra_fields, you can pass role directly!
        user = User.objects.create_user(
            email='faisal@test.com',
            password='securepassword123',
            username='dr_faisal',
            role='instructor' 
        )

        self.assertEqual(user.username, 'dr_faisal')
        self.assertEqual(user.role, 'instructor')
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        """Test creating a superuser with the custom manager."""
        admin_user = User.objects.create_superuser(
            email='admin@seecs.edu.pk',
            password='supersecretadmin',
            role='admin'
        )
        
        self.assertEqual(admin_user.email, 'admin@seecs.edu.pk')
        self.assertEqual(admin_user.role, 'admin')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_create_user_without_email_raises_error(self):
        """Test that the UserManager correctly blocks users without an email."""
        with self.assertRaisesMessage(ValueError, "Users must have an email address"):
            User.objects.create_user(
                email='', 
                password='securepassword123'
            )

    def test_create_superuser_with_is_staff_false_raises_error(self):
        """Test that a superuser cannot be created with is_staff=False."""
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email='fakeadmin@seecs.edu.pk',
                password='password123',
                is_staff=False
            )

    def test_user_string_representation(self):
        """Test the __str__ method of the User model."""
        user = User.objects.create_user(
            email='test@example.com',
            password='password123'
        )
        self.assertEqual(str(user), 'test@example.com')

    def test_email_is_normalized_on_create_user(self):
        user = User.objects.create_user(
            email='Student@SEECS.edu.pk',
            password='password123'
        )

        self.assertEqual(user.email, 'Student@seecs.edu.pk')

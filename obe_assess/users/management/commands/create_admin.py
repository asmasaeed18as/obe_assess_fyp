from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from users.models import User


class Command(BaseCommand):
    help = 'Create an admin user'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Admin email address')
        parser.add_argument('--password', type=str, help='Admin password')
        parser.add_argument('--first-name', type=str, default='Admin', help='Admin first name')
        parser.add_argument('--last-name', type=str, default='User', help='Admin last name')

    def handle(self, *args, **options):
        email = options.get('email')
        password = options.get('password')
        first_name = options.get('first_name')
        last_name = options.get('last_name')

        if not email:
            email = input('Enter admin email: ').strip()
        if not password:
            password = input('Enter admin password: ').strip()

        if not email or not password:
            self.stdout.write(self.style.ERROR('Email and password are required'))
            return

        try:
            # Check if user already exists (idempotent)
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'Admin user already exists: {email}'))
                return

            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='admin'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user: {user.email}')
            )
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f'Validation Error: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

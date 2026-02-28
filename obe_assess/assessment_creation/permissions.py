# assessment_creation/permissions.py
from rest_framework.permissions import BasePermission

class IsInstructor(BasePermission):
    """
    Allows access only to authenticated users who have the 'instructor' role.
    """
    def has_permission(self, request, view):
        # 1. Check if the user is logged in
        # 2. Check if their role is exactly 'instructor'
        return bool(
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, 'role', '') == 'instructor'
        )
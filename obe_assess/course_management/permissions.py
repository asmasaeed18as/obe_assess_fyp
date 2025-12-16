# course_management/permissions.py
from rest_framework import permissions

class IsAdminOrQA(permissions.BasePermission):
    """
    Custom permission to only allow Admins or QA users to create courses.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Check if user role is 'admin' or 'qa'
        return request.user.role in ['admin', 'qa'] or request.user.is_superuser
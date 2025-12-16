# course_management/urls.py
from django.urls import path
from .views import (
    CourseCreateView, 
    CourseListView, 
    CourseDetailView, 
    EnrollSelfView, 
    UploadOutlineView, 
    ListCourseCLOsView,
    CLOUpdateView
)

urlpatterns = [
    # List all courses (GET)
    path("", CourseListView.as_view(), name="course-list"),
    
    # Create course (POST) - Admin/QA only
    path("create/", CourseCreateView.as_view(), name="course-create"),
    
    # Course Detail (GET)
    path("<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
    
    # Enroll (POST)
    path("<int:course_id>/enroll/", EnrollSelfView.as_view(), name="enroll-self"),
    
    # Upload Outline (POST)
    path("<int:course_id>/upload-outline/", UploadOutlineView.as_view(), name="upload-outline"),
    
    # Get CLOs (GET)
    path("<int:course_id>/clos/", ListCourseCLOsView.as_view(), name="course-clos"),
    # ✅ NEW: Route for Editing a CLO (uses UUID because your model uses uuid)
    path("clo/<uuid:pk>/", CLOUpdateView.as_view(), name="clo-update"),
]
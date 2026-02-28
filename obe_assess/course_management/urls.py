from django.urls import path
from .views import (
    # Admin / Hierarchy
    LMSHierarchyView,
    ResourceListView,
    SectionCreateView,
    CourseCreateView,
    # Student / Enrollment
    JoinSectionView,
    MyEnrollmentsView,
    
    # Content / CLOs
    CourseListView,
    CourseDetailView, # âœ… IMPORT THE NEW VIEW
    CourseDetailBySectionView,
    CourseCLOAnalyticsView,
    UploadOutlineView,
    UploadOutlineBySectionView,
    ListCourseCLOsView,
    ListSectionCLOsView,
    CLOUpdateView
)

urlpatterns = [
    # --- Admin Dashboard Routes ---
    path("hierarchy/", LMSHierarchyView.as_view(), name="lms-hierarchy"), # Tree Data
    path("resources/", ResourceListView.as_view(), name="lms-resources"), # Dropdowns
    path("sections/create/", SectionCreateView.as_view(), name="section-create"), # Register Teacher
    path('courses/create/', CourseCreateView.as_view(), name='course-create-admin'),
    # --- Student Routes ---
    path("join/", JoinSectionView.as_view(), name="student-join"), # Join via Code
    path("my-enrollments/", MyEnrollmentsView.as_view(), name="my-enrollments"), # Dashboard List
    
    # --- Generic Course & Content Routes ---
    path("courses/", CourseListView.as_view(), name="course-list"), # Catalog
    # Course details by section UUID
    path("courses/<uuid:section_id>/", CourseDetailBySectionView.as_view(), name="course-detail-by-section"),
    # âœ… ADD THIS NEW PATH RIGHT HERE:
    path("courses/<int:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path("courses/<int:pk>/analytics/clo/", CourseCLOAnalyticsView.as_view(), name="course-clo-analytics"),
    # CLO & Outline (Linked to Generic Course ID)
    path("courses/<uuid:section_id>/upload-outline/", UploadOutlineBySectionView.as_view(), name="upload-outline-by-section"),
    path("courses/<int:course_id>/upload-outline/", UploadOutlineView.as_view(), name="upload-outline"),
    path("courses/<int:course_id>/clos/", ListCourseCLOsView.as_view(), name="course-clos"),
    path("courses/<uuid:section_id>/clos/", ListSectionCLOsView.as_view(), name="section-clos"),
    path("clo/<uuid:pk>/", CLOUpdateView.as_view(), name="clo-update"),
]

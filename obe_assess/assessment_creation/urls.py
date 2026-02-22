from django.urls import path
from .views import (
    UploadMaterialAndGenerateAssessment, 
    DownloadSpecificAssessment, 
    CourseAssessmentListView,
    DownloadAssessmentZip  # <--- MAKE SURE THIS IS IMPORTED
)

urlpatterns = [
    # 1. Generate Assessment
    path('generate/', UploadMaterialAndGenerateAssessment.as_view(), name='generate_assessment'),
    
    # 2. Download ZIP Bundle (The missing one causing your 404)
    path('download-zip/<uuid:assessment_id>/<str:file_format>/', 
         DownloadAssessmentZip.as_view(), 
         name='download_zip'),

    # 3. Download Single File (Legacy/Optional)
    path('download/<uuid:assessment_id>/<str:content_type>/<str:file_format>/', 
         DownloadSpecificAssessment.as_view(), 
         name='download_specific'),
    path('course/<int:course_id>/', CourseAssessmentListView.as_view(), name='course_assessments'),
]
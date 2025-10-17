# assessment_creation/urls.py
from django.urls import path
from .views import UploadMaterialAndGenerateAssessment

urlpatterns = [
    path("generate/", UploadMaterialAndGenerateAssessment.as_view(), name="generate_assessment"),
]

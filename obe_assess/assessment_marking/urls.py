from django.urls import path
from .views import GradeAssessmentView

urlpatterns = [
    path('grade/', GradeAssessmentView.as_view(), name='grade_assessment'),
]
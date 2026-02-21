from django.urls import path
from .views import GradeAssessmentView, GradedSubmissionDetailView

urlpatterns = [
    path('grade/', GradeAssessmentView.as_view(), name='grade_assessment'),
    path('grade/<uuid:submission_id>/', GradedSubmissionDetailView.as_view(), name='graded_submission_detail'),
]

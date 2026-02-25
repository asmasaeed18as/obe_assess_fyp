from django.urls import path
from .views import GradeAssessmentView, GradedSubmissionDetailView, GradedSubmissionCLOAnalyticsView

urlpatterns = [
    path('grade/', GradeAssessmentView.as_view(), name='grade_assessment'),
    path('grade/<uuid:submission_id>/', GradedSubmissionDetailView.as_view(), name='graded_submission_detail'),
    path('grade/<uuid:submission_id>/analytics/clo/', GradedSubmissionCLOAnalyticsView.as_view(), name='graded_submission_clo_analytics'),
]


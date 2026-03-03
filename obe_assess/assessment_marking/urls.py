from django.urls import path
from .views import GradeAssessmentView, GradedSubmissionDetailView, GradedSubmissionCLOAnalyticsView, CourseSubmissionsDeleteView

urlpatterns = [
    path('grade/', GradeAssessmentView.as_view(), name='grade_assessment'),
    path('grade/<uuid:submission_id>/', GradedSubmissionDetailView.as_view(), name='graded_submission_detail'),
    path('grade/<uuid:submission_id>/analytics/clo/', GradedSubmissionCLOAnalyticsView.as_view(), name='graded_submission_clo_analytics'),
    path('course/<int:course_id>/submissions/', CourseSubmissionsDeleteView.as_view(), name='course_submissions_delete'),
]



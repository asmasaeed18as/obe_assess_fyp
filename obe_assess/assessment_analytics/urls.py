from django.urls import path
from .views import SubmissionCLOAnalyticsView, BatchSubmissionCLOAnalyticsView

urlpatterns = [
    path('submission/<uuid:submission_id>/clo/', SubmissionCLOAnalyticsView.as_view(), name='submission_clo_analytics'),
    path('submissions/clo/', BatchSubmissionCLOAnalyticsView.as_view(), name='batch_submission_clo_analytics'),
]

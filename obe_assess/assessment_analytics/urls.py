from django.urls import path
from .views import SubmissionCLOAnalyticsView

urlpatterns = [
    path('submission/<uuid:submission_id>/clo/', SubmissionCLOAnalyticsView.as_view(), name='submission_clo_analytics'),
]

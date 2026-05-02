from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.GenerateAssessmentView.as_view(), name='generate_assessment'),
    path('mark/', views.MarkQuestionView.as_view(), name='mark_question'),
]

import uuid
from django.db import models
from django.conf import settings

def grading_upload_to(instance, filename):
    return f"grading/{instance.id}/{filename}"

class GradedSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey('course_management.Course', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255, default="Assessment Grading")
    
    student_file = models.FileField(upload_to=grading_upload_to)
    rubric_file = models.FileField(upload_to=grading_upload_to)
    
    ai_result_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Grading {self.id}"
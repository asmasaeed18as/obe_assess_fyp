# assessment_creation/models.py
import uuid
from django.db import models
from django.conf import settings

def assessment_upload_to(instance, filename):
    return f"assessments/{instance.id}/{filename}"

class LectureMaterial(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="materials/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # optional: store extracted text or other metadata
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material = models.ForeignKey(LectureMaterial, on_delete=models.CASCADE, related_name='assessments')
    clo = models.CharField(max_length=512)
    bloom_level = models.CharField(max_length=50)
    assessment_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    # store the structured JSON the LLM returned (questions, rubrics, answers)
    result_json = models.JSONField(blank=True, null=True)

    # store generated PDF file
    pdf = models.FileField(upload_to=assessment_upload_to, blank=True, null=True)

    def __str__(self):
        return f"Assessment {self.id} - {self.assessment_type}"

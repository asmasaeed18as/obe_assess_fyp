import uuid
from django.db import models
from django.conf import settings

def assessment_upload_to(instance, filename):
    return f"assessments/{instance.id}/{filename}"

class LectureMaterial(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="materials/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Stores extracted text from the PDF to avoid re-processing
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material = models.ForeignKey(LectureMaterial, on_delete=models.CASCADE, related_name='assessments')
    
    # The type of assessment (Quiz, Exam, Assignment, etc.)
    assessment_type = models.CharField(max_length=50)

    # ✅ NEW: Stores the specific configuration for each question 
    # (e.g. [{"id":1, "clo":"CLO-1", "weightage":"5", ...}])
    questions_config = models.JSONField(default=list, blank=True)

    # Modified: These are now optional or used for summary/tags since detailed info is in questions_config
    clo = models.CharField(max_length=512, blank=True, null=True)
    bloom_level = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    # Stores the structured JSON the LLM returned (questions, rubrics, answers)
    result_json = models.JSONField(blank=True, null=True)

    # Stores the generated PDF file
    pdf = models.FileField(upload_to=assessment_upload_to, blank=True, null=True)

    def __str__(self):
        return f"Assessment {self.id} - {self.assessment_type}"
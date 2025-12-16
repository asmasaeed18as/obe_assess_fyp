import uuid
from django.db import models
from django.conf import settings

def assessment_upload_to(instance, filename):
    return f"assessments/{instance.id}/{filename}"

class LectureMaterial(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="materials/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ✅ NEW: Link Assessment to a specific Course
    # We use a string reference to avoid circular imports with course_management app
    course = models.ForeignKey(
        'course_management.Course', 
        on_delete=models.CASCADE, 
        related_name='assessments',
        null=True, 
        blank=True
    )

    material = models.ForeignKey(LectureMaterial, on_delete=models.CASCADE, related_name='assessments')
    assessment_type = models.CharField(max_length=50)
    
    # Stores specific config: [{"id":1, "clo":"CLO-1", "weightage":"5"}]
    questions_config = models.JSONField(default=list, blank=True)

    # Summaries
    clo = models.CharField(max_length=512, blank=True, null=True)
    bloom_level = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    # Stores the LLM result
    result_json = models.JSONField(blank=True, null=True)

    # Generated PDF
    pdf = models.FileField(upload_to=assessment_upload_to, blank=True, null=True)

    def __str__(self):
        return f"Assessment {self.id} - {self.assessment_type}"
from django.db import models
from django.conf import settings
import uuid
import os

def outline_upload_to(instance, filename):
    return f"course_outlines/{instance.course.id}/{filename}"

class Course(models.Model):
    code = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} — {self.title}"

class CourseEnrollment(models.Model):
    ROLE_CHOICES = (("instructor","Instructor"), ("student","Student"))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_enrollments")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "user", "role")

    def __str__(self):
        return f"{self.user.email} as {self.role} in {self.course.code}"

class CourseOutline(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="outlines")
    file = models.FileField(upload_to=outline_upload_to)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Outline for {self.course.code} ({self.uploaded_at.date()})"

class CLO(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="clos")
    code = models.CharField(max_length=64, blank=True)
    text = models.TextField()
    bloom_level = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("course", "code", "text")

    def __str__(self):
        return f"{self.course.code} - {self.code or '[no-code]'}"

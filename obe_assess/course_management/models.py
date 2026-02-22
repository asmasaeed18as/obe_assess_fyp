from django.db import models
from django.conf import settings
import uuid
import random
import string

# --- Helper Functions ---
def generate_enrollment_code():
    """Generates a unique 6-character alphanumeric code (e.g., X7k9Pz)"""
    length = 6
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not CourseSection.objects.filter(enrollment_code=code).exists():
            return code

# --- 1. Department (e.g., SEECS, SMME) ---
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True) # e.g., "SEECS"
    full_name = models.CharField(max_length=255, blank=True) # "School of Electrical..."

    def __str__(self):
        return self.name

# --- 2. Program (e.g., BESE, BSCS) ---
class Program(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="programs")
    name = models.CharField(max_length=100) # e.g., "BESE"
    full_name = models.CharField(max_length=255) # "Bachelors of Software Engineering"

    class Meta:
        unique_together = ('department', 'name')

    def __str__(self):
        return f"{self.name} ({self.department.name})"

# --- 3. Batch/Intake (e.g., BESE-13 Fall 2022) ---
class StudentBatch(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="batches")
    name = models.CharField(max_length=100) # e.g., "BESE-13 (Fall 2022 Intake)"
    start_year = models.IntegerField() # e.g., 2022

    class Meta:
        ordering = ['-start_year'] # Newest batches first

    def __str__(self):
        return self.name

# --- 4. Semester (e.g., 8th Semester SP-2026) ---
class Semester(models.Model):
    batch = models.ForeignKey(StudentBatch, on_delete=models.CASCADE, related_name="semesters")
    name = models.CharField(max_length=100) # e.g., "8th Semester (SP-2026)"
    is_active = models.BooleanField(default=True) # Only current semesters are active

    def __str__(self):
        return f"{self.name} - {self.batch.name}"

# --- 5. Catalog Course (Generic Subject) ---
class Course(models.Model):
    """The generic subject catalog (e.g., CS-402)"""
    code = models.CharField(max_length=32, unique=True) # e.g., "CS-402"
    title = models.CharField(max_length=255)            # e.g., "Community Service Learning"
    credit_hours = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.code} {self.title}"

# --- 6. The Class / Section (Where Enrollment Happens) ---
class CourseSection(models.Model):
    """
    The actual class instance linked to a specific Semester.
    Teacher is assigned HERE. Code is generated HERE.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="sections")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    
    # e.g., "Section A", "Section 12B"
    section_name = models.CharField(max_length=50, default="Section A") 
    
    # The Instructor assigned by Admin
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'instructor'},
        related_name="teaching_sections"
    )
    
    # The Auto-Generated Code for Students
    enrollment_code = models.CharField(
        max_length=8, 
        unique=True, 
        default=generate_enrollment_code,
        editable=False
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("semester", "course", "section_name")

    def __str__(self):
        return f"{self.course.code}-{self.section_name} ({self.semester.name})"

# --- 7. Enrollment ---
class CourseEnrollment(models.Model):
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    role = models.CharField(max_length=20, default="student")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("section", "user")
        
# ... (your existing code ends here)

# --- 8. Course Outline (Uploaded File) ---
class CourseOutline(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Linked to the Generic Course (e.g., CS-101) so it works for all sections
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="outlines")
    file = models.FileField(upload_to="course_outlines/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Outline for {self.course.code}"

# --- 9. CLOs (Course Learning Outcomes) ---
class CLO(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="clos")
    code = models.CharField(max_length=64, blank=True)
    text = models.TextField()
    bloom_level = models.CharField(max_length=20, blank=True, null=True)
    mapped_plos = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.course.code} - {self.code}"
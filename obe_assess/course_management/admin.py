from django.contrib import admin
from .models import (
    Department, Program, StudentBatch, Semester, 
    Course, CourseSection, CourseEnrollment, 
    CourseOutline, CLO
)

# --- Hierarchy Management ---
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name")

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "department")
    list_filter = ("department",)

@admin.register(StudentBatch)
class StudentBatchAdmin(admin.ModelAdmin):
    list_display = ("name", "program", "start_year")
    list_filter = ("program",)

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "batch", "is_active")
    list_filter = ("is_active", "batch")

# --- Course & Content ---
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "credit_hours")
    search_fields = ("code", "title")

@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ("course", "section_name", "semester", "instructor", "enrollment_code")
    list_filter = ("semester", "course")
    readonly_fields = ("enrollment_code",)

@admin.register(CourseEnrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    # ✅ FIX: Changed 'course' to 'section'
    list_display = ("user", "section", "role", "enrolled_at")
    list_filter = ("role", "section")

@admin.register(CourseOutline)
class OutlineAdmin(admin.ModelAdmin):
    list_display = ("course", "uploaded_by", "uploaded_at")

@admin.register(CLO)
class CLOAdmin(admin.ModelAdmin):
    list_display = ("course", "code", "bloom_level", "created_at")
    search_fields = ("text", "code")
from django.contrib import admin
from .models import Course, CourseEnrollment, CourseOutline, CLO

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code","title","created_at")
    search_fields = ("code","title")

@admin.register(CourseEnrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("course","user","role","enrolled_at")
    list_filter = ("role","course")

@admin.register(CourseOutline)
class OutlineAdmin(admin.ModelAdmin):
    list_display = ("course","uploaded_by","uploaded_at")

@admin.register(CLO)
class CLOAdmin(admin.ModelAdmin):
    list_display = ("course","code","bloom_level","created_at")
    search_fields = ("text","code")

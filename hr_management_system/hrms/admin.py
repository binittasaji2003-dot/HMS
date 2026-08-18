from django.contrib import admin
from .models import (
    Announcement,
    Candidate,
    Department,
    Employee,
    EmployeePerformance,
    HRManager,
    JobVacancy,
    PerformanceWarning,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    search_fields = ("name", "description")
    list_filter = ("status",)


@admin.register(HRManager)
class HRManagerAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "phone", "created_at")
    search_fields = ("user__email", "user__name", "department__name")


@admin.register(JobVacancy)
class JobVacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "openings_count", "status", "created_at")
    list_filter = ("status", "department")
    search_fields = ("title", "description", "requirements")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name", "job_vacancy", "email", "phone", "status", "applied_at")
    list_filter = ("status", "job_vacancy__department")
    search_fields = ("full_name", "email", "phone")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "designation", "status", "date_of_joining")
    list_filter = ("status", "department")
    search_fields = ("user__email", "user__name", "designation")


@admin.register(EmployeePerformance)
class EmployeePerformanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "review_period", "rating", "reviewed_by", "created_at")
    list_filter = ("review_period", "rating")
    search_fields = ("employee__user__email", "employee__user__name", "feedback")


@admin.register(PerformanceWarning)
class PerformanceWarningAdmin(admin.ModelAdmin):
    list_display = ("title", "employee", "severity", "status", "created_at")
    list_filter = ("severity", "status")
    search_fields = ("title", "reason", "employee__user__name")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "target_audience", "is_active", "created_by", "created_at")
    list_filter = ("target_audience", "is_active")
    search_fields = ("title", "content")

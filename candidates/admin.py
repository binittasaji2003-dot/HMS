from django.contrib import admin

from .models import Candidate, JobApplication, JobVacancy


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
	list_display = ("candidate_id", "first_name", "last_name", "user", "profile_completed")
	search_fields = ("first_name", "last_name", "user__email")


@admin.register(JobVacancy)
class JobVacancyAdmin(admin.ModelAdmin):
	list_display = ("title", "department", "status", "posted_date", "closing_date")
	list_filter = ("status", "department")
	search_fields = ("title", "description", "skills_required")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
	list_display = ("application_id", "candidate", "vacancy", "status", "applied_at")
	list_filter = ("status",)
	search_fields = ("candidate__first_name", "candidate__last_name", "vacancy__title")

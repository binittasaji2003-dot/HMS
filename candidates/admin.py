from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Department,
    Job,
    Candidate,
    CandidateEducation,
    CandidateSkill,
    CandidateDocument,
    Application,
    AptitudeTest,
    Question,
    TestResult,
    Interview,
    Notification,
)
from .onboarding import create_employee_record, get_employee_record, is_candidate_onboarded


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at")
    search_fields = ("name", "code")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "job_type", "experience_required", "location", "status", "posted_at")
    list_filter = ("status", "department", "job_type")
    search_fields = ("title", "description", "skills_required")


class CandidateEducationInline(admin.TabularInline):
    model = CandidateEducation
    extra = 1


class CandidateSkillInline(admin.TabularInline):
    model = CandidateSkill
    extra = 1


class CandidateDocumentInline(admin.StackedInline):
    model = CandidateDocument
    can_delete = False


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = (
        "candidate_code",
        "full_name",
        "phone",
        "profile_completion_pct",
        "is_selected_display",
        "is_onboarded_display",
        "created_at",
    )
    search_fields = ("candidate_code", "full_name", "phone", "city")
    list_filter = ("gender", "experience_level")
    inlines = [CandidateEducationInline, CandidateSkillInline, CandidateDocumentInline]

    @admin.display(description="Selected", boolean=True)
    def is_selected_display(self, obj):
        return obj.is_selected

    @admin.display(description="Onboarded", boolean=True)
    def is_onboarded_display(self, obj):
        return obj.is_onboarded


@admin.register(CandidateDocument)
class CandidateDocumentAdmin(admin.ModelAdmin):
    list_display = ("candidate", "verification_status", "uploaded_at")
    list_filter = ("verification_status",)
    search_fields = ("candidate__full_name", "candidate__candidate_code")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "application_code",
        "candidate",
        "job",
        "status",
        "onboarding_status",
        "onboarding_action",
        "applied_at",
    )
    list_filter = ("status", "job__department")
    search_fields = ("application_code", "candidate__full_name", "job__title")
    actions = ["create_employee_record_action"]

    @admin.display(description="Onboarding Status")
    def onboarding_status(self, obj):
        if obj.status != Application.Status.SELECTED:
            return "-"
        emp = get_employee_record(candidate_id=obj.candidate_id, user_id=obj.candidate.user_id)
        if emp:
            return format_html(
                '<span style="color:#20A47A; font-weight:700;">Active ({})</span>',
                emp["employee_code"],
            )
        return format_html('<span style="color:#1976F3; font-weight:700;">Awaiting Onboarding</span>')

    @admin.display(description="Onboarding Action")
    def onboarding_action(self, obj):
        if obj.status == Application.Status.SELECTED:
            url = reverse("candidates:candidate_onboarding_dossier", kwargs={"candidate_id": obj.candidate_id})
            return format_html(
                '<a class="button" style="padding:3px 8px; font-size:11px;" href="{}">View Dossier</a>',
                url,
            )
        return "-"

    @admin.action(description="Onboard Selected Candidates into employee_table")
    def create_employee_record_action(self, request, queryset):
        created_count = 0
        already_count = 0
        for app in queryset:
            if app.status == Application.Status.SELECTED:
                if is_candidate_onboarded(candidate_id=app.candidate_id, user_id=app.candidate.user_id):
                    already_count += 1
                else:
                    create_employee_record(
                        candidate_id=app.candidate_id,
                        user_id=app.candidate.user_id,
                        created_by=request.user.id,
                    )
                    created_count += 1
        messages.success(
            request,
            f"Onboarding processed: {created_count} employee record(s) created in employee_table. ({already_count} already onboarded)",
        )



class QuestionInline(admin.TabularInline):
    model = Question
    extra = 2


@admin.register(AptitudeTest)
class AptitudeTestAdmin(admin.ModelAdmin):
    list_display = ("title", "job", "duration_minutes", "total_questions", "passing_percentage", "status", "is_active")
    list_filter = ("status", "is_active")
    search_fields = ("title", "description")
    filter_horizontal = ("assigned_candidates",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_id", "test", "question_text", "correct_option", "marks")
    list_filter = ("test", "correct_option")
    search_fields = ("question_text",)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ("candidate", "test", "score_percentage", "is_passed", "completed_at")
    list_filter = ("is_passed", "test")
    search_fields = ("candidate__full_name", "test__title")


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ("candidate", "job", "interview_round", "date", "time", "mode", "status")
    list_filter = ("status", "mode", "date")
    search_fields = ("candidate__full_name", "job__title", "interviewer")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "candidate", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read")
    search_fields = ("title", "message", "candidate__full_name")

import json

from admin_module.models import Department, EmployeeApproval, Holiday
from admin_module.models import AdminNotification, Department, EmployeeApproval
from candidates.models import JobApplication, JobVacancy, ResumeScreening, send_candidate_notification
from candidates.screening_service import screen_job_application, run_resume_screening
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from employees.models import (
    Employee,
    EmployeeDocument,
    EmployeePerformance,
    EmployeeReport,
    Notification,
    PerformanceReview as EmployeePerformanceReview,
    PerformanceWarning,
    Team,
)

from .forms import (
    AptitudeQuestionForm,
    AptitudeTestForm,
    EmployeePerformanceEvaluationForm,
    HRDocumentUploadForm,
    HREducationForm,
    HRExperienceForm,
    HRProfileEditForm,
    HRWeeklyReportForm,
    JobVacancyForm,
)
from .models import (
    AptitudeAttempt,
    AptitudeQuestion,
    AptitudeResult,
    AptitudeTest,
    HRDocument,
    HREducation,
    HRExperience,
    HRManager,
    HRNotification,
    HRPerformanceReview,
    HRWeeklyReport,
    Interview,
    InterviewEvaluation,
    InterviewLocation,
    InterviewSlot,
)
from .question_bank import seed_default_questions

User = get_user_model()


class HRRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Enforces access control strictly for HR Managers, Staff, or Superusers."""

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.is_staff
            or getattr(user, "role", "") == "HR"
            or hasattr(user, "hr_profile")
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Access restricted to HR Personnel.")
        return redirect("users:redirect")


class HRDashboardView(HRRequiredMixin, TemplateView):
    template_name = "hr/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        hr_profile = getattr(user, "hr_profile", None)
        if not hr_profile and (getattr(user, "role", "") == User.RoleChoices.HR or user.is_staff or user.is_superuser):
            hr_profile, _ = HRManager.objects.get_or_create(
                user=user,
                defaults={"employee_code": f"HR-{user.id:04d}"},
            )

        if hr_profile:
            is_complete = hr_profile.update_profile_completion_status()
            context["hr_profile"] = hr_profile
            context["profile_completed"] = is_complete
            context["is_profile_incomplete"] = not is_complete
            context["profile_completion_percentage"] = hr_profile.completion_percentage
        else:
            context["profile_completed"] = True
            context["is_profile_incomplete"] = False
            context["profile_completion_percentage"] = 100

        # 1. Metric Counts for Summary Cards
        total_employees = Employee.objects.filter(employment_status="ACTIVE").count()
        pending_reports = EmployeeReport.objects.filter(status="SUBMITTED").count()
        active_warnings = PerformanceWarning.objects.filter(status="OPEN").count()
        escalations = PerformanceWarning.objects.filter(status="SENT_TO_ADMIN").count()

        context["metrics"] = {
            "total_employees": total_employees,
            "pending_reports": pending_reports,
            "active_warnings": active_warnings,
            "escalations": escalations,
        }

        # 2. Recent Work Reports pending HR Review
        context["recent_reports"] = EmployeeReport.objects.select_related("employee__user").order_by("-submitted_at")[:5]

        # 3. Recent Performance Reviews & Ratings
        context["recent_reviews"] = EmployeePerformance.objects.select_related("employee__user").order_by("-review_date")[:5]

        # 4. Performance Warnings / Escalation Pipeline
        holidays = Holiday.objects.filter(is_active=True).order_by("date")
        holidays_data = [
            {
                "id": f"holiday-{h.holiday_id}",
                "title": h.name,
                "date": h.date.strftime("%Y-%m-%d"),
                "category": h.holiday_type,
                "description": h.description or "Public Holiday",
                "is_public": (h.holiday_type == "PUBLIC"),
            }
            for h in holidays
        ]
        context["holidays_json"] = json.dumps(holidays_data)

        context["critical_warnings"] = PerformanceWarning.objects.select_related("employee__user").filter(
            Q(status="OPEN") | Q(status="SENT_TO_ADMIN")
        ).order_by("-warning_date")[:5]

        return context


# HR Views and Management

class HRRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Enforces access control strictly for HR Managers, Staff, or Superusers."""

    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.is_staff
            or getattr(user, "role", "") == "HR"
            or hasattr(user, "hr_profile")
        )

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Access restricted to HR Personnel.")
        return redirect("users:redirect")


class HRProfileView(HRRequiredMixin, View):
    """View aggregated HR profile details and manage document uploads, education records, and experience."""
    template_name = "hr/profile.html"

    def get_or_create_hr_profile(self, user):
        hr_profile = getattr(user, "hr_profile", None)
        if not hr_profile and (getattr(user, "role", "") == User.RoleChoices.HR or user.is_staff or user.is_superuser):
            hr_profile, _ = HRManager.objects.get_or_create(
                user=user,
                defaults={"employee_code": f"HR-{user.id:04d}"},
            )
        if hr_profile:
            hr_profile.update_profile_completion_status()
        return hr_profile

    def get_context(self, request, doc_form=None, edu_form=None, exp_form=None):
        user = request.user
        hr_profile = self.get_or_create_hr_profile(user)

        education_records = hr_profile.education_records.all() if hr_profile else []
        experience_records = hr_profile.experience_records.all() if hr_profile else []
        documents = hr_profile.documents.all() if hr_profile else []

        return {
            "hr_profile": hr_profile,
            "user_obj": user,
            "education_records": education_records,
            "experience_records": experience_records,
            "documents": documents,
            "profile_photo": hr_profile.profile_photo if hr_profile else None,
            "doc_form": doc_form or HRDocumentUploadForm(),
            "edu_form": edu_form or HREducationForm(),
            "exp_form": exp_form or HRExperienceForm(),
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context(request))

    def post(self, request):
        action = request.POST.get("action")
        hr_profile = self.get_or_create_hr_profile(request.user)

        if not hr_profile:
            messages.error(request, "HR profile record could not be found.")
            return redirect("hr:profile")

        if action == "upload_document":
            doc_form = HRDocumentUploadForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.hr = hr_profile
                doc.save()
                hr_profile.update_profile_completion_status()
                messages.success(request, f"Document '{doc.get_document_type_display()}' uploaded successfully.")
                return redirect("hr:profile")
            else:
                messages.error(request, "Please correct the errors in the document upload form.")
                return render(request, self.template_name, self.get_context(request, doc_form=doc_form))

        elif action == "delete_document":
            doc_id = request.POST.get("document_id")
            doc = get_object_or_404(HRDocument, pk=doc_id, hr=hr_profile)
            doc_title = str(doc)
            doc.delete()
            hr_profile.update_profile_completion_status()
            messages.success(request, f"Document '{doc_title}' deleted successfully.")
            return redirect("hr:profile")

        elif action == "add_education":
            edu_form = HREducationForm(request.POST)
            if edu_form.is_valid():
                edu = edu_form.save(commit=False)
                edu.hr = hr_profile
                edu.save()
                hr_profile.update_profile_completion_status()
                messages.success(request, f"Education record '{edu.degree}' added successfully.")
                return redirect("hr:profile")
            else:
                messages.error(request, "Please correct the errors in the education form.")
                return render(request, self.template_name, self.get_context(request, edu_form=edu_form))

        elif action == "delete_education":
            edu_id = request.POST.get("education_id")
            edu = get_object_or_404(HREducation, pk=edu_id, hr=hr_profile)
            degree_name = edu.degree
            edu.delete()
            hr_profile.update_profile_completion_status()
            messages.success(request, f"Education record '{degree_name}' deleted successfully.")
            return redirect("hr:profile")

        elif action == "add_experience":
            exp_form = HRExperienceForm(request.POST)
            if exp_form.is_valid():
                exp = exp_form.save(commit=False)
                exp.hr = hr_profile
                exp.save()
                hr_profile.update_profile_completion_status()
                messages.success(request, f"Experience record '{exp.designation}' added successfully.")
                return redirect("hr:profile")
            else:
                messages.error(request, "Please correct the errors in the experience form.")
                return render(request, self.template_name, self.get_context(request, exp_form=exp_form))

        elif action == "delete_experience":
            exp_id = request.POST.get("experience_id")
            exp = get_object_or_404(HRExperience, pk=exp_id, hr=hr_profile)
            role_name = exp.designation
            exp.delete()
            hr_profile.update_profile_completion_status()
            messages.success(request, f"Experience record '{role_name}' deleted successfully.")
            return redirect("hr:profile")

        return redirect("hr:profile")


class HRProfileEditView(HRRequiredMixin, View):
    """Update personal info, contact, address, and experience status for HR Manager."""
    template_name = "hr/profile_edit.html"

    def get_or_create_hr_profile(self, user):
        hr_profile = getattr(user, "hr_profile", None)
        if not hr_profile and (getattr(user, "role", "") == User.RoleChoices.HR or user.is_staff or user.is_superuser):
            hr_profile, _ = HRManager.objects.get_or_create(
                user=user,
                defaults={"employee_code": f"HR-{user.id:04d}"},
            )
        return hr_profile

    def get(self, request):
        hr_profile = self.get_or_create_hr_profile(request.user)
        form = HRProfileEditForm(instance=hr_profile, user=request.user)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "hr_profile": hr_profile,
                "user_obj": request.user,
                "profile_photo": hr_profile.profile_photo if hr_profile else None,
            },
        )

    def post(self, request):
        hr_profile = self.get_or_create_hr_profile(request.user)
        form = HRProfileEditForm(
            request.POST,
            request.FILES,
            instance=hr_profile,
            user=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "HR Profile updated successfully.")
            return redirect("hr:profile")

        messages.error(request, "Please correct the errors in the form below.")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "hr_profile": hr_profile,
                "user_obj": request.user,
                "profile_photo": hr_profile.profile_photo if hr_profile else None,
            },
        )


class HREducationUpdateView(HRRequiredMixin, View):
    """Edit an existing education record."""
    template_name = "hr/education_edit.html"

    def get(self, request, pk):
        hr_profile = getattr(request.user, "hr_profile", None)
        edu = get_object_or_404(HREducation, pk=pk, hr=hr_profile)
        form = HREducationForm(instance=edu)
        return render(request, self.template_name, {"form": form, "edu": edu, "hr_profile": hr_profile})

    def post(self, request, pk):
        hr_profile = getattr(request.user, "hr_profile", None)
        edu = get_object_or_404(HREducation, pk=pk, hr=hr_profile)
        form = HREducationForm(request.POST, instance=edu)
        if form.is_valid():
            form.save()
            hr_profile.update_profile_completion_status()
            messages.success(request, f"Education record '{edu.degree}' updated successfully.")
            return redirect("hr:profile")
        return render(request, self.template_name, {"form": form, "edu": edu, "hr_profile": hr_profile})


class HRExperienceUpdateView(HRRequiredMixin, View):
    """Edit an existing work experience record."""
    template_name = "hr/experience_edit.html"

    def get(self, request, pk):
        hr_profile = getattr(request.user, "hr_profile", None)
        exp = get_object_or_404(HRExperience, pk=pk, hr=hr_profile)
        form = HRExperienceForm(instance=exp)
        return render(request, self.template_name, {"form": form, "exp": exp, "hr_profile": hr_profile})

    def post(self, request, pk):
        hr_profile = getattr(request.user, "hr_profile", None)
        exp = get_object_or_404(HRExperience, pk=pk, hr=hr_profile)
        form = HRExperienceForm(request.POST, instance=exp)
        if form.is_valid():
            form.save()
            hr_profile.update_profile_completion_status()
            messages.success(request, f"Experience record '{exp.designation}' updated successfully.")
            return redirect("hr:profile")
        return render(request, self.template_name, {"form": form, "exp": exp, "hr_profile": hr_profile})


class HRPasswordChangeView(HRRequiredMixin, View):
    """Change HR account password without dropping login session."""
    template_name = "hr/change_password.html"

    def get(self, request):
        form = PasswordChangeForm(user=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was changed successfully.")
            return redirect("hr:profile")
        return render(request, self.template_name, {"form": form})

class JobVacancyListView(HRRequiredMixin, ListView):
    model = JobVacancy
    template_name = "hr/job_list.html"
    context_object_name = "jobs"
    paginate_by = 10

    def get_queryset(self):
        # Auto-update any expired vacancies
        JobVacancy.update_all_expired()

        queryset = (
            JobVacancy.objects.select_related("department", "posted_by", "closed_by")
            .annotate(applicant_count=Count("applications"))
            .order_by("-posted_date")
        )

        status_filter = self.request.GET.get("status")
        dept_filter = self.request.GET.get("department")
        search_query = self.request.GET.get("q", "").strip()

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if dept_filter:
            queryset = queryset.filter(department_id=dept_filter)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(role_designation__icontains=search_query)
                | Q(skills_required__icontains=search_query)
                | Q(department__name__icontains=search_query)
                | Q(location__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_vacancies = JobVacancy.objects.all()
        today = timezone.localdate()

        context["total_jobs"] = all_vacancies.count()
        context["active_jobs"] = all_vacancies.filter(status="OPEN").count()
        context["closed_jobs"] = all_vacancies.filter(status="CLOSED").count()
        context["total_applications"] = JobApplication.objects.count()
        context["departments"] = Department.objects.filter(is_active=True).order_by("name")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_dept"] = self.request.GET.get("department", "")
        context["search_query"] = self.request.GET.get("q", "")
        context["today"] = today
        return context


class JobVacancyCreateView(HRRequiredMixin, CreateView):
    model = JobVacancy
    form_class = JobVacancyForm
    template_name = "hr/job_form.html"
    success_url = reverse_lazy("hr:job_list")

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Job vacancy "{self.object.title}" created and published successfully.')
        return response


class JobVacancyUpdateView(HRRequiredMixin, UpdateView):
    model = JobVacancy
    form_class = JobVacancyForm
    template_name = "hr/job_form.html"
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("hr:job_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Job vacancy "{self.object.title}" updated successfully.')
        return response


class JobVacancyDetailView(HRRequiredMixin, DetailView):
    model = JobVacancy
    template_name = "hr/job_detail.html"
    context_object_name = "job"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return JobVacancy.objects.select_related("department", "posted_by", "closed_by").prefetch_related(
            "applications__candidate__user"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        job.check_and_update_status()

        applications = job.applications.select_related("candidate__user").order_by("-applied_at")
        context["applications"] = applications
        context["applications_count"] = applications.count()
        context["shortlisted_count"] = applications.filter(status="SHORTLISTED").count()
        context["selected_count"] = applications.filter(status="SELECTED").count()
        context["rejected_count"] = applications.filter(status="REJECTED").count()
        return context


class JobVacancyCloseView(HRRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(JobVacancy, pk=pk)
        job.status = "CLOSED"
        job.closed_reason = "MANUALLY_CLOSED"
        job.closed_at = timezone.now()
        job.closed_by = request.user
        job.save()

        # Automatically screen applications submitted before closure
        try:
            from candidates.screening_service import run_resume_screening
            run_resume_screening(job, force_rescreen=False, screened_by=request.user)
        except Exception:
            pass

        messages.info(request, f'Job vacancy "{job.title}" has been manually closed and applicant screening has been processed.')
        return redirect("hr:job_list")


class JobScreeningView(HRRequiredMixin, View):
    """Job-specific Resume Screening Dashboard for HR."""
    template_name = "hr/job_screening.html"

    def get(self, request, vacancy_id):
        job = get_object_or_404(JobVacancy.objects.select_related("department"), vacancy_id=vacancy_id)
        job.check_and_update_status()

        # Handle batch re-screen action if requested
        if request.GET.get("action") == "rescreen":
            run_resume_screening(job, force_rescreen=True, screened_by=request.user)
            messages.success(request, f"Resume screening re-evaluated for all applicants of '{job.title}'.")
            return redirect("hr:job_screening", vacancy_id=vacancy_id)

        applications = (
            job.applications.select_related("candidate__user", "screening_result")
            .order_by("-applied_at")
        )

        # Auto-screen any applications that don't have a screening result yet
        for app in applications:
            if not hasattr(app, "screening_result"):
                screen_job_application(app)

        # Re-fetch applications with fresh screening results
        applications = list(
            job.applications.select_related("candidate__user", "screening_result")
            .order_by("-applied_at")
        )

        status_filter = request.GET.get("status", "").strip()
        search_query = request.GET.get("q", "").strip()
        sort_by = request.GET.get("sort", "-applied_at").strip()

        filtered_apps = []
        for app in applications:
            scr = getattr(app, "screening_result", None)
            if status_filter and scr:
                if scr.status != status_filter:
                    continue

            if search_query:
                q_lower = search_query.lower()
                cand_name = f"{app.candidate.first_name} {app.candidate.last_name}".lower()
                cand_email = (app.candidate.user.email or "").lower()
                cand_skills = " ".join(scr.extracted_skills if scr else []).lower()
                if q_lower not in cand_name and q_lower not in cand_email and q_lower not in cand_skills:
                    continue

            filtered_apps.append(app)

        # Sorting
        if sort_by == "skills_matched":
            filtered_apps.sort(
                key=lambda a: getattr(a, "screening_result", None).required_skills_matched
                if getattr(a, "screening_result", None)
                else 0,
                reverse=True,
            )
        elif sort_by == "score":
            filtered_apps.sort(
                key=lambda a: getattr(a, "screening_result", None).match_score
                if getattr(a, "screening_result", None)
                else 0.0,
                reverse=True,
            )
        elif sort_by == "date_asc":
            filtered_apps.sort(key=lambda a: a.applied_at)
        else:  # default date desc
            filtered_apps.sort(key=lambda a: a.applied_at, reverse=True)

        # Metric counts
        all_screenings = [
            getattr(a, "screening_result", None)
            for a in applications
            if hasattr(a, "screening_result")
        ]
        total_count = len(applications)
        shortlisted_count = sum(
            1 for s in all_screenings if s and s.status == "SHORTLISTED"
        )
        not_shortlisted_count = sum(
            1 for s in all_screenings if s and s.status == "NOT_SHORTLISTED"
        )
        manual_review_count = sum(
            1 for s in all_screenings if s and s.status == "MANUAL_REVIEW"
        )

        context = {
            "job": job,
            "applications": filtered_apps,
            "total_count": total_count,
            "shortlisted_count": shortlisted_count,
            "not_shortlisted_count": not_shortlisted_count,
            "manual_review_count": manual_review_count,
            "selected_status": status_filter,
            "search_query": search_query,
            "sort_by": sort_by,
        }
        return render(request, self.template_name, context)


class JobShortlistedView(HRRequiredMixin, DetailView):
    """View specifically displaying all shortlisted candidates for a job vacancy."""
    model = JobVacancy
    template_name = "hr/job_shortlisted.html"
    context_object_name = "job"
    pk_url_kwarg = "vacancy_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        job.check_and_update_status()

        # If job is closed/expired, ensure all applications have been screened
        if job.status == "CLOSED":
            for app in job.applications.all():
                if not hasattr(app, "screening_result"):
                    screen_job_application(app)

        shortlisted_apps = (
            job.applications.filter(status="SHORTLISTED")
            .select_related("candidate__user", "screening_result", "aptitude_test")
            .order_by("-screening_result__match_score", "-applied_at")
        )

        context["shortlisted_applications"] = shortlisted_apps
        context["shortlisted_count"] = shortlisted_apps.count()
        return context


class ApplicationScreeningDetailView(HRRequiredMixin, DetailView):
    """Detailed criteria-by-criteria breakdown of resume screening result for an application."""
    model = JobApplication
    template_name = "hr/screening_detail.html"
    context_object_name = "application"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return JobApplication.objects.select_related(
            "candidate__user", "vacancy__department", "screening_result"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        app = self.object
        # Ensure screening result exists
        if not hasattr(app, "screening_result"):
            screen_job_application(app)
            app.refresh_from_db()

        context["screening"] = app.screening_result
        context["job"] = app.vacancy
        context["candidate"] = app.candidate
        return context


class ApplicationScreeningOverrideView(HRRequiredMixin, View):
    """Allows HR to manually override a screening decision with an audit note."""
    def post(self, request, pk):
        application = get_object_or_404(
            JobApplication.objects.select_related("screening_result", "vacancy", "candidate"),
            pk=pk,
        )
        new_status = request.POST.get("status")
        override_notes = request.POST.get("override_notes", "").strip()

        if new_status in ["SHORTLISTED", "NOT_SHORTLISTED", "MANUAL_REVIEW"]:
            if not hasattr(application, "screening_result"):
                screen_job_application(application)
                application.refresh_from_db()

            screening = application.screening_result
            screening.status = new_status
            screening.is_manual_override = True
            screening.override_notes = override_notes
            screening.screened_by = request.user
            screening.save()

            try:
                applications_url = reverse_lazy("candidates:applications")
            except Exception:
                applications_url = "/candidates/applications/"

            if new_status == "SHORTLISTED":
                application.status = "SHORTLISTED"
                application.save(update_fields=["status", "updated_at"])
                send_candidate_notification(
                    candidate=application.candidate,
                    application=application,
                    title="Congratulations! You have been shortlisted",
                    message=(
                        f"Congratulations! Your resume has been shortlisted for the {application.vacancy.title} position.\n\n"
                        f"You have successfully moved to the next step of the recruitment process.\n\n"
                        f"Next Step:\nAptitude Round\n\n"
                        f"Please check your Candidate Portal for further details."
                    ),
                    notification_type="SHORTLISTED",
                    link_url=str(applications_url),
                )
            elif new_status == "NOT_SHORTLISTED":
                send_candidate_notification(
                    candidate=application.candidate,
                    application=application,
                    title="Application Update",
                    message=(
                        f"Thank you for applying for the {application.vacancy.title} position.\n\n"
                        f"After reviewing your application against the requirements for this position, "
                        f"your application has not been shortlisted for the next stage of the recruitment process.\n\n"
                        f"We appreciate your interest and encourage you to apply for other suitable opportunities."
                    ),
                    notification_type="NOT_SHORTLISTED",
                    link_url=str(applications_url),
                )

            messages.success(
                request,
                f"Screening outcome for {application.candidate.first_name} {application.candidate.last_name} updated to '{screening.get_status_display()}'.",
            )

        return redirect("hr:application_screening_detail", pk=pk)


class ApplicationListView(HRRequiredMixin, ListView):
    model = JobApplication
    template_name = "hr/application_list.html"
    context_object_name = "applications"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            JobApplication.objects.select_related(
                "candidate__user", "candidate", "vacancy", "vacancy__department", "screening_result"
            ).prefetch_related("interviews").order_by("-applied_at")
        )

        status_filter = self.request.GET.get("status", "").strip()
        search_query = self.request.GET.get("q", "").strip()

        if status_filter == "APPLIED":
            queryset = queryset.filter(
                status__in=["APPLIED", "RESUME_REVIEW"]
            )
        elif status_filter in ["RESUME_REVIEW", "UNDER_REVIEW"]:
            queryset = queryset.filter(
                Q(status__in=["RESUME_REVIEW", "APPLIED"])
                | Q(screening_result__status__in=["MANUAL_REVIEW", "EXTRACTION_FAILED"])
            )
        elif status_filter == "SHORTLISTED":
            queryset = queryset.filter(
                Q(status="SHORTLISTED") | Q(screening_result__status="SHORTLISTED")
            )
        elif status_filter in ["APTITUDE", "APTITUDE_TEST_SCHEDULED", "APTITUDE_REVIEW"]:
            queryset = queryset.filter(
                Q(status__in=["APTITUDE_TEST_SCHEDULED", "APTITUDE", "APTITUDE_REVIEW"])
                | Q(aptitude_date__isnull=False)
                | Q(aptitude_test__isnull=False)
            )
        elif status_filter in ["INTERVIEW", "INTERVIEW_SCHEDULED", "INTERVIEW_SCHEDULING", "INTERVIEW_REVIEW"]:
            queryset = queryset.filter(
                Q(status__in=["INTERVIEW", "INTERVIEW_SCHEDULED", "INTERVIEW_SCHEDULING", "INTERVIEW_REVIEW"])
                | Q(interviews__isnull=False)
            ).distinct()
        elif status_filter in ["SELECTED", "HIRED"]:
            queryset = queryset.filter(
                status__in=["SELECTED", "FORWARDED_TO_ADMIN", "HIRED"]
            )
        elif status_filter == "REJECTED":
            queryset = queryset.filter(
                Q(status="REJECTED") | Q(screening_result__status="NOT_SHORTLISTED")
            )
        elif status_filter:
            queryset = queryset.filter(status=status_filter)

        if search_query:
            queryset = queryset.filter(
                Q(candidate__first_name__icontains=search_query)
                | Q(candidate__last_name__icontains=search_query)
                | Q(candidate__user__name__icontains=search_query)
                | Q(candidate__user__email__icontains=search_query)
                | Q(vacancy__title__icontains=search_query)
                | Q(vacancy__department__name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "").strip()
        context["search_query"] = self.request.GET.get("q", "").strip()

        base_qs = JobApplication.objects.all()
        context["count_all"] = base_qs.count()
        context["count_applied"] = base_qs.filter(status__in=["APPLIED", "RESUME_REVIEW"]).count()
        context["count_under_review"] = base_qs.filter(
            Q(status="RESUME_REVIEW") | Q(screening_result__status__in=["MANUAL_REVIEW", "EXTRACTION_FAILED"])
        ).distinct().count()
        context["count_shortlisted"] = base_qs.filter(
            Q(status="SHORTLISTED") | Q(screening_result__status="SHORTLISTED")
        ).distinct().count()
        context["count_aptitude"] = base_qs.filter(
            Q(status__in=["APTITUDE_TEST_SCHEDULED", "APTITUDE", "APTITUDE_REVIEW"])
            | Q(aptitude_date__isnull=False)
            | Q(aptitude_test__isnull=False)
        ).distinct().count()
        context["count_interview"] = base_qs.filter(
            Q(status__in=["INTERVIEW", "INTERVIEW_SCHEDULED", "INTERVIEW_SCHEDULING", "INTERVIEW_REVIEW"])
            | Q(interviews__isnull=False)
        ).distinct().count()
        context["count_selected"] = base_qs.filter(
            status__in=["SELECTED", "FORWARDED_TO_ADMIN", "HIRED"]
        ).count()
        context["count_rejected"] = base_qs.filter(
            Q(status="REJECTED") | Q(screening_result__status="NOT_SHORTLISTED")
        ).distinct().count()
        return context


class ApplicationDetailView(HRRequiredMixin, DetailView):
    model = JobApplication
    template_name = "hr/application_detail.html"
    context_object_name = "app"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return (
            JobApplication.objects.select_related(
                "candidate__user", "candidate", "vacancy", "vacancy__department", "aptitude_test", "screening_result"
            ).prefetch_related(
                "aptitude_results__test",
                "interviews__interviewer",
                "interviews__interviewer__user",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.object
        if not hasattr(application, "screening_result"):
            screen_job_application(application)
            application.refresh_from_db()

        context["screening"] = getattr(application, "screening_result", None)
        context["aptitude_tests"] = AptitudeTest.objects.filter(status="ACTIVE")
        context["hr_managers"] = HRManager.objects.select_related("user").all()
        context["locations"] = InterviewLocation.objects.filter(is_active=True)
        context["available_slots"] = InterviewSlot.objects.filter(
            Q(vacancy=application.vacancy) | Q(vacancy__isnull=True),
            status="AVAILABLE",
            interview_date__gte=timezone.localdate(),
        ).select_related("location", "interviewer__user").order_by("interview_date", "start_time")
        
        # Onboarding lookups
        context["departments"] = Department.objects.filter(is_active=True).select_related("department_leader").order_by("name")
        context["teams"] = Team.objects.filter(is_active=True).select_related("department", "team_lead").order_by("team_name")
        context["eligible_team_leads"] = User.objects.filter(
            role__in=[User.RoleChoices.HR, User.RoleChoices.EMPLOYEE], is_active=True
        ).order_by("name", "email")

        # Check if an employee record or approval exists for this candidate
        if application and application.candidate:
            cand_user = getattr(application.candidate, "user", None)
            employee = None
            if cand_user:
                employee = Employee.objects.filter(user=cand_user).select_related(
                    "department", "department__department_leader", "team", "team_lead", "created_by"
                ).first()
            if not employee:
                employee = Employee.objects.filter(candidate=application.candidate).select_related(
                    "department", "department__department_leader", "team", "team_lead", "created_by"
                ).first()
            if employee:
                context["employee_record"] = employee
                context["employee_approval"] = EmployeeApproval.objects.filter(employee=employee).select_related("approved_by", "requested_by").first()
        return context


class ApplicationAcceptEmployeeView(HRRequiredMixin, View):
    """Allows HR Manager to accept a candidate as an employee and submit an approval request to Admin (New Employee Approvals)."""

    def post(self, request, pk):
        application = get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy__department"),
            pk=pk,
        )

        cand_user = application.candidate.user
        dept = application.vacancy.department
        if not dept:
            dept = Department.objects.first()

        with transaction.atomic():
            # Create or get Employee record in INACTIVE/pending status
            employee, emp_created = Employee.objects.get_or_create(
                user=cand_user,
                defaults={
                    "candidate": application.candidate,
                    "employee_code": f"EMP{cand_user.id:04d}",
                    "department": dept,
                    "designation": application.vacancy.title,
                    "joining_date": timezone.now().date(),
                    "employment_status": "INACTIVE",
                    "created_by": request.user,
                },
            )
            if not emp_created:
                employee.candidate = application.candidate
                employee.department = dept
                employee.designation = application.vacancy.title
                employee.created_by = request.user
                employee.save(update_fields=["candidate", "department", "designation", "created_by", "updated_at"])

            # Create or reset EmployeeApproval to PENDING
            approval, app_created = EmployeeApproval.objects.get_or_create(
                employee=employee,
                defaults={"status": "PENDING"},
            )
            if not app_created:
                approval.status = "PENDING"
                approval.comments = ""
                approval.approved_by = None
                approval.approved_at = None
                approval.save(update_fields=["status", "comments", "approved_by", "approved_at"])

            application.status = "SELECTED"
            application.save(update_fields=["status", "updated_at"])

        messages.success(
            request,
            f"Candidate '{application.candidate.first_name} {application.candidate.last_name}' accepted as Employee. Approval request submitted to Admin (New Employee Approvals).",
        )
        return redirect("hr:application_detail", pk=pk)


class ApplicationStatusUpdateView(HRRequiredMixin, View):
    """Allows HR to progress an application through Alan's exact STATUS_CHOICES and dispatches candidate notifications."""

    def post(self, request, pk):
        import datetime
        from django.utils import timezone

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate", "vacancy"),
            pk=pk,
        )
        new_status = request.POST.get("status")

        valid_choices = [c[0] for c in JobApplication.STATUS_CHOICES]
        if new_status in valid_choices:
            application.status = new_status

            # Handle Aptitude scheduling inputs
            apt_date = request.POST.get("aptitude_date")
            apt_time = request.POST.get("aptitude_time")
            apt_duration = request.POST.get("aptitude_duration_minutes")
            apt_test_id = request.POST.get("aptitude_test_id")
            apt_remarks = request.POST.get("aptitude_remarks", "").strip()

            if apt_date:
                application.aptitude_date = apt_date
            if apt_time:
                application.aptitude_time = apt_time
            if apt_duration and apt_duration.isdigit():
                application.aptitude_duration_minutes = int(apt_duration)
            if apt_remarks:
                application.aptitude_remarks = apt_remarks
            if apt_test_id:
                application.aptitude_test_id = apt_test_id

            if application.aptitude_date and application.aptitude_time:
                try:
                    d = datetime.date.fromisoformat(str(application.aptitude_date)) if isinstance(application.aptitude_date, str) else application.aptitude_date
                    t = datetime.time.fromisoformat(str(application.aptitude_time)) if isinstance(application.aptitude_time, str) else application.aptitude_time
                    comb = datetime.datetime.combine(d, t)
                    s_dt = timezone.make_aware(comb) if timezone.is_naive(comb) else comb
                    dur = application.aptitude_duration_minutes or 30
                    application.aptitude_start_datetime = s_dt
                    application.aptitude_end_datetime = s_dt + datetime.timedelta(minutes=dur)
                except Exception:
                    pass

            application.save()

            # Dispatch targeted notification to the affected candidate
            from candidates.models import send_candidate_notification

            notif_title = "Application Status Updated"
            notif_msg = f"Your application for '{application.vacancy.title}' has been updated to {application.get_status_display()}."
            notif_type = "STATUS_UPDATE"

            if new_status == "SHORTLISTED":
                notif_title = "Application Shortlisted"
                notif_msg = f"Great news! Your application for '{application.vacancy.title}' has been shortlisted by our recruitment team."
            elif new_status in ["APTITUDE_TEST_SCHEDULED", "APTITUDE"]:
                notif_title = "Aptitude Test Scheduled"
                notif_type = "APTITUDE_SCHEDULED"
                if application.aptitude_date and application.aptitude_time:
                    f_date = application.aptitude_date.strftime("%d %B %Y") if hasattr(application.aptitude_date, "strftime") else str(application.aptitude_date)
                    f_time = application.aptitude_time.strftime("%I:%M %p") if hasattr(application.aptitude_time, "strftime") else str(application.aptitude_time)
                    f_dur = application.aptitude_duration_minutes or 30
                    notif_msg = (
                        f"Your aptitude test for the {application.vacancy.title} position has been scheduled.\n\n"
                        f"Date: {f_date}\n"
                        f"Time: {f_time}\n"
                        f"Duration: {f_dur} Minutes\n\n"
                        f"Kindly be available at the scheduled date and time.\n\n"
                        f"Please check your Candidate Portal for further details."
                    )
                else:
                    notif_msg = f"Your application for '{application.vacancy.title}' has entered the Aptitude Assessment round."
            elif new_status == "INTERVIEW":
                notif_title = "Interview Stage Reached"
                notif_type = "INTERVIEW_SCHEDULED"
                notif_msg = (
                    f"Congratulations! You have successfully completed the aptitude stage and have been moved to the interview round.\n\n"
                    f"Please check your Candidate Portal for interview details."
                )
            elif new_status == "SELECTED":
                notif_title = "Application Selected"
                notif_msg = f"Congratulations! You have been selected for the position of '{application.vacancy.title}'."
            elif new_status == "REJECTED":
                notif_title = "Application Status Update"
                notif_msg = f"Thank you for your interest in '{application.vacancy.title}'. At this time, we have chosen to proceed with other candidates."
            elif new_status == "RESUME_REVIEW":
                notif_title = "Application Under Review"
                notif_type = "APPLICATION_UNDER_REVIEW"
                notif_msg = (
                    f"Thank you for your patience.\n\n"
                    f"Your application for the {application.vacancy.title} position is currently under review by our recruitment team.\n\n"
                    f"We will update you as soon as the review process is complete."
                )

            send_candidate_notification(
                candidate=application.candidate,
                application=application,
                title=notif_title,
                message=notif_msg,
                notification_type=notif_type,
                link_url=reverse_lazy("candidates:applications"),
            )

            messages.success(
                request,
                f"Application status updated to '{application.get_status_display()}'.",
            )
        else:
            messages.error(request, "Invalid status submitted.")

        return redirect("hr:application_detail", pk=pk)


class AptitudeScheduleView(HRRequiredMixin, View):
    """Allows HR to schedule an aptitude test for a candidate with strict date/time/duration validation."""

    def post(self, request, pk):
        import datetime
        from django.utils import timezone
        from candidates.models import send_candidate_notification

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate", "vacancy"),
            pk=pk,
        )

        test_id = request.POST.get("aptitude_test_id")
        date_str = request.POST.get("aptitude_date", "").strip()
        time_str = request.POST.get("aptitude_time", "").strip()
        duration_str = request.POST.get("aptitude_duration_minutes", "").strip()
        remarks = request.POST.get("aptitude_remarks", "").strip()
        passing_score_str = request.POST.get("aptitude_passing_score", "").strip()

        if not date_str or not time_str:
            messages.error(request, "Assessment date and start time are required.")
            return redirect("hr:application_detail", pk=pk)

        try:
            apt_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            messages.error(request, "Invalid assessment date format.")
            return redirect("hr:application_detail", pk=pk)

        try:
            time_parts = time_str.split(":")
            apt_time = datetime.time(int(time_parts[0]), int(time_parts[1]))
        except Exception:
            messages.error(request, "Invalid assessment start time format.")
            return redirect("hr:application_detail", pk=pk)

        try:
            duration = int(duration_str) if duration_str else 30
            if duration <= 0:
                raise ValueError("Duration must be positive.")
        except ValueError:
            messages.error(request, "Test duration must be greater than 0 minutes.")
            return redirect("hr:application_detail", pk=pk)

        # Timezone-aware combined start datetime
        combined_naive = datetime.datetime.combine(apt_date, apt_time)
        start_datetime = timezone.make_aware(combined_naive) if timezone.is_naive(combined_naive) else combined_naive

        today = timezone.localdate()
        if apt_date < today:
            messages.error(request, "Assessment date cannot be in the past.")
            return redirect("hr:application_detail", pk=pk)

        now = timezone.now()
        if start_datetime < now:
            start_datetime = now

        end_datetime = start_datetime + datetime.timedelta(minutes=duration)

        test = None
        if test_id:
            test = AptitudeTest.objects.filter(pk=test_id, status="ACTIVE").first()
        if not test:
            test = AptitudeTest.objects.filter(status="ACTIVE").order_by("-created_at").first()

        application.aptitude_date = apt_date
        application.aptitude_time = apt_time
        application.aptitude_duration_minutes = duration
        application.aptitude_start_datetime = start_datetime
        application.aptitude_end_datetime = end_datetime
        application.aptitude_test = test
        application.aptitude_remarks = remarks
        if passing_score_str and passing_score_str.isdigit():
            application.aptitude_passing_score = int(passing_score_str)
        application.status = "APTITUDE_TEST_SCHEDULED"
        application.save()

        formatted_date = apt_date.strftime("%d %B %Y")
        formatted_time = apt_time.strftime("%I:%M %p")

        notif_msg = (
            f"Your aptitude test for the {application.vacancy.title} position has been scheduled.\n\n"
            f"Date: {formatted_date}\n"
            f"Time: {formatted_time}\n"
            f"Duration: {duration} Minutes\n\n"
            f"Kindly be available at the scheduled date and time.\n\n"
            f"Please check your Candidate Portal for further details."
        )

        send_candidate_notification(
            candidate=application.candidate,
            application=application,
            title="Aptitude Test Scheduled",
            message=notif_msg,
            notification_type="APTITUDE_SCHEDULED",
            link_url=reverse_lazy("candidates:applications"),
        )

        messages.success(
            request,
            f"Aptitude test scheduled successfully for {application.candidate.first_name} {application.candidate.last_name} on {formatted_date} at {formatted_time}.",
        )
        return redirect("hr:application_detail", pk=pk)


class AptitudeRescheduleView(HRRequiredMixin, View):
    """Allows HR to reschedule an aptitude test before it starts."""

    def post(self, request, pk):
        import datetime
        from django.utils import timezone
        from candidates.models import send_candidate_notification

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate", "vacancy"),
            pk=pk,
        )

        date_str = request.POST.get("aptitude_date", "").strip()
        time_str = request.POST.get("aptitude_time", "").strip()
        duration_str = request.POST.get("aptitude_duration_minutes", "").strip()
        remarks = request.POST.get("aptitude_remarks", "").strip()

        if not date_str or not time_str:
            messages.error(request, "Assessment date and start time are required.")
            return redirect("hr:application_detail", pk=pk)

        try:
            apt_date = datetime.date.fromisoformat(date_str)
            time_parts = time_str.split(":")
            apt_time = datetime.time(int(time_parts[0]), int(time_parts[1]))
            duration = int(duration_str) if duration_str else (application.aptitude_duration_minutes or 30)
            if duration <= 0:
                raise ValueError()
        except Exception:
            messages.error(request, "Invalid reschedule inputs.")
            return redirect("hr:application_detail", pk=pk)

        combined_naive = datetime.datetime.combine(apt_date, apt_time)
        start_datetime = timezone.make_aware(combined_naive) if timezone.is_naive(combined_naive) else combined_naive

        if start_datetime <= timezone.now():
            messages.error(request, "New assessment date and start time must be in the future.")
            return redirect("hr:application_detail", pk=pk)

        end_datetime = start_datetime + datetime.timedelta(minutes=duration)

        application.aptitude_date = apt_date
        application.aptitude_time = apt_time
        application.aptitude_duration_minutes = duration
        application.aptitude_start_datetime = start_datetime
        application.aptitude_end_datetime = end_datetime
        if remarks:
            application.aptitude_remarks = remarks
        application.status = "APTITUDE_TEST_SCHEDULED"
        application.save()

        reschedule_reason = request.POST.get("reschedule_reason", "").strip()

        formatted_date = apt_date.strftime("%d %B %Y")
        formatted_time = apt_time.strftime("%I:%M %p")

        notif_msg = (
            f"Your aptitude test for the {application.vacancy.title} position has been rescheduled.\n\n"
            f"New Date:\n{formatted_date}\n\n"
            f"New Time:\n{formatted_time}\n\n"
            f"Duration:\n{duration} Minutes"
        )
        if reschedule_reason:
            notif_msg += f"\n\nReason:\n{reschedule_reason}"
        notif_msg += "\n\nKindly be available at the new scheduled date and time."

        send_candidate_notification(
            candidate=application.candidate,
            application=application,
            title="Aptitude Test Rescheduled",
            message=notif_msg,
            notification_type="APTITUDE_RESCHEDULED",
            link_url=reverse_lazy("candidates:applications"),
        )

        messages.success(request, f"Aptitude test rescheduled to {formatted_date} at {formatted_time}.")
        return redirect("hr:application_detail", pk=pk)


class AptitudeCancelView(HRRequiredMixin, View):
    """Allows HR to cancel an aptitude schedule before test starts, reverting application to SHORTLISTED."""

    def post(self, request, pk):
        from candidates.models import send_candidate_notification

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate", "vacancy"),
            pk=pk,
        )

        cancellation_reason = request.POST.get("cancellation_reason", "").strip()

        application.status = "SHORTLISTED"
        application.aptitude_date = None
        application.aptitude_time = None
        application.aptitude_start_datetime = None
        application.aptitude_end_datetime = None
        application.save()

        notif_msg = (
            f"Your scheduled aptitude test for the {application.vacancy.title} position has been cancelled."
        )
        if cancellation_reason:
            notif_msg += f"\n\nReason:\n{cancellation_reason}"
        notif_msg += "\n\nOur recruitment team will update you with new details shortly."

        send_candidate_notification(
            candidate=application.candidate,
            application=application,
            title="Aptitude Test Cancelled",
            message=notif_msg,
            notification_type="APTITUDE_CANCELLED",
            link_url=reverse_lazy("candidates:applications"),
        )

        messages.info(request, f"Aptitude schedule for {application.candidate.first_name} {application.candidate.last_name} has been cancelled.")
        return redirect("hr:application_detail", pk=pk)


class ApplicationAptitudeReviewView(HRRequiredMixin, View):
    """HR-only detailed review view for a candidate's completed aptitude assessment."""
    template_name = "hr/aptitude_review.html"

    def get(self, request, pk):
        application = get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy__department", "aptitude_test"),
            pk=pk,
        )
        attempt = AptitudeAttempt.objects.filter(application=application).order_by("-started_at").first()
        result = AptitudeResult.objects.filter(application=application).order_by("-completed_at").first()

        if not result and not attempt:
            messages.warning(request, "No aptitude assessment submission found for this application.")
            return redirect("hr:application_detail", pk=pk)

        questions_breakdown = []
        if attempt and attempt.questions_data:
            candidate_answers = attempt.answers_data or {}
            for q in attempt.questions_data:
                qid = str(q.get("question_id"))
                cand_key = candidate_answers.get(qid)
                corr_key = q.get("correct_key")

                options_map = {opt["key"]: opt["text"] for opt in q.get("options", [])}
                cand_text = options_map.get(cand_key, "No answer selected") if cand_key else "Unanswered"
                corr_text = options_map.get(corr_key, "")

                is_correct = (cand_key == corr_key) if cand_key else False
                is_unanswered = (cand_key is None or cand_key == "")

                questions_breakdown.append({
                    "question_id": qid,
                    "category": q.get("category", ""),
                    "category_display": q.get("category_display", ""),
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "candidate_key": cand_key,
                    "candidate_text": cand_text,
                    "correct_key": corr_key,
                    "correct_text": corr_text,
                    "is_correct": is_correct,
                    "is_unanswered": is_unanswered,
                })

        context = {
            "app": application,
            "candidate": application.candidate,
            "job": application.vacancy,
            "attempt": attempt,
            "result": result,
            "questions_breakdown": questions_breakdown,
        }
        return render(request, self.template_name, context)


class ApplicationAptitudeDecisionView(HRRequiredMixin, View):
    """Handles HR decision on completed aptitude test: Proceed to Interview OR Reject."""

    def post(self, request, pk):
        from candidates.models import send_candidate_notification

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate", "vacancy"),
            pk=pk,
        )
        result = AptitudeResult.objects.filter(application=application).order_by("-completed_at").first()

        decision = request.POST.get("decision")
        hr_comments = request.POST.get("hr_comments", "").strip()

        if result:
            result.hr_decision = decision
            result.hr_comments = hr_comments
            result.save()

        if decision in ["INTERVIEW", "PROCEED_INTERVIEW", "PASS"]:
            application.status = "INTERVIEW_SCHEDULING"
            application.save(update_fields=["status", "updated_at"])

            notif_msg = (
                f"Congratulations! You have successfully passed the aptitude round and are eligible for the interview round. "
                f"Please select an available interview slot from your candidate portal."
            )
            send_candidate_notification(
                candidate=application.candidate,
                application=application,
                title="Offline Interview Slot Selection Open",
                message=notif_msg,
                notification_type="INTERVIEW_ELIGIBLE",
                link_url=reverse_lazy("candidates:applications"),
            )
            messages.success(
                request,
                f"Candidate {application.candidate.first_name} {application.candidate.last_name} passed aptitude and is now eligible for Interview Slot Selection.",
            )
        elif decision in ["REJECT", "FAIL"]:
            application.status = "REJECTED"
            application.save(update_fields=["status", "updated_at"])

            notif_msg = (
                f"Thank you for completing the aptitude assessment for the {application.vacancy.title} position.\n\n"
                f"After careful review of your results, we have chosen to proceed with other candidates for this role.\n\n"
                f"We appreciate your interest and wish you the best in your career pursuits."
            )
            send_candidate_notification(
                candidate=application.candidate,
                application=application,
                title="Application Status Update",
                message=notif_msg,
                notification_type="NOT_SHORTLISTED",
                link_url=reverse_lazy("candidates:applications"),
            )
            messages.info(
                request,
                f"Application for {application.candidate.first_name} {application.candidate.last_name} marked as REJECTED.",
            )
        else:
            messages.error(request, "Invalid HR decision submitted.")

        return redirect("hr:application_detail", pk=pk)

# --- Aptitude Test Views ---
class AptitudeTestListView(HRRequiredMixin, ListView):
    model = AptitudeTest
    template_name = "hr/aptitude_test_list.html"
    context_object_name = "tests"

    def get_queryset(self):
        return AptitudeTest.objects.annotate(
            question_count=Count("questions")
        ).order_by("-created_at")


class AptitudeTestCreateView(HRRequiredMixin, CreateView):
    model = AptitudeTest
    template_name = "hr/aptitude_test_form.html"
    form_class = AptitudeTestForm
    success_url = reverse_lazy("hr:aptitude_test_list")

    def form_valid(self, form):
        form.instance.created_by = getattr(self.request.user, "hr_profile", None)
        response = super().form_valid(form)
        # Seed predefined questions for the new test
        try:
            seed_default_questions(test=self.object)
        except Exception:
            pass
        messages.success(self.request, "Aptitude test created with standard question bank.")
        return response


class AptitudeTestUpdateView(HRRequiredMixin, UpdateView):
    model = AptitudeTest
    template_name = "hr/aptitude_test_form.html"
    form_class = AptitudeTestForm
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("hr:aptitude_test_list")

    def form_valid(self, form):
        messages.success(self.request, "Aptitude test updated successfully.")
        return super().form_valid(form)


class AptitudeQuestionManageView(HRRequiredMixin, View):
    """View to list existing questions for a test with category filtering and add new ones."""
    template_name = "hr/aptitude_questions.html"

    def get(self, request, test_id):
        test = get_object_or_404(AptitudeTest, pk=test_id)

        # Auto-seed predefined question bank if test has no questions yet
        if not test.questions.exists():
            seed_default_questions(test=test)

        all_questions = test.questions.all()

        total_count = all_questions.count()
        quant_count = all_questions.filter(category="QUANTITATIVE").count()
        logical_count = all_questions.filter(category="LOGICAL").count()
        verbal_count = all_questions.filter(category="VERBAL").count()
        active_count = all_questions.filter(is_active=True).count()

        category = request.GET.get("category", "").strip()
        status_filter = request.GET.get("status", "").strip()

        questions = all_questions
        if category in ["QUANTITATIVE", "LOGICAL", "VERBAL"]:
            questions = questions.filter(category=category)
        if status_filter == "ACTIVE":
            questions = questions.filter(is_active=True)
        elif status_filter == "INACTIVE":
            questions = questions.filter(is_active=False)

        form = AptitudeQuestionForm()

        return render(
            request,
            self.template_name,
            {
                "test": test,
                "questions": questions,
                "form": form,
                "selected_category": category,
                "selected_status": status_filter,
                "total_count": total_count,
                "quant_count": quant_count,
                "logical_count": logical_count,
                "verbal_count": verbal_count,
                "active_count": active_count,
            },
        )

    def post(self, request, test_id):
        test = get_object_or_404(AptitudeTest, pk=test_id)
        form = AptitudeQuestionForm(request.POST)

        if form.is_valid():
            question = form.save(commit=False)
            question.test = test
            question.save()
            messages.success(request, f"New question added to {question.get_category_display()} successfully.")
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {err}")

        return redirect("hr:aptitude_questions", test_id=test.pk)


class AptitudeQuestionUpdateView(HRRequiredMixin, View):
    """Update an existing aptitude question."""

    def post(self, request, question_id):
        question = get_object_or_404(AptitudeQuestion, pk=question_id)
        test_id = question.test.pk if question.test else None

        form = AptitudeQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated successfully.")
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {err}")

        if test_id:
            return redirect("hr:aptitude_questions", test_id=test_id)
        return redirect("hr:aptitude_test_list")


class AptitudeQuestionToggleStatusView(HRRequiredMixin, View):
    """Toggle active/inactive status of a question."""

    def post(self, request, question_id):
        question = get_object_or_404(AptitudeQuestion, pk=question_id)
        test_id = question.test.pk if question.test else None

        question.is_active = not question.is_active
        question.save(update_fields=["is_active"])

        status_text = "Active" if question.is_active else "Inactive"
        messages.info(request, f"Question marked as {status_text}.")

        if test_id:
            return redirect("hr:aptitude_questions", test_id=test_id)
        return redirect("hr:aptitude_test_list")


class AptitudeQuestionLoadBankView(HRRequiredMixin, View):
    """Load or refresh the predefined question bank into a test."""

    def post(self, request, test_id):
        test = get_object_or_404(AptitudeTest, pk=test_id)
        created, existing = seed_default_questions(test=test)
        messages.success(
            request,
            f"Question bank synced successfully: {created} new questions added, {existing} questions verified.",
        )
        return redirect("hr:aptitude_questions", test_id=test.pk)


class AptitudeQuestionDeleteView(HRRequiredMixin, View):
    """Delete a question from a test."""

    def post(self, request, question_id):
        question = get_object_or_404(AptitudeQuestion, pk=question_id)
        test_id = question.test.pk if question.test else None
        question.delete()
        messages.info(request, "Question removed successfully.")
        if test_id:
            return redirect("hr:aptitude_questions", test_id=test_id)
        return redirect("hr:aptitude_test_list")

    
class InterviewSlotListView(HRRequiredMixin, ListView):
    model = InterviewSlot
    template_name = "hr/interview_slots.html"
    context_object_name = "slots"
    paginate_by = 20

    def get_queryset(self):
        queryset = InterviewSlot.objects.select_related(
            "vacancy", "interviewer__user", "location", "booked_by__user", "booked_application"
        ).order_by("-interview_date", "-start_time")

        vacancy_id = self.request.GET.get("vacancy_id")
        status_filter = self.request.GET.get("status")
        date_filter = self.request.GET.get("date")

        if vacancy_id:
            queryset = queryset.filter(vacancy_id=vacancy_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_filter:
            queryset = queryset.filter(interview_date=date_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vacancies"] = JobVacancy.objects.filter(status="OPEN")
        context["locations"] = InterviewLocation.objects.filter(is_active=True)
        context["interviewers"] = HRManager.objects.filter(is_active=True).select_related("user")
        context["selected_vacancy"] = self.request.GET.get("vacancy_id", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_date"] = self.request.GET.get("date", "")
        return context


class InterviewSlotCreateView(HRRequiredMixin, View):
    """Allows HR to define available offline interview slots with location, interviewer, date & times."""

    def post(self, request):
        import datetime

        vacancy_id = request.POST.get("vacancy_id")
        location_id = request.POST.get("location_id")
        interviewer_id = request.POST.get("interviewer_id")
        interview_type = request.POST.get("interview_type", "TECHNICAL")
        date_str = request.POST.get("interview_date", "").strip()
        start_time_str = request.POST.get("start_time", "").strip()
        end_time_str = request.POST.get("end_time", "").strip()
        instructions = request.POST.get("instructions", "").strip()

        if not (location_id and date_str and start_time_str and end_time_str):
            messages.error(request, "Location, date, start time, and end time are required.")
            return redirect("hr:interview_slots")

        location = get_object_or_404(InterviewLocation, pk=location_id, is_active=True)

        interviewer = None
        if interviewer_id:
            interviewer = HRManager.objects.filter(pk=interviewer_id, is_active=True).first()
        if not interviewer:
            interviewer = getattr(request.user, "hr_profile", None)

        if not interviewer:
            messages.error(request, "A valid HR interviewer is required.")
            return redirect("hr:interview_slots")

        vacancy = None
        if vacancy_id:
            vacancy = JobVacancy.objects.filter(pk=vacancy_id).first()

        try:
            slot_date = datetime.date.fromisoformat(date_str)
            s_parts = start_time_str.split(":")
            e_parts = end_time_str.split(":")
            start_time = datetime.time(int(s_parts[0]), int(s_parts[1]))
            end_time = datetime.time(int(e_parts[0]), int(e_parts[1]))
        except Exception:
            messages.error(request, "Invalid date or time format.")
            return redirect("hr:interview_slots")

        if slot_date < timezone.localdate():
            messages.error(request, "Interview date cannot be in the past.")
            return redirect("hr:interview_slots")

        if start_time >= end_time:
            messages.error(request, "End time must be after start time.")
            return redirect("hr:interview_slots")

        # Conflict check: Interviewer cannot be double booked with overlapping time intervals
        existing_conflict = InterviewSlot.objects.filter(
            interviewer=interviewer,
            interview_date=slot_date,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status__in=["AVAILABLE", "BOOKED"],
        ).exists()

        if existing_conflict:
            messages.error(
                request,
                f"Interviewer {interviewer.user.get_full_name() or interviewer.user.email} already has a slot scheduled on {slot_date} overlapping with {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}.",
            )
            return redirect("hr:interview_slots")

        slot = InterviewSlot.objects.create(
            vacancy=vacancy,
            interviewer=interviewer,
            location=location,
            interview_type=interview_type,
            interview_date=slot_date,
            start_time=start_time,
            end_time=end_time,
            instructions=instructions,
            status="AVAILABLE",
        )

        messages.success(
            request,
            f"Interview slot created successfully: {slot.interview_date} ({slot.formatted_time_range}) at {slot.location.location_name}.",
        )
        return redirect("hr:interview_slots")


class InterviewSlotCancelView(HRRequiredMixin, View):
    """Allows HR to cancel an interview slot."""

    def post(self, request, pk):
        slot = get_object_or_404(InterviewSlot.objects.select_related("booked_application__candidate", "vacancy"), pk=pk)
        slot.status = "CANCELLED"
        slot.save(update_fields=["status"])

        if slot.booked_application:
            app = slot.booked_application
            app.status = "INTERVIEW_SCHEDULING"
            app.save(update_fields=["status", "updated_at"])

            send_candidate_notification(
                candidate=app.candidate,
                application=app,
                title="Interview Slot Cancelled",
                message=f"Your booked interview slot on {slot.interview_date} at {slot.formatted_time_range} was cancelled by HR. Please log in to select another available interview slot.",
                notification_type="INTERVIEW_CANCELLED",
                link_url=reverse_lazy("candidates:applications"),
            )

        messages.info(request, f"Interview slot #{pk} has been cancelled.")
        return redirect("hr:interview_slots")


class InterviewListView(HRRequiredMixin, ListView):
    model = Interview
    template_name = "hr/interview_list.html"
    context_object_name = "interviews"
    paginate_by = 20

    def get_queryset(self):
        queryset = Interview.objects.select_related(
            "application__candidate__user",
            "application__vacancy__department",
            "interviewer__user",
            "location",
            "slot",
            "evaluation",
        ).order_by("-interview_date", "-interview_time")

        status_filter = self.request.GET.get("status")
        attendance_filter = self.request.GET.get("attendance")
        vacancy_filter = self.request.GET.get("vacancy_id")

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if attendance_filter:
            queryset = queryset.filter(attendance=attendance_filter)
        if vacancy_filter:
            queryset = queryset.filter(application__vacancy_id=vacancy_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_attendance"] = self.request.GET.get("attendance", "")
        context["selected_vacancy"] = self.request.GET.get("vacancy_id", "")
        context["vacancies"] = JobVacancy.objects.all().order_by("title")
        context["locations"] = InterviewLocation.objects.filter(is_active=True)
        context["interviewers"] = HRManager.objects.filter(is_active=True).select_related("user")

        # Candidates eligible for interview (at INTERVIEW_SCHEDULING or INTERVIEW_SCHEDULED)
        context["eligible_applications"] = JobApplication.objects.filter(
            status__in=["INTERVIEW_SCHEDULING", "INTERVIEW_SCHEDULED", "INTERVIEW", "INTERVIEW_REVIEW"]
        ).select_related("candidate__user", "vacancy")
        return context


class InterviewScheduleView(HRRequiredMixin, View):
    """Allows HR to directly assign an interview slot or create a scheduled offline interview for a candidate."""

    def post(self, request, application_id):
        import datetime

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy"),
            pk=application_id,
        )
        slot_id = request.POST.get("slot_id")
        interview_date_str = request.POST.get("interview_date", "").strip()
        interview_time_str = request.POST.get("interview_time", "").strip()
        location_id = request.POST.get("location_id")
        interviewer_id = request.POST.get("interviewer_id")
        interview_type = request.POST.get("interview_type", "TECHNICAL")
        instructions = request.POST.get("instructions", "").strip()
        remarks = request.POST.get("remarks", "").strip()

        with transaction.atomic():
            if slot_id:
                slot = get_object_or_404(InterviewSlot, pk=slot_id, status="AVAILABLE")
                slot.status = "BOOKED"
                slot.booked_by = application.candidate
                slot.booked_application = application
                slot.save(update_fields=["status", "booked_by", "booked_application"])

                interview = Interview.objects.create(
                    application=application,
                    slot=slot,
                    location=slot.location,
                    interviewer=slot.interviewer,
                    interview_type=slot.interview_type,
                    interview_date=slot.interview_date,
                    interview_time=slot.start_time,
                    instructions=slot.instructions or instructions,
                    remarks=remarks,
                    status="SCHEDULED",
                    attendance="NOT_MARKED",
                )
            else:
                if not (interview_date_str and interview_time_str):
                    messages.error(request, "Interview date and start time are required.")
                    return redirect("hr:application_detail", pk=application.pk)

                try:
                    i_date = datetime.date.fromisoformat(interview_date_str)
                    t_parts = interview_time_str.split(":")
                    i_time = datetime.time(int(t_parts[0]), int(t_parts[1]))
                except Exception:
                    messages.error(request, "Invalid date or time format.")
                    return redirect("hr:application_detail", pk=application.pk)

                location = None
                if location_id:
                    location = InterviewLocation.objects.filter(pk=location_id, is_active=True).first()
                if not location:
                    location = InterviewLocation.objects.filter(is_active=True).first()
                if not location:
                    location = InterviewLocation.objects.create(
                        location_name="Smart HRMS Corporate HQ",
                        address="Main Campus, Tech Hub",
                        city="Corporate",
                        is_active=True,
                    )

                interviewer = None
                if interviewer_id:
                    interviewer = HRManager.objects.filter(pk=interviewer_id, is_active=True).first()
                if not interviewer:
                    interviewer = getattr(request.user, "hr_profile", None)

                interview = Interview.objects.create(
                    application=application,
                    location=location,
                    interviewer=interviewer,
                    interview_type=interview_type,
                    interview_date=i_date,
                    interview_time=i_time,
                    instructions=instructions,
                    remarks=remarks,
                    status="SCHEDULED",
                    attendance="NOT_MARKED",
                )

            application.status = "INTERVIEW_SCHEDULED"
            application.save(update_fields=["status", "updated_at"])

            venue_display = interview.location.location_name if interview.location else "Headquarters"
            addr_display = interview.location.address if interview.location else ""
            formatted_date = interview.interview_date.strftime("%d %B %Y")
            formatted_time = interview.interview_time.strftime("%I:%M %p")

            notif_msg = (
                f"Your interview for {application.vacancy.title} has been successfully scheduled.\n\n"
                f"Date: {formatted_date}\n"
                f"Time: {formatted_time}\n"
                f"Venue: {venue_display}\n"
                f"Address: {addr_display}\n\n"
                f"Please report to the interview venue at least 10 minutes before the scheduled time."
            )

            send_candidate_notification(
                candidate=application.candidate,
                application=application,
                title="Interview Scheduled",
                message=notif_msg,
                notification_type="INTERVIEW_SCHEDULED",
                link_url=reverse_lazy("candidates:applications"),
            )

        messages.success(
            request,
            f"Interview successfully scheduled for {application.candidate.first_name} {application.candidate.last_name} on {formatted_date} at {formatted_time}.",
        )
        return redirect("hr:application_detail", pk=application.pk)


class InterviewCreateView(HRRequiredMixin, View):
    """Allows creating or scheduling an interview via POST with application_id in body."""

    def post(self, request):
        application_id = request.POST.get("application_id")
        if application_id:
            return InterviewScheduleView().post(request, application_id=application_id)
        messages.error(request, "Application ID is required to schedule interview.")
        return redirect("hr:application_list")


class InterviewAttendanceView(HRRequiredMixin, View):
    """Allows HR / Interviewer to record offline candidate attendance (ATTENDED / NO_SHOW)."""

    def post(self, request, pk):
        interview = get_object_or_404(
            Interview.objects.select_related("application__candidate", "application__vacancy"),
            pk=pk,
        )
        attendance = request.POST.get("attendance")
        app = interview.application

        if attendance == "ATTENDED":
            interview.attendance = "ATTENDED"
            interview.status = "SCHEDULED"
            interview.save(update_fields=["attendance", "status", "updated_at"])

            app.status = "INTERVIEW_REVIEW"
            app.save(update_fields=["status", "updated_at"])

            messages.success(
                request,
                f"Candidate {app.candidate.first_name} {app.candidate.last_name} marked as ATTENDED. You may now complete the Interview Evaluation.",
            )
        elif attendance == "NO_SHOW":
            interview.attendance = "NO_SHOW"
            interview.status = "COMPLETED"
            interview.save(update_fields=["attendance", "status", "updated_at"])

            app.status = "REJECTED"
            app.save(update_fields=["status", "updated_at"])

            send_candidate_notification(
                candidate=app.candidate,
                application=app,
                title="Interview Attendance Update",
                message=f"We noted that you were unable to attend your scheduled offline interview for {app.vacancy.title}. As attendance was not recorded, your application has been closed.",
                notification_type="INTERVIEW_NO_SHOW",
                link_url=reverse_lazy("candidates:applications"),
            )
            messages.warning(
                request,
                f"Candidate {app.candidate.first_name} {app.candidate.last_name} marked as NO-SHOW. Application has been closed.",
            )
        else:
            messages.error(request, "Invalid attendance status.")

        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("hr:interview_list")


class InterviewEvaluationView(HRRequiredMixin, View):
    """Allows HR / Interviewer to score an attended interview across 5 dimensions, write confidential notes, and make a PASS/FAIL decision."""

    def get(self, request, pk):
        interview = get_object_or_404(
            Interview.objects.select_related(
                "application__candidate__user",
                "application__vacancy__department",
                "interviewer__user",
                "location",
            ),
            pk=pk,
        )
        if interview.attendance != "ATTENDED":
            messages.warning(request, "Interview evaluation can only be performed after candidate attendance is marked as ATTENDED.")
            return redirect("hr:interview_list")

        existing_eval = getattr(interview, "evaluation", None)

        context = {
            "interview": interview,
            "application": interview.application,
            "candidate": interview.application.candidate,
            "job": interview.application.vacancy,
            "evaluation": existing_eval,
        }
        return render(request, "hr/interview_evaluation.html", context)

    def post(self, request, pk):
        interview = get_object_or_404(
            Interview.objects.select_related("application__candidate", "application__vacancy"),
            pk=pk,
        )

        if interview.attendance != "ATTENDED":
            messages.error(request, "Cannot evaluate an interview that was not attended.")
            return redirect("hr:interview_list")

        tech_rating = int(request.POST.get("technical_rating", 3))
        comm_rating = int(request.POST.get("communication_rating", 3))
        ps_rating = int(request.POST.get("problem_solving_rating", 3))
        role_rating = int(request.POST.get("role_skill_rating", 3))
        prof_rating = int(request.POST.get("professionalism_rating", 3))
        comments = request.POST.get("comments", "").strip()
        decision = request.POST.get("decision", "PASS")

        # Clamp ratings between 1 and 5
        tech_rating = max(1, min(5, tech_rating))
        comm_rating = max(1, min(5, comm_rating))
        ps_rating = max(1, min(5, ps_rating))
        role_rating = max(1, min(5, role_rating))
        prof_rating = max(1, min(5, prof_rating))

        overall_rating = (tech_rating + comm_rating + ps_rating + role_rating + prof_rating) / 5.0
        hr_profile = getattr(request.user, "hr_profile", None)

        with transaction.atomic():
            evaluation, _ = InterviewEvaluation.objects.update_or_create(
                interview=interview,
                defaults={
                    "technical_rating": tech_rating,
                    "communication_rating": comm_rating,
                    "problem_solving_rating": ps_rating,
                    "role_skill_rating": role_rating,
                    "professionalism_rating": prof_rating,
                    "overall_rating": round(overall_rating, 2),
                    "comments": comments,
                    "result": decision,
                    "evaluated_by": hr_profile,
                },
            )

            interview.status = "COMPLETED"
            interview.save(update_fields=["status", "updated_at"])

            app = interview.application

            if decision == "PASS":
                app.status = "SELECTED"
                app.save(update_fields=["status", "updated_at"])

                # Send Selected Candidate Notification
                send_candidate_notification(
                    candidate=app.candidate,
                    application=app,
                    title="Congratulations! You Are Selected",
                    message=f"Congratulations! You have been selected for the position of {app.vacancy.title}. Please check your candidate portal for further joining information.",
                    notification_type="INTERVIEW_PASSED",
                    link_url=reverse_lazy("candidates:applications"),
                )

                messages.success(
                    request,
                    f"Interview evaluation submitted successfully! Candidate {app.candidate.first_name} {app.candidate.last_name} is marked as SELECTED.",
                )
            else:
                app.status = "REJECTED"
                app.save(update_fields=["status", "updated_at"])

                send_candidate_notification(
                    candidate=app.candidate,
                    application=app,
                    title="Interview Result",
                    message=(
                        f"Thank you for participating in the interview for {app.vacancy.title}. "
                        f"After completing the selection process, we regret to inform you that you have not been selected for this position. "
                        f"We appreciate your time and interest in our organization and wish you success in your future opportunities."
                    ),
                    notification_type="INTERVIEW_FAILED",
                    link_url=reverse_lazy("candidates:applications"),
                )

                messages.info(
                    request,
                    f"Interview evaluation submitted. Candidate {app.candidate.first_name} {app.candidate.last_name} marked as REJECTED.",
                )

        return redirect("hr:interview_list")


class InterviewStatusUpdateView(HRRequiredMixin, View):
    """Allows HR to update interview status (SCHEDULED, COMPLETED, CANCELLED)."""

    def post(self, request, pk):
        interview = get_object_or_404(Interview, pk=pk)
        new_status = request.POST.get("status")
        if new_status in ["SCHEDULED", "COMPLETED", "CANCELLED"]:
            interview.status = new_status
            interview.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Interview status updated to {new_status}.")
        next_url = request.POST.get("next") or reverse("hr:interview_list")
        return redirect(next_url)


class CandidateForwardToAdminView(HRRequiredMixin, View):
    """Allows HR to forward a SELECTED candidate to Admin for employee onboarding and verification."""

    def post(self, request, pk):
        import datetime
        from django.urls import reverse

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy__department"),
            pk=pk,
        )

        if application.status not in ["SELECTED", "FORWARDED_TO_ADMIN"]:
            messages.error(request, "Only candidates who have been marked as SELECTED can be forwarded to Admin.")
            return redirect("hr:application_detail", pk=pk)

        cand_user = application.candidate.user
        
        # Check existing onboarding status
        existing_emp = Employee.objects.filter(Q(user=cand_user) | Q(candidate=application.candidate)).first()
        if existing_emp:
            existing_approval = EmployeeApproval.objects.filter(employee=existing_emp).first()
            if existing_approval and existing_approval.status == "APPROVED":
                messages.warning(request, "Employee onboarding has already been completed.")
                return redirect("hr:application_detail", pk=pk)

        custom_dept_id = request.POST.get("department")
        dept = None
        if custom_dept_id:
            dept = Department.objects.filter(pk=custom_dept_id).first()
        if not dept:
            dept = application.vacancy.department or Department.objects.first()

        custom_designation = request.POST.get("designation", "").strip()
        designation = custom_designation or application.vacancy.title

        team_id = request.POST.get("team")
        team = None
        if team_id:
            team = Team.objects.filter(pk=team_id).first()

        team_lead_id = request.POST.get("team_lead")
        team_lead = None
        if team_lead_id:
            team_lead = User.objects.filter(pk=team_lead_id).first()
        elif team and team.team_lead:
            team_lead = team.team_lead

        joining_date_str = request.POST.get("joining_date", "").strip()
        try:
            joining_date = datetime.date.fromisoformat(joining_date_str) if joining_date_str else timezone.now().date()
        except Exception:
            joining_date = timezone.now().date()

        employment_type = request.POST.get("employment_type", "FULL_TIME")
        work_location = request.POST.get("work_location", "").strip()
        notes = request.POST.get("notes", "").strip() or request.POST.get("hr_justification", "").strip()

        with transaction.atomic():
            application.is_forwarded_to_admin = True
            application.forwarded_at = timezone.now()
            application.forwarded_by = request.user
            application.status = "FORWARDED_TO_ADMIN"
            application.save(update_fields=["is_forwarded_to_admin", "forwarded_at", "forwarded_by", "status", "updated_at"])

            # Ensure Employee record in INACTIVE state
            emp_code = f"EMP{cand_user.pk:04d}"
            employee, emp_created = Employee.objects.get_or_create(
                user=cand_user,
                defaults={
                    "candidate": application.candidate,
                    "employee_code": emp_code,
                    "department": dept,
                    "team": team,
                    "team_lead": team_lead,
                    "designation": designation,
                    "joining_date": joining_date,
                    "employment_type": employment_type,
                    "employment_status": "INACTIVE",
                    "work_location": work_location,
                    "created_by": request.user,
                },
            )
            if not emp_created:
                employee.candidate = application.candidate
                employee.department = dept
                employee.team = team
                employee.team_lead = team_lead
                employee.designation = designation
                employee.joining_date = joining_date
                employee.employment_type = employment_type
                employee.employment_status = "INACTIVE"
                employee.work_location = work_location
                employee.created_by = request.user
                employee.save(update_fields=[
                    "candidate", "department", "team", "team_lead", "designation",
                    "joining_date", "employment_type", "employment_status", "work_location", "created_by", "updated_at"
                ])

            # Ensure EmployeeApproval record in PENDING state
            approval, _ = EmployeeApproval.objects.get_or_create(
                employee=employee,
                defaults={
                    "status": "PENDING",
                    "requested_by": request.user,
                    "comments": notes,
                },
            )
            if approval.status != "PENDING":
                approval.status = "PENDING"
                approval.requested_by = request.user
                approval.comments = notes
                approval.save(update_fields=["status", "requested_by", "comments"])

            # Create real Admin Notification
            hr_name = request.user.name or (request.user.hr_profile.full_name if hasattr(request.user, "hr_profile") else request.user.email)
            cand_name = f"{application.candidate.first_name} {application.candidate.last_name}".strip()
            pos_title = application.vacancy.title
            AdminNotification.objects.create(
                title="New Employee Onboarding Request",
                message=f"{hr_name} has submitted an employee onboarding request for {cand_name} ({pos_title}).",
                notification_type="EMPLOYEE_APPROVAL",
                link_url=reverse("admin_module:recruitment_approval_review", kwargs={"employee_id": employee.pk}),
            )

        messages.success(
            request,
            "Employee onboarding request submitted successfully and is awaiting Admin approval.",
        )
        return redirect("hr:application_detail", pk=pk)


class DepartmentDetailsAPIView(HRRequiredMixin, View):
    """API endpoint returning department leader, teams, and eligible team leads for a department."""

    def get(self, request, department_id):
        dept = get_object_or_404(Department.objects.select_related("department_leader"), pk=department_id)
        teams = Team.objects.filter(department=dept, is_active=True).select_related("team_lead")

        teams_data = [
            {
                "id": t.pk,
                "name": t.team_name,
                "team_lead_id": t.team_lead.pk if t.team_lead else None,
                "team_lead_name": t.team_lead.get_full_name() or t.team_lead.email if t.team_lead else "",
            }
            for t in teams
        ]

        leader_name = ""
        leader_id = None
        if dept.department_leader:
            leader_name = dept.department_leader.get_full_name() or dept.department_leader.email
            leader_id = dept.department_leader.pk

        return JsonResponse({
            "department_id": dept.pk,
            "department_name": dept.name,
            "department_leader": leader_name,
            "department_leader_id": leader_id,
            "teams": teams_data,
        })

User = get_user_model()
class WarningListView(HRRequiredMixin, ListView):
    model = PerformanceWarning
    template_name = "hr/warning_list.html"
    context_object_name = "warnings"
    paginate_by = 10

    def get_queryset(self):
        queryset = PerformanceWarning.objects.select_related(
            "employee", "issued_by__user"
        ).all()
        severity = self.request.GET.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_severity"] = self.request.GET.get("severity", "")
        context["employees"] = User.objects.filter(is_active=True).exclude(
            pk=self.request.user.pk
        )
        return context


''' 
class WarningCreateView(HRRequiredMixin, View):
    def post(self, request):
        employee_id = request.POST.get("employee_id")
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        severity = request.POST.get("severity", "LOW")
        action_plan = request.POST.get("action_plan", "").strip()

        employee = get_object_or_404(User, pk=employee_id)
        hr_profile = getattr(request.user, "hr_profile", None)

        PerformanceWarning.objects.create(
            employee=employee,
            issued_by=hr_profile,
            subject=subject,
            description=description,
            severity=severity,
            action_plan=action_plan,
        )
        messages.success(
            request,
            f"Notice recorded for {employee.get_full_name() or employee.username}.",
        )
        return redirect("hr:warning_list")


class WarningStatusUpdateView(HRRequiredMixin, View):
    def post(self, request, pk):
        warning_record = get_object_or_404(PerformanceWarning, pk=pk)
        new_status = request.POST.get("status")
        if new_status in ["ACTIVE", "RESOLVED", "ESCALATED"]:
            warning_record.status = new_status
            warning_record.save()
            messages.info(
                request,
                f"Warning status updated to {warning_record.get_status_display()}.",
            )
        return redirect("hr:warning_list")

'''
class AptitudeResultListView(HRRequiredMixin, ListView):
    model = AptitudeResult
    template_name = "hr/aptitude_test_list.html"
    context_object_name = "results"
    paginate_by = 15

    def get_queryset(self):
        queryset = AptitudeResult.objects.select_related(
            "test",
            "application__candidate__user",
            "application__vacancy",
        ).order_by("-completed_at")

        test_id = self.request.GET.get("test_id")
        if test_id:
            queryset = queryset.filter(test_id=test_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tests"] = AptitudeTest.objects.all()
        context["selected_test"] = self.request.GET.get("test_id", "")
        return context


class EmployeeReportListView(HRRequiredMixin, ListView):
    model = EmployeeReport
    template_name = "hr/employee_report_list.html"
    context_object_name = "reports"
    paginate_by = 10

    def get_queryset(self):
        queryset = EmployeeReport.objects.select_related(
            "employee__user", "employee__department", "reviewed_by__user", "performance_review"
        ).order_by("-submitted_at")

        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "")
        return context


class EmployeeReportReviewView(HRRequiredMixin, View):
    template_name = "hr/employee_report_review.html"

    def get(self, request, pk):
        report = get_object_or_404(
            EmployeeReport.objects.select_related(
                "employee__user", "employee__department", "reviewed_by__user"
            ),
            pk=pk,
        )

        # Automatically transition SUBMITTED -> UNDER_REVIEW if not yet reviewed
        if report.status == "SUBMITTED":
            report.status = "UNDER_REVIEW"
            report.save(update_fields=["status"])

        existing_review = getattr(report, "performance_review", None)
        initial_data = {}
        if existing_review:
            initial_data["status_decision"] = report.status if report.status in ["REVIEWED", "NEEDS_CORRECTION"] else "REVIEWED"

        form = EmployeePerformanceEvaluationForm(instance=existing_review, initial=initial_data)

        # Get employee performance history
        previous_reports = EmployeeReport.objects.filter(
            employee=report.employee,
            status="REVIEWED",
            performance_review__isnull=False,
        ).exclude(pk=report.pk).select_related("performance_review").order_by("-week_start_date")[:5]

        hr_profile = getattr(request.user, "hr_profile", None)

        return render(
            request,
            self.template_name,
            {
                "report": report,
                "review": existing_review,
                "form": form,
                "hr_profile": hr_profile,
                "previous_reports": previous_reports,
            },
        )

    def post(self, request, pk):
        report = get_object_or_404(
            EmployeeReport.objects.select_related("employee__user"),
            pk=pk,
        )
        existing_review = getattr(report, "performance_review", None)
        form = EmployeePerformanceEvaluationForm(request.POST, instance=existing_review)

        if form.is_valid():
            review = form.save(commit=False)
            review.employee_report = report
            review.employee = report.employee
            hr_profile = getattr(request.user, "hr_profile", None)
            review.reviewed_by = hr_profile
            review.calculate_scores()
            review.save()

            status_decision = form.cleaned_data.get("status_decision", "REVIEWED")
            report.status = status_decision
            report.hr_comments = form.cleaned_data.get("overall_feedback") or ""
            report.reviewed_by = hr_profile
            report.reviewed_at = timezone.now()
            report.save()

            # Create notification for employee
            if status_decision == "REVIEWED":
                notif_title = "Weekly Report Reviewed & Graded"
                notif_msg = f"HR reviewed your weekly report '{report.title}' ({report.week_start_date} to {report.week_end_date}) with a score of {review.average_score}/5.0 ({review.performance_percentage}%)."
            else:
                notif_title = "Weekly Report Needs Correction"
                notif_msg = f"HR returned your weekly report '{report.title}' ({report.week_start_date} to {report.week_end_date}) for corrections. Feedback: {(review.overall_feedback or '')[:100]}..."

            Notification.objects.create(
                employee=report.employee,
                title=notif_title,
                message=notif_msg,
                notification_type="REPORT_FEEDBACK",
            )

            status_text = "reviewed and evaluated" if status_decision == "REVIEWED" else "returned for correction"
            messages.success(
                request,
                f"Weekly report for {report.employee.full_name or report.employee.user.username} has been {status_text} successfully!",
            )
            return redirect("hr:employee_report_list")
        else:
            messages.error(request, "Please correct the errors in the evaluation matrix form.")
            hr_profile = getattr(request.user, "hr_profile", None)
            previous_reports = EmployeeReport.objects.filter(
                employee=report.employee,
                status="REVIEWED",
                performance_review__isnull=False,
            ).exclude(pk=report.pk).select_related("performance_review").order_by("-week_start_date")[:5]

            return render(
                request,
                self.template_name,
                {
                    "report": report,
                    "review": existing_review,
                    "form": form,
                    "hr_profile": hr_profile,
                    "previous_reports": previous_reports,
                },
            )


class EmployeePerformanceAnalysisView(HRRequiredMixin, View):
    template_name = "hr/employee_performance_analysis.html"

    def get(self, request):
        employee_id = request.GET.get("employee_id")
        department_id = request.GET.get("department_id")

        reports = EmployeeReport.objects.filter(
            status="REVIEWED",
            performance_review__isnull=False,
        ).select_related("employee__user", "employee__department", "performance_review").order_by("-week_start_date")

        if employee_id:
            reports = reports.filter(employee_id=employee_id)
        if department_id:
            reports = reports.filter(employee__department_id=department_id)

        all_employees = Employee.objects.filter(employment_status="ACTIVE").select_related("user", "department")
        departments = Department.objects.filter(is_active=True)

        total_evaluated = reports.count()
        if total_evaluated > 0:
            avg_score = sum(r.performance_review.average_score for r in reports) / total_evaluated
            avg_percentage = sum(r.performance_review.performance_percentage for r in reports) / total_evaluated
            excellent_count = sum(1 for r in reports if r.performance_review.performance_percentage >= 90)
            good_count = sum(1 for r in reports if 75 <= r.performance_review.performance_percentage < 90)
            average_count = sum(1 for r in reports if 60 <= r.performance_review.performance_percentage < 75)
            improvement_count = sum(1 for r in reports if r.performance_review.performance_percentage < 60)
        else:
            avg_score = 0.0
            avg_percentage = 0.0
            excellent_count = 0
            good_count = 0
            average_count = 0
            improvement_count = 0

        context = {
            "reports": reports[:25],
            "all_employees": all_employees,
            "departments": departments,
            "selected_employee": employee_id,
            "selected_department": department_id,
            "total_evaluated": total_evaluated,
            "avg_score": round(avg_score, 2),
            "avg_percentage": round(avg_percentage, 1),
            "excellent_count": excellent_count,
            "good_count": good_count,
            "average_count": average_count,
            "improvement_count": improvement_count,
        }
        return render(request, self.template_name, context)


class WarningListView(HRRequiredMixin, ListView):
    model = PerformanceWarning
    template_name = "hr/warning_list.html"
    context_object_name = "warnings"
    paginate_by = 10

    def get_queryset(self):
        queryset = PerformanceWarning.objects.select_related(
            "employee__user", "employee__department", "issued_by__user"
        ).order_by("-warning_date")

        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "")
        context["employees"] = Employee.objects.filter(
            employment_status="ACTIVE"
        ).select_related("user")
        return context


class WarningCreateView(HRRequiredMixin, View):

    def post(self, request):
        employee_id = request.POST.get("employee_id")
        reason = request.POST.get("reason", "").strip()
        hr_recommendation = request.POST.get("hr_recommendation", "").strip()

        employee = get_object_or_404(Employee, pk=employee_id)
        hr_profile = getattr(request.user, "hr_profile", None)

        PerformanceWarning.objects.create(
            employee=employee,
            issued_by=hr_profile,
            reason=reason,
            hr_recommendation=hr_recommendation,
            status="OPEN",
        )
        Notification.objects.create(
            employee=employee,
            title="Performance Warning Notice",
            message=f"A performance warning has been issued: {reason}",
            notification_type="WARNING",
        )
        messages.success(
            request, f"Warning issued for {employee.employee_code}."
        )
        return redirect("hr:warning_list")


class WarningStatusUpdateView(HRRequiredMixin, View):

    def post(self, request, pk):
        warning_record = get_object_or_404(PerformanceWarning, pk=pk)
        new_status = request.POST.get("status")
        if new_status in ["OPEN", "SENT_TO_ADMIN", "RESOLVED"]:
            warning_record.status = new_status
            warning_record.save()
            messages.info(
                request,
                f"Warning status updated to {warning_record.get_status_display()}.",
            )
        return redirect("hr:warning_list")


class PerformanceReviewListView(HRRequiredMixin, ListView):
  model = EmployeePerformance
  template_name = "hr/performance_list.html"
  context_object_name = "reviews"
  paginate_by = 10

  def get_queryset(self):
    queryset = EmployeePerformance.objects.select_related(
        "employee__user", "employee__department", "reviewed_by__user"
    ).order_by("-review_date")

    rating_filter = self.request.GET.get("rating")
    if rating_filter:
      queryset = queryset.filter(rating=rating_filter)
    return queryset

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["selected_rating"] = self.request.GET.get("rating", "")
    context["employees"] = Employee.objects.filter(
        employment_status="ACTIVE"
    ).select_related("user", "department")
    return context


class PerformanceReviewCreateView(HRRequiredMixin, View):

  def post(self, request):
    employee_id = request.POST.get("employee_id")
    review_period = request.POST.get("review_period", "").strip()
    rating = request.POST.get("rating")
    comments = request.POST.get("comments", "").strip()

    employee = get_object_or_404(Employee, pk=employee_id)
    hr_profile = getattr(request.user, "hr_profile", None)

    EmployeePerformance.objects.create(
        employee=employee,
        reviewed_by=hr_profile,
        review_period=review_period,
        rating=rating,
        comments=comments,
    )
    Notification.objects.create(
        employee=employee,
        title="Performance Review Logged",
        message=f"HR has completed your performance appraisal for {review_period}.",
        notification_type="GENERAL",
    )
    messages.success(
        request,
        f"Performance evaluation logged for {employee.employee_code}.",
    )
    return redirect("hr:performance_list")


def send_admin_notification(title, message, notification_type="GENERAL", link_url=""):
    """Helper to dispatch a real notification to Admin user(s)."""
    from admin_module.models import AdminNotification
    admin_users = User.objects.filter(role=User.RoleChoices.ADMIN)
    created = []
    for admin_u in admin_users:
        created.append(
            AdminNotification.objects.create(
                admin_user=admin_u,
                title=title,
                message=message,
                notification_type=notification_type,
                link_url=link_url,
            )
        )
    return created


def send_hr_notification(hr_manager, title, message, notification_type="GENERAL", link_url=""):
    """Helper to dispatch a real notification to an HR Manager."""
    return HRNotification.objects.create(
        hr_manager=hr_manager,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url,
    )


class HRWeeklyReportListView(HRRequiredMixin, ListView):
    model = HRWeeklyReport
    template_name = "hr/weekly_report_list.html"
    context_object_name = "reports"
    paginate_by = 10

    def get_queryset(self):
        hr_profile = getattr(self.request.user, "hr_profile", None)
        if not hr_profile:
            return HRWeeklyReport.objects.none()

        qs = HRWeeklyReport.objects.filter(hr_manager=hr_profile).select_related(
            "hr_manager", "performance_review"
        ).order_by("-week_start_date", "-created_at")

        status_filter = self.request.GET.get("status")
        if status_filter:
            if status_filter == "SUBMITTED":
                qs = qs.filter(status__in=["SUBMITTED", "UNDER_REVIEW"])
            else:
                qs = qs.filter(status=status_filter)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hr_profile = getattr(self.request.user, "hr_profile", None)
        all_reports = HRWeeklyReport.objects.filter(hr_manager=hr_profile) if hr_profile else HRWeeklyReport.objects.none()

        context["selected_status"] = self.request.GET.get("status", "")
        context["total_reports_count"] = all_reports.count()
        context["draft_count"] = all_reports.filter(status="DRAFT").count()
        context["submitted_count"] = all_reports.filter(status__in=["SUBMITTED", "UNDER_REVIEW"]).count()
        context["reviewed_count"] = all_reports.filter(status="REVIEWED").count()
        context["needs_improvement_count"] = all_reports.filter(status="NEEDS_IMPROVEMENT").count()

        # Performance summary metrics
        reviewed_reports = all_reports.filter(status="REVIEWED", performance_review__isnull=False)
        if reviewed_reports.exists():
            avg_pct = sum([r.performance_review.performance_percentage for r in reviewed_reports]) / reviewed_reports.count()
            avg_score = sum([r.performance_review.average_score for r in reviewed_reports]) / reviewed_reports.count()
            context["overall_avg_percentage"] = round(avg_pct, 1)
            context["overall_avg_score"] = round(avg_score, 2)
        else:
            context["overall_avg_percentage"] = None
            context["overall_avg_score"] = None

        return context


class HRWeeklyReportCreateView(HRRequiredMixin, View):
    template_name = "hr/weekly_report_form.html"

    def get(self, request):
        hr_profile = get_object_or_404(HRManager, user=request.user)
        today = timezone.localdate()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)

        form = HRWeeklyReportForm(
            hr_manager=hr_profile,
            initial={
                "week_start_date": start_of_week,
                "week_end_date": end_of_week,
            }
        )
        return render(request, self.template_name, {
            "form": form,
            "hr_profile": hr_profile,
            "is_edit": False,
        })

    def post(self, request):
        hr_profile = get_object_or_404(HRManager, user=request.user)
        form = HRWeeklyReportForm(request.POST, hr_manager=hr_profile)
        action = request.POST.get("action", "SUBMIT")

        if form.is_valid():
            report = form.save(commit=False)
            report.hr_manager = hr_profile

            if action == "SUBMIT":
                report.status = "SUBMITTED"
                report.submitted_at = timezone.now()
                report.save()

                admin_link = f"/admin-portal/hr-managers/reports/{report.pk}/"
                send_admin_notification(
                    title="New HR Weekly Report Submitted",
                    message=f"{hr_profile.full_name}, HR Manager, submitted a weekly performance report for {report.week_display}.",
                    notification_type="HR_REPORT_SUBMITTED",
                    link_url=admin_link,
                )
                messages.success(request, f"Weekly report for {report.week_display} successfully submitted to Admin!")
            else:
                report.status = "DRAFT"
                report.save()
                messages.info(request, f"Weekly report for {report.week_display} saved as Draft.")

            return redirect("hr:weekly_report_list")

        return render(request, self.template_name, {
            "form": form,
            "hr_profile": hr_profile,
            "is_edit": False,
        })


class HRWeeklyReportUpdateView(HRRequiredMixin, View):
    template_name = "hr/weekly_report_form.html"

    def get(self, request, pk):
        hr_profile = get_object_or_404(HRManager, user=request.user)
        report = get_object_or_404(HRWeeklyReport, pk=pk, hr_manager=hr_profile)

        if not report.is_editable:
            messages.warning(request, "This report has already been submitted or reviewed and cannot be edited.")
            return redirect("hr:weekly_report_detail", pk=pk)

        form = HRWeeklyReportForm(instance=report, hr_manager=hr_profile)
        return render(request, self.template_name, {
            "form": form,
            "report": report,
            "hr_profile": hr_profile,
            "is_edit": True,
        })

    def post(self, request, pk):
        hr_profile = get_object_or_404(HRManager, user=request.user)
        report = get_object_or_404(HRWeeklyReport, pk=pk, hr_manager=hr_profile)

        if not report.is_editable:
            messages.warning(request, "This report has already been submitted or reviewed and cannot be edited.")
            return redirect("hr:weekly_report_detail", pk=pk)

        form = HRWeeklyReportForm(request.POST, instance=report, hr_manager=hr_profile)
        action = request.POST.get("action", "SUBMIT")

        if form.is_valid():
            report = form.save(commit=False)
            if action == "SUBMIT":
                report.status = "SUBMITTED"
                report.submitted_at = timezone.now()
                report.save()

                admin_link = f"/admin-portal/hr-managers/reports/{report.pk}/"
                send_admin_notification(
                    title="HR Weekly Report Submitted",
                    message=f"{hr_profile.full_name}, HR Manager, submitted an updated weekly report for {report.week_display}.",
                    notification_type="HR_REPORT_SUBMITTED",
                    link_url=admin_link,
                )
                messages.success(request, f"Weekly report for {report.week_display} submitted to Admin!")
            else:
                report.status = "DRAFT"
                report.save()
                messages.info(request, f"Weekly report for {report.week_display} updated successfully.")

            return redirect("hr:weekly_report_list")

        return render(request, self.template_name, {
            "form": form,
            "report": report,
            "hr_profile": hr_profile,
            "is_edit": True,
        })


class HRWeeklyReportSubmitView(HRRequiredMixin, View):
    def post(self, request, pk):
        hr_profile = get_object_or_404(HRManager, user=request.user)
        report = get_object_or_404(HRWeeklyReport, pk=pk, hr_manager=hr_profile)

        if report.status in ["DRAFT", "NEEDS_IMPROVEMENT"]:
            report.status = "SUBMITTED"
            report.submitted_at = timezone.now()
            report.save()

            admin_link = f"/admin-portal/hr-managers/reports/{report.pk}/"
            send_admin_notification(
                title="HR Weekly Report Submitted",
                message=f"{hr_profile.full_name}, HR Manager, submitted a weekly performance report for {report.week_display}.",
                notification_type="HR_REPORT_SUBMITTED",
                link_url=admin_link,
            )
            messages.success(request, f"Weekly report for {report.week_display} submitted to Admin.")
        else:
            messages.warning(request, "Report is already submitted or reviewed.")

        return redirect("hr:weekly_report_list")


class HRWeeklyReportDetailView(HRRequiredMixin, View):
    template_name = "hr/weekly_report_detail.html"

    def get(self, request, pk):
        hr_profile = get_object_or_404(HRManager, user=request.user)
        report = get_object_or_404(
            HRWeeklyReport.objects.select_related("hr_manager", "performance_review__reviewed_by"),
            pk=pk,
            hr_manager=hr_profile,
        )

        notif_id = request.GET.get("notif_id")
        if notif_id:
            HRNotification.objects.filter(notification_id=notif_id, hr_manager=hr_profile).update(is_read=True)

        review = getattr(report, "performance_review", None)
        return render(request, self.template_name, {
            "report": report,
            "review": review,
            "hr_profile": hr_profile,
        })


class HRPerformanceAnalysisView(HRRequiredMixin, View):
    template_name = "hr/performance_analysis.html"

    def get(self, request):
        hr_profile = get_object_or_404(HRManager, user=request.user)
        reports = HRWeeklyReport.objects.filter(
            hr_manager=hr_profile,
            status="REVIEWED",
            performance_review__isnull=False,
        ).select_related("performance_review").order_by("-week_start_date")

        total_submitted = HRWeeklyReport.objects.filter(hr_manager=hr_profile).count()
        total_reviewed = reports.count()
        pending_review = HRWeeklyReport.objects.filter(
            hr_manager=hr_profile,
            status__in=["SUBMITTED", "UNDER_REVIEW"]
        ).count()

        if total_reviewed > 0:
            avg_pct = sum([r.performance_review.performance_percentage for r in reports]) / total_reviewed
            avg_score = sum([r.performance_review.average_score for r in reports]) / total_reviewed
            overall_avg_pct = round(avg_pct, 1)
            overall_avg_score = round(avg_score, 2)
        else:
            overall_avg_pct = 0.0
            overall_avg_score = 0.0

        return render(request, self.template_name, {
            "hr_profile": hr_profile,
            "reports": reports,
            "total_submitted": total_submitted,
            "total_reviewed": total_reviewed,
            "pending_review": pending_review,
            "overall_avg_pct": overall_avg_pct,
            "overall_avg_score": overall_avg_score,
        })
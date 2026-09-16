
from admin_module.models import Department
from candidates.models import JobApplication
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.utils import timezone
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
    PerformanceWarning,
)

from .forms import (
    AptitudeQuestionForm,
    AptitudeTestForm,
    HRDocumentUploadForm,
    HRProfileEditForm,
)
from .models import (
    AptitudeAttempt,
    AptitudeQuestion,
    AptitudeResult,
    AptitudeTest,
    HRManager,
    Interview,
    JobVacancy,
)
from .question_bank import seed_default_questions

User = get_user_model()

''' 
from django.views.generic import TemplateView,ListView, CreateView, UpdateView,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin , UserPassesTestMixin
from django.db.models import Count, Q
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from admin_module.models import Department
#from .models import HRManager,JobVacancy
#from .models import HRManager,EmployeeWarning
from candidates.models import JobApplication,JobVacancy
from django.contrib.auth import get_user_model
from employees.models import PerformanceWarning
# Import models based on your project structure
#from .models import Employee, EmployeeReport, EmployeePerformance, PerformanceWarning
from employees.models import (
    Employee,
    EmployeeReport,
    EmployeePerformance,
    PerformanceWarning,
)

from .models import (
    HRManager,
    AptitudeTest,
    AptitudeQuestion,
    AptitudeResult,
    Interview,
    JobVacancy , #as HRJobVacancy,
)

from candidates.models import JobApplication
''' 

class HRDashboardView(LoginRequiredMixin, TemplateView):
#class HRDashboardView( TemplateView):
    template_name = "hr/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
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
        context["critical_warnings"] = PerformanceWarning.objects.select_related("employee__user").filter(
            Q(status="OPEN") | Q(status="SENT_TO_ADMIN")
        ).order_by("-warning_date")[:5]

        return context



#Login Page Related Stuff

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
        return redirect("home")


class HRProfileView(HRRequiredMixin, View):
    """View aggregated HR profile details and manage document uploads."""
    template_name = "hr/profile.html"

    def get_context(self, request, doc_form=None):
        user = request.user
        hr_profile = getattr(user, "hr_profile", None)
        if not hr_profile and getattr(user, "role", "") == User.RoleChoices.HR:
            hr_profile, _ = HRManager.objects.get_or_create(
                user=user,
                defaults={"employee_code": f"HR-{user.id:04d}"},
            )
        linked_employee = getattr(user, "employee_profile", None)
        linked_candidate = getattr(user, "candidate_profile", None) or (
            getattr(linked_employee, "candidate", None) if linked_employee else None
        )
        documents = linked_employee.documents.all().order_by("-uploaded_at") if linked_employee else []
        profile_photo = (
            linked_employee.profile_photo
            if (linked_employee and linked_employee.profile_photo)
            else (linked_candidate.profile_photo if (linked_candidate and linked_candidate.profile_photo) else None)
        )

        name_parts = (user.name or "").strip().split(" ", 1)
        first_name_fallback = name_parts[0] if name_parts else ""
        last_name_fallback = name_parts[1] if len(name_parts) > 1 else ""

        return {
            "hr_profile": hr_profile,
            "user_obj": user,
            "linked_employee": linked_employee,
            "linked_candidate": linked_candidate,
            "documents": documents,
            "profile_photo": profile_photo,
            "first_name_fallback": first_name_fallback,
            "last_name_fallback": last_name_fallback,
            "doc_form": doc_form or HRDocumentUploadForm(),
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context(request))

    def post(self, request):
        action = request.POST.get("action")
        user = request.user
        hr_profile = getattr(user, "hr_profile", None)
        if not hr_profile and getattr(user, "role", "") == User.RoleChoices.HR:
            hr_profile, _ = HRManager.objects.get_or_create(
                user=user,
                defaults={"employee_code": f"HR-{user.id:04d}"},
            )

        linked_employee = getattr(user, "employee_profile", None)
        if not linked_employee:
            linked_employee = Employee.objects.create(
                user=user,
                employee_code=hr_profile.employee_code or f"HR-{user.id:04d}",
                department=hr_profile.department or Department.objects.first(),
                designation="HR Manager",
                joining_date=hr_profile.joining_date or timezone.now().date(),
                employment_status="ACTIVE",
            )

        if action == "upload_document":
            doc_form = HRDocumentUploadForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.employee = linked_employee
                doc.save()
                messages.success(request, "Document uploaded successfully.")
                return redirect("hr:profile")
            else:
                messages.error(request, "Please correct the errors in the document upload form.")
                return render(request, self.template_name, self.get_context(request, doc_form=doc_form))

        elif action == "delete_document":
            doc_id = request.POST.get("document_id")
            doc = get_object_or_404(EmployeeDocument, pk=doc_id, employee=linked_employee)
            doc.delete()
            messages.success(request, "Document deleted successfully.")
            return redirect("hr:profile")

        return redirect("hr:profile")


class HRProfileEditView(HRRequiredMixin, View):
    """Update user identity details and HR profile records."""
    template_name = "hr/profile_edit.html"

    def get_context(self, request, form=None):
        user = request.user
        hr_profile = getattr(user, "hr_profile", None)
        if not hr_profile and getattr(user, "role", "") == User.RoleChoices.HR:
            hr_profile, _ = HRManager.objects.get_or_create(
                user=user,
                defaults={"employee_code": f"HR-{user.id:04d}"},
            )
        linked_employee = getattr(user, "employee_profile", None)
        linked_candidate = getattr(user, "candidate_profile", None) or (
            getattr(linked_employee, "candidate", None) if linked_employee else None
        )
        profile_photo = (
            linked_employee.profile_photo
            if (linked_employee and linked_employee.profile_photo)
            else (linked_candidate.profile_photo if (linked_candidate and linked_candidate.profile_photo) else None)
        )
        if form is None:
            form = HRProfileEditForm(
                user=user,
                hr_profile=hr_profile,
                linked_employee=linked_employee,
                linked_candidate=linked_candidate,
            )
        return {
            "form": form,
            "hr_profile": hr_profile,
            "user_obj": user,
            "linked_employee": linked_employee,
            "linked_candidate": linked_candidate,
            "profile_photo": profile_photo,
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context(request))

    def post(self, request):
        user = request.user
        hr_profile = getattr(user, "hr_profile", None)
        if not hr_profile and getattr(user, "role", "") == User.RoleChoices.HR:
            hr_profile, _ = HRManager.objects.get_or_create(
                user=user,
                defaults={"employee_code": f"HR-{user.id:04d}"},
            )
        linked_employee = getattr(user, "employee_profile", None)
        linked_candidate = getattr(user, "candidate_profile", None) or (
            getattr(linked_employee, "candidate", None) if linked_employee else None
        )

        form = HRProfileEditForm(
            request.POST,
            request.FILES,
            user=user,
            hr_profile=hr_profile,
            linked_employee=linked_employee,
            linked_candidate=linked_candidate,
        )
        if form.is_valid():
            form.save(user=user, hr_profile=hr_profile)
            messages.success(request, "HR Profile updated successfully.")
            return redirect("hr:profile")

        messages.error(request, "Please correct the errors in the form below.")
        return render(request, self.template_name, self.get_context(request, form=form))


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
        # Change -posted_date to -created_at
        queryset = JobVacancy.objects.select_related("posted_by__user").order_by("-created_at")
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset
class JobVacancyCreateView(HRRequiredMixin, CreateView):
    model = JobVacancy
    template_name = "hr/job_form.html"
    fields = [
        "title",
        "department_name",
        "job_type",
        "experience_required",
        "openings_count",
        "description",
        "requirements",
    ]
    success_url = reverse_lazy("hr:job_list")

    def form_valid(self, form):
        # Assign HRManager profile instead of standard User
        form.instance.posted_by = getattr(self.request.user, "hr_profile", None)
        form.instance.status = "OPEN"
        response = super().form_valid(form)
        try:
            from candidates.models import JobVacancy as CandJobVacancy
            dept_obj = None
            dept_name = form.cleaned_data.get("department_name")
            if dept_name:
                dept_obj, _ = Department.objects.get_or_create(
                    name=dept_name,
                    defaults={"is_active": True, "description": f"{dept_name} Department"}
                )
            else:
                dept_obj = Department.objects.first()
            CandJobVacancy.objects.get_or_create(
                title=form.instance.title,
                defaults={
                    "department": dept_obj,
                    "description": form.instance.description,
                    "responsibilities": form.instance.requirements,
                    "qualifications": form.instance.requirements,
                    "skills_required": form.instance.requirements,
                    "experience_required": form.instance.experience_required,
                    "location": "Headquarters",
                    "posted_by": self.request.user,
                    "status": "OPEN",
                }
            )
        except Exception:
            pass
        messages.success(self.request, "Job vacancy published successfully.")
        return response


class JobVacancyUpdateView(HRRequiredMixin, UpdateView):
    model = JobVacancy
    template_name = "hr/job_form.html"
    fields = [
        "title",
        "department_name",
        "job_type",
        "experience_required",
        "openings_count",
        "status",
        "description",
        "requirements",
    ]
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("hr:job_list")

    def form_valid(self, form):
        messages.success(self.request, "Job vacancy updated successfully.")
        return super().form_valid(form)


class JobVacancyCloseView(HRRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(JobVacancy, pk=pk)
        job.status = "CLOSED"
        job.save()
        try:
            from candidates.models import JobVacancy as CandJobVacancy
            CandJobVacancy.objects.filter(title=job.title).update(status="CLOSED")
        except Exception:
            pass
        messages.info(request, f'Job vacancy "{job.title}" has been closed.')
        return redirect("hr:job_list")

    
class ApplicationListView(HRRequiredMixin, ListView):
    model = JobApplication
    template_name = "hr/application_list.html"
    context_object_name = "applications"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            JobApplication.objects.select_related(
                "candidate__user", "candidate", "vacancy", "vacancy__department"
            ).order_by("-applied_at")
        )

        status_filter = self.request.GET.get("status")
        search_query = self.request.GET.get("q", "").strip()

        if status_filter:
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
        context["selected_status"] = self.request.GET.get("status", "")
        context["search_query"] = self.request.GET.get("q", "").strip()
        return context


class ApplicationDetailView(HRRequiredMixin, DetailView):
    model = JobApplication
    template_name = "hr/application_detail.html"
    context_object_name = "app"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return (
            JobApplication.objects.select_related(
                "candidate__user", "vacancy", "vacancy__department", "aptitude_test"
            ).prefetch_related(
                "aptitude_results__test",
                "interviews__interviewer",
                "interviews__interviewer__user",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["aptitude_tests"] = AptitudeTest.objects.filter(status="ACTIVE")
        context["hr_managers"] = HRManager.objects.select_related("user").all()
        return context


class ApplicationStatusUpdateView(HRRequiredMixin, View):
    """Allows HR to progress an application through Alan's exact STATUS_CHOICES and dispatches candidate notifications."""

    def post(self, request, pk):
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
            apt_test_id = request.POST.get("aptitude_test_id")
            apt_remarks = request.POST.get("aptitude_remarks", "").strip()

            if apt_date:
                application.aptitude_date = apt_date
            if apt_time:
                application.aptitude_time = apt_time
            if apt_remarks:
                application.aptitude_remarks = apt_remarks
            if apt_test_id:
                application.aptitude_test_id = apt_test_id

            application.save()

            # Dispatch targeted notification to the affected candidate
            from candidates.models import send_candidate_notification

            notif_title = "Application Status Updated"
            notif_msg = f"Your application for '{application.vacancy.title}' has been updated to {application.get_status_display()}."
            notif_type = "STATUS_UPDATE"

            if new_status == "SHORTLISTED":
                notif_title = "Application Shortlisted"
                notif_msg = f"Great news! Your application for '{application.vacancy.title}' has been shortlisted by our recruitment team."
            elif new_status == "APTITUDE":
                notif_title = "Aptitude Assessment Scheduled"
                notif_type = "APTITUDE_SCHEDULED"
                if application.aptitude_date and application.aptitude_time:
                    notif_msg = f"Your aptitude assessment for '{application.vacancy.title}' has been scheduled for {application.aptitude_date} at {application.aptitude_time}."
                else:
                    notif_msg = f"Your application for '{application.vacancy.title}' has entered the Aptitude Assessment round."
            elif new_status == "INTERVIEW":
                notif_title = "Interview Stage Reached"
                notif_type = "INTERVIEW_SCHEDULED"
                notif_msg = f"Your application for '{application.vacancy.title}' has advanced to the Interview stage."
            elif new_status == "SELECTED":
                notif_title = "Application Selected"
                notif_msg = f"Congratulations! You have been selected for the position of '{application.vacancy.title}'."
            elif new_status == "REJECTED":
                notif_title = "Application Status Update"
                notif_msg = f"Thank you for your interest in '{application.vacancy.title}'. At this time, we have chosen to proceed with other candidates."
            elif new_status == "RESUME_REVIEW":
                notif_title = "Application Under Review"
                notif_msg = f"Your application for '{application.vacancy.title}' is currently under review by our HR team."

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

    
class InterviewListView(HRRequiredMixin, ListView):
    model = Interview
    template_name = "hr/interview_list.html"
    context_object_name = "interviews"

    def get_queryset(self):
        queryset = Interview.objects.select_related(
            "application__candidate__user",
            "application__vacancy",
            "interviewer__user"
        ).order_by("-interview_date", "-interview_time")
        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "")
        context["applications"] = JobApplication.objects.filter(
            status__in=["APPLIED", "RESUME_REVIEW", "SHORTLISTED", "APTITUDE", "INTERVIEW"]
        ).select_related("candidate__user", "vacancy")
        return context


class InterviewScheduleView(HRRequiredMixin, View):
    def get(self, request, application_id):
        get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy"),
            pk=application_id
        )
        return redirect("hr:interview_list")

    def post(self, request, application_id):
        application = get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy"),
            pk=application_id
        )
        interview_date = request.POST.get("interview_date")
        interview_time = request.POST.get("interview_time")
        remarks = request.POST.get("remarks", "").strip()
        interviewer_id = request.POST.get("interviewer_id")

        if interview_date and interview_time:
            interviewer = None
            if interviewer_id:
                interviewer = HRManager.objects.filter(pk=interviewer_id).first()
            if not interviewer:
                interviewer = getattr(request.user, "hr_profile", None)

            interview = Interview.objects.create(
                application=application,
                interviewer=interviewer,
                interview_date=interview_date,
                interview_time=interview_time,
                remarks=remarks,
                status="SCHEDULED",
            )
            # Update application status to defined choice "INTERVIEW"
            application.status = "INTERVIEW"
            application.save()

            from candidates.models import send_candidate_notification
            send_candidate_notification(
                candidate=application.candidate,
                application=application,
                title="Interview Scheduled",
                message=f"Your interview for '{application.vacancy.title}' has been scheduled on {interview.interview_date} at {interview.interview_time}." + (f" Note: {remarks}" if remarks else ""),
                notification_type="INTERVIEW_SCHEDULED",
                link_url=reverse_lazy("candidates:applications"),
            )

            messages.success(request, f"Interview successfully scheduled for {application.candidate.user.get_full_name() or application.candidate.user.username}.")
            next_url = request.POST.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("hr:application_detail", pk=application.pk)

        messages.error(request, "Please provide a valid date and time.")
        return redirect("hr:application_detail", pk=application.pk)


class InterviewCreateView(HRRequiredMixin, View):
    def post(self, request):
        application_id = request.POST.get("application_id")
        interview_date = request.POST.get("interview_date")
        interview_time = request.POST.get("interview_time")
        remarks = request.POST.get("remarks", "").strip()
        interviewer_id = request.POST.get("interviewer_id")

        application = get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy"),
            pk=application_id
        )
        interviewer = None
        if interviewer_id:
            interviewer = HRManager.objects.filter(pk=interviewer_id).first()
        if not interviewer:
            interviewer = getattr(request.user, "hr_profile", None)

        interview = Interview.objects.create(
            application=application,
            interviewer=interviewer,
            interview_date=interview_date,
            interview_time=interview_time,
            remarks=remarks,
            status="SCHEDULED",
        )

        application.status = "INTERVIEW"
        application.save()

        from candidates.models import send_candidate_notification
        send_candidate_notification(
            candidate=application.candidate,
            application=application,
            title="Interview Scheduled",
            message=f"Your interview for '{application.vacancy.title}' has been scheduled on {interview.interview_date} at {interview.interview_time}." + (f" Note: {remarks}" if remarks else ""),
            notification_type="INTERVIEW_SCHEDULED",
            link_url=reverse_lazy("candidates:applications"),
        )

        messages.success(
            request,
            f"Interview scheduled for {application.candidate.user.get_full_name() or application.candidate.user.username}."
        )
        return redirect("hr:interview_list")


class InterviewStatusUpdateView(HRRequiredMixin, View):
    def post(self, request, pk):
        interview = get_object_or_404(
            Interview.objects.select_related("application__candidate", "application__vacancy"),
            pk=pk
        )
        new_status = request.POST.get("status")
        remarks = request.POST.get("remarks", "").strip()

        if new_status in ["SCHEDULED", "COMPLETED", "CANCELLED"]:
            interview.status = new_status
            if remarks:
                interview.remarks = remarks
            interview.save()

            from candidates.models import send_candidate_notification
            send_candidate_notification(
                candidate=interview.application.candidate,
                application=interview.application,
                title=f"Interview {interview.get_status_display()}",
                message=f"Your interview for '{interview.application.vacancy.title}' on {interview.interview_date} has been marked as {interview.get_status_display()}." + (f" Remarks: {remarks}" if remarks else ""),
                notification_type="INTERVIEW_UPDATE",
                link_url=reverse_lazy("candidates:applications"),
            )

            messages.info(request, f"Interview marked as {interview.get_status_display()}.")
        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("hr:interview_list")

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
        "employee__user", "employee__department", "reviewed_by__user"
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

  def post(self, request, pk):
    report = get_object_or_404(EmployeeReport, pk=pk)
    action = request.POST.get("action")
    hr_comments = request.POST.get("hr_comments", "").strip()

    if action == "REVIEWED":
      report.status = "REVIEWED"
      messages.success(
          request,
          f"Report for {report.employee.employee_code} marked as Reviewed.",
      )
    elif action == "NEEDS_CORRECTION":
      report.status = "NEEDS_CORRECTION"
      messages.warning(
          request,
          f"Report for {report.employee.employee_code} returned for"
          " correction.",
      )
    elif action == "UNDER_REVIEW":
      report.status = "UNDER_REVIEW"
      messages.info(
          request,
          f"Report for {report.employee.employee_code} put under review.",
      )
    else:
      messages.error(request, "Invalid action submitted.")
      return redirect("hr:employee_report_list")

    report.hr_comments = hr_comments
    report.reviewed_by = getattr(request.user, "hr_profile", None)
    report.reviewed_at = timezone.now()
    report.save()

    Notification.objects.create(
        employee=report.employee,
        title="Weekly Report Reviewed",
        message=f"HR has reviewed your report '{report.title}' ({report.get_status_display()}).",
        notification_type="REPORT_FEEDBACK",
    )

    return redirect("hr:employee_report_list")


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
          f"Warning updated to {warning_record.get_status_display()}.",
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
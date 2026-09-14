
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
    EmployeePerformance,
    EmployeeReport,
    PerformanceWarning,
)

from .models import (
    AptitudeQuestion,
    AptitudeResult,
    AptitudeTest,
    HRManager,
    Interview,
    JobVacancy,
)

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
    """Enforces access control strictly for HR Managers or Superusers."""

    def test_func(self):
        user = self.request.user
        return user.is_superuser or hasattr(user, "hr_profile")

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Access restricted to HR Personnel.")
        return redirect("home")


class HRProfileView(HRRequiredMixin, TemplateView):
    """View HR profile details."""
    template_name = "hr/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hr_profile, _ = HRManager.objects.get_or_create(
            user=self.request.user,
            defaults={"employee_code": f"HR-{self.request.user.id:04d}"},
        )
        context["hr_profile"] = hr_profile
        return context


class HRProfileEditView(HRRequiredMixin, View):
    """Update user identity details and HR profile records."""
    template_name = "hr/profile_edit.html"

    def get(self, request):
        hr_profile, _ = HRManager.objects.get_or_create(
            user=request.user,
            defaults={"employee_code": f"HR-{request.user.id:04d}"},
        )
        departments = Department.objects.all()
        return render(
            request,
            self.template_name,
            {"hr_profile": hr_profile, "departments": departments},
        )

    def post(self, request):
        hr_profile, _ = HRManager.objects.get_or_create(
            user=request.user,
            defaults={"employee_code": f"HR-{request.user.id:04d}"},
        )
        user = request.user

        # User personal information
        user.first_name = request.POST.get("first_name", "").strip()
        user.last_name = request.POST.get("last_name", "").strip()
        user.email = request.POST.get("email", "").strip()
        user.save()

        # Department assignment
        dept_id = request.POST.get("department")
        if dept_id:
            hr_profile.department = get_object_or_404(Department, pk=dept_id)
        else:
            hr_profile.department = None

        hr_profile.save()
        messages.success(request, "HR Profile updated successfully.")
        return redirect("hr:profile")


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
        messages.success(self.request, "Job vacancy published successfully.")
        return super().form_valid(form)


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
        messages.info(request, f'Job vacancy "{job.title}" has been closed.')
        return redirect("hr:job_list")

    
class ApplicationListView(HRRequiredMixin, ListView):
    model = JobApplication
    template_name = "hr/application_list.html"
    context_object_name = "applications"
    paginate_by = 10

    def get_queryset(self):
        # 'vacancy' is the exact FK on JobApplication
        queryset = JobApplication.objects.select_related(
            "candidate__user", "vacancy"
        ).order_by("-applied_at")

        status_filter = self.request.GET.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "")
        return context


class ApplicationDetailView(HRRequiredMixin, DetailView):
    model = JobApplication
    template_name = "hr/application_detail.html"
    context_object_name = "app"
    pk_url_kwarg = "pk"

    def get_queryset(self):
        return JobApplication.objects.select_related(
            "candidate__user", "vacancy"
        ).prefetch_related("aptitude_results__test", "interviews__interviewer")


class ApplicationStatusUpdateView(HRRequiredMixin, View):
    """Allows HR to progress an application through Alan's exact STATUS_CHOICES."""

    def post(self, request, pk):
        application = get_object_or_404(JobApplication, pk=pk)
        new_status = request.POST.get("status")

        valid_choices = [c[0] for c in JobApplication.STATUS_CHOICES]
        if new_status in valid_choices:
            application.status = new_status
            application.save()
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
    fields = ["title", "description", "duration_minutes", "status"]
    success_url = reverse_lazy("hr:aptitude_test_list")

    def form_valid(self, form):
        form.instance.created_by = getattr(self.request.user, "hr_profile", None)
        messages.success(self.request, "Aptitude test created successfully.")
        return super().form_valid(form)


class AptitudeTestUpdateView(HRRequiredMixin, UpdateView):
    model = AptitudeTest
    template_name = "hr/aptitude_test_form.html"
    fields = ["title", "description", "duration_minutes", "status"]
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("hr:aptitude_test_list")

    def form_valid(self, form):
        messages.success(self.request, "Aptitude test updated successfully.")
        return super().form_valid(form)


class AptitudeQuestionManageView(HRRequiredMixin, View):
    """View to list existing questions for a test and add new ones."""
    template_name = "hr/aptitude_questions.html"

    def get(self, request, test_id):
        test = get_object_or_404(AptitudeTest, pk=test_id)
        questions = test.questions.all()
        return render(request, self.template_name, {"test": test, "questions": questions})

    def post(self, request, test_id):
        test = get_object_or_404(AptitudeTest, pk=test_id)
        
        question_text = request.POST.get("question", "").strip()
        opt_a = request.POST.get("option_a", "").strip()
        opt_b = request.POST.get("option_b", "").strip()
        opt_c = request.POST.get("option_c", "").strip()
        opt_d = request.POST.get("option_d", "").strip()
        correct = request.POST.get("correct_answer", "").strip().upper()

        if question_text and opt_a and opt_b and opt_c and opt_d and correct:
            AptitudeQuestion.objects.create(
                test=test,
                question=question_text,
                option_a=opt_a,
                option_b=opt_b,
                option_c=opt_c,
                option_d=opt_d,
                correct_answer=correct,
            )
            messages.success(request, "Question added to test successfully.")
        else:
            messages.error(request, "Please fill in all question fields and options.")

        return redirect("hr:aptitude_questions", test_id=test.pk)


class AptitudeQuestionDeleteView(HRRequiredMixin, View):
    """Delete a question from a test."""
    def post(self, request, question_id):
        question = get_object_or_404(AptitudeQuestion, pk=question_id)
        test_id = question.test.pk
        question.delete()
        messages.info(request, "Question removed.")
        return redirect("hr:aptitude_questions", test_id=test_id)

    
class InterviewListView(HRRequiredMixin, ListView):
    model = Interview
    template_name = "hr/interview_list.html"
    context_object_name = "interviews"

    def get_queryset(self):
        # Notice application.vacancy (matches Alan's model) and interviewer.user
        return Interview.objects.select_related(
            "application__candidate__user",
            "application__vacancy",
            "interviewer__user"
        ).order_by("-interview_date", "-interview_time")


class InterviewScheduleView(HRRequiredMixin, View):
    template_name = "hr/interview_schedule.html"

    def get(self, request, application_id):
        application = get_object_or_404(
            JobApplication.objects.select_related("candidate__user", "vacancy"),
            pk=application_id
        )
        return render(request, self.template_name, {"application": application})

    def post(self, request, application_id):
        application = get_object_or_404(JobApplication, pk=application_id)
        interview_date = request.POST.get("interview_date")
        interview_time = request.POST.get("interview_time")
        remarks = request.POST.get("remarks", "").strip()

        if interview_date and interview_time:
            hr_profile = getattr(request.user, "hr_profile", None)
            Interview.objects.create(
                application=application,
                interviewer=hr_profile,
                interview_date=interview_date,
                interview_time=interview_time,
                remarks=remarks,
                status="SCHEDULED",
            )
            # Update Alan's application status to his defined choice "INTERVIEW"
            application.status = "INTERVIEW"
            application.save()

            messages.success(request, "Interview successfully scheduled.")
            return redirect("hr:interview_list")

        messages.error(request, "Please provide a valid date and time.")
        return render(request, self.template_name, {"application": application})

class InterviewCreateView(HRRequiredMixin, View):
    def post(self, request):
        application_id = request.POST.get("application_id")
        interview_date = request.POST.get("interview_date")
        interview_time = request.POST.get("interview_time")
        remarks = request.POST.get("remarks", "").strip()

        application = get_object_or_404(JobApplication, pk=application_id)
        hr_profile = getattr(request.user, "hr_profile", None)

        Interview.objects.create(
            application=application,
            interviewer=hr_profile,
            interview_date=interview_date,
            interview_time=interview_time,
            remarks=remarks,
            status="SCHEDULED",
        )

        if hasattr(application, "status"):
            application.status = "INTERVIEW_SCHEDULED"
            application.save()

        messages.success(
            request,
            f"Interview scheduled for {application.candidate.user.get_full_name() or application.candidate.user.username}."
        )
        return redirect("hr:interview_list")

class InterviewStatusUpdateView(HRRequiredMixin, View):
    def post(self, request, pk):
        interview = get_object_or_404(Interview, pk=pk)
        new_status = request.POST.get("status")
        remarks = request.POST.get("remarks", "").strip()

        if new_status in ["SCHEDULED", "COMPLETED", "CANCELLED"]:
            interview.status = new_status
            if remarks:
                interview.remarks = remarks
            interview.save()
            messages.info(request, f"Interview marked as {interview.get_status_display()}.")
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
    template_name = "hr/aptitude_results.html"
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
    messages.success(
        request,
        f"Performance evaluation logged for {employee.employee_code}.",
    )
    return redirect("hr:performance_list")
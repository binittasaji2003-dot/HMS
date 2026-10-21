import json
import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from admin_module.models import Announcement, Department, Holiday

from .forms import (
    EmployeeDocumentForm,
    EmployeeEducationForm,
    EmployeeExperienceForm,
    EmployeePersonalInfoForm,
    EmployeeWeeklyReportForm,
    ForgotPasswordForm,
)
from .models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeExperience,
    EmployeeReport,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    Notification,
    PerformanceReview,
    Team,
)

User = get_user_model()


def homepage(request):
    employees = Employee.objects.all()
    return render(request, "employees/homepage.html", {"employees": employees})


def employee_login(request):
    """Unified login: redirect to single system login page."""
    if request.user.is_authenticated:
        return redirect("users:redirect")
    next_url = request.GET.get("next")
    if next_url:
        return redirect(f"{reverse('account_login')}?next={next_url}")
    return redirect("account_login")


def _legacy_employee_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect("admin:index")
        if hasattr(request.user, "employee_profile"):
            return redirect("employees:dashboard")

    if request.method == "POST":
        identifier = (
            request.POST.get("email") or request.POST.get("username") or ""
        ).strip()
        password = (request.POST.get("password") or "").strip()

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            user = authenticate(request, email=identifier, password=password)
        if user is None:
            emp_rec = (
                Employee.objects.filter(employee_code__iexact=identifier)
                .select_related("user")
                .first()
            )
            if emp_rec and emp_rec.user.check_password(password):
                user = emp_rec.user

        if user is None:
            messages.error(request, "Invalid email/ID or password.")
            return render(request, "employees/login.html")

        if not user.is_active:
            messages.error(request, "This account is currently inactive.")
            return render(request, "employees/login.html")

        if user.is_superuser or user.is_staff:
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            return redirect("admin:index")

        # If user is a Candidate without active employee approval, redirect to Candidate Portal
        if getattr(user, "role", "") == "Candidate" and not (hasattr(user, "employee_profile") and user.employee_profile.employment_status == "ACTIVE"):
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            messages.info(request, "Signed in with Candidate access. Redirecting to Candidate Portal.")
            return redirect("candidates:dashboard")

        if not hasattr(user, "employee_profile"):
            dept, _ = Department.objects.get_or_create(
                name="Information Technology",
                defaults={"description": "IT Department", "is_active": True},
            )
            Employee.objects.create(
                user=user,
                employee_code=f"EMP{user.id:04d}",
                department=dept,
                designation="Software Developer",
                joining_date=timezone.now().date(),
                employment_status="ACTIVE",
            )

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        return redirect("employees:dashboard")

    return render(request, "employees/login.html")


def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "Password reset instructions have been sent to your email address.",
            )
            return redirect("employees:login")
    return render(request, "employees/forgot_password.html", {"form": form})


@login_required
def employee_dashboard(request):
    if getattr(request.user, "role", "") == "Candidate" and not (hasattr(request.user, "employee_profile") and request.user.employee_profile.employment_status == "ACTIVE"):
        messages.info(request, "Your account is currently registered as a Candidate. Please access the Candidate Portal.")
        return redirect("candidates:dashboard")

    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        dept, _ = Department.objects.get_or_create(
            name="Information Technology",
            defaults={"description": "IT Department", "is_active": True},
        )
        employee = Employee.objects.create(
            user=request.user,
            employee_code=f"EMP{request.user.id:04d}",
            department=dept,
            designation="Staff" if request.user.is_staff else "Employee",
            joining_date=timezone.now().date(),
            employment_status="ACTIVE",
        )

    # Metrics & Data
    reports = employee.reports.all().order_by("-submitted_at")
    recent_reports = reports[:5]

    # Latest report status
    latest_report = reports.first()
    monthly_report_status = (
        latest_report.get_status_display() if latest_report else "No Reports"
    )

    # Performance score
    perf_reviews = employee.performance_reviews.all().order_by("-review_date")
    latest_perf = perf_reviews.first()
    has_perf_review = bool(latest_perf)
    perf_score = float(latest_perf.score) if latest_perf else None
    perf_rating = latest_perf.get_rating_display() if latest_perf else "Pending Evaluation"
    perf_comments = (
        latest_perf.comments
        if latest_perf
        else "No performance evaluations recorded yet. Evaluations will appear here after HR reviews your weekly work submissions."
    )

    # Unread Notifications & Announcements
    notifications = employee.notifications.all().order_by("-created_at")
    if not notifications.exists():
        Notification.objects.bulk_create([
            Notification(
                employee=employee,
                title="Welcome to HRMS",
                message="Welcome to your employee portal. You can manage your profile, submit weekly reports, and track feedback here.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Weekly Report Reminder",
                message="Please remember to submit your weekly work report before Friday 5:00 PM.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Company Guidelines",
                message="Please review the company employee guidelines and leave policy.",
                is_read=False,
            ),
        ])
        notifications = employee.notifications.all().order_by("-created_at")

    unread_notifications_count = notifications.filter(is_read=False).count()
    recent_notifications = notifications[:5]

    announcements = Announcement.objects.filter(is_published=True).order_by(
        "-published_at",
        "-created_at",
    )[:4]

    # Pending tasks count
    pending_tasks = (
        reports.filter(status="DRAFT").count()
        + reports.filter(status="NEEDS_CORRECTION").count()
    )
    if pending_tasks == 0:
        pending_tasks = 0

    # Check for newly reviewed report by HR to trigger popup message
    latest_reviewed_report = (
        reports.filter(status__in=["REVIEWED", "NEEDS_CORRECTION"])
        .order_by("-reviewed_at")
        .first()
    )
    show_report_popup = False
    if latest_reviewed_report and latest_reviewed_report.reviewed_at:
        session_key = f"seen_report_review_{latest_reviewed_report.pk}_{latest_reviewed_report.status}"
        if not request.session.get(session_key):
            show_report_popup = True

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
    holidays_json = json.dumps(holidays_data)

    # Leave Balance & Team Lead Metrics
    current_year = timezone.now().year
    leave_balance = employee.get_or_create_leave_balance(current_year)
    is_team_lead = employee.is_team_lead

    team_pending_leave_count = 0
    team_approved_this_month = 0
    team_rejected_this_month = 0
    recent_team_leave_requests = []

    if is_team_lead:
        team_requests = get_team_lead_leave_requests(request.user)
        team_pending_leave_count = team_requests.filter(status="PENDING").count()
        team_approved_this_month = team_requests.filter(
            status="APPROVED",
            approved_at__year=current_year,
            approved_at__month=timezone.now().month,
        ).count()
        team_rejected_this_month = team_requests.filter(
            status="REJECTED",
            rejected_at__year=current_year,
            rejected_at__month=timezone.now().month,
        ).count()
        recent_team_leave_requests = team_requests.order_by("-submitted_at")[:5]

    context = {
        "employee": employee,
        "reports": recent_reports,
        "total_reports_count": reports.count(),
        "latest_report": latest_report,
        "latest_reviewed_report": latest_reviewed_report,
        "show_report_popup": show_report_popup,
        "monthly_report_status": monthly_report_status,
        "has_perf_review": has_perf_review,
        "perf_score": perf_score,
        "perf_rating": perf_rating,
        "perf_comments": perf_comments,
        "pending_tasks": pending_tasks,
        "unread_notifications_count": unread_notifications_count,
        "announcements": announcements,
        "notifications": recent_notifications,
        "leave_balance": leave_balance,
        "is_team_lead": is_team_lead,
        "team_pending_leave_count": team_pending_leave_count,
        "team_approved_this_month": team_approved_this_month,
        "team_rejected_this_month": team_rejected_this_month,
        "holidays_json": holidays_json,
        "recent_team_leave_requests": recent_team_leave_requests,
    }

    return render(request, "employees/dashboard.html", context)


@login_required
def dismiss_report_popup(request, report_id):
    try:
        report = get_object_or_404(
            EmployeeReport, pk=report_id, employee=request.user.employee_profile
        )
        session_key = f"seen_report_review_{report.pk}_{report.status}"
        request.session[session_key] = True
        return JsonResponse({"status": "success"})
    except Exception:
        return JsonResponse({"status": "error"}, status=400)


@login_required
def profile_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    # Sync fields from candidate profile if empty
    employee.sync_from_candidate_if_empty()

    profile_form = EmployeePersonalInfoForm(instance=employee, user=request.user)
    education_form = EmployeeEducationForm()
    experience_form = EmployeeExperienceForm()
    doc_form = EmployeeDocumentForm()
    pwd_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            profile_form = EmployeePersonalInfoForm(
                request.POST,
                request.FILES,
                instance=employee,
                user=request.user,
            )
            if profile_form.is_valid():
                profile_form.save()
                messages.success(
                    request,
                    "Your profile information has been updated successfully!",
                )
                return redirect("employees:profile")
            else:
                messages.error(request, "Please correct the errors in the profile form.")

        elif action == "upload_document":
            doc_form = EmployeeDocumentForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.employee = employee
                doc.save()
                messages.success(request, "Document uploaded successfully!")
                return redirect("employees:profile")
            else:
                messages.error(request, "Failed to upload document. Please check the file and try again.")

        elif action == "change_password":
            pwd_form = PasswordChangeForm(user=request.user, data=request.POST)
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password was updated successfully!")
                return redirect("employees:profile")
            messages.error(request, "Please correct the password errors below.")

    educations = employee.educations.all().order_by("-year_of_passing")
    experiences = employee.experiences.all().order_by("-start_date")
    documents = employee.documents.all().order_by("-uploaded_at")

    context = {
        "employee": employee,
        "profile_form": profile_form,
        "education_form": education_form,
        "experience_form": experience_form,
        "doc_form": doc_form,
        "pwd_form": pwd_form,
        "educations": educations,
        "experiences": experiences,
        "documents": documents,
    }
    return render(request, "employees/profile.html", context)


@login_required
def education_add_view(request):
    if request.method != "POST":
        return redirect("employees:profile")
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    form = EmployeeEducationForm(request.POST)
    if form.is_valid():
        edu = form.save(commit=False)
        edu.employee = employee
        edu.save()
        messages.success(request, "Education record added successfully!")
    else:
        for error in form.errors.values():
            messages.error(request, error)
    return redirect("employees:profile")


@login_required
def education_delete_view(request, pk):
    if request.method != "POST":
        return redirect("employees:profile")
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        return redirect("employees:login")
    edu = get_object_or_404(EmployeeEducation, pk=pk, employee=employee)
    edu.delete()
    messages.success(request, "Education record removed successfully.")
    return redirect("employees:profile")


@login_required
def experience_add_view(request):
    if request.method != "POST":
        return redirect("employees:profile")
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    form = EmployeeExperienceForm(request.POST)
    if form.is_valid():
        exp = form.save(commit=False)
        exp.employee = employee
        exp.save()
        messages.success(request, "Experience record added successfully!")
    else:
        for error in form.errors.values():
            messages.error(request, error)
    return redirect("employees:profile")


@login_required
def experience_delete_view(request, pk):
    if request.method != "POST":
        return redirect("employees:profile")
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        return redirect("employees:login")
    exp = get_object_or_404(EmployeeExperience, pk=pk, employee=employee)
    exp.delete()
    messages.success(request, "Experience record removed successfully.")
    return redirect("employees:profile")


@login_required
def document_delete_view(request, pk):
    if request.method != "POST":
        return redirect("employees:profile")
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        return redirect("employees:login")
    doc = get_object_or_404(EmployeeDocument, pk=pk, employee=employee)
    doc.delete()
    messages.success(request, "Document removed successfully.")
    return redirect("employees:profile")


@login_required
def subordinate_profile_view(request, employee_id):
    """Allows Team Leads, HR, or Admins to view an assigned subordinate's profile."""
    target_employee = get_object_or_404(
        Employee.objects.select_related("user", "department", "team_lead"),
        pk=employee_id
    )

    subordinates = get_team_lead_subordinates(request.user)
    is_authorized = (
        request.user.is_superuser
        or request.user.is_staff
        or getattr(request.user, "role", "") == "HR"
        or target_employee in subordinates
        or target_employee.team_lead == request.user
    )
    if not is_authorized:
        messages.error(request, "You do not have permission to view this subordinate profile.")
        return redirect("employees:dashboard")

    educations = target_employee.educations.all().order_by("-year_of_passing")
    experiences = target_employee.experiences.all().order_by("-start_date")
    documents = target_employee.documents.all().order_by("-uploaded_at")
    recent_reports = target_employee.reports.all().order_by("-week_start_date")[:5]

    context = {
        "target_employee": target_employee,
        "educations": educations,
        "experiences": experiences,
        "documents": documents,
        "recent_reports": recent_reports,
    }
    return render(request, "employees/subordinate_profile.html", context)


@login_required
def reports_list(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    reports = employee.reports.all().select_related("performance_review").order_by("-week_start_date", "-submitted_at")

    context = {
        "employee": employee,
        "reports": reports,
    }
    return render(request, "employees/reports_list.html", context)


@login_required
def submit_report(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    if request.method == "POST":
        action = request.POST.get("action", "submit_report")
        form = EmployeeWeeklyReportForm(request.POST, employee=employee)
        if form.is_valid():
            report = form.save(commit=False)
            report.employee = employee

            if action == "save_draft":
                report.status = "DRAFT"
                report.save()
                messages.success(request, "Weekly report saved as Draft. You can edit and submit it anytime.")
                return redirect("employees:reports_list")
            else:
                if not form.cleaned_data.get("declaration_accepted"):
                    messages.error(request, "You must accept the truthfulness declaration before submitting the report.")
                    return render(request, "employees/report_form.html", {"form": form, "action": "Submit", "employee": employee})

                report.status = "SUBMITTED"
                report.submitted_at = timezone.now()
                report.save()

                # Notify HR Managers
                from hr.models import HRManager
                hr_managers = HRManager.objects.filter(is_active=True).select_related("user")
                for hr_m in hr_managers:
                    if hasattr(hr_m.user, "employee_profile"):
                        Notification.objects.create(
                            employee=hr_m.user.employee_profile,
                            title="New Weekly Report Submitted",
                            message=f"{employee.full_name or employee.user.username} has submitted a weekly report for period {report.week_start_date} to {report.week_end_date}.",
                            notification_type="REPORT_REMINDER",
                        )

                # Notify employee
                Notification.objects.create(
                    employee=employee,
                    title="Weekly Report Submitted",
                    message=f"Your weekly report '{report.title}' ({report.week_start_date} to {report.week_end_date}) has been submitted for HR review.",
                    notification_type="REPORT_REMINDER",
                )

                messages.success(request, "Weekly report submitted successfully to HR!")
                return redirect("employees:reports_list")
        else:
            messages.error(request, "Please fix the validation errors in your report submission.")
    else:
        form = EmployeeWeeklyReportForm(employee=employee)

    return render(
        request,
        "employees/report_form.html",
        {"form": form, "action": "Submit", "employee": employee},
    )


@login_required
def edit_report(request, report_id):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    report = get_object_or_404(EmployeeReport, report_id=report_id, employee=employee)

    if report.status in ["REVIEWED", "UNDER_REVIEW"]:
        messages.error(
            request,
            "You cannot edit a report that is currently Under Review or has already been Reviewed by HR.",
        )
        return redirect("employees:reports_list")

    if request.method == "POST":
        action = request.POST.get("action", "submit_report")
        form = EmployeeWeeklyReportForm(request.POST, instance=report, employee=employee)
        if form.is_valid():
            report = form.save(commit=False)
            if action == "save_draft":
                report.status = "DRAFT"
                report.save()
                messages.success(request, "Weekly report draft updated successfully.")
                return redirect("employees:reports_list")
            else:
                if not form.cleaned_data.get("declaration_accepted"):
                    messages.error(request, "You must accept the truthfulness declaration before submitting the report.")
                    return render(request, "employees/report_form.html", {"form": form, "action": "Edit", "report": report, "employee": employee})

                report.status = "SUBMITTED"
                report.submitted_at = timezone.now()
                report.save()

                # Notify HR Managers
                from hr.models import HRManager
                hr_managers = HRManager.objects.filter(is_active=True).select_related("user")
                for hr_m in hr_managers:
                    if hasattr(hr_m.user, "employee_profile"):
                        Notification.objects.create(
                            employee=hr_m.user.employee_profile,
                            title="Weekly Report Resubmitted",
                            message=f"{employee.full_name or employee.user.username} resubmitted their weekly report ({report.week_start_date} to {report.week_end_date}).",
                            notification_type="REPORT_REMINDER",
                        )

                # Notify employee
                Notification.objects.create(
                    employee=employee,
                    title="Weekly Report Submitted",
                    message=f"Your weekly report '{report.title}' ({report.week_start_date} to {report.week_end_date}) has been submitted for HR review.",
                    notification_type="REPORT_REMINDER",
                )

                messages.success(request, "Weekly report submitted successfully to HR!")
                return redirect("employees:reports_list")
        else:
            messages.error(request, "Please fix the validation errors in your report.")
    else:
        form = EmployeeWeeklyReportForm(instance=report, employee=employee)

    return render(
        request,
        "employees/report_form.html",
        {"form": form, "action": "Edit", "report": report, "employee": employee},
    )


@login_required
def report_detail_view(request, report_id):
    employee = getattr(request.user, "employee_profile", None)
    report = get_object_or_404(
        EmployeeReport.objects.select_related("employee__user", "employee__department"),
        report_id=report_id,
    )

    is_owner = (employee and report.employee == employee)
    subordinates = get_team_lead_subordinates(request.user)
    is_authorized = (
        is_owner
        or request.user.is_superuser
        or request.user.is_staff
        or getattr(request.user, "role", "") == "HR"
        or (employee and report.employee in subordinates)
    )
    if not is_authorized:
        messages.error(request, "You do not have permission to view this report.")
        return redirect("employees:reports_list")

    evaluation = getattr(report, "performance_review", None)

    context = {
        "employee": employee,
        "report": report,
        "evaluation": evaluation,
        "is_owner": is_owner,
    }
    return render(request, "employees/report_detail.html", context)


@login_required
def performance_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    reports = employee.reports.all().select_related("performance_review__reviewed_by__user").order_by("-week_start_date")
    reviewed_reports = [r for r in reports if hasattr(r, "performance_review") and r.performance_review is not None]

    total_submitted = reports.filter(status__in=["SUBMITTED", "UNDER_REVIEW", "REVIEWED", "NEEDS_CORRECTION"]).count()
    total_reviewed = len(reviewed_reports)

    if total_reviewed > 0:
        avg_score = round(sum(float(r.performance_review.average_score) for r in reviewed_reports) / total_reviewed, 2)
        avg_percentage = round(sum(float(r.performance_review.performance_percentage) for r in reviewed_reports) / total_reviewed, 1)
        if avg_score >= 4.5:
            performance_badge = "Excellent"
            badge_color = "success"
        elif avg_score >= 3.5:
            performance_badge = "Good Performer"
            badge_color = "primary"
        elif avg_score >= 2.5:
            performance_badge = "Average"
            badge_color = "warning"
        else:
            performance_badge = "Needs Improvement"
            badge_color = "danger"
    else:
        avg_score = None
        avg_percentage = None
        performance_badge = "Pending Evaluation"
        badge_color = "secondary"

    legacy_reviews = employee.performance_reviews.all().order_by("-review_date")
    warnings = employee.performance_warnings.all().order_by("-warning_date")

    context = {
        "employee": employee,
        "reports": reports,
        "reviewed_reports": reviewed_reports,
        "total_submitted": total_submitted,
        "total_reviewed": total_reviewed,
        "avg_score": round(avg_score, 2) if avg_score is not None else None,
        "avg_percentage": round(avg_percentage, 1) if avg_percentage is not None else None,
        "performance_badge": performance_badge,
        "badge_color": badge_color,
        "legacy_reviews": legacy_reviews,
        "warnings": warnings,
    }
    return render(request, "employees/performance.html", context)



@login_required
def announcements_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    announcements = Announcement.objects.filter(is_published=True).order_by(
        "-published_at",
        "-created_at",
    )

    context = {
        "employee": employee,
        "announcements": announcements,
    }
    return render(request, "employees/announcements.html", context)


@login_required
def notifications_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    notifications = employee.notifications.all().order_by("-created_at")
    if not notifications.exists():
        Notification.objects.bulk_create([
            Notification(
                employee=employee,
                title="Welcome to HRMS",
                message="Welcome to your employee portal. You can manage your profile, submit weekly reports, and track feedback here.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Weekly Report Reminder",
                message="Please remember to submit your weekly work report before Friday 5:00 PM.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Company Guidelines",
                message="Please review the company employee guidelines and leave policy.",
                is_read=False,
            ),
        ])
        notifications = employee.notifications.all().order_by("-created_at")

    unread_notifications_count = notifications.filter(is_read=False).count()

    context = {
        "employee": employee,
        "notifications": notifications,
        "unread_notifications_count": unread_notifications_count,
    }
    return render(request, "employees/notifications.html", context)


@login_required
def mark_all_notifications_read(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        return redirect("employees:login")

    employee.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("employees:notifications")


@login_required
def mark_notification_read(request, notification_id):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        return redirect("employees:login")

    notif = get_object_or_404(
        Notification,
        notification_id=notification_id,
        employee=employee,
    )
    notif.is_read = True
    notif.save()
    return redirect("employees:notifications")


def employee_logout(request):
    logout(request)
    return redirect("employees:login")


# ========================================================
# LEAVE MANAGEMENT & TEAM LEAD APPROVAL VIEWS
# ========================================================

def ensure_default_leave_types():
    """Ensure standard leave types exist in database."""
    default_types = [
        ("General / Casual Leave", "GENERAL", "Standard annual / casual leave allowance"),
        ("Sick Leave", "SICK", "Leave for medical issues, illness, or medical appointments"),
        ("Earned Leave", "EARNED", "Privilege or earned leave from tenure"),
        ("Maternity Leave", "MATERNITY", "Leave for expectant mothers"),
        ("Paternity Leave", "PATERNITY", "Leave for new fathers"),
        ("Emergency Leave", "EMERGENCY", "Unforeseen family or urgent personal emergencies"),
        ("Other", "OTHER", "Other approved leave category"),
    ]
    for name, code, desc in default_types:
        LeaveType.objects.get_or_create(
            code=code,
            defaults={"name": name, "description": desc, "is_active": True},
        )


def get_team_lead_subordinates(user):
    """Return queryset of active subordinates assigned to this user as Team Lead or Department Head."""
    q_filter = Q(team_lead=user) | Q(team__team_lead=user)
    
    employee_profile = getattr(user, "employee_profile", None)
    if employee_profile and employee_profile.is_department_head:
        q_filter |= Q(department=employee_profile.department)
        
    return Employee.objects.filter(q_filter).exclude(user=user).distinct()


def get_team_lead_leave_requests(user):
    """Return queryset of leave requests that this team lead is responsible for approving."""
    subordinate_emps = get_team_lead_subordinates(user)
    return LeaveRequest.objects.filter(
        Q(approver=user) | Q(employee__in=subordinate_emps)
    ).exclude(employee__user=user).distinct()


@login_required
def leave_management_view(request):
    """
    Main Leave Management dashboard for employees:
    - Balance overview (Total 15, Taken, Pending, Remaining)
    - Apply for leave form
    - My leave request history
    - Team approvals preview (if user is a Team Lead)
    """
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:dashboard")

    ensure_default_leave_types()
    current_year = timezone.now().year
    leave_balance = employee.get_or_create_leave_balance(current_year)
    leave_types = LeaveType.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        leave_type_id = request.POST.get("leave_type")
        start_date_str = (request.POST.get("start_date") or "").strip()
        end_date_str = (request.POST.get("end_date") or "").strip()
        reason = (request.POST.get("reason") or "").strip()
        declaration = request.POST.get("declaration_accepted")

        # 1. Validate declaration
        if not declaration:
            messages.error(request, "You must accept the declaration to submit a leave request.")
            return redirect("employees:leave_management")

        # 2. Validate reason
        if not reason:
            messages.error(request, "Please provide a valid reason for your leave request.")
            return redirect("employees:leave_management")

        # 3. Validate leave type
        leave_type = get_object_or_404(LeaveType, id=leave_type_id, is_active=True)

        # 4. Validate dates
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Please select valid start and end dates in YYYY-MM-DD format.")
            return redirect("employees:leave_management")

        if end_date < start_date:
            messages.error(request, "End date cannot be earlier than start date.")
            return redirect("employees:leave_management")

        # Calculate inclusive days (e.g. Sep 23 to Sep 25 = 3 days)
        number_of_days = (end_date - start_date).days + 1
        request_year = start_date.year
        target_balance = employee.get_or_create_leave_balance(request_year)

        # 5. Validate leave balance
        if number_of_days > target_balance.remaining_days:
            messages.error(
                request,
                f"Insufficient leave balance. You requested {number_of_days} day(s), but only have {target_balance.remaining_days} day(s) remaining for {request_year}."
            )
            return redirect("employees:leave_management")

        # 6. Validate overlapping leaves
        overlap = LeaveRequest.objects.filter(
            employee=employee,
            status__in=["PENDING", "APPROVED"],
            start_date__lte=end_date,
            end_date__gte=start_date,
        ).exists()
        if overlap:
            messages.error(request, "You already have an active or pending leave request covering these dates.")
            return redirect("employees:leave_management")

        # 7. Determine approver
        approver = employee.team_lead
        if not approver and employee.team and employee.team.team_lead:
            approver = employee.team.team_lead

        # Ensure no self-approver assignment
        if approver == request.user:
            approver = None

        if not approver:
            # Fallback to HR Manager or Staff / Superuser
            approver = User.objects.filter(
                Q(is_superuser=True) | Q(is_staff=True) | Q(role="HR")
            ).exclude(id=request.user.id).first()

        # 8. Create LeaveRequest atomically
        with transaction.atomic():
            leave_req = LeaveRequest.objects.create(
                employee=employee,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                number_of_days=number_of_days,
                reason=reason,
                declaration_accepted=True,
                status="PENDING",
                approver=approver,
            )

            # Notification to employee
            Notification.objects.create(
                employee=employee,
                notification_type="LEAVE_REQUEST",
                title="Leave Request Submitted",
                message=f"Your {leave_type.name} request for {number_of_days} day(s) ({start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}) has been submitted for review.",
                is_read=False,
            )

            # Notification to approver if applicable
            if approver and hasattr(approver, "employee_profile"):
                Notification.objects.create(
                    employee=approver.employee_profile,
                    notification_type="LEAVE_REQUEST",
                    title="Subordinate Leave Request",
                    message=f"{employee.user.get_full_name() or employee.user.username} submitted a {leave_type.name} request for {number_of_days} day(s) ({start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}).",
                    is_read=False,
                )

        messages.success(request, f"Leave request for {number_of_days} day(s) submitted successfully.")
        return redirect("employees:leave_management")

    # GET Request Handling
    status_filter = request.GET.get("status", "ALL").upper()
    my_requests = employee.leave_requests.all().select_related(
        "leave_type", "approver", "approved_by", "rejected_by"
    ).order_by("-submitted_at")

    if status_filter in ["PENDING", "APPROVED", "REJECTED", "CANCELLED"]:
        my_requests = my_requests.filter(status=status_filter)

    # Team Lead Metrics if user leads subordinates
    is_team_lead = employee.is_team_lead
    team_requests = []
    team_pending_count = 0
    team_approved_count = 0
    team_rejected_count = 0

    if is_team_lead:
        all_team_reqs = get_team_lead_leave_requests(request.user).select_related(
            "employee__user", "employee__department", "leave_type"
        )
        team_pending_count = all_team_reqs.filter(status="PENDING").count()
        team_approved_count = all_team_reqs.filter(status="APPROVED").count()
        team_rejected_count = all_team_reqs.filter(status="REJECTED").count()
        team_requests = all_team_reqs.order_by("-submitted_at")[:10]

    context = {
        "employee": employee,
        "leave_balance": leave_balance,
        "leave_types": leave_types,
        "my_requests": my_requests,
        "current_year": current_year,
        "status_filter": status_filter,
        "is_team_lead": is_team_lead,
        "team_requests": team_requests,
        "team_pending_count": team_pending_count,
        "team_approved_count": team_approved_count,
        "team_rejected_count": team_rejected_count,
    }
    return render(request, "employees/leave_management.html", context)


@login_required
def leave_cancel_view(request, request_id):
    """Allows an employee to cancel their pending or approved leave request."""
    if request.method != "POST":
        return redirect("employees:leave_management")

    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:leave_management")

    leave_req = get_object_or_404(LeaveRequest, id=request_id, employee=employee)

    if leave_req.status not in ["PENDING", "APPROVED"]:
        messages.error(request, f"Cannot cancel a request that is already {leave_req.get_status_display()}.")
        return redirect("employees:leave_management")

    was_approved = (leave_req.status == "APPROVED")
    leave_req.status = "CANCELLED"
    leave_req.cancelled_at = timezone.now()
    leave_req.save()

    # Create notification for employee
    Notification.objects.create(
        employee=employee,
        notification_type="LEAVE_CANCELLED",
        title="Leave Request Cancelled",
        message=f"Your {leave_req.leave_type.name} request for {leave_req.number_of_days} day(s) ({leave_req.start_date.strftime('%b %d, %Y')} to {leave_req.end_date.strftime('%b %d, %Y')}) has been cancelled." + (" Your leave balance has been restored." if was_approved else ""),
        is_read=False,
    )

    # Notify approver if exists
    if leave_req.approver and hasattr(leave_req.approver, "employee_profile"):
        Notification.objects.create(
            employee=leave_req.approver.employee_profile,
            notification_type="LEAVE_CANCELLED",
            title="Subordinate Cancelled Leave",
            message=f"{employee.user.get_full_name() or employee.user.username} cancelled their {leave_req.leave_type.name} request for {leave_req.number_of_days} day(s) ({leave_req.start_date.strftime('%b %d, %Y')} to {leave_req.end_date.strftime('%b %d, %Y')}).",
            is_read=False,
        )

    restore_msg = " Leave balance has been restored." if was_approved else ""
    messages.success(request, f"Leave request #{leave_req.id} cancelled successfully.{restore_msg}")
    return redirect("employees:leave_management")


@login_required
def team_lead_leave_requests_view(request):
    """Dedicated subordinate leave approval list for Team Leads."""
    employee = getattr(request.user, "employee_profile", None)
    is_team_lead = employee and employee.is_team_lead
    if not (request.user.is_superuser or request.user.is_staff or is_team_lead):
        messages.error(request, "Access restricted to Team Leads.")
        return redirect("employees:leave_management")

    all_team_reqs = get_team_lead_leave_requests(request.user).select_related(
        "employee__user", "employee__department", "leave_type", "approved_by", "rejected_by"
    )

    status_filter = request.GET.get("status", "ALL").upper()
    search_q = (request.GET.get("q") or "").strip()

    filtered_reqs = all_team_reqs
    if status_filter in ["PENDING", "APPROVED", "REJECTED", "CANCELLED"]:
        filtered_reqs = filtered_reqs.filter(status=status_filter)

    if search_q:
        filtered_reqs = filtered_reqs.filter(
            Q(employee__user__first_name__icontains=search_q) |
            Q(employee__user__last_name__icontains=search_q) |
            Q(employee__user__username__icontains=search_q) |
            Q(employee__employee_code__icontains=search_q) |
            Q(reason__icontains=search_q) |
            Q(leave_type__name__icontains=search_q)
        )

    total_count = all_team_reqs.count()
    pending_count = all_team_reqs.filter(status="PENDING").count()
    approved_count = all_team_reqs.filter(status="APPROVED").count()
    rejected_count = all_team_reqs.filter(status="REJECTED").count()

    context = {
        "employee": employee,
        "requests": filtered_reqs.order_by("-submitted_at"),
        "status_filter": status_filter,
        "search_q": search_q,
        "total_count": total_count,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
    }
    return render(request, "employees/team_lead_leave_requests.html", context)


@login_required
def team_lead_leave_detail_view(request, request_id):
    """Detailed review dossier of a subordinate leave request."""
    employee = getattr(request.user, "employee_profile", None)
    is_team_lead = employee and employee.is_team_lead
    if not (request.user.is_superuser or request.user.is_staff or is_team_lead):
        messages.error(request, "Access restricted to Team Leads.")
        return redirect("employees:leave_management")

    leave_req = get_object_or_404(
        LeaveRequest.objects.select_related(
            "employee__user", "employee__department", "leave_type", "approver", "approved_by", "rejected_by"
        ),
        id=request_id,
    )

    # Permission check: must be approver or subordinate's team lead or staff/admin
    subordinates = get_team_lead_subordinates(request.user)
    if not (request.user.is_superuser or request.user.is_staff or leave_req.approver == request.user or leave_req.employee in subordinates):
        messages.error(request, "You do not have permission to view or review this leave request.")
        return redirect("employees:team_lead_leave_requests")

    # Subordinate leave balance
    sub_balance = leave_req.employee.get_or_create_leave_balance(leave_req.start_date.year)

    # Check for other approved leaves in the same period within the team
    overlapping_team_leaves = LeaveRequest.objects.filter(
        employee__in=subordinates,
        status="APPROVED",
        start_date__lte=leave_req.end_date,
        end_date__gte=leave_req.start_date,
    ).exclude(id=leave_req.id).select_related("employee__user", "leave_type")

    context = {
        "employee": employee,
        "leave_req": leave_req,
        "sub_balance": sub_balance,
        "overlapping_team_leaves": overlapping_team_leaves,
    }
    return render(request, "employees/team_lead_leave_detail.html", context)


@login_required
def team_lead_leave_approve_view(request, request_id):
    """POST-only view for Team Lead to approve a subordinate leave request."""
    if request.method != "POST":
        return redirect("employees:team_lead_leave_requests")

    leave_req = get_object_or_404(
        LeaveRequest.objects.select_related("employee__user", "leave_type"),
        id=request_id,
    )

    # 1. Authority Check
    subordinates = get_team_lead_subordinates(request.user)
    if not (request.user.is_superuser or request.user.is_staff or leave_req.approver == request.user or leave_req.employee in subordinates):
        messages.error(request, "You do not have permission to approve this leave request.")
        return redirect("employees:team_lead_leave_requests")

    # 2. Strict Self-Approval Check
    if leave_req.employee.user == request.user:
        messages.error(request, "Self-approval is strictly prohibited. You cannot approve your own leave request.")
        return redirect("employees:team_lead_leave_requests")

    # 3. Status Check
    if leave_req.status != "PENDING":
        messages.warning(request, f"This request cannot be approved because its current status is {leave_req.get_status_display()}.")
        return redirect("employees:team_lead_leave_requests")

    # 4. Atomic balance check & approval
    with transaction.atomic():
        locked_req = LeaveRequest.objects.select_for_update().get(id=request_id)
        balance = locked_req.employee.get_or_create_leave_balance(locked_req.start_date.year)

        if locked_req.number_of_days > balance.remaining_days:
            messages.error(
                request,
                f"Cannot approve: Employee only has {balance.remaining_days} remaining day(s) for {locked_req.start_date.year}."
            )
            return redirect("employees:team_lead_leave_requests")

        locked_req.status = "APPROVED"
        locked_req.approved_by = request.user
        locked_req.approved_at = timezone.now()
        locked_req.save()

        # Create notification for subordinate
        Notification.objects.create(
            employee=locked_req.employee,
            notification_type="LEAVE_APPROVED",
            title="Leave Request Approved",
            message=f"Your {locked_req.leave_type.name} request for {locked_req.number_of_days} day(s) ({locked_req.start_date.strftime('%b %d, %Y')} to {locked_req.end_date.strftime('%b %d, %Y')}) has been APPROVED by {request.user.get_full_name() or request.user.username}.",
            is_read=False,
        )

    emp_name = leave_req.employee.user.get_full_name() or leave_req.employee.user.username
    messages.success(request, f"Leave request #{leave_req.id} for {emp_name} ({leave_req.number_of_days} days) has been APPROVED.")
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("employees:team_lead_leave_requests")


@login_required
def team_lead_leave_reject_view(request, request_id):
    """POST-only view for Team Lead to reject a subordinate leave request with mandatory reason."""
    if request.method != "POST":
        return redirect("employees:team_lead_leave_requests")

    leave_req = get_object_or_404(
        LeaveRequest.objects.select_related("employee__user", "leave_type"),
        id=request_id,
    )

    # 1. Authority Check
    subordinates = get_team_lead_subordinates(request.user)
    if not (request.user.is_superuser or request.user.is_staff or leave_req.approver == request.user or leave_req.employee in subordinates):
        messages.error(request, "You do not have permission to reject this leave request.")
        return redirect("employees:team_lead_leave_requests")

    # 2. Strict Self-Review Check
    if leave_req.employee.user == request.user:
        messages.error(request, "Self-review is strictly prohibited.")
        return redirect("employees:team_lead_leave_requests")

    # 3. Status Check
    if leave_req.status != "PENDING":
        messages.warning(request, f"This request cannot be rejected because its current status is {leave_req.get_status_display()}.")
        return redirect("employees:team_lead_leave_requests")

    # 4. Mandatory Rejection Reason
    rejection_reason = (request.POST.get("rejection_reason") or "").strip()
    if not rejection_reason:
        messages.error(request, "Please provide a valid reason for rejecting this leave request.")
        return redirect(request.POST.get("next") or "employees:team_lead_leave_requests")

    # 5. Atomic Rejection
    with transaction.atomic():
        locked_req = LeaveRequest.objects.select_for_update().get(id=request_id)
        locked_req.status = "REJECTED"
        locked_req.rejected_by = request.user
        locked_req.rejected_at = timezone.now()
        locked_req.rejection_reason = rejection_reason
        locked_req.save()

        # Notification for subordinate
        Notification.objects.create(
            employee=locked_req.employee,
            notification_type="LEAVE_REJECTED",
            title="Leave Request Rejected",
            message=f"Your {locked_req.leave_type.name} request for {locked_req.number_of_days} day(s) was REJECTED by {request.user.get_full_name() or request.user.username}. Reason: {rejection_reason}",
            is_read=False,
        )

    emp_name = leave_req.employee.user.get_full_name() or leave_req.employee.user.username
    messages.warning(request, f"Leave request #{leave_req.id} for {emp_name} has been REJECTED.")
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("employees:team_lead_leave_requests")


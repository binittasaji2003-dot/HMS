from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.conf import settings
from django.urls import reverse

from .decorators import admin_required
from .forms import (
    AdminDecisionForm,
    AdminIssueWarningForm,
    AdminLoginForm,
    AdminRegistrationForm,
    AnnouncementForm,
    DepartmentForm,
    EmployeeCreateForm,
    EmployeeProfileForm,
    HRManagerCreateForm,
    HRManagerProfileForm,
)
from .models import AdminNotification, Announcement, Department, EmployeeApproval

from employees.models import (
    Employee,
    EmployeePerformance,
    EmployeeReport,
    Notification,
    PerformanceWarning,
    Team,
)
from hr.forms import HRPerformanceReviewForm
from hr.models import (
    AptitudeTest,
    HRManager,
    HRNotification,
    HRPerformanceReview,
    HRWeeklyReport,
    Interview,
)
from candidates.models import Candidate, CandidateNotification, JobApplication, JobVacancy

User = get_user_model()


def get_sidebar_context():
    """Helper function to get common sidebar context variables for all admin views."""
    pending_recs = 0
    try:
        pending_recs = PerformanceWarning.objects.exclude(
            hr_recommendation=""
        ).filter(status__in=["OPEN", "SENT_TO_ADMIN"]).count()
    except Exception:
        pending_recs = 0

    pending_hr_reports = 0
    unread_admin_notifs = 0
    recent_admin_notifs = []
    try:
        pending_hr_reports = HRWeeklyReport.objects.filter(status__in=["SUBMITTED", "UNDER_REVIEW"]).count()
        unread_admin_notifs = AdminNotification.objects.filter(is_read=False).count()
        recent_admin_notifs = AdminNotification.objects.all().order_by("-created_at")[:5]
    except Exception:
        pass

    return {
        "employees_count": Employee.objects.count(),
        "hr_managers_count": HRManager.objects.filter(user__role=User.RoleChoices.HR).count(),
        "departments_count": Department.objects.count(),
        "open_vacancies_count": JobVacancy.objects.filter(status="OPEN").count(),
        "candidates_count": Candidate.objects.count(),
        "approvals_pending_count": EmployeeApproval.objects.filter(status="PENDING").count(),
        "pending_recommendations_count": pending_recs,
        "pending_hr_reports_count": pending_hr_reports,
        "unread_admin_notifications_count": unread_admin_notifs,
        "recent_admin_notifications": recent_admin_notifs,
        "announcements_count": Announcement.objects.count(),
    }


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================


def admin_register_view(request):
    """Register the single System Administrator."""
    if User.objects.filter(role=User.RoleChoices.ADMIN).exists():
        messages.info(
            request,
            "The System Administrator account has already been created. Please log in.",
        )
        return redirect("admin_module:admin_login")

    if request.user.is_authenticated:
        return redirect("admin_module:admin_dashboard")

    if request.method == "POST":
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(
                request,
                f"Administrator account for '{user.email}' registered and signed in.",
            )
            return redirect("admin_module:admin_dashboard")
        messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = AdminRegistrationForm()

    return render(
        request,
        "admin_module/register.html",
        {
            "form": form,
            "page_title": "Admin Registration - Smart HRMS",
        },
    )


def admin_login_view(request):
    """Sign in an existing System Administrator."""
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.RoleChoices.ADMIN:
        return redirect("admin_module:admin_dashboard")

    next_url = request.GET.get("next") or request.POST.get("next") or "admin_module:admin_dashboard"

    if request.method == "POST":
        form = AdminLoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            if not form.cleaned_data.get("remember_me"):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(60 * 60 * 24 * 30)

            messages.success(request, f"Welcome back, {user.name or user.email}!")
            return redirect(next_url)
        messages.error(request, "Sign-in failed. Please check your credentials.")
    else:
        form = AdminLoginForm(request=request)

    return render(
        request,
        "admin_module/login.html",
        {
            "form": form,
            "next": next_url,
            "page_title": "Admin Login - Smart HRMS",
        },
    )


def admin_logout_view(request):
    """Sign out the current administrator."""
    logout(request)
    messages.info(request, "You have been logged out of the Admin Portal.")
    return redirect("admin_module:admin_login")


# ============================================================================
# DASHBOARD VIEW
# ============================================================================


@admin_required
def admin_dashboard_view(request):
    """Main administrative dashboard with KPIs, operational feeds, and quick actions."""
    context = get_sidebar_context()

    recent_announcements = Announcement.objects.filter(is_published=True).order_by(
        "-published_at", "-created_at"
    )[:5]

    recent_employees = Employee.objects.select_related("user", "department").order_by(
        "-created_at"
    )[:5]

    recent_hr_managers = HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user", "department").order_by(
        "-created_at"
    )[:5]

    department_stats = (
        Department.objects.annotate(employee_count=Count("employees"))
        .order_by("-employee_count")[:5]
    )

    dept_labels = [department.name for department in department_stats]
    dept_values = [department.employee_count for department in department_stats]
    total_chart_emps = sum(dept_values)

    dept_summary = [
        {
            "name": department.name,
            "count": department.employee_count,
        }
        for department in department_stats
    ]

    pending_approvals = EmployeeApproval.objects.filter(status="PENDING").select_related(
        "employee", "employee__user", "employee__department"
    )[:5]

    pending_warnings = PerformanceWarning.objects.filter(
        status__in=["OPEN", "SENT_TO_ADMIN"]
    ).select_related("employee", "employee__user", "issued_by")[:5]

    context.update({
        "page_title": "Executive Dashboard - Smart HRMS Admin",
        "current_page": "dashboard",
        "recent_announcements": recent_announcements,
        "recent_employees": recent_employees,
        "recent_hr_managers": recent_hr_managers,
        "department_stats": department_stats,
        "dept_labels": dept_labels,
        "dept_values": dept_values,
        "total_chart_emps": total_chart_emps,
        "dept_summary": dept_summary,
        "pending_approvals": pending_approvals,
        "pending_warnings": pending_warnings,
    })
    return render(request, "admin_module/dashboard.html", context)


# ============================================================================
# DEPARTMENT MANAGEMENT VIEWS
# ============================================================================


@admin_required
def admin_departments_management_view(request):
    """List all departments with workforce metrics."""
    departments = Department.objects.annotate(
        employee_count=Count("employees"),
        hr_count=Count("hr_managers", filter=Q(hr_managers__user__role=User.RoleChoices.HR)),
    ).order_by("name")

    context = get_sidebar_context()
    context.update({
        "page_title": "Departments Directory - Smart HRMS Admin",
        "current_page": "departments",
        "departments": departments,
        "show_add_button": True,
    })
    return render(request, "admin_module/manage_departments.html", context)


@admin_required
def admin_department_create_view(request):
    """Add a new company department."""
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            department.created_by = request.user
            department.save()
            messages.success(request, f"Department '{department.name}' created successfully.")
            return redirect("admin_module:departments_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = DepartmentForm()

    context = get_sidebar_context()
    context.update({
        "page_title": "Create Department - Smart HRMS Admin",
        "current_page": "departments",
        "form": form,
        "title": "Create Department",
        "submit_label": "Create Department",
        "back_url": "admin_module:departments_list",
    })
    return render(request, "admin_module/department_form.html", context)


@admin_required
def admin_department_detail_view(request, department_id):
    """Detailed view for a department, showing workforce and vacancies."""
    department = get_object_or_404(Department, pk=department_id)
    dept_employees = department.employees.select_related("user").order_by("-created_at")
    dept_hr_managers = department.hr_managers.filter(user__role=User.RoleChoices.HR).select_related("user").order_by("-created_at")
    dept_vacancies = department.job_vacancies.all().order_by("-posted_date")

    context = get_sidebar_context()
    context.update({
        "page_title": f"{department.name} - Department Detail",
        "current_page": "departments",
        "department": department,
        "employees": dept_employees,
        "employee_count": dept_employees.count(),
        "hr_managers": dept_hr_managers,
        "vacancies": dept_vacancies,
    })
    return render(request, "admin_module/department_detail.html", context)


@admin_required
def admin_department_edit_view(request, department_id):
    """Update department info."""
    department = get_object_or_404(Department, pk=department_id)

    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{department.name}' updated successfully.")
            return redirect("admin_module:departments_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = DepartmentForm(instance=department)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Edit Department: {department.name}",
        "current_page": "departments",
        "form": form,
        "department": department,
        "title": f"Edit Department: {department.name}",
        "submit_label": "Save Changes",
        "back_url": "admin_module:departments_list",
    })
    return render(request, "admin_module/department_form.html", context)


@admin_required
def admin_department_delete_view(request, department_id):
    """Delete a department with safety checks."""
    department = get_object_or_404(Department, pk=department_id)
    employee_count = department.employees.count()
    hr_manager_count = department.hr_managers.count()

    if request.method == "POST":
        name = department.name
        department.delete()
        messages.success(request, f"Department '{name}' was deleted.")
        return redirect("admin_module:departments_list")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Delete Department: {department.name}",
        "current_page": "departments",
        "object_type": "Department",
        "object_name": department.name,
        "object_id": department_id,
        "delete_url": "admin_module:department_delete",
        "back_url": "admin_module:departments_list",
        "warning_message": (
            f"This department has {employee_count} employee(s) and {hr_manager_count} HR manager(s). "
            "Deleting it will remove their department assignments."
            if employee_count > 0 or hr_manager_count > 0
            else None
        ),
    })
    return render(request, "admin_module/confirm_delete.html", context)


# ============================================================================
# EMPLOYEE MANAGEMENT VIEWS
# ============================================================================


@admin_required
def admin_employees_management_view(request):
    """Directory of all employees with filtering and search."""
    employees = Employee.objects.select_related("user", "department").order_by("-created_at")

    search_query = request.GET.get("q", "").strip()
    dept_filter = request.GET.get("department", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        employees = employees.filter(
            Q(user__name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(designation__icontains=search_query)
            | Q(employee_code__icontains=search_query)
        )

    if dept_filter:
        employees = employees.filter(department_id=dept_filter)

    if status_filter:
        employees = employees.filter(employment_status=status_filter)

    departments = Department.objects.all().order_by("name")

    context = get_sidebar_context()
    context.update({
        "page_title": "Employee Directory - Smart HRMS Admin",
        "current_page": "employees",
        "employees": employees,
        "departments": departments,
        "search_query": search_query,
        "selected_dept": dept_filter,
        "selected_status": status_filter,
    })
    return render(request, "admin_module/manage_employees.html", context)


@admin_required
def admin_employee_create_view(request):
    """Create a new user account and associated Employee profile."""
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            employee = form.save(admin_user=request.user)
            messages.success(
                request,
                f"Employee record for '{employee.user.name or employee.user.email}' created successfully.",
            )
            return redirect("admin_module:employees_list")
        messages.error(request, "Please correct the errors in the employee form below.")
    else:
        form = EmployeeCreateForm()

    context = get_sidebar_context()
    context.update({
        "page_title": "Add New Employee - Smart HRMS Admin",
        "current_page": "employees",
        "form": form,
        "title": "Add New Employee",
        "submit_label": "Create Employee Account",
        "back_url": "admin_module:employees_list",
    })
    return render(request, "admin_module/employee_form.html", context)


@admin_required
def admin_employee_profile_view(request, employee_id):
    """Profile view for a single employee displaying aggregated account, personal, employment, documents, and historical records."""
    employee = get_object_or_404(
        Employee.objects.select_related("user", "department", "candidate", "created_by"),
        pk=employee_id,
    )
    documents = employee.documents.all().order_by("-uploaded_at")
    performance_reviews = employee.performance_reviews.select_related("reviewed_by__user").order_by("-review_date")
    warnings = employee.performance_warnings.select_related("issued_by__user", "decided_by").order_by("-warning_date")
    reports = employee.reports.select_related("reviewed_by__user").order_by("-submitted_at")
    notifications = employee.notifications.all().order_by("-created_at")[:10]

    profile_photo = employee.profile_photo if employee.profile_photo else (
        employee.candidate.profile_photo if (employee.candidate and employee.candidate.profile_photo) else None
    )

    context = get_sidebar_context()
    context.update({
        "page_title": f"{employee.user.name or employee.user.email} - Employee Profile",
        "current_page": "employees",
        "employee": employee,
        "profile_photo": profile_photo,
        "documents": documents,
        "performance_reviews": performance_reviews,
        "warnings": warnings,
        "reports": reports,
        "notifications": notifications,
        "back_url": "admin_module:employees_list",
        "title": "Employee Profile",
    })
    return render(request, "admin_module/employee_profile.html", context)


@admin_required
def admin_employee_edit_view(request, employee_id):
    """Edit an existing employee profile."""
    employee = get_object_or_404(
        Employee.objects.select_related("user", "department"),
        pk=employee_id,
    )

    if request.method == "POST":
        form = EmployeeProfileForm(request.POST, employee=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Profile for '{employee.user.name or employee.user.email}' updated.")
            return redirect("admin_module:employee_detail", employee_id=employee.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeProfileForm(employee=employee)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Edit Employee: {employee.user.name or employee.user.email}",
        "current_page": "employees",
        "form": form,
        "employee": employee,
        "title": f"Edit Employee: {employee.user.name or employee.user.email}",
        "submit_label": "Save Changes",
        "back_url": "admin_module:employees_list",
    })
    return render(request, "admin_module/employee_form.html", context)


@admin_required
def admin_employee_delete_view(request, employee_id):
    """Deactivate and terminate an employee profile while preserving all historical records."""
    employee = get_object_or_404(
        Employee.objects.select_related("user", "department"),
        pk=employee_id,
    )

    if request.method == "POST":
        name = employee.user.name or employee.user.email
        # Safely mark employee as TERMINATED
        employee.employment_status = "TERMINATED"
        employee.save(update_fields=["employment_status", "updated_at"])

        # Deactivate corresponding user account
        user = employee.user
        user.is_active = False
        user.status = User.StatusChoices.INACTIVE
        user.save(update_fields=["is_active", "status"])

        messages.success(
            request,
            f"Employee '{name}' has been deactivated and marked as Terminated. All historical records have been preserved.",
        )
        return redirect("admin_module:employees_list")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Terminate Employee: {employee.user.name or employee.user.email}",
        "current_page": "employees",
        "object_type": "Employee",
        "object_name": f"{employee.user.name or employee.user.email} ({employee.designation})",
        "object_id": employee_id,
        "delete_url": "admin_module:employee_delete",
        "back_url": "admin_module:employees_list",
        "warning_message": "Terminating this employee will deactivate their login account while preserving all historical work reports, performance reviews, warnings, and documents.",
    })
    return render(request, "admin_module/confirm_delete.html", context)


# ============================================================================
# HR MANAGER MANAGEMENT VIEWS
# ============================================================================


@admin_required
def admin_hr_managers_management_view(request):
    """List and manage HR Managers."""
    hr_managers = HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user", "department").order_by("-created_at")

    search_query = request.GET.get("q", "").strip()
    dept_filter = request.GET.get("department", "")

    if search_query:
        hr_managers = hr_managers.filter(
            Q(user__name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(employee_code__icontains=search_query)
        )

    if dept_filter:
        hr_managers = hr_managers.filter(department_id=dept_filter)

    departments = Department.objects.all().order_by("name")

    context = get_sidebar_context()
    context.update({
        "page_title": "HR Managers Directory - Smart HRMS Admin",
        "current_page": "hr_managers",
        "hr_managers": hr_managers,
        "departments": departments,
        "search_query": search_query,
        "selected_dept": dept_filter,
    })
    return render(request, "admin_module/manage_hr_managers.html", context)


@admin_required
def admin_hr_manager_create_view(request):
    """Create a new HR Manager."""
    if request.method == "POST":
        form = HRManagerCreateForm(request.POST)
        if form.is_valid():
            manager = form.save(admin_user=request.user)
            messages.success(
                request,
                f"HR Manager profile for '{manager.user.name or manager.user.email}' created successfully.",
            )
            return redirect("admin_module:hr_managers_list")
        messages.error(request, "Please correct the errors in the form below.")
    else:
        form = HRManagerCreateForm()

    context = get_sidebar_context()
    context.update({
        "page_title": "Add New HR Manager - Smart HRMS Admin",
        "current_page": "hr_managers",
        "form": form,
        "title": "Add New HR Manager",
        "submit_label": "Create HR Manager Account",
        "back_url": "admin_module:hr_managers_list",
    })
    return render(request, "admin_module/hr_manager_form.html", context)


@admin_required
def admin_hr_manager_profile_view(request, manager_id):
    """Profile detail for an HR Manager displaying aggregated profile, education, experience, documents, account, and activity."""
    manager = get_object_or_404(
        HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user", "department"),
        pk=manager_id,
    )
    linked_employee = getattr(manager.user, "employee_profile", None)
    documents = list(manager.documents.all().order_by("-uploaded_at"))
    if not documents and linked_employee:
        documents = list(linked_employee.documents.all().order_by("-uploaded_at"))

    education_records = manager.education_records.all()
    experience_records = manager.experience_records.all()
    profile_photo = manager.profile_photo or (linked_employee.profile_photo if linked_employee else None)

    aptitude_tests = manager.aptitude_tests.all().order_by("-created_at")
    interviews = manager.interviews.select_related("application", "application__candidate").order_by("-interview_date")
    posted_jobs = manager.posted_jobs.all().order_by("-created_at")
    reviewed_reports = manager.reviewed_employee_reports.select_related("employee__user").order_by("-reviewed_at")
    performance_reviews = manager.employee_performance_reviews.select_related("employee__user").order_by("-review_date")
    issued_warnings = manager.issued_warnings.select_related("employee__user").order_by("-warning_date")

    context = get_sidebar_context()
    context.update({
        "page_title": f"{manager.full_name} - HR Manager Profile",
        "current_page": "hr_managers",
        "manager": manager,
        "linked_employee": linked_employee,
        "profile_photo": profile_photo,
        "education_records": education_records,
        "experience_records": experience_records,
        "documents": documents,
        "aptitude_tests": aptitude_tests,
        "interviews": interviews,
        "posted_jobs": posted_jobs,
        "reviewed_reports": reviewed_reports,
        "performance_reviews": performance_reviews,
        "issued_warnings": issued_warnings,
        "back_url": "admin_module:hr_managers_list",
        "title": "HR Manager Profile",
    })
    return render(request, "admin_module/hr_manager_profile.html", context)


@admin_required
def admin_hr_manager_edit_view(request, manager_id):
    """Update HR Manager profile."""
    manager = get_object_or_404(
        HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user", "department"),
        pk=manager_id,
    )

    if request.method == "POST":
        form = HRManagerProfileForm(request.POST, manager=manager)
        if form.is_valid():
            form.save()
            messages.success(request, f"HR Manager '{manager.user.name or manager.user.email}' updated.")
            return redirect("admin_module:hr_manager_detail", manager_id=manager.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = HRManagerProfileForm(manager=manager)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Edit HR Manager: {manager.user.name or manager.user.email}",
        "current_page": "hr_managers",
        "form": form,
        "manager": manager,
        "title": f"Edit HR Manager: {manager.user.name or manager.user.email}",
        "submit_label": "Save Changes",
        "back_url": "admin_module:hr_managers_list",
    })
    return render(request, "admin_module/hr_manager_form.html", context)


@admin_required
def admin_hr_manager_delete_view(request, manager_id):
    """Delete HR Manager profile and account."""
    manager = get_object_or_404(
        HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user"),
        pk=manager_id,
    )

    if request.method == "POST":
        name = manager.user.name or manager.user.email
        user = manager.user
        manager.delete()
        user.delete()
        messages.success(request, f"HR Manager '{name}' was deleted.")
        return redirect("admin_module:hr_managers_list")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Delete HR Manager: {manager.user.name or manager.user.email}",
        "current_page": "hr_managers",
        "object_type": "HR Manager",
        "object_name": manager.user.name or manager.user.email,
        "object_id": manager_id,
        "delete_url": "admin_module:hr_manager_delete",
        "back_url": "admin_module:hr_managers_list",
        "warning_message": "Deleting this HR Manager removes their account and leaves historical records intact.",
    })
    return render(request, "admin_module/confirm_delete.html", context)


@admin_required
def admin_hr_manager_toggle_status_view(request, manager_id):
    """Toggle active status for an HR Manager."""
    manager = get_object_or_404(HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user"), pk=manager_id)
    if request.method == "POST":
        new_active = not manager.is_active
        manager.is_active = new_active
        manager.save(update_fields=["is_active"])
        manager.user.is_active = new_active
        manager.user.status = User.StatusChoices.ACTIVE if new_active else User.StatusChoices.INACTIVE
        manager.user.save(update_fields=["is_active", "status"])

        state_label = "activated" if new_active else "deactivated"
        messages.success(request, f"HR Manager '{manager.user.name or manager.user.email}' has been {state_label}.")
    return redirect("admin_module:hr_managers_list")


# ============================================================================
# ANNOUNCEMENT MANAGEMENT VIEWS
# ============================================================================


@admin_required
def admin_announcements_management_view(request):
    """List all broadcasts and announcements."""
    announcements = Announcement.objects.select_related("created_by").order_by("-created_at")

    type_filter = request.GET.get("type", "")
    audience_filter = request.GET.get("audience", "")

    if type_filter:
        announcements = announcements.filter(announcement_type=type_filter)

    if audience_filter:
        announcements = announcements.filter(target_audience=audience_filter)

    total_count = Announcement.objects.count()
    company_wide_count = Announcement.objects.filter(target_audience="All").count()
    targeted_count = Announcement.objects.exclude(target_audience="All").count()

    context = get_sidebar_context()
    context.update({
        "page_title": "Announcements - Smart HRMS Admin",
        "current_page": "announcements",
        "announcements": announcements,
        "total_count": total_count,
        "company_wide_count": company_wide_count,
        "targeted_count": targeted_count,
        "selected_type": type_filter,
        "audience_filter": audience_filter,
        "show_add_button": True,
    })
    return render(request, "admin_module/manage_announcements.html", context)


@admin_required
def admin_announcement_create_view(request):
    """Compose and immediately publish a new broadcast announcement."""
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.is_published = True
            announcement.published_at = timezone.now()
            announcement.is_active = True
            announcement.save()

            messages.success(
                request,
                f"Announcement '{announcement.title}' has been published successfully."
            )
            return redirect("admin_module:announcements_list")

        messages.error(request, "Please correct the errors in the announcement form below.")
    else:
        form = AnnouncementForm()

    context = get_sidebar_context()
    context.update({
        "page_title": "New Announcement - Smart HRMS Admin",
        "current_page": "announcements",
        "form": form,
        "title": "Create Announcement",
        "submit_label": "Publish Announcement",
        "back_url": "admin_module:announcements_list",
    })
    return render(request, "admin_module/announcement_form.html", context)


@admin_required
def admin_announcement_detail_view(request, announcement_id):
    """View full details of an announcement."""
    announcement = get_object_or_404(Announcement.objects.select_related("created_by"), pk=announcement_id)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Announcement: {announcement.title}",
        "current_page": "announcements",
        "announcement": announcement,
    })
    return render(request, "admin_module/announcement_detail.html", context)


@admin_required
def admin_announcement_edit_view(request, announcement_id):
    """Edit an announcement."""
    announcement = get_object_or_404(Announcement, pk=announcement_id)

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.is_published = True
            if not announcement.published_at:
                announcement.published_at = timezone.now()
            announcement.is_active = True
            announcement.save()
            messages.success(request, f"Announcement '{announcement.title}' was updated successfully.")
            return redirect("admin_module:announcements_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AnnouncementForm(instance=announcement)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Edit Announcement: {announcement.title}",
        "current_page": "announcements",
        "form": form,
        "announcement": announcement,
        "title": f"Edit Announcement: {announcement.title}",
        "submit_label": "Save Changes",
        "back_url": "admin_module:announcements_list",
    })
    return render(request, "admin_module/announcement_form.html", context)


@admin_required
def admin_announcement_delete_view(request, announcement_id):
    """Delete an announcement."""
    announcement = get_object_or_404(Announcement, pk=announcement_id)

    if request.method == "POST":
        title = announcement.title
        announcement.delete()
        messages.success(request, f"Announcement '{title}' has been deleted.")
        return redirect("admin_module:announcements_list")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Delete Announcement: {announcement.title}",
        "current_page": "announcements",
        "object_type": "Announcement",
        "object_name": announcement.title,
        "object_id": announcement_id,
        "delete_url": "admin_module:announcement_delete",
        "back_url": "admin_module:announcements_list",
    })
    return render(request, "admin_module/confirm_delete.html", context)


@admin_required
def admin_announcement_publish_view(request, announcement_id):
    """Ensure announcement is published (fallback handler)."""
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    if request.method == "POST":
        if not announcement.is_published:
            announcement.is_published = True
            announcement.published_at = timezone.now()
            announcement.is_active = True
            announcement.save(update_fields=["is_published", "published_at", "is_active", "updated_at"])
            messages.success(request, f"Announcement '{announcement.title}' has been published.")
    return redirect("admin_module:announcements_list")


# ============================================================================
# CANDIDATE MANAGEMENT VIEWS
# ============================================================================


@admin_required
def admin_candidates_management_view(request):
    """List and manage candidate applications."""
    candidates = Candidate.objects.select_related("user").prefetch_related("applications", "applications__vacancy", "applications__vacancy__department").order_by("-created_at")
    
    # Attach helper properties for template compatibility
    for cand in candidates:
        name_parts = [cand.first_name, cand.middle_name, cand.last_name]
        cand.full_name = " ".join([p for p in name_parts if p])
        cand.email = cand.user.email if cand.user else ""
        latest_app = cand.applications.order_by("-applied_at").first()
        cand.job_vacancy = latest_app.vacancy if latest_app else None
        cand.status = latest_app.status if latest_app else "APPLIED"
        cand.applied_at = latest_app.applied_at if latest_app else cand.created_at

    context = get_sidebar_context()
    context.update({
        "page_title": "Candidates Directory - Smart HRMS Admin",
        "current_page": "candidates",
        "candidates": candidates,
    })
    return render(request, "admin_module/manage_candidates.html", context)



@admin_required
def admin_candidate_delete_view(request, candidate_id):
    """Delete candidate and their user account."""
    candidate = get_object_or_404(Candidate.objects.select_related("user"), pk=candidate_id)
    full_name = f"{candidate.first_name} {candidate.last_name}".strip()

    if request.method == "POST":
        user = candidate.user
        candidate.delete()
        if user:
            user.delete()
        messages.success(request, f"Candidate application for '{full_name}' was deleted.")
        return redirect("admin_module:candidates_list")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Delete Candidate: {full_name}",
        "current_page": "candidates",
        "object_type": "Candidate",
        "object_name": full_name,
        "object_id": candidate_id,
        "delete_url": "admin_module:candidate_delete",
        "back_url": "admin_module:candidates_list",
    })
    return render(request, "admin_module/confirm_delete.html", context)


# ============================================================================
# RECRUITMENT MONITORING & EMPLOYEE APPROVAL VIEWS
# ============================================================================


@admin_required
def admin_recruitment_jobs_view(request):
    """Monitor active and closed job vacancies."""
    vacancies = JobVacancy.objects.select_related("department", "posted_by").annotate(
        applications_count=Count("applications")
    ).order_by("-posted_date")

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")

    if search_query:
        vacancies = vacancies.filter(
            Q(title__icontains=search_query)
            | Q(department__name__icontains=search_query)
            | Q(location__icontains=search_query)
        )

    if status_filter:
        vacancies = vacancies.filter(status__iexact=status_filter)

    total_jobs = JobVacancy.objects.count()
    open_jobs = JobVacancy.objects.filter(status__iexact="OPEN").count()
    total_applications = JobApplication.objects.count()
    selections_count = JobApplication.objects.filter(status="SELECTED").count()
    approvals_pending_count = EmployeeApproval.objects.filter(status="PENDING").count()

    job_rows = []
    for v in vacancies:
        owner_name = (v.posted_by.name or v.posted_by.email) if v.posted_by else "HR Operations"
        owner_role = getattr(v.posted_by, "role", "HR Manager") if v.posted_by else "HR Manager"
        job_rows.append({
            "vacancy": v,
            "owner_name": owner_name,
            "owner_role": owner_role,
            "applicants_count": getattr(v, "applications_count", v.applications.count()),
        })

    context = get_sidebar_context()
    context.update({
        "page_title": "Recruitment Job Postings - Smart HRMS Admin",
        "current_page": "recruitment",
        "job_rows": job_rows,
        "vacancies": vacancies,
        "search": search_query,
        "status_filter": status_filter,
        "job_statuses": JobVacancy.STATUS_CHOICES,
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "total_applications": total_applications,
        "selections_count": selections_count,
        "approvals_pending_count": approvals_pending_count,
    })
    return render(request, "admin_module/recruitment_jobs.html", context)


@admin_required
def admin_recruitment_status_view(request):
    """Recruitment status dashboard tracking applicants through each hiring stage."""
    vacancies = JobVacancy.objects.select_related("department").all().order_by("-posted_date")

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "")

    if search_query:
        vacancies = vacancies.filter(
            Q(title__icontains=search_query)
            | Q(department__name__icontains=search_query)
        )

    if status_filter:
        vacancies = vacancies.filter(status__iexact=status_filter)

    stages = ["Applied", "Shortlisted", "Interviewing", "Selected", "Hired", "Rejected"]

    global_totals = {
        "Applied": JobApplication.objects.filter(status="APPLIED").count(),
        "Shortlisted": JobApplication.objects.filter(status__in=["SHORTLISTED", "RESUME_REVIEW", "APTITUDE"]).count(),
        "Interviewing": JobApplication.objects.filter(status="INTERVIEW").count(),
        "Selected": JobApplication.objects.filter(status="SELECTED").count(),
        "Hired": 0,
        "Rejected": JobApplication.objects.filter(status="REJECTED").count(),
    }
    total_applications = JobApplication.objects.count()

    job_rows = []
    for v in vacancies:
        apps = v.applications.all()
        row_stages = {
            "Applied": apps.filter(status="APPLIED").count(),
            "Shortlisted": apps.filter(status__in=["SHORTLISTED", "RESUME_REVIEW", "APTITUDE"]).count(),
            "Interviewing": apps.filter(status="INTERVIEW").count(),
            "Selected": apps.filter(status="SELECTED").count(),
            "Hired": 0,
            "Rejected": apps.filter(status="REJECTED").count(),
        }
        job_rows.append({
            "vacancy": v,
            "applicants_count": apps.count(),
            "stages": row_stages,
        })

    context = get_sidebar_context()
    context.update({
        "page_title": "Recruitment Status - Smart HRMS Admin",
        "current_page": "recruitment",
        "job_rows": job_rows,
        "stages": stages,
        "global_totals": global_totals,
        "total_applications": total_applications,
        "search": search_query,
        "status_filter": status_filter,
        "job_statuses": JobVacancy.STATUS_CHOICES,
    })
    return render(request, "admin_module/recruitment_status.html", context)


@admin_required
def admin_recruitment_job_status_view(request, vacancy_id):
    """Pipeline candidates for a single job opening."""
    vacancy = get_object_or_404(JobVacancy.objects.select_related("department"), pk=vacancy_id)
    applications = vacancy.applications.select_related("candidate", "candidate__user").order_by("-applied_at")

    stage_filter = request.GET.get("stage", "")
    if stage_filter:
        applications = applications.filter(status=stage_filter)

    stage_counts = {
        "APPLIED": vacancy.applications.filter(status="APPLIED").count(),
        "SHORTLISTED": vacancy.applications.filter(status__in=["SHORTLISTED", "RESUME_REVIEW", "APTITUDE"]).count(),
        "INTERVIEW": vacancy.applications.filter(status="INTERVIEW").count(),
        "SELECTED": vacancy.applications.filter(status="SELECTED").count(),
        "REJECTED": vacancy.applications.filter(status="REJECTED").count(),
    }

    # Attach candidate attributes for template
    cand_list = []
    for app in applications:
        c = app.candidate
        c.full_name = f"{c.first_name} {c.last_name}".strip()
        c.email = c.user.email if c.user else ""
        c.application_status = app.status
        c.application_pk = app.pk
        cand_list.append(c)

    context = get_sidebar_context()
    context.update({
        "page_title": f"{vacancy.title} - Candidate Pipeline",
        "current_page": "recruitment",
        "vacancy": vacancy,
        "applications": applications,
        "candidates": cand_list,
        "stage_counts": stage_counts,
        "selected_stage": stage_filter,
    })
    return render(request, "admin_module/recruitment_job_status.html", context)


@admin_required
def admin_recruitment_selected_view(request):
    """List candidates who reached the Selected stage."""
    selected_apps = JobApplication.objects.filter(status="SELECTED").select_related(
        "candidate", "candidate__user", "vacancy", "vacancy__department"
    ).order_by("-updated_at")

    search_query = request.GET.get("q", "").strip()
    vacancy_filter = request.GET.get("vacancy", "")

    if search_query:
        selected_apps = selected_apps.filter(
            Q(candidate__first_name__icontains=search_query)
            | Q(candidate__last_name__icontains=search_query)
            | Q(candidate__user__email__icontains=search_query)
        )

    if vacancy_filter:
        selected_apps = selected_apps.filter(vacancy_id=vacancy_filter)

    selected_candidates = []
    for app in selected_apps:
        cand = app.candidate
        cand.full_name = f"{cand.first_name} {cand.last_name}".strip()
        cand.email = cand.user.email if cand.user else ""
        cand.job_vacancy = app.vacancy
        cand.status = app.status
        cand.updated_at = app.updated_at
        cand.pk = cand.candidate_id
        selected_candidates.append(cand)

    vacancies = JobVacancy.objects.all().order_by("title")

    context = get_sidebar_context()
    context.update({
        "page_title": "Selected Candidates - Smart HRMS Admin",
        "current_page": "recruitment",
        "selected_candidates": selected_candidates,
        "vacancies": vacancies,
        "search": search_query,
        "vacancy_filter": vacancy_filter,
        "selected_count": len(selected_candidates),
        "hired_count": Employee.objects.filter(candidate__isnull=False).count(),
        "total_count": len(selected_candidates),
    })
    return render(request, "admin_module/recruitment_selected.html", context)


@admin_required
def admin_recruitment_candidate_detail_view(request, candidate_id):
    """Read-only candidate application profile."""
    candidate = get_object_or_404(Candidate.objects.select_related("user"), pk=candidate_id)
    candidate.full_name = f"{candidate.first_name} {candidate.last_name}".strip()
    candidate.email = candidate.user.email if candidate.user else ""

    latest_app = candidate.applications.select_related("vacancy", "vacancy__department").order_by("-applied_at").first()
    candidate.job_vacancy = latest_app.vacancy if latest_app else None
    candidate.status = latest_app.status if latest_app else "APPLIED"

    context = get_sidebar_context()
    context.update({
        "page_title": f"Candidate: {candidate.full_name}",
        "current_page": "recruitment",
        "candidate": candidate,
        "application": latest_app,
    })
    return render(request, "admin_module/recruitment_candidate_detail.html", context)


def generate_unique_employee_code():
    """Generates sequential and unique employee codes in standard format (e.g., EMP0001, EMP0002)."""
    import re
    existing_codes = Employee.objects.filter(employee_code__startswith="EMP").values_list("employee_code", flat=True)
    max_num = 0
    for code in existing_codes:
        m = re.search(r"EMP-?(\d+)", code)
        if m:
            try:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    next_num = max(max_num + 1, Employee.objects.count() + 1)
    new_code = f"EMP{next_num:04d}"
    while Employee.objects.filter(employee_code=new_code).exists():
        next_num += 1
        new_code = f"EMP{next_num:04d}"
    return new_code


@admin_required
def admin_recruitment_approvals_view(request):
    """View employee approvals pending or historical admin review."""
    status_filter = request.GET.get("status", "PENDING").strip().upper()
    search_query = request.GET.get("q", "").strip()

    approvals = EmployeeApproval.objects.select_related(
        "employee", "employee__user", "employee__department", "employee__department__department_leader",
        "employee__team", "employee__team_lead", "employee__candidate", "employee__created_by", "requested_by", "approved_by"
    ).order_by("-employee__created_at")

    if status_filter and status_filter != "ALL":
        approvals = approvals.filter(status=status_filter)

    if search_query:
        approvals = approvals.filter(
            Q(employee__user__name__icontains=search_query)
            | Q(employee__user__email__icontains=search_query)
            | Q(employee__designation__icontains=search_query)
            | Q(employee__department__name__icontains=search_query)
            | Q(employee__employee_code__icontains=search_query)
        )

    pending_count = EmployeeApproval.objects.filter(status="PENDING").count()
    approved_count = EmployeeApproval.objects.filter(status="APPROVED").count()
    rejected_count = EmployeeApproval.objects.filter(status="REJECTED").count()
    active_employees = Employee.objects.filter(employment_status="ACTIVE").count()
    total_employees = Employee.objects.count()

    context = get_sidebar_context()
    context.update({
        "page_title": "Employee Approval Requests - Smart HRMS Admin",
        "current_page": "recruitment",
        "current_page": "recruitment_approvals",
        "pending_approvals": approvals,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "active_employees": active_employees,
        "total_employees": total_employees,
        "status_filter": status_filter,
        "search": search_query,
    })
    return render(request, "admin_module/recruitment_approvals.html", context)


@admin_required
def admin_recruitment_approval_review_view(request, employee_id):
    """Review screen for approving a newly selected candidate into the workforce."""
    employee = get_object_or_404(
        Employee.objects.select_related(
            "user", "department", "department__department_leader", "team", "team_lead", "candidate", "created_by"
        ),
        pk=employee_id,
    )
    approval, _ = EmployeeApproval.objects.get_or_create(
        employee=employee,
        defaults={"status": "PENDING"},
    )

    # Fetch candidate profile details, application info, aptitude results, and interview notes
    candidate = employee.candidate
    latest_app = None
    aptitude_results = []
    interviews = []
    screening_result = None
    if candidate:
        latest_app = candidate.applications.select_related("vacancy", "vacancy__department", "aptitude_test", "screening_result").order_by("-applied_at").first()
        if latest_app:
            screening_result = getattr(latest_app, "screening_result", None)
            aptitude_results = latest_app.aptitude_results.select_related("test").all()
            interviews = latest_app.interviews.select_related("interviewer__user", "location", "evaluation").order_by("interview_date", "interview_time")

    departments = Department.objects.filter(is_active=True).select_related("department_leader").order_by("name")
    teams = Team.objects.filter(is_active=True).select_related("department", "team_lead").order_by("team_name")
    eligible_team_leads = User.objects.filter(
        role__in=[User.RoleChoices.HR, User.RoleChoices.EMPLOYEE], is_active=True
    ).order_by("name", "email")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Review Approval: {employee.user.name or employee.user.email}",
        "current_page": "recruitment",
        "current_page": "recruitment_approvals",
        "employee": employee,
        "approval": approval,
        "candidate": candidate,
        "latest_app": latest_app,
        "screening": screening_result,
        "aptitude_results": aptitude_results,
        "interviews": interviews,
        "departments": departments,
        "teams": teams,
        "eligible_team_leads": eligible_team_leads,
    })
    return render(request, "admin_module/recruitment_approval_review.html", context)


@admin_required
def admin_recruitment_approval_approve_view(request, employee_id):
    """Execute approval of new employee record atomically."""
    import datetime
    from django.core.mail import send_mail

    if request.method != "POST":
        return redirect("admin_module:recruitment_approval_review", employee_id=employee_id)

    employee = get_object_or_404(Employee.objects.select_related("user", "candidate", "department", "team", "team_lead"), pk=employee_id)
    employee = get_object_or_404(
        Employee.objects.select_related("user", "candidate", "department", "team", "team_lead", "created_by"),
        pk=employee_id,
    )
    approval, _ = EmployeeApproval.objects.get_or_create(
        employee=employee,
        defaults={"status": "PENDING"},
    )

    if approval.status == "APPROVED":
        messages.warning(request, "This employee creation request has already been approved.")
        messages.warning(request, "This employee onboarding request has already been approved.")
        return redirect("admin_module:recruitment_approvals")

    comments = request.POST.get("comments", "").strip()
    temporary_password = (
        request.POST.get("temporary_password", "").strip()
        or request.POST.get("temp_password", "").strip()
    )

    # Optional Admin Overrides
    custom_dept_id = request.POST.get("department")
    if custom_dept_id:
        dept = Department.objects.filter(pk=custom_dept_id).first()
        if dept:
            employee.department = dept

    custom_designation = request.POST.get("designation", "").strip()
    if custom_designation:
        employee.designation = custom_designation

    custom_team_id = request.POST.get("team")
    if custom_team_id:
        team = Team.objects.filter(pk=custom_team_id).first()
        if team:
            employee.team = team

    custom_lead_id = request.POST.get("team_lead")
    if custom_lead_id:
        lead = User.objects.filter(pk=custom_lead_id).first()
        if lead:
            employee.team_lead = lead

    custom_joining_date = request.POST.get("joining_date", "").strip()
    if custom_joining_date:
        try:
            employee.joining_date = datetime.date.fromisoformat(custom_joining_date)
        except Exception:
            pass

    custom_emp_type = request.POST.get("employment_type", "").strip()
    if custom_emp_type in ["FULL_TIME", "PART_TIME", "CONTRACT", "INTERN"]:
        employee.employment_type = custom_emp_type

    with transaction.atomic():
        # Ensure unique Employee Code
        if not employee.employee_code or employee.employee_code.startswith("EMP0000") or Employee.objects.filter(employee_code=employee.employee_code).exclude(pk=employee.pk).exists():
            employee.employee_code = generate_unique_employee_code()

        employee.employment_status = "ACTIVE"
        employee.save()

        # Update User Role & Set Temporary Password if supplied
        user = employee.user
        user.role = User.RoleChoices.EMPLOYEE
        user.is_active = True
        user.status = User.StatusChoices.ACTIVE
        if temporary_password:
            user.set_password(temporary_password)
        user.save()

        # Update Approval Record
        approval.status = "APPROVED"
        approval.approved_by = request.user
        approval.approved_at = timezone.now()
        approval.comments = comments
        approval.save(update_fields=["status", "approved_by", "approved_at", "comments"])

        # Update Candidate Job Application
        cand = employee.candidate or getattr(employee.user, "candidate_profile", None) or Candidate.objects.filter(user=employee.user).first()
        latest_app = None
        if cand:
            latest_app = cand.applications.filter(status__in=["FORWARDED_TO_ADMIN", "SELECTED"]).order_by("-applied_at").first() or cand.applications.order_by("-applied_at").first()
            if latest_app:
                latest_app.status = "HIRED"
                latest_app.save(update_fields=["status", "updated_at"])

        dept_name = employee.department.name if employee.department else "General Operations"
        joining_date_str = employee.joining_date.strftime("%d %B %Y") if employee.joining_date else "Immediate"
        pass_display = temporary_password if temporary_password else "Use your existing candidate account password"

        # 1. In-app notification for Candidate
        if cand:
            CandidateNotification.objects.create(
                candidate=cand,
                application=latest_app,
                title="🎉 Official Onboarding Complete - Welcome to the Team!",
                message=(
                    f"Dear {user.name or cand.first_name},\n\n"
                    f"Your employee onboarding has been approved by the Admin.\n\n"
                    f"You can now log in to the HRMS Employee Portal.\n\n"
                    f"Employee ID: {employee.employee_code}\n"
                    f"Email: {user.email}\n"
                    f"Temporary Password: {pass_display}\n"
                    f"Department: {dept_name}\n"
                    f"Designation: {employee.designation}\n"
                    f"Joining Date: {joining_date_str}\n\n"
                    f"Please log in and change your password after your first login."
                ),
                notification_type="EMPLOYEE_CONVERTED",
                link_url="/employees/login/",
                is_read=False,
            )

        # 2. In-app notification for Employee Profile
        Notification.objects.create(
            employee=employee,
            title="Welcome to the Organization",
            message=f"Your employee account ({employee.employee_code}) has been activated. Welcome to the {dept_name} team!",
            notification_type="PROFILE_UPDATE",
            is_read=False,
        )

        # 3. In-app notification for HR Manager
        if employee.created_by and hasattr(employee.created_by, "hr_profile"):
            HRNotification.objects.create(
                hr_manager=employee.created_by.hr_profile,
                title="Employee Onboarding Approved",
                message=f"Admin has approved the onboarding request for {user.name or user.email} ({employee.employee_code}) as {employee.designation}.",
                notification_type="GENERAL",
                link_url=reverse("hr:application_detail", kwargs={"pk": latest_app.pk}) if latest_app else "",
                is_read=False,
            )

        # 4. Dispatch Email to Candidate
        try:
            subject = "Your HRMS Employee Account Has Been Created"
            email_body = (
                f"Dear {user.name or employee.candidate.first_name if employee.candidate else user.email},\n\n"
                f"Your employee onboarding has been approved by the Admin.\n\n"
                f"You can now log in to the HRMS Employee Portal.\n\n"
                f"Employee ID:\n{employee.employee_code}\n\n"
                f"Email:\n{user.email}\n\n"
                f"Temporary Password:\n{pass_display}\n\n"
                f"Department:\n{dept_name}\n\n"
                f"Designation:\n{employee.designation}\n\n"
                f"Joining Date:\n{joining_date_str}\n\n"
                f"Please log in and change your password after your first login.\n\n"
                f"Best regards,\nHR Management Team"
            )
            send_mail(
                subject,
                email_body,
                getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@hrms.local"),
                [user.email],
                fail_silently=True,
            )
        except Exception:
            pass

    messages.success(
        request,
        f"Employee onboarding approved successfully. Employee account {employee.employee_code} has been created and login credentials have been sent.",
    )
    return redirect("admin_module:recruitment_approvals")


@admin_required
def admin_recruitment_approval_reject_view(request, employee_id):
    """Execute rejection of new employee record atomically."""
    if request.method != "POST":
        return redirect("admin_module:recruitment_approval_review", employee_id=employee_id)

    employee = get_object_or_404(Employee.objects.select_related("user", "candidate"), pk=employee_id)
    employee = get_object_or_404(
        Employee.objects.select_related("user", "candidate", "created_by"),
        pk=employee_id,
    )
    approval, _ = EmployeeApproval.objects.get_or_create(
        employee=employee,
        defaults={"status": "PENDING"},
    )

    if approval.status == "APPROVED":
        messages.warning(request, "This approval has already been approved and cannot be rejected.")
        return redirect("admin_module:recruitment_approvals")

    rejection_reason = request.POST.get("rejection_reason", "").strip() or request.POST.get("comments", "").strip()
    if not rejection_reason:
        rejection_reason = "Application does not meet the necessary criteria at this time."

    with transaction.atomic():
        approval.status = "REJECTED"
        approval.approved_by = request.user
        approval.approved_at = timezone.now()
        approval.comments = rejection_reason
        approval.rejection_reason = rejection_reason
        approval.save(update_fields=["status", "approved_by", "approved_at", "comments", "rejection_reason"])

        employee.employment_status = "INACTIVE"
        employee.save(update_fields=["employment_status", "updated_at"])

        # Candidate remains in SELECTED status
        # Candidate remains in SELECTED status (not converted to employee)
        latest_app = None
        if employee.candidate:
            app = employee.candidate.applications.order_by("-applied_at").first()
            if app:
                app.status = "SELECTED"
                app.save(update_fields=["status", "updated_at"])
            latest_app = employee.candidate.applications.order_by("-applied_at").first()
            if latest_app:
                latest_app.status = "SELECTED"
                latest_app.save(update_fields=["status", "updated_at"])

        # Notify HR Manager of rejection with reason
        if employee.created_by and hasattr(employee.created_by, "hr_profile"):
            HRNotification.objects.create(
                hr_manager=employee.created_by.hr_profile,
                title="Employee Onboarding Request Rejected",
                message=f"Employee onboarding request for {employee.user.name or employee.user.email} was rejected by Admin. Reason: {rejection_reason}",
                notification_type="GENERAL",
                link_url=reverse("hr:application_detail", kwargs={"pk": latest_app.pk}) if latest_app else "",
                is_read=False,
            )

    messages.warning(
        request,
        f"Employee creation request for '{employee.user.name or employee.user.email}' has been rejected with administrative feedback.",
        f"Employee onboarding request for '{employee.user.name or employee.user.email}' was rejected.",
    )
    return redirect("admin_module:recruitment_approvals")


# ============================================================================
# ADMIN RESPONSIBILITIES VIEWS (Warnings & HR Recommendations)
# ============================================================================


@admin_required
def admin_responsibilities_warnings_view(request):
    """List performance warnings issued across the organization."""
    warnings = PerformanceWarning.objects.select_related(
        "employee", "employee__user", "employee__department", "issued_by", "issued_by__user"
    ).order_by("-warning_date")

    status_filter = request.GET.get("status", "")
    if status_filter:
        warnings = warnings.filter(status=status_filter)

    open_count = PerformanceWarning.objects.filter(status="OPEN").count()
    sent_count = PerformanceWarning.objects.filter(status="SENT_TO_ADMIN").count()
    resolved_count = PerformanceWarning.objects.filter(status="RESOLVED").count()

    context = get_sidebar_context()
    context.update({
        "page_title": "Performance Warnings - Smart HRMS Admin",
        "current_page": "responsibilities",
        "warnings": warnings,
        "selected_status": status_filter,
        "open_count": open_count,
        "sent_count": sent_count,
        "resolved_count": resolved_count,
    })
    return render(request, "admin_module/responsibilities_warnings.html", context)


@admin_required
def admin_responsibilities_warning_detail_view(request, warning_id):
    """Detailed view for a specific performance warning."""
    warning = get_object_or_404(
        PerformanceWarning.objects.select_related(
            "employee", "employee__user", "employee__department", "issued_by", "issued_by__user", "performance"
        ),
        pk=warning_id,
    )

    context = get_sidebar_context()
    context.update({
        "page_title": f"Warning: {warning.employee.user.name or warning.employee.user.email}",
        "current_page": "responsibilities",
        "warning": warning,
    })
    return render(request, "admin_module/responsibilities_warning_detail.html", context)


@admin_required
def admin_responsibilities_recommendations_view(request):
    """Review HR recommendations that require administrative resolution."""
    recommendations = PerformanceWarning.objects.exclude(
        hr_recommendation=""
    ).filter(
        status__in=["OPEN", "SENT_TO_ADMIN"]
    ).select_related(
        "employee", "employee__user", "employee__department", "issued_by", "issued_by__user"
    ).order_by("-warning_date")

    context = get_sidebar_context()
    context.update({
        "page_title": "HR Recommendations for Review - Smart HRMS Admin",
        "current_page": "responsibilities",
        "recommendations": recommendations,
        "pending_count": recommendations.count(),
    })
    return render(request, "admin_module/responsibilities_recommendations.html", context)


@admin_required
def admin_responsibilities_review_view(request, warning_id):
    """Review and prepare a decision on an HR recommendation."""
    warning = get_object_or_404(
        PerformanceWarning.objects.select_related(
            "employee", "employee__user", "employee__department", "issued_by", "issued_by__user", "performance"
        ),
        pk=warning_id,
    )
    form = AdminDecisionForm()

    context = get_sidebar_context()
    context.update({
        "page_title": f"Review Recommendation: {warning.employee.user.name or warning.employee.user.email}",
        "current_page": "responsibilities",
        "warning": warning,
        "form": form,
    })
    return render(request, "admin_module/responsibilities_review.html", context)


@admin_required
def admin_responsibilities_decision_view(request, warning_id):
    """Process the Admin's final decision on a performance warning."""
    if request.method != "POST":
        return redirect("admin_module:admin_responsibilities_review", warning_id=warning_id)

    warning = get_object_or_404(
        PerformanceWarning.objects.select_related("employee", "employee__user"),
        pk=warning_id,
    )
    form = AdminDecisionForm(request.POST)

    if form.is_valid():
        decision = form.cleaned_data["decision"]
        comments = form.cleaned_data["admin_comments"]

        warning.admin_decision = decision
        warning.admin_comments = comments
        warning.decided_by = request.user
        warning.decision_date = timezone.now()
        warning.status = "RESOLVED"
        warning.save()

        if decision == "TERMINATION":
            warning.employee.employment_status = "TERMINATED"
            warning.employee.save(update_fields=["employment_status", "updated_at"])
            if warning.employee.user:
                warning.employee.user.is_active = False
                warning.employee.user.status = User.StatusChoices.INACTIVE
                warning.employee.user.save(update_fields=["is_active", "status"])
            Notification.objects.create(
                employee=warning.employee,
                title="Employment Status Notice: Terminated",
                message=f"Your employment has been terminated following administrative review.\nDirective: {comments}",
                notification_type="WARNING",
                is_read=False,
            )
            messages.warning(
                request,
                f"Termination decision recorded. Employee '{warning.employee.user.name or warning.employee.user.email}' has been terminated.",
            )
        elif decision == "ANOTHER_WARNING":
            new_reason = form.cleaned_data.get("new_warning_reason") or comments
            PerformanceWarning.objects.create(
                employee=warning.employee,
                performance=warning.performance,
                issued_by=warning.issued_by,
                reason=new_reason,
                status="OPEN",
            )
            Notification.objects.create(
                employee=warning.employee,
                title="Performance Warning Notice",
                message=f"A performance warning has been issued by Administration.\nReason: {warning.reason}\nDirective: {comments}",
                notification_type="WARNING",
                is_read=False,
            )
            messages.info(
                request,
                f"A follow-up warning was issued to '{warning.employee.user.name or warning.employee.user.email}'.",
            )
        else:
            messages.success(
                request,
                f"Decision recorded: Continue employment for '{warning.employee.user.name or warning.employee.user.email}'.",
            )

        return redirect("admin_module:admin_responsibilities_warnings")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Review Recommendation: {warning.employee.user.name or warning.employee.user.email}",
        "current_page": "responsibilities",
        "warning": warning,
        "form": form,
    })
    return render(request, "admin_module/responsibilities_review.html", context)


@admin_required
def admin_responsibilities_issue_warning_view(request, warning_id):
    """Allow Admin to issue a formal warning directive and notification directly to the employee."""
    warning = get_object_or_404(
        PerformanceWarning.objects.select_related(
            "employee", "employee__user", "employee__department", "issued_by", "issued_by__user"
        ),
        pk=warning_id,
    )
    emp_name = warning.employee.user.name or warning.employee.user.email

    if request.method == "POST":
        form = AdminIssueWarningForm(request.POST)
        if form.is_valid():
            warning_message = form.cleaned_data["warning_message"]

            # Update existing PerformanceWarning
            warning.admin_decision = "ANOTHER_WARNING"
            warning.admin_comments = warning_message
            warning.decided_by = request.user
            warning.decision_date = timezone.now()
            warning.status = "RESOLVED"
            warning.save(update_fields=["admin_decision", "admin_comments", "decided_by", "decision_date", "status"])

            # Create an Employee Notification for THAT EXACT employee
            Notification.objects.create(
                employee=warning.employee,
                title="Performance Warning Notice",
                message=f"A formal performance warning has been issued by Administration.\n\nReason: {warning.reason}\n\nAdmin Warning Message:\n{warning_message}",
                notification_type="WARNING",
                is_read=False,
            )

            messages.success(
                request,
                f"Warning issued to {emp_name} successfully.",
            )
            return redirect("admin_module:admin_responsibilities_warnings")
        else:
            messages.error(request, "Please correct the errors in the warning form below.")
    else:
        initial = {}
        if warning.admin_comments:
            initial["warning_message"] = warning.admin_comments
        form = AdminIssueWarningForm(initial=initial)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Issue Warning: {emp_name}",
        "current_page": "responsibilities",
        "warning": warning,
        "employee": warning.employee,
        "form": form,
        "back_url": "admin_module:admin_responsibilities_warnings",
    })
    return render(request, "admin_module/responsibilities_issue_warning.html", context)



# ============================================================================
# ADMIN REPORTS VIEWS
# ============================================================================


@admin_required
def admin_hr_reports_list_view(request):
    """Admin view listing all submitted HR Weekly Reports with search, status filters, and KPIs."""
    reports = HRWeeklyReport.objects.select_related(
        "hr_manager__user", "hr_manager__department", "performance_review"
    ).order_by("-week_start_date", "-created_at")

    hr_filter = request.GET.get("hr_id")
    status_filter = request.GET.get("status")
    search_query = request.GET.get("q", "").strip()

    if hr_filter:
        reports = reports.filter(hr_manager_id=hr_filter)
    if status_filter:
        if status_filter == "SUBMITTED":
            reports = reports.filter(status__in=["SUBMITTED", "UNDER_REVIEW"])
        else:
            reports = reports.filter(status=status_filter)
    if search_query:
        reports = reports.filter(
            Q(hr_manager__first_name__icontains=search_query) |
            Q(hr_manager__last_name__icontains=search_query) |
            Q(hr_manager__employee_code__icontains=search_query) |
            Q(work_summary__icontains=search_query)
        )

    all_reports = HRWeeklyReport.objects.all()
    reviewed_reports = all_reports.filter(status="REVIEWED", performance_review__isnull=False)
    
    avg_performance = 0.0
    if reviewed_reports.exists():
        total_pct = sum([r.performance_review.performance_percentage for r in reviewed_reports])
        avg_performance = round(float(total_pct) / reviewed_reports.count(), 1)

    hr_managers = HRManager.objects.filter(is_active=True).select_related("user", "department")

    context = get_sidebar_context()
    context.update({
        "page_title": "HR Weekly Performance Reports - Smart HRMS Admin",
        "current_page": "reports_hr_weekly",
        "reports": reports,
        "hr_managers": hr_managers,
        "selected_hr": hr_filter or "",
        "selected_status": status_filter or "",
        "search_query": search_query,
        "total_reports": all_reports.count(),
        "pending_review_count": all_reports.filter(status__in=["SUBMITTED", "UNDER_REVIEW"]).count(),
        "reviewed_count": reviewed_reports.count(),
        "avg_performance": avg_performance,
    })
    return render(request, "admin_module/hr_reports_list.html", context)


# Alias for backwards compatibility
admin_reports_hr_weekly_view = admin_hr_reports_list_view


@admin_required
def admin_hr_report_detail_and_review_view(request, report_id):
    """Admin view for inspecting HR Weekly Report and performing Performance Matrix Review."""
    report = get_object_or_404(
        HRWeeklyReport.objects.select_related(
            "hr_manager__user", "hr_manager__department", "performance_review__reviewed_by"
        ),
        pk=report_id,
    )

    # Automatically transition SUBMITTED to UNDER_REVIEW when opened by Admin
    if report.status == "SUBMITTED":
        report.status = "UNDER_REVIEW"
        report.save(update_fields=["status", "updated_at"])

    notif_id = request.GET.get("notif_id")
    if notif_id:
        AdminNotification.objects.filter(pk=notif_id).update(is_read=True)

    review_instance = getattr(report, "performance_review", None)

    if request.method == "POST":
        form = HRPerformanceReviewForm(request.POST, instance=review_instance)
        if form.is_valid():
            review = form.save(commit=False)
            review.report = report
            review.reviewed_by = request.user
            review.save()  # Triggers calculate_scores() automatically

            status_decision = form.cleaned_data.get("status_decision", "REVIEWED")
            report.status = status_decision
            report.reviewed_at = timezone.now()
            report.save()

            # Create Real Database Notification for the HR Manager
            if status_decision == "REVIEWED":
                HRNotification.objects.create(
                    hr_manager=report.hr_manager,
                    title="Performance Review Completed",
                    message=f"Your weekly performance report for {report.week_display} has been reviewed by Admin. Performance Score: {review.performance_percentage}% ({review.get_performance_status_display()}).",
                    notification_type="PERFORMANCE_REVIEWED",
                    link_url=f"/hr/reports/weekly/{report.pk}/",
                )
                messages.success(
                    request,
                    f"Performance review for {report.hr_manager.full_name} saved successfully! Score: {review.performance_percentage}% ({review.get_performance_status_display()})."
                )
            else:
                HRNotification.objects.create(
                    hr_manager=report.hr_manager,
                    title="Weekly Report Needs Improvement",
                    message=f"Your weekly performance report for {report.week_display} requires updates. Please check Admin remarks and recommendations.",
                    notification_type="REPORT_NEEDS_IMPROVEMENT",
                    link_url=f"/hr/reports/weekly/{report.pk}/",
                )
                messages.warning(
                    request,
                    f"Report returned to {report.hr_manager.full_name} with status 'Needs Improvement'."
                )

            return redirect("admin_module:hr_report_detail", report_id=report.pk)
    else:
        form = HRPerformanceReviewForm(instance=review_instance)

    history_reviews = HRWeeklyReport.objects.filter(
        hr_manager=report.hr_manager,
        status="REVIEWED",
        performance_review__isnull=False,
    ).exclude(pk=report.pk).select_related("performance_review").order_by("-week_start_date")[:5]

    context = get_sidebar_context()
    context.update({
        "page_title": f"Review HR Report - {report.hr_manager.full_name}",
        "current_page": "reports_hr_weekly",
        "report": report,
        "review": review_instance,
        "form": form,
        "history_reviews": history_reviews,
    })
    return render(request, "admin_module/hr_report_review.html", context)


@admin_required
def admin_hr_performance_analysis_view(request):
    """Admin dashboard for viewing HR Managers performance analysis matrix, analytics, and history."""
    hr_managers = HRManager.objects.filter(is_active=True).select_related("user", "department")
    selected_hr_id = request.GET.get("hr_id")

    selected_hr = None
    if selected_hr_id:
        selected_hr = HRManager.objects.filter(pk=selected_hr_id).select_related("user", "department").first()

    manager_stats = []
    for m in hr_managers:
        m_reports = HRWeeklyReport.objects.filter(hr_manager=m)
        m_reviewed = m_reports.filter(status="REVIEWED", performance_review__isnull=False)
        
        avg_pct = 0.0
        avg_score = 0.0
        if m_reviewed.exists():
            avg_pct = round(sum([float(r.performance_review.performance_percentage) for r in m_reviewed]) / m_reviewed.count(), 1)
            avg_score = round(sum([float(r.performance_review.average_score) for r in m_reviewed]) / m_reviewed.count(), 2)

        if avg_pct >= 85:
            tier = "EXCELLENT"
        elif avg_pct >= 70:
            tier = "GOOD"
        elif avg_pct >= 50:
            tier = "NEEDS_IMPROVEMENT"
        elif m_reviewed.exists():
            tier = "UNSATISFACTORY"
        else:
            tier = "NO_REVIEWS"

        manager_stats.append({
            "manager": m,
            "total_submitted": m_reports.count(),
            "total_reviewed": m_reviewed.count(),
            "pending_review": m_reports.filter(status__in=["SUBMITTED", "UNDER_REVIEW"]).count(),
            "avg_pct": avg_pct,
            "avg_score": avg_score,
            "tier": tier,
        })

    selected_hr_history = []
    selected_hr_criteria_averages = {}
    if selected_hr:
        selected_hr_history = HRWeeklyReport.objects.filter(
            hr_manager=selected_hr,
            status="REVIEWED",
            performance_review__isnull=False,
        ).select_related("performance_review").order_by("-week_start_date")

        if selected_hr_history.exists():
            count = selected_hr_history.count()
            selected_hr_criteria_averages = {
                "task_completion": round(sum([r.performance_review.task_completion for r in selected_hr_history]) / count, 2),
                "quality_of_work": round(sum([r.performance_review.quality_of_work for r in selected_hr_history]) / count, 2),
                "recruitment_coordination": round(sum([r.performance_review.recruitment_coordination for r in selected_hr_history]) / count, 2),
                "timeliness": round(sum([r.performance_review.timeliness for r in selected_hr_history]) / count, 2),
                "documentation": round(sum([r.performance_review.documentation for r in selected_hr_history]) / count, 2),
                "communication": round(sum([r.performance_review.communication for r in selected_hr_history]) / count, 2),
                "problem_solving": round(sum([r.performance_review.problem_solving for r in selected_hr_history]) / count, 2),
                "weekly_goal_achievement": round(sum([r.performance_review.weekly_goal_achievement for r in selected_hr_history]) / count, 2),
            }

    context = get_sidebar_context()
    context.update({
        "page_title": "HR Performance Analysis - Smart HRMS Admin",
        "current_page": "reports_performance",
        "hr_managers": hr_managers,
        "selected_hr": selected_hr,
        "manager_stats": manager_stats,
        "selected_hr_history": selected_hr_history,
        "selected_hr_criteria_averages": selected_hr_criteria_averages,
    })
    return render(request, "admin_module/hr_performance_analysis.html", context)


# Alias for performance reports view
admin_reports_performance_view = admin_hr_performance_analysis_view


@admin_required
def admin_notification_mark_read_view(request, notification_id):
    """Mark an admin notification as read and redirect to its target link."""
    notif = get_object_or_404(AdminNotification, pk=notification_id)
    notif.is_read = True
    notif.save()
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect("admin_module:admin_dashboard")


@admin_required
def admin_reports_employee_weekly_view(request):
    """Employee weekly activity reports."""
    reports = EmployeeReport.objects.select_related(
        "employee", "employee__user", "employee__department", "reviewed_by", "reviewed_by__user"
    ).order_by("-week_start_date")

    context = get_sidebar_context()
    context.update({
        "page_title": "Employee Weekly Reports - Smart HRMS Admin",
        "current_page": "reports",
        "reports": reports,
        "total_reports": reports.count(),
    })
    return render(request, "admin_module/reports_employee_weekly.html", context)


@admin_required
def admin_reports_recruitment_view(request):
    """Recruitment analytics report."""
    period = request.GET.get("period", "all")
    report_periods = [
        ("all", "All Time"),
        ("30d", "Last 30 Days"),
        ("90d", "Last 90 Days"),
        ("year", "This Year"),
    ]
    period_labels = {
        "all": "All Time",
        "30d": "Last 30 Days",
        "90d": "Last 90 Days",
        "year": "This Year",
    }
    period_label = period_labels.get(period, "All Time")

    vacancies = JobVacancy.objects.select_related("department").all().order_by("-posted_date")
    total_jobs = vacancies.count()
    open_jobs = vacancies.filter(status__iexact="OPEN").count()

    apps = JobApplication.objects.all()
    if period == "30d":
        cutoff = timezone.now() - timedelta(days=30)
        apps = apps.filter(applied_at__gte=cutoff)
    elif period == "90d":
        cutoff = timezone.now() - timedelta(days=90)
        apps = apps.filter(applied_at__gte=cutoff)
    elif period == "year":
        apps = apps.filter(applied_at__year=timezone.now().year)

    applications = apps.count()
    shortlisted = apps.filter(status__in=["SHORTLISTED", "RESUME_REVIEW", "APTITUDE"]).count()
    selected = apps.filter(status="SELECTED").count()
    hired = 0
    rejected = apps.filter(status="REJECTED").count()

    job_rows = []
    chart_labels = []
    chart_values = []
    for v in vacancies:
        v_apps = apps.filter(vacancy=v)
        v_app_count = v_apps.count()
        v_shortlisted = v_apps.filter(status__in=["SHORTLISTED", "RESUME_REVIEW", "APTITUDE"]).count()
        v_selected = v_apps.filter(status="SELECTED").count()
        v_rejected = v_apps.filter(status="REJECTED").count()

        job_rows.append({
            "vacancy": v,
            "applicants": v_app_count,
            "shortlisted": v_shortlisted,
            "selected": v_selected,
            "hired": 0,
            "rejected": v_rejected,
        })
        chart_labels.append(v.title[:20])
        chart_values.append(v_app_count)

    context = get_sidebar_context()
    context.update({
        "page_title": "Recruitment Analytics Report - Smart HRMS Admin",
        "current_page": "reports",
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "applications": applications,
        "shortlisted": shortlisted,
        "selected": selected,
        "hired": hired,
        "rejected": rejected,
        "period": period,
        "period_label": period_label,
        "report_periods": report_periods,
        "job_rows": job_rows,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    })
    return render(request, "admin_module/reports_recruitment.html", context)


@admin_required
def admin_reports_departments_view(request):
    """Department allocation and headcount report."""
    departments = Department.objects.annotate(
        employee_count=Count("employees"),
        hr_count=Count("hr_managers", filter=Q(hr_managers__user__role=User.RoleChoices.HR)),
    ).order_by("name")

    total_departments = departments.count()
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(employment_status="ACTIVE").count()
    avg_headcount = round(total_employees / total_departments, 1) if total_departments > 0 else 0

    rows = []
    chart_labels = []
    chart_values = []
    for dept in departments:
        dept_employees = dept.employees.select_related("user").order_by("-created_at")
        rows.append({
            "department": dept,
            "employee_count": dept.employee_count,
            "employees": dept_employees,
        })
        chart_labels.append(dept.name)
        chart_values.append(dept.employee_count)

    context = get_sidebar_context()
    context.update({
        "page_title": "Departments Workforce Report - Smart HRMS Admin",
        "current_page": "reports",
        "departments": departments,
        "total_departments": total_departments,
        "total_employees": total_employees,
        "active_employees": active_employees,
        "avg_headcount": avg_headcount,
        "rows": rows,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    })
    return render(request, "admin_module/reports_departments.html", context)


@admin_required
def admin_reports_performance_view(request):
    """Organization performance and appraisal report."""
    reviews = EmployeePerformance.objects.select_related(
        "employee", "employee__user", "reviewed_by"
    ).order_by("-review_date")
    warnings = PerformanceWarning.objects.select_related("employee", "employee__user").order_by("-warning_date")

    context = get_sidebar_context()
    context.update({
        "page_title": "Performance Analytics Report - Smart HRMS Admin",
        "current_page": "reports",
        "reviews": reviews,
        "warnings": warnings,
        "total_reviews": reviews.count(),
        "total_warnings": warnings.count(),
    })
    return render(request, "admin_module/reports_performance.html", context)


# ============================================================================
# PLACEHOLDER VIEW
# ============================================================================


@admin_required
def admin_placeholder_view(request, module_name="Module"):
    """Placeholder view for modular navigation links."""
    context = get_sidebar_context()
    context.update({
        "page_title": f"{module_name.title()} - Smart HRMS",
        "current_page": module_name,
        "module_name": module_name.title(),
    })
    return render(request, "admin_module/placeholder.html", context)





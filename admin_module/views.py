from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
from .models import Announcement, Department, EmployeeApproval

from employees.models import (
    Employee,
    EmployeePerformance,
    EmployeeReport,
    Notification,
    PerformanceWarning,
)
from hr.models import AptitudeTest, HRManager, Interview
from candidates.models import Candidate, JobApplication, JobVacancy

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

    return {
        "employees_count": Employee.objects.count(),
        "hr_managers_count": HRManager.objects.filter(user__role=User.RoleChoices.HR).count(),
        "departments_count": Department.objects.count(),
        "open_vacancies_count": JobVacancy.objects.filter(status="OPEN").count(),
        "candidates_count": Candidate.objects.count(),
        "approvals_pending_count": EmployeeApproval.objects.filter(status="PENDING").count(),
        "pending_recommendations_count": pending_recs,
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

    context = {
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
    }
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

    return render(
        request,
        "admin_module/confirm_delete.html",
        {
            "page_title": f"Terminate Employee: {employee.user.name or employee.user.email}",
            "current_page": "employees",
            "object_type": "Employee",
            "object_name": f"{employee.user.name or employee.user.email} ({employee.designation})",
            "object_id": employee_id,
            "delete_url": "admin_module:employee_delete",
            "back_url": "admin_module:employees_list",
            "warning_message": "Terminating this employee will deactivate their login account while preserving all historical work reports, performance reviews, warnings, and documents.",
        },
    )


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
    """Profile detail for an HR Manager displaying aggregated profile, account, documents, and activity."""
    manager = get_object_or_404(
        HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user", "department"),
        pk=manager_id,
    )
    linked_employee = getattr(manager.user, "employee_profile", None)
    documents = linked_employee.documents.all().order_by("-uploaded_at") if linked_employee else []
    profile_photo = linked_employee.profile_photo if (linked_employee and linked_employee.profile_photo) else None

    aptitude_tests = manager.aptitude_tests.all().order_by("-created_at")
    interviews = manager.interviews.select_related("application", "application__candidate").order_by("-interview_date")
    posted_jobs = manager.posted_jobs.all().order_by("-created_at")
    reviewed_reports = manager.reviewed_employee_reports.select_related("employee__user").order_by("-reviewed_at")
    performance_reviews = manager.employee_performance_reviews.select_related("employee__user").order_by("-review_date")
    issued_warnings = manager.issued_warnings.select_related("employee__user").order_by("-warning_date")

    context = get_sidebar_context()
    context.update({
        "page_title": f"{manager.user.name or manager.user.email} - HR Manager Profile",
        "current_page": "hr_managers",
        "manager": manager,
        "linked_employee": linked_employee,
        "profile_photo": profile_photo,
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

    return render(
        request,
        "admin_module/confirm_delete.html",
        {
            "page_title": f"Delete HR Manager: {manager.user.name or manager.user.email}",
            "current_page": "hr_managers",
            "object_type": "HR Manager",
            "object_name": manager.user.name or manager.user.email,
            "object_id": manager_id,
            "delete_url": "admin_module:hr_manager_delete",
            "back_url": "admin_module:hr_managers_list",
            "warning_message": "Deleting this HR Manager removes their account and leaves historical records intact.",
        },
    )


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

    return render(
        request,
        "admin_module/confirm_delete.html",
        {
            "page_title": f"Delete Announcement: {announcement.title}",
            "current_page": "announcements",
            "object_type": "Announcement",
            "object_name": announcement.title,
            "object_id": announcement_id,
            "delete_url": "admin_module:announcement_delete",
            "back_url": "admin_module:announcements_list",
        },
    )


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

    return render(
        request,
        "admin_module/confirm_delete.html",
        {
            "page_title": f"Delete Candidate: {full_name}",
            "current_page": "candidates",
            "object_type": "Candidate",
            "object_name": full_name,
            "object_id": candidate_id,
            "delete_url": "admin_module:candidate_delete",
            "back_url": "admin_module:candidates_list",
        },
    )


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


@admin_required
def admin_recruitment_approvals_view(request):
    """View employee approvals pending admin review."""
    approvals = EmployeeApproval.objects.filter(status="PENDING").select_related(
        "employee", "employee__user", "employee__department", "employee__candidate"
    ).order_by("-employee__created_at")

    search_query = request.GET.get("q", "").strip()
    if search_query:
        approvals = approvals.filter(
            Q(employee__user__name__icontains=search_query)
            | Q(employee__user__email__icontains=search_query)
            | Q(employee__designation__icontains=search_query)
        )

    pending_list = [a.employee for a in approvals]
    active_employees = Employee.objects.filter(employment_status="ACTIVE").count()
    total_employees = Employee.objects.count()

    context = get_sidebar_context()
    context.update({
        "page_title": "New Employee Approvals - Smart HRMS Admin",
        "current_page": "recruitment",
        "pending_list": pending_list,
        "pending_count": len(pending_list),
        "active_employees": active_employees,
        "total_employees": total_employees,
        "search": search_query,
    })
    return render(request, "admin_module/recruitment_approvals.html", context)


@admin_required
def admin_recruitment_approval_review_view(request, employee_id):
    """Review screen for approving a newly selected candidate into the workforce."""
    employee = get_object_or_404(
        Employee.objects.select_related("user", "department", "candidate"),
        pk=employee_id,
    )
    approval, _ = EmployeeApproval.objects.get_or_create(
        employee=employee,
        defaults={"status": "PENDING"},
    )

    if approval.status != "PENDING":
        messages.info(request, f"The approval for '{employee.user.name or employee.user.email}' has already been processed ({approval.status}).")
        return redirect("admin_module:recruitment_approvals")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Review Approval: {employee.user.name or employee.user.email}",
        "current_page": "recruitment",
        "employee": employee,
        "approval": approval,
    })
    return render(request, "admin_module/recruitment_approval_review.html", context)


@admin_required
def admin_recruitment_approval_approve_view(request, employee_id):
    """Execute approval of new employee record."""
    if request.method != "POST":
        return redirect("admin_module:recruitment_approval_review", employee_id=employee_id)

    employee = get_object_or_404(Employee.objects.select_related("user"), pk=employee_id)
    approval, _ = EmployeeApproval.objects.get_or_create(
        employee=employee,
        defaults={"status": "PENDING"},
    )

    if approval.status != "PENDING":
        messages.warning(request, "This approval has already been processed.")
        return redirect("admin_module:recruitment_approvals")

    approval.status = "APPROVED"
    approval.approved_by = request.user
    approval.approved_at = timezone.now()
    approval.comments = request.POST.get("comments", "").strip()
    approval.save()

    employee.employment_status = "ACTIVE"
    employee.save(update_fields=["employment_status", "updated_at"])

    if employee.user:
        employee.user.is_active = True
        employee.user.status = User.StatusChoices.ACTIVE
        employee.user.save(update_fields=["is_active", "status"])

    messages.success(
        request,
        f"Employee '{employee.user.name or employee.user.email}' was approved and added to the active workforce.",
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
def admin_reports_hr_weekly_view(request):
    """HR operations weekly summary report."""
    hr_managers = HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user", "department").all()

    reports = []
    for m in hr_managers:
        reports.append({
            "manager": m,
            "tests_created": m.aptitude_tests.count(),
            "interviews_scheduled": m.interviews.count(),
            "warnings_issued": m.issued_warnings.count(),
        })

    context = get_sidebar_context()
    context.update({
        "page_title": "HR Weekly Report - Smart HRMS Admin",
        "current_page": "reports",
        "hr_reports": reports,
        "total_managers": hr_managers.count(),
    })
    return render(request, "admin_module/reports_hr_weekly.html", context)


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





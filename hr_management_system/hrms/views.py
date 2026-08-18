from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .decorators import admin_required
from .forms import AdminLoginForm
from .forms import AdminRegistrationForm
from .forms import EmployeeCreateForm
from .forms import EmployeeProfileForm
from .forms import HRManagerCreateForm
from .forms import HRManagerProfileForm
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

User = get_user_model()


def admin_register_view(request):
    """Register the single System Administrator."""

    # Only one Admin account is allowed.
    if User.objects.filter(
        role=User.RoleChoices.ADMIN
    ).exists():
        messages.info(
            request,
            "The System Administrator account has already been created. "
            "Please log in.",
        )
        return redirect("hrms:admin_login")

    if request.user.is_authenticated:
        return redirect("hrms:admin_dashboard")

    if request.method == "POST":
        form = AdminRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            messages.success(
                request,
                "Administrator account created successfully. "
                "You can now log in.",
            )

            return redirect("hrms:admin_login")

        messages.error(
            request,
            "Please correct the errors below to complete registration.",
        )

    else:
        form = AdminRegistrationForm()

    return render(
        request,
        "admin/register.html",
        {
            "form": form,
            "page_title": "Admin Registration - Smart HRMS",
        },
    )


def admin_login_view(request):
    """Admin Login View with strict Admin role check."""
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.RoleChoices.ADMIN:
        return redirect("hrms:admin_dashboard")

    next_url = request.GET.get("next") or request.POST.get("next") or "hrms:admin_dashboard"

    if request.method == "POST":
        form = AdminLoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if form.cleaned_data.get("remember_me"):
                # Session expires after 30 days
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                # Session expires when user closes browser
                request.session.set_expiry(0)

            messages.success(request, f"Welcome back, {user.name or user.email}!")
            return redirect(next_url)
        messages.error(request, "Authentication failed. Please verify your credentials.")
    else:
        form = AdminLoginForm(request=request)

    return render(
        request,
        "admin/login.html",
        {
            "form": form,
            "next": next_url,
            "page_title": "Admin Login - Smart HRMS",
        },
    )


def admin_logout_view(request):
    """Admin Logout View."""
    logout(request)
    messages.info(request, "You have been safely logged out of the Admin Portal.")
    return redirect("hrms:admin_login")


@admin_required
def admin_dashboard_view(request):
    """
    Admin Dashboard View displaying real live statistics from all 9 tables:
    users, departments, hr_managers, job_vacancies, candidates,
    employees, employee_performance, performance_warnings, announcements.
    """
    # 1. Total Users
    total_users_count = User.objects.count()

    # 2. HR Managers
    hr_managers_count = HRManager.objects.count()
    if hr_managers_count == 0:
        hr_managers_count = User.objects.filter(role=User.RoleChoices.HR).count()

    # 3. Departments
    departments_count = Department.objects.count()

    # 4. Open Vacancies
    open_vacancies_count = JobVacancy.objects.filter(status=JobVacancy.StatusChoices.OPEN).count()

    # 5. Candidates
    candidates_count = Candidate.objects.count()

    # 6. Employees
    employees_count = Employee.objects.count()

    # 7. Pending Employee Approvals
    pending_approvals_count = Employee.objects.filter(
        status=Employee.StatusChoices.PENDING_APPROVAL
    ).count()

    # 8. Pending Performance Warnings
    pending_warnings_count = PerformanceWarning.objects.filter(
        status=PerformanceWarning.StatusChoices.PENDING
    ).count()

    # Total Performance Records
    total_reviews_count = EmployeePerformance.objects.count()
    total_announcements_count = Announcement.objects.count()

    # Query Recent Records for Dashboard Sections
    recent_users = User.objects.order_by("-date_joined")[:6]
    recent_vacancies = JobVacancy.objects.select_related("department", "created_by").order_by("-created_at")[:5]
    recent_candidates = Candidate.objects.select_related("job_vacancy", "job_vacancy__department").order_by("-applied_at")[:5]
    pending_approvals_list = Employee.objects.select_related("user", "department").filter(
        status=Employee.StatusChoices.PENDING_APPROVAL
    ).order_by("-created_at")[:5]
    recent_announcements = Announcement.objects.select_related("created_by").order_by("-created_at")[:4]
    recent_warnings = PerformanceWarning.objects.select_related("employee", "employee__user").order_by("-created_at")[:4]

    # Role breakdown for user distribution chart/pills
    role_counts = {
        "Admin": User.objects.filter(role=User.RoleChoices.ADMIN).count(),
        "HR": User.objects.filter(role=User.RoleChoices.HR).count(),
        "Employee": User.objects.filter(role=User.RoleChoices.EMPLOYEE).count(),
        "Candidate": User.objects.filter(role=User.RoleChoices.CANDIDATE).count(),
    }

    context = {
        "page_title": "Admin Dashboard - Smart HRMS",
        "current_page": "dashboard",
        # 8 Core Statistics Required
        "total_users_count": total_users_count,
        "hr_managers_count": hr_managers_count,
        "departments_count": departments_count,
        "open_vacancies_count": open_vacancies_count,
        "candidates_count": candidates_count,
        "employees_count": employees_count,
        "pending_approvals_count": pending_approvals_count,
        "pending_warnings_count": pending_warnings_count,
        # Additional summary statistics
        "total_reviews_count": total_reviews_count,
        "total_announcements_count": total_announcements_count,
        "role_counts": role_counts,
        # Real Recent Data Lists
        "recent_users": recent_users,
        "recent_vacancies": recent_vacancies,
        "recent_candidates": recent_candidates,
        "pending_approvals_list": pending_approvals_list,
        "recent_announcements": recent_announcements,
        "recent_warnings": recent_warnings,
    }

    return render(request, "admin/dashboard.html", context)


@admin_required
def admin_employees_management_view(request):
    """List and manage employees from the admin dashboard."""
    employees = Employee.objects.select_related("user", "department").order_by("-created_at")
    context = {
        "page_title": "Manage Employees - Smart HRMS Admin",
        "current_page": "employees",
        "employees": employees,
        "show_add_button": True,
    }
    return render(request, "admin/manage_employees.html", context)


@admin_required
def admin_employee_create_view(request):
    """Create a new Employee user and Employee profile record."""
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            user = form.save(admin_user=request.user)
            messages.success(request, f"Employee '{user.name or user.email}' was created successfully.")
            return redirect("hrms:employees_list")
        messages.error(request, "Please correct the errors below before creating the employee record.")
    else:
        form = EmployeeCreateForm()

    return render(
        request,
        "admin/employee_form.html",
        {
            "page_title": "Add Employee - Smart HRMS Admin",
            "current_page": "employees",
            "form": form,
            "title": "Add Employee",
            "submit_label": "Create Employee",
            "back_url": "hrms:employees_list",
        },
    )


@admin_required
def admin_employee_profile_view(request, employee_id):
    """View and edit employee profile details after the initial creation."""
    employee = Employee.objects.select_related("user", "department").get(pk=employee_id)

    if request.method == "POST":
        form = EmployeeProfileForm(request.POST, employee=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Employee profile for '{employee.user.name or employee.user.email}' was updated.")
            return redirect("hrms:employees_list")
        messages.error(request, "Please correct the profile information below.")
    else:
        form = EmployeeProfileForm(employee=employee)

    return render(
        request,
        "admin/employee_profile.html",
        {
            "page_title": f"Profile: {employee.user.name or employee.user.email}",
            "current_page": "employees",
            "employee": employee,
            "form": form,
            "title": "Employee Profile",
            "submit_label": "Save Changes",
            "back_url": "hrms:employees_list",
        },
    )


@admin_required
def admin_hr_managers_management_view(request):
    """List and manage HR manager records in the admin dashboard."""
    hr_managers = HRManager.objects.select_related("user", "department").order_by("-created_at")
    context = {
        "page_title": "Manage HR Managers - Smart HRMS Admin",
        "current_page": "hr_managers",
        "hr_managers": hr_managers,
        "show_add_button": True,
    }
    return render(request, "admin/manage_hr_managers.html", context)


@admin_required
def admin_hr_manager_create_view(request):
    """Create a new HR Manager user and HRManager profile record."""
    if request.method == "POST":
        form = HRManagerCreateForm(request.POST)
        if form.is_valid():
            user = form.save(admin_user=request.user)
            messages.success(request, f"HR Manager '{user.name or user.email}' was created successfully.")
            return redirect("hrms:hr_managers_list")
        messages.error(request, "Please correct the errors below before creating the HR manager record.")
    else:
        form = HRManagerCreateForm()

    return render(
        request,
        "admin/hr_manager_form.html",
        {
            "page_title": "Add HR Manager - Smart HRMS Admin",
            "current_page": "hr_managers",
            "form": form,
            "title": "Add HR Manager",
            "submit_label": "Create HR Manager",
            "back_url": "hrms:hr_managers_list",
        },
    )


@admin_required
def admin_hr_manager_profile_view(request, manager_id):
    """View and edit HR manager details after creation."""
    manager = HRManager.objects.select_related("user", "department").get(pk=manager_id)

    if request.method == "POST":
        form = HRManagerProfileForm(request.POST, manager=manager)
        if form.is_valid():
            form.save()
            messages.success(request, f"HR Manager profile for '{manager.user.name or manager.user.email}' was updated.")
            return redirect("hrms:hr_managers_list")
        messages.error(request, "Please correct the profile information below.")
    else:
        form = HRManagerProfileForm(manager=manager)

    return render(
        request,
        "admin/hr_manager_profile.html",
        {
            "page_title": f"HR Manager: {manager.user.name or manager.user.email}",
            "current_page": "hr_managers",
            "manager": manager,
            "form": form,
            "title": "HR Manager Profile",
            "submit_label": "Save Changes",
            "back_url": "hrms:hr_managers_list",
        },
    )


# Modular placeholder views for future admin features
@admin_required
def admin_placeholder_view(request, module_name):
    """Modular placeholder view for remaining Admin navigation links."""
    readable_name = module_name.replace("_", " ").title()
    return render(
        request,
        "admin/placeholder.html",
        {
            "page_title": f"{readable_name} - Smart HRMS Admin",
            "current_page": module_name,
            "module_name": readable_name,
        },
    )

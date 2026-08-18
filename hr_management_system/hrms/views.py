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
    """Admin Registration View."""
    if request.user.is_authenticated and getattr(request.user, "role", None) == User.RoleChoices.ADMIN:
        return redirect("hrms:admin_dashboard")

    if request.method == "POST":
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Administrator account '{user.email}' created successfully! You can now log in.",
            )
            return redirect("hrms:admin_login")
        messages.error(request, "Please correct the errors below to complete registration.")
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

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth import logout
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .decorators import admin_required
from .forms import AdminDecisionForm
from .forms import AdminLoginForm
from .forms import AdminRegistrationForm
from .forms import AnnouncementForm
from .forms import CandidateForm
from .forms import DepartmentForm
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


def get_sidebar_context():
    """Helper function to get common sidebar context variables for all admin views."""
    pending_recs = 0
    try:
        from employees.models import PerformanceWarning as StandalonePerformanceWarning

        pending_recs = StandalonePerformanceWarning.objects.exclude(
            hr_recommendation=""
        ).filter(status__in=["OPEN", "SENT_TO_ADMIN"]).count()
    except Exception:
        pending_recs = 0

    return {
        "employees_count": Employee.objects.count(),
        "hr_managers_count": HRManager.objects.count(),
        "departments_count": Department.objects.count(),
        "open_vacancies_count": JobVacancy.objects.filter(status=JobVacancy.StatusChoices.OPEN).count(),
        "candidates_count": Candidate.objects.count(),
        "approvals_pending_count": Employee.objects.filter(
            status=Employee.StatusChoices.PENDING_APPROVAL
        ).count(),
        "pending_recommendations_count": pending_recs,
        "announcements_count": Announcement.objects.count(),
    }



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
    HRCortex Executive Admin Dashboard View displaying rich operational metrics:
    KPIs (Total Employees, New Hires, Open Positions, Attendance Rate),
    Headcount by Department, Leave Requests Pending Approval,
    Gender Demographics, Quick Actions, Events & Milestones, and Live Activity Feed.
    """
    from django.db.models import Count
    
    # Core DB statistics
    total_users_count = User.objects.count()

    hr_managers_count = HRManager.objects.count()
    if hr_managers_count == 0:
        hr_managers_count = User.objects.filter(role=User.RoleChoices.HR).count()

    departments_count = Department.objects.count()
    open_vacancies_count = JobVacancy.objects.filter(status=JobVacancy.StatusChoices.OPEN).count()

    candidates_count = Candidate.objects.count()
    employees_count = Employee.objects.count()

    pending_approvals_count = Employee.objects.filter(
        status=Employee.StatusChoices.PENDING_APPROVAL
    ).count()

    pending_warnings_count = PerformanceWarning.objects.filter(
        status=PerformanceWarning.StatusChoices.PENDING
    ).count()

    total_reviews_count = EmployeePerformance.objects.count()

    # Query Recent Records for Dashboard Sections
    recent_users = User.objects.order_by("-date_joined")[:6]
    recent_employees = Employee.objects.select_related("user", "department").order_by("-created_at")[:5]
    recent_vacancies = JobVacancy.objects.select_related("department", "created_by").order_by("-created_at")[:5]
    recent_candidates = Candidate.objects.select_related("job_vacancy", "job_vacancy__department").order_by("-applied_at")[:5]
    pending_approvals_list = Employee.objects.select_related("user", "department").filter(
        status=Employee.StatusChoices.PENDING_APPROVAL
    ).order_by("-created_at")[:5]
    recent_warnings = PerformanceWarning.objects.select_related("employee", "employee__user").order_by("-created_at")[:4]
    recent_announcements = Announcement.objects.select_related("created_by").order_by("-created_at")[:5]

    # Query Recent HR Managers for dashboard display matching UI reference
    recent_hr_managers = list(HRManager.objects.select_related("user", "department").order_by("-created_at")[:5])
    if not recent_hr_managers:
        hr_users = User.objects.filter(role=User.RoleChoices.HR).order_by("-date_joined")[:5]
        recent_hr_managers = [
            {
                "user": u,
                "department": None,
                "created_at": u.date_joined,
            }
            for u in hr_users
        ]

    # Department headcount chart data - REAL DATA from database
    departments_data = list(Department.objects.annotate(
        emp_count=Count("employees")
    ).order_by("-emp_count")[:6])
    
    dept_labels = [dept.name for dept in departments_data]
    dept_values = [dept.emp_count for dept in departments_data]
    
    total_chart_emps = sum(dept_values)
    dept_percentages = []
    if total_chart_emps > 0:
        dept_percentages = [round((val / total_chart_emps) * 100) for val in dept_values]
    
    # Department distribution summary list for template rendering
    dept_summary = []
    dept_colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#94a3b8"]
    for i, dept in enumerate(departments_data):
        pct = dept_percentages[i] if i < len(dept_percentages) else 0
        color = dept_colors[i % len(dept_colors)]
        dept_summary.append({
            "name": dept.name,
            "count": dept.emp_count,
            "percentage": pct,
            "color": color,
        })

    context = get_sidebar_context()
    context.update({
        "page_title": "Admin Dashboard - Smart HRMS",
        "current_page": "dashboard",
        # Charts
        "dept_labels": dept_labels,
        "dept_values": dept_values,
        "dept_percentages": dept_percentages,
        "dept_summary": dept_summary,
        "total_chart_emps": total_chart_emps,
        # Underlying Data
        "total_users_count": total_users_count,
        "pending_approvals_count": pending_approvals_count,
        "pending_warnings_count": pending_warnings_count,
        "recent_users": recent_users,
        "recent_employees": recent_employees,
        "recent_hr_managers": recent_hr_managers,
        "recent_vacancies": recent_vacancies,
        "recent_candidates": recent_candidates,
        "pending_approvals_list": pending_approvals_list,
        "recent_warnings": recent_warnings,
        "recent_announcements": recent_announcements,
    })

    return render(request, "admin/dashboard.html", context)


@admin_required
def admin_employees_management_view(request):
    """List and manage employees from the admin dashboard."""
    employees = Employee.objects.select_related("user", "department").order_by("-created_at")
    
    context = get_sidebar_context()
    context.update({
        "page_title": "Manage Employees - Smart HRMS Admin",
        "current_page": "employees",
        "employees": employees,
        "show_add_button": True,
    })
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

    context = get_sidebar_context()
    context.update({
        "page_title": "Add Employee - Smart HRMS Admin",
        "current_page": "employees",
        "form": form,
        "title": "Add Employee",
        "submit_label": "Create Employee",
        "back_url": "hrms:employees_list",
    })
    return render(request, "admin/employee_form.html", context)


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

    context = get_sidebar_context()
    context.update({
        "page_title": f"Profile: {employee.user.name or employee.user.email}",
        "current_page": "employees",
        "employee": employee,
        "form": form,
        "title": "Employee Profile",
        "submit_label": "Save Changes",
        "back_url": "hrms:employees_list",
    })
    return render(request, "admin/employee_profile.html", context)


@admin_required
def admin_hr_managers_management_view(request):
    """List and manage HR manager records in the admin dashboard."""
    hr_managers = HRManager.objects.select_related("user", "department").order_by("-created_at")
    
    context = get_sidebar_context()
    context.update({
        "page_title": "Manage HR Managers - Smart HRMS Admin",
        "current_page": "hr_managers",
        "hr_managers": hr_managers,
        "show_add_button": True,
    })
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

    context = get_sidebar_context()
    context.update({
        "page_title": "Add HR Manager - Smart HRMS Admin",
        "current_page": "hr_managers",
        "form": form,
        "title": "Add HR Manager",
        "submit_label": "Create HR Manager",
        "back_url": "hrms:hr_managers_list",
    })
    return render(request, "admin/hr_manager_form.html", context)


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

    context = get_sidebar_context()
    context.update({
        "page_title": f"HR Manager: {manager.user.name or manager.user.email}",
        "current_page": "hr_managers",
        "manager": manager,
        "form": form,
        "title": "HR Manager Profile",
        "submit_label": "Save Changes",
        "back_url": "hrms:hr_managers_list",
    })
    return render(request, "admin/hr_manager_profile.html", context)


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


# ============================================================================
# EMPLOYEE EDIT & DELETE VIEWS
# ============================================================================


@admin_required
def admin_employee_edit_view(request, employee_id):
    """Edit employee details using EmployeeProfileForm."""
    try:
        employee = Employee.objects.select_related("user", "department").get(pk=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect("hrms:employees_list")

    if request.method == "POST":
        form = EmployeeProfileForm(request.POST, employee=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Employee '{employee.user.name or employee.user.email}' was updated successfully.")
            return redirect("hrms:employees_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeProfileForm(employee=employee)

    return render(
        request,
        "admin/employee_form.html",
        {
            "page_title": f"Edit Employee: {employee.user.name or employee.user.email}",
            "current_page": "employees",
            "form": form,
            "employee": employee,
            "title": "Edit Employee",
            "submit_label": "Update Employee",
            "back_url": "hrms:employees_list",
        },
    )


@admin_required
def admin_employee_delete_view(request, employee_id):
    """Delete an employee after confirmation."""
    try:
        employee = Employee.objects.select_related("user").get(pk=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect("hrms:employees_list")

    if request.method == "POST":
        user = employee.user
        employee_name = user.name or user.email
        employee.delete()
        user.delete()
        messages.success(request, f"Employee '{employee_name}' and associated user account have been deleted.")
        return redirect("hrms:employees_list")

    # Confirmation page
    return render(
        request,
        "admin/confirm_delete.html",
        {
            "page_title": f"Delete Employee: {employee.user.name or employee.user.email}",
            "current_page": "employees",
            "object_type": "Employee",
            "object_name": employee.user.name or employee.user.email,
            "object_id": employee_id,
            "delete_url": "hrms:employee_delete",
            "back_url": "hrms:employees_list",
        },
    )


# ============================================================================
# HR MANAGER EDIT, DELETE & STATUS TOGGLE VIEWS
# ============================================================================


@admin_required
def admin_hr_manager_edit_view(request, manager_id):
    """Edit HR manager details using HRManagerProfileForm."""
    try:
        manager = HRManager.objects.select_related("user", "department").get(pk=manager_id)
    except HRManager.DoesNotExist:
        messages.error(request, "HR Manager not found.")
        return redirect("hrms:hr_managers_list")

    if request.method == "POST":
        form = HRManagerProfileForm(request.POST, manager=manager)
        if form.is_valid():
            form.save()
            messages.success(request, f"HR Manager '{manager.user.name or manager.user.email}' was updated successfully.")
            return redirect("hrms:hr_managers_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = HRManagerProfileForm(manager=manager)

    return render(
        request,
        "admin/hr_manager_form.html",
        {
            "page_title": f"Edit HR Manager: {manager.user.name or manager.user.email}",
            "current_page": "hr_managers",
            "form": form,
            "manager": manager,
            "title": "Edit HR Manager",
            "submit_label": "Update HR Manager",
            "back_url": "hrms:hr_managers_list",
        },
    )


@admin_required
def admin_hr_manager_delete_view(request, manager_id):
    """Delete an HR manager after confirmation."""
    try:
        manager = HRManager.objects.select_related("user").get(pk=manager_id)
    except HRManager.DoesNotExist:
        messages.error(request, "HR Manager not found.")
        return redirect("hrms:hr_managers_list")

    if request.method == "POST":
        user = manager.user
        manager_name = user.name or user.email
        manager.delete()
        user.delete()
        messages.success(request, f"HR Manager '{manager_name}' and associated user account have been deleted.")
        return redirect("hrms:hr_managers_list")

    # Confirmation page
    return render(
        request,
        "admin/confirm_delete.html",
        {
            "page_title": f"Delete HR Manager: {manager.user.name or manager.user.email}",
            "current_page": "hr_managers",
            "object_type": "HR Manager",
            "object_name": manager.user.name or manager.user.email,
            "object_id": manager_id,
            "delete_url": "hrms:hr_manager_delete",
            "back_url": "hrms:hr_managers_list",
        },
    )


@admin_required
def admin_hr_manager_toggle_status_view(request, manager_id):
    """Toggle HR Manager active/inactive status."""
    if request.method != "POST":
        messages.warning(request, "Please confirm the status change from the form.")
        return redirect("hrms:hr_managers_list")

    try:
        manager = HRManager.objects.select_related("user").get(pk=manager_id)
    except HRManager.DoesNotExist:
        messages.error(request, "HR Manager not found.")
        return redirect("hrms:hr_managers_list")

    user = manager.user
    old_status = user.status
    
    # Toggle status
    new_status = (
        User.StatusChoices.INACTIVE
        if user.status == User.StatusChoices.ACTIVE
        else User.StatusChoices.ACTIVE
    )
    user.status = new_status
    user.is_active = (new_status == User.StatusChoices.ACTIVE)
    user.save(update_fields=["status", "is_active"])

    action = "activated" if new_status == User.StatusChoices.ACTIVE else "deactivated"
    messages.success(request, f"HR Manager '{user.name or user.email}' has been {action}.")
    
    return redirect("hrms:hr_managers_list")


# ============================================================================
# DEPARTMENT MANAGEMENT VIEWS
# ============================================================================


@admin_required
def admin_departments_management_view(request):
    """List and manage departments."""
    departments = Department.objects.all().order_by("name")
    
    # Calculate employee count for each department
    from django.db.models import Count
    departments = departments.annotate(employee_count=Count("employees"))
    
    context = get_sidebar_context()
    context.update({
        "page_title": "Manage Departments - Smart HRMS Admin",
        "current_page": "departments",
        "departments": departments,
        "show_add_button": True,
    })
    return render(request, "admin/manage_departments.html", context)


@admin_required
def admin_department_create_view(request):
    """Create a new department."""
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f"Department '{department.name}' was created successfully.")
            return redirect("hrms:departments_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = DepartmentForm()

    context = get_sidebar_context()
    context.update({
        "page_title": "Add Department - Smart HRMS Admin",
        "current_page": "departments",
        "form": form,
        "title": "Add Department",
        "submit_label": "Create Department",
        "back_url": "hrms:departments_list",
    })
    return render(request, "admin/department_form.html", context)


@admin_required
def admin_department_detail_view(request, department_id):
    """View department details."""
    try:
        department = Department.objects.get(pk=department_id)
    except Department.DoesNotExist:
        messages.error(request, "Department not found.")
        return redirect("hrms:departments_list")

    employees = department.employees.select_related("user").all()
    hr_managers = department.hr_managers.select_related("user").all()

    context = {
        "page_title": f"Department: {department.name}",
        "current_page": "departments",
        "department": department,
        "employees": employees,
        "hr_managers": hr_managers,
        "employee_count": employees.count(),
    }
    return render(request, "admin/department_detail.html", context)


@admin_required
def admin_department_edit_view(request, department_id):
    """Edit a department."""
    try:
        department = Department.objects.get(pk=department_id)
    except Department.DoesNotExist:
        messages.error(request, "Department not found.")
        return redirect("hrms:departments_list")

    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{department.name}' was updated successfully.")
            return redirect("hrms:departments_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = DepartmentForm(instance=department)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Edit Department: {department.name}",
        "current_page": "departments",
        "form": form,
        "department": department,
        "title": "Edit Department",
        "submit_label": "Update Department",
        "back_url": "hrms:departments_list",
    })
    return render(request, "admin/department_form.html", context)


@admin_required
def admin_department_delete_view(request, department_id):
    """Delete a department after confirmation."""
    try:
        department = Department.objects.get(pk=department_id)
    except Department.DoesNotExist:
        messages.error(request, "Department not found.")
        return redirect("hrms:departments_list")

    # Check for related employees or HR managers
    employee_count = department.employees.count()
    hr_manager_count = department.hr_managers.count()

    if request.method == "POST":
        department_name = department.name
        
        # Handle related records
        if employee_count > 0 or hr_manager_count > 0:
            # Optionally move them to a default department or warn the user
            messages.warning(
                request,
                f"Note: Department '{department_name}' had {employee_count} employees and {hr_manager_count} HR managers. "
                f"These records will have their department assignment removed."
            )
        
        department.delete()
        messages.success(request, f"Department '{department_name}' has been deleted.")
        return redirect("hrms:departments_list")

    context = {
        "page_title": f"Delete Department: {department.name}",
        "current_page": "departments",
        "object_type": "Department",
        "object_name": department.name,
        "object_id": department_id,
        "delete_url": "hrms:department_delete",
        "back_url": "hrms:departments_list",
        "warning_message": (
            f"This department has {employee_count} employee(s) and {hr_manager_count} HR manager(s). "
            "Deleting it will remove their department assignments."
            if employee_count > 0 or hr_manager_count > 0
            else None
        ),
    }
    return render(request, "admin/confirm_delete.html", context)


# ============================================================================
# CANDIDATE MANAGEMENT VIEWS
# ============================================================================


@admin_required
def admin_candidates_management_view(request):
    """List and manage candidate applications."""
    candidates = Candidate.objects.select_related("job_vacancy", "job_vacancy__department").order_by("-applied_at")
    context = get_sidebar_context()
    context.update({
        "page_title": "Candidates Directory - HRCortex Admin",
        "current_page": "candidates",
        "candidates": candidates,
    })
    return render(request, "admin/manage_candidates.html", context)


@admin_required
def admin_candidate_create_view(request):
    """Register a new candidate application."""
    if request.method == "POST":
        form = CandidateForm(request.POST)
        if form.is_valid():
            candidate = form.save()
            messages.success(request, f"Candidate application for '{candidate.full_name}' was registered successfully.")
            return redirect("hrms:candidates_list")
        messages.error(request, "Please correct the errors in the candidate application below.")
    else:
        form = CandidateForm()

    context = get_sidebar_context()
    context.update({
        "page_title": "Register Candidate - HRCortex Admin",
        "current_page": "candidates",
        "form": form,
        "title": "Register Candidate Application",
        "submit_label": "Create Candidate Application",
        "back_url": "hrms:candidates_list",
    })
    return render(request, "admin/candidate_form.html", context)


@admin_required
def admin_candidate_edit_view(request, candidate_id):
    """Edit candidate details and pipeline stage."""
    try:
        candidate = Candidate.objects.select_related("job_vacancy").get(pk=candidate_id)
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate not found.")
        return redirect("hrms:candidates_list")

    if request.method == "POST":
        form = CandidateForm(request.POST, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, f"Candidate application for '{candidate.full_name}' was updated.")
            return redirect("hrms:candidates_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = CandidateForm(instance=candidate)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Edit Candidate: {candidate.full_name}",
        "current_page": "candidates",
        "form": form,
        "candidate": candidate,
        "title": "Edit Candidate Application",
        "submit_label": "Update Application",
        "back_url": "hrms:candidates_list",
    })
    return render(request, "admin/candidate_form.html", context)


@admin_required
def admin_candidate_delete_view(request, candidate_id):
    """Delete candidate application."""
    try:
        candidate = Candidate.objects.get(pk=candidate_id)
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate not found.")
        return redirect("hrms:candidates_list")

    if request.method == "POST":
        name = candidate.full_name
        candidate.delete()
        messages.success(request, f"Candidate application for '{name}' was deleted.")
        return redirect("hrms:candidates_list")

    return render(
        request,
        "admin/confirm_delete.html",
        {
            "page_title": f"Delete Candidate: {candidate.full_name}",
            "current_page": "candidates",
            "object_type": "Candidate",
            "object_name": candidate.full_name,
            "object_id": candidate_id,
            "delete_url": "hrms:candidate_delete",
            "back_url": "hrms:candidates_list",
        },
    )


# ============================================================================
# RECRUITMENT MONITORING VIEWS (Admin read-only + new-employee approvals)
#
# These views monitor the recruitment data that the HR/Candidate modules
# produce (job postings, candidate applications and pipeline stages, and
# employee records awaiting approval). Admin never creates, edits or deletes
# recruitment records here - the pages are read-only, with the single
# exception of approving new employee records.
# ============================================================================

# Pipeline stage values stored on Candidate.status records.
RECRUITMENT_STAGES = list(Candidate.StatusChoices.values)


def _recruitment_stage_totals():
    """Return {vacancy_id: {status: count}} for every job posting."""
    stage_rows = (
        Candidate.objects.values("job_vacancy_id", "status")
        .annotate(count=Count("id"))
        .order_by("job_vacancy_id")
    )
    totals = {}
    for row in stage_rows:
        totals.setdefault(row["job_vacancy_id"], {})[row["status"]] = row["count"]
    return totals


def _vacancy_owner_details(vacancy):
    """Return (name, subtitle) describing who owns a job posting."""
    creator = getattr(vacancy, "created_by", None)
    if creator is None:
        return "Unassigned", "Awaiting HR owner"

    owner_name = creator.name or creator.email
    hr_profile = HRManager.objects.filter(user=creator).first()
    if hr_profile is not None:
        return owner_name, "HR Manager"

    role_label = dict(User.RoleChoices.choices).get(creator.role, "Staff")
    if creator.role == User.RoleChoices.HR:
        role_label = "HR (no profile)"
    return owner_name, role_label


@admin_required
def admin_recruitment_jobs_view(request):
    """
    Recruitment Monitoring - View All Job Postings.

    Read-only directory of job postings with department, posting owner / HR
    manager, live applicant count, status and dates. No create/edit/delete
    actions are offered here - that stays with the HR/Candidate modules.
    """
    jobs_qs = (
        JobVacancy.objects.select_related("department", "created_by")
        .annotate(applicants_count=Count("candidates"))
        .order_by("-created_at")
    )

    search = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=search) | Q(department__name__icontains=search)
        )
    if status_filter in JobVacancy.StatusChoices.values:
        jobs_qs = jobs_qs.filter(status=status_filter)

    job_rows = []
    for vacancy in jobs_qs:
        owner_name, owner_role = _vacancy_owner_details(vacancy)
        job_rows.append(
            {
                "vacancy": vacancy,
                "applicants_count": vacancy.applicants_count,
                "owner_name": owner_name,
                "owner_role": owner_role,
                "created_by": vacancy.created_by,
            }
        )

    total_applications = Candidate.objects.count()
    selections_count = Candidate.objects.filter(
        status__in=[Candidate.StatusChoices.SELECTED, Candidate.StatusChoices.HIRED]
    ).count()

    context = get_sidebar_context()
    context.update(
        {
            "page_title": "Job Postings - Recruitment Monitoring",
            "current_page": "recruitment_jobs",
            "job_rows": job_rows,
            "search": search,
            "status_filter": status_filter,
            "job_statuses": JobVacancy.StatusChoices.choices,
            "total_jobs": JobVacancy.objects.count(),
            "open_jobs": JobVacancy.objects.filter(
                status=JobVacancy.StatusChoices.OPEN
            ).count(),
            "total_applications": total_applications,
            "selections_count": selections_count,
        }
    )
    return render(request, "admin/recruitment_jobs.html", context)


@admin_required
def admin_recruitment_status_view(request):
    """
    Recruitment Monitoring - Recruitment Status.

    Pipeline progress per job posting computed from the live candidate
    application records (stage counts). Totals come straight from the
    database - nothing is hardcoded.
    """
    stage_totals = _recruitment_stage_totals()
    global_totals = {stage: 0 for stage in RECRUITMENT_STAGES}

    jobs_qs = JobVacancy.objects.select_related("department").order_by("-created_at")
    search = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=search) | Q(department__name__icontains=search)
        )
    if status_filter in JobVacancy.StatusChoices.values:
        jobs_qs = jobs_qs.filter(status=status_filter)

    job_rows = []
    for vacancy in jobs_qs:
        stages = stage_totals.get(vacancy.pk, {})
        applicants_count = sum(stages.values())
        row_stages = {stage: stages.get(stage, 0) for stage in RECRUITMENT_STAGES}
        for stage, count in row_stages.items():
            global_totals[stage] += count
        job_rows.append(
            {
                "vacancy": vacancy,
                "applicants_count": applicants_count,
                "stages": row_stages,
            }
        )

    context = get_sidebar_context()
    context.update(
        {
            "page_title": "Recruitment Status - Recruitment Monitoring",
            "current_page": "recruitment_status",
            "job_rows": job_rows,
            "search": search,
            "status_filter": status_filter,
            "job_statuses": JobVacancy.StatusChoices.choices,
            "stages": RECRUITMENT_STAGES,
            "global_totals": global_totals,
            "total_applications": sum(global_totals.values()),
        }
    )
    return render(request, "admin/recruitment_status.html", context)


@admin_required
def admin_recruitment_job_status_view(request, vacancy_id):
    """Recruitment Monitoring - drill-down pipeline for a single job posting."""
    try:
        vacancy = JobVacancy.objects.select_related("department", "created_by").get(
            pk=vacancy_id
        )
    except JobVacancy.DoesNotExist:
        messages.error(request, "Job posting not found.")
        return redirect("hrms:recruitment_status")

    candidates_qs = vacancy.candidates.select_related("user").order_by("-applied_at")
    stage_filter = request.GET.get("stage", "").strip()
    search = request.GET.get("q", "").strip()

    if stage_filter in Candidate.StatusChoices.values:
        candidates_qs = candidates_qs.filter(status=stage_filter)
    if search:
        candidates_qs = candidates_qs.filter(
            Q(full_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    stage_rows = list(vacancy.candidates.values("status").annotate(count=Count("id")))
    stage_counts = {row["status"]: row["count"] for row in stage_rows}
    total_applicants = sum(stage_counts.values())

    owner_name, owner_role = _vacancy_owner_details(vacancy)

    context = get_sidebar_context()
    context.update(
        {
            "page_title": f"Pipeline: {vacancy.title}",
            "current_page": "recruitment_status",
            "vacancy": vacancy,
            "candidates": candidates_qs,
            "stages": RECRUITMENT_STAGES,
            "stage_counts": stage_counts,
            "stage_filter": stage_filter,
            "search": search,
            "status_choices": Candidate.StatusChoices.choices,
            "total_applicants": total_applicants,
            "owner_name": owner_name,
            "owner_role": owner_role,
        }
    )
    return render(request, "admin/recruitment_job_status.html", context)


@admin_required
def admin_recruitment_selected_view(request):
    """
    Recruitment Monitoring - View Selected Candidates.

    Read-only list of candidates whose application is in the Selected or
    Hired stage, with position, department, selection date and status.
    """
    selected_qs = (
        Candidate.objects.select_related("job_vacancy", "job_vacancy__department")
        .filter(
            status__in=[Candidate.StatusChoices.SELECTED, Candidate.StatusChoices.HIRED]
        )
        .order_by("-updated_at")
    )

    search = request.GET.get("q", "").strip()
    vacancy_filter = request.GET.get("vacancy", "").strip()

    if search:
        selected_qs = selected_qs.filter(
            Q(full_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(job_vacancy__title__icontains=search)
        )
    if vacancy_filter.isdigit():
        selected_qs = selected_qs.filter(job_vacancy_id=int(vacancy_filter))

    selected_count = Candidate.objects.filter(
        status=Candidate.StatusChoices.SELECTED
    ).count()
    hired_count = Candidate.objects.filter(
        status=Candidate.StatusChoices.HIRED
    ).count()

    context = get_sidebar_context()
    context.update(
        {
            "page_title": "Selected Candidates - Recruitment Monitoring",
            "current_page": "recruitment_selected",
            "selected_candidates": selected_qs,
            "search": search,
            "vacancy_filter": vacancy_filter,
            "vacancies": JobVacancy.objects.order_by("title"),
            "selected_count": selected_count,
            "hired_count": hired_count,
            "total_count": selected_qs.count(),
        }
    )
    return render(request, "admin/recruitment_selected.html", context)


@admin_required
def admin_recruitment_candidate_detail_view(request, candidate_id):
    """
    Recruitment Monitoring - read-only candidate / recruitment detail view.
    """
    try:
        candidate = Candidate.objects.select_related(
            "job_vacancy", "job_vacancy__department", "user"
        ).get(pk=candidate_id)
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate application not found.")
        return redirect("hrms:recruitment_selected")

    # Other applications filed by the same person (same linked account/email).
    other_applications = Candidate.objects.none()
    if candidate.user_id:
        other_applications = Candidate.objects.filter(user_id=candidate.user_id).exclude(
            pk=candidate.pk
        )
    elif candidate.email:
        other_applications = Candidate.objects.filter(email=candidate.email).exclude(
            pk=candidate.pk
        )
    other_applications = other_applications.select_related("job_vacancy")[:10]

    owner_name, owner_role = _vacancy_owner_details(candidate.job_vacancy)

    context = get_sidebar_context()
    context.update(
        {
            "page_title": f"Candidate: {candidate.full_name}",
            "current_page": "recruitment_selected",
            "candidate": candidate,
            "other_applications": other_applications,
            "owner_name": owner_name,
            "owner_role": owner_role,
        }
    )
    return render(request, "admin/recruitment_candidate_detail.html", context)


@admin_required
def admin_recruitment_approvals_view(request):
    """
    Recruitment Monitoring - Approve New Employee Records.

    Lists employee records raised by HR from selected candidates that are
    awaiting Admin approval. Approval simply confirms the record - duplicate
    approvals are blocked server-side by the status guard in the approve view.
    """
    pending_qs = (
        Employee.objects.select_related("user", "department")
        .filter(status=Employee.StatusChoices.PENDING_APPROVAL)
        .order_by("-created_at")
    )

    search = request.GET.get("q", "").strip()
    if search:
        pending_qs = pending_qs.filter(
            Q(user__name__icontains=search)
            | Q(user__email__icontains=search)
            | Q(designation__icontains=search)
            | Q(department__name__icontains=search)
        )

    pending_list = list(pending_qs)
    pending_count = len(pending_list)
    active_employees = Employee.objects.filter(
        status=Employee.StatusChoices.ACTIVE
    ).count()
    total_employees = Employee.objects.count()
    recently_processed = (
        Employee.objects.select_related("user", "department")
        .filter(status=Employee.StatusChoices.ACTIVE)
        .order_by("-created_at")[:6]
    )

    context = get_sidebar_context()
    context.update(
        {
            "page_title": "New Employee Approvals - Recruitment Monitoring",
            "current_page": "recruitment_approvals",
            "pending_list": pending_list,
            "pending_count": pending_count,
            "active_employees": active_employees,
            "total_employees": total_employees,
            "recently_processed": recently_processed,
            "search": search,
        }
    )
    return render(request, "admin/recruitment_approvals.html", context)


@admin_required
def admin_recruitment_approval_review_view(request, employee_id):
    """
    Recruitment Monitoring - review screen for one pending employee record.
    """
    try:
        employee = Employee.objects.select_related("user", "department").get(
            pk=employee_id
        )
    except Employee.DoesNotExist:
        messages.error(request, "Employee record not found.")
        return redirect("hrms:recruitment_approvals")

    if employee.status != Employee.StatusChoices.PENDING_APPROVAL:
        messages.info(
            request,
            f"This employee record has already been processed "
            f"(status: {employee.get_status_display()}). "
            "Duplicate approvals are not allowed.",
        )
        return redirect("hrms:recruitment_approvals")

    context = get_sidebar_context()
    context.update(
        {
            "page_title": f"Review Employee Approval: {employee.user.name or employee.user.email}",
            "current_page": "recruitment_approvals",
            "employee": employee,
        }
    )
    return render(request, "admin/recruitment_approval_review.html", context)


@admin_required
def admin_recruitment_approval_approve_view(request, employee_id):
    """
    Recruitment Monitoring - Approve action for a new employee record.

    POST only. The atomic status guard makes a second approval a no-op, so an
    employee record can never be approved twice (duplicate approvals are
    prevented) and no duplicate employee records are ever created here.
    """
    if request.method != "POST":
        messages.warning(
            request, "Use the review screen to confirm the employee approval."
        )
        return redirect("hrms:recruitment_approvals")

    approved_count = Employee.objects.filter(
        pk=employee_id,
        status=Employee.StatusChoices.PENDING_APPROVAL,
    ).update(status=Employee.StatusChoices.ACTIVE)

    if approved_count == 0:
        messages.error(
            request,
            "Approval could not be completed: this record is missing or has "
            "already been processed. Duplicate approvals are not allowed.",
        )
        return redirect("hrms:recruitment_approvals")

    employee = Employee.objects.select_related("user", "department").get(
        pk=employee_id
    )

    # Activate the linked employee account if it is still inactive/pending so
    # the new hire can sign in after approval.
    user = employee.user
    if user.status != User.StatusChoices.ACTIVE or not user.is_active:
        user.status = User.StatusChoices.ACTIVE
        user.is_active = True
        user.save(update_fields=["status", "is_active"])

    messages.success(
        request,
        f"Employee record for '{user.name or user.email}' has been approved "
        "and moved to the Active workforce.",
    )
    return redirect("hrms:recruitment_approvals")


# ============================================================================
# ADMIN REPORTS VIEWS (view & analyze only - never manage the source data)
#
# All five reports are read-only. They aggregate the existing HR, Employee,
# Recruitment, Department and Performance records; Admin cannot create, edit
# or delete any of the underlying data from these pages.
# ============================================================================

REPORT_PERIODS = [
    ("7d", "Last 7 Days"),
    ("14d", "Last 14 Days"),
    ("30d", "Last 30 Days"),
    ("all", "All Time"),
]

REPORT_PERIOD_LABELS = dict(REPORT_PERIODS)


def _report_period_start(period_code):
    """Return the start datetime for a reporting period (None = all time)."""
    if period_code == "7d":
        return timezone.now() - timedelta(days=7)
    if period_code == "14d":
        return timezone.now() - timedelta(days=14)
    if period_code == "30d":
        return timezone.now() - timedelta(days=30)
    return None


def _report_context(period, current_page, page_title):
    """Shared context for report pages: sidebar counts, filters and page info."""
    context = get_sidebar_context()
    context.update(
        {
            "current_page": current_page,
            "page_title": page_title,
            "period": period,
            "period_label": REPORT_PERIOD_LABELS.get(period, "All Time"),
            "report_periods": REPORT_PERIODS,
        }
    )
    return context


@admin_required
def admin_reports_hr_weekly_view(request):
    """
    Admin Reports - HR Weekly Reports.

    Weekly HR activity report per HR manager, computed from the existing
    recruitment records they own (jobs posted, applications received and
    pipeline progress) inside the selected reporting period. There is no
    separate report-writing model - the figures always reflect the database.
    """
    period = request.GET.get("period", "all").strip()
    if period not in REPORT_PERIOD_LABELS:
        period = "all"
    period_start = _report_period_start(period)

    managers = HRManager.objects.select_related("user", "department").order_by(
        "user__name"
    )

    rows = []
    for manager in managers:
        jobs = JobVacancy.objects.filter(created_by=manager.user)
        jobs_in_period = jobs.filter(created_at__gte=period_start) if period_start else jobs

        applications = Candidate.objects.filter(job_vacancy__in=jobs)
        applications_in_period = (
            applications.filter(applied_at__gte=period_start) if period_start else applications
        )

        def stage_count(stage):
            return applications_in_period.filter(status=stage).count()

        rows.append(
            {
                "manager": manager,
                "department_name": manager.department.name if manager.department else "Unassigned",
                "jobs_posted": jobs_in_period.count(),
                "open_jobs": jobs.filter(status=JobVacancy.StatusChoices.OPEN).count(),
                "applications": applications_in_period.count(),
                "shortlisted": stage_count(Candidate.StatusChoices.SHORTLISTED),
                "selected": stage_count(Candidate.StatusChoices.SELECTED),
                "hired": stage_count(Candidate.StatusChoices.HIRED),
                "rejected": stage_count(Candidate.StatusChoices.REJECTED),
            }
        )

    context = _report_context(period, "reports_hr_weekly", "HR Weekly Reports")
    context.update(
        {
            "rows": rows,
            "total_managers": len(rows),
            "total_jobs_posted": sum(row["jobs_posted"] for row in rows),
            "total_applications": sum(row["applications"] for row in rows),
            "total_selections": sum(row["selected"] + row["hired"] for row in rows),
        }
    )
    return render(request, "admin/reports_hr_weekly.html", context)


@admin_required
def admin_reports_employee_weekly_view(request):
    """
    Admin Reports - Employee Weekly Reports.

    Shows the weekly work reports submitted by employees. These records come
    from the existing employees module (employees.models.EmployeeReport) - the
    page is strictly read-only for Admin.
    """
    from employees.models import EmployeeReport  # existing weekly report model

    reports_qs = EmployeeReport.objects.select_related(
        "employee__user", "employee__department", "reviewed_by__user"
    ).order_by("-week_start_date")

    search = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    from_date = request.GET.get("from", "").strip()
    to_date = request.GET.get("to", "").strip()

    if search:
        reports_qs = reports_qs.filter(
            Q(employee__user__name__icontains=search)
            | Q(employee__user__email__icontains=search)
            | Q(work_summary__icontains=search)
            | Q(tasks_completed__icontains=search)
        )
    if status_filter in dict(EmployeeReport.REPORT_STATUS).keys():
        reports_qs = reports_qs.filter(status=status_filter)
    if from_date:
        reports_qs = reports_qs.filter(week_start_date__gte=from_date)
    if to_date:
        reports_qs = reports_qs.filter(week_end_date__lte=to_date)

    total_reports = EmployeeReport.objects.count()
    submitted_count = EmployeeReport.objects.filter(
        status="SUBMITTED"
    ).count()
    reviewed_count = EmployeeReport.objects.filter(status="REVIEWED").count()
    needs_correction_count = EmployeeReport.objects.filter(
        status="NEEDS_CORRECTION"
    ).count()

    context = _report_context("all", "reports_employee_weekly", "Employee Weekly Reports")
    context.update(
        {
            "reports": reports_qs,
            "statuses": EmployeeReport.REPORT_STATUS,
            "search": search,
            "status_filter": status_filter,
            "from_date": from_date,
            "to_date": to_date,
            "total_reports": total_reports,
            "submitted_count": submitted_count,
            "reviewed_count": reviewed_count,
            "needs_correction_count": needs_correction_count,
            "filtered_count": reports_qs.count(),
        }
    )
    return render(request, "admin/reports_employee_weekly.html", context)


@admin_required
def admin_reports_recruitment_view(request):
    """
    Admin Reports - Recruitment Reports.

    Recruitment statistics computed live from job postings and candidate
    applications. The reporting period filters application activity; the
    job-posting directory and statuses always reflect the database.
    """
    period = request.GET.get("period", "all").strip()
    if period not in REPORT_PERIOD_LABELS:
        period = "all"
    period_start = _report_period_start(period)

    stage_rows = (
        Candidate.objects.values("job_vacancy_id", "status")
        .annotate(count=Count("id"))
        .order_by("job_vacancy_id")
    )
    if period_start:
        period_candidates = Candidate.objects.filter(applied_at__gte=period_start)
        stage_rows = (
            period_candidates.values("job_vacancy_id", "status")
            .annotate(count=Count("id"))
            .order_by("job_vacancy_id")
        )

    stage_by_job = {}
    for row in stage_rows:
        stage_by_job.setdefault(row["job_vacancy_id"], {})[row["status"]] = row["count"]

    jobs = JobVacancy.objects.select_related("department").order_by("-created_at")
    job_rows = []
    for vacancy in jobs:
        stages = stage_by_job.get(vacancy.pk, {})
        job_rows.append(
            {
                "vacancy": vacancy,
                "applicants": sum(stages.values()),
                "shortlisted": stages.get(Candidate.StatusChoices.SHORTLISTED, 0),
                "selected": stages.get(Candidate.StatusChoices.SELECTED, 0),
                "hired": stages.get(Candidate.StatusChoices.HIRED, 0),
                "rejected": stages.get(Candidate.StatusChoices.REJECTED, 0),
            }
        )

    applications = sum(row["applicants"] for row in job_rows)
    shortlisted = sum(row["shortlisted"] for row in job_rows)
    selected = sum(row["selected"] for row in job_rows)
    hired = sum(row["hired"] for row in job_rows)
    rejected = sum(row["rejected"] for row in job_rows)

    chart_labels = [row["vacancy"].title for row in job_rows[:10]]
    chart_values = [row["applicants"] for row in job_rows[:10]]

    context = _report_context(period, "reports_recruitment", "Recruitment Reports")
    context.update(
        {
            "job_rows": job_rows,
            "total_jobs": JobVacancy.objects.count(),
            "open_jobs": JobVacancy.objects.filter(
                status=JobVacancy.StatusChoices.OPEN
            ).count(),
            "applications": applications,
            "shortlisted": shortlisted,
            "selected": selected,
            "hired": hired,
            "rejected": rejected,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
        }
    )
    return render(request, "admin/reports_recruitment.html", context)


@admin_required
def admin_reports_departments_view(request):
    """
    Admin Reports - Department-wise Employee Report.

    Employees grouped by department with accurate headcounts computed with an
    aggregation over the existing employee records.
    """
    search = request.GET.get("q", "").strip()
    emp_status = request.GET.get("emp_status", "").strip()

    departments_qs = Department.objects.annotate(
        employee_count=Count("employees")
    ).order_by("-employee_count", "name")

    if search:
        departments_qs = departments_qs.filter(name__icontains=search)

    rows = []
    for department in departments_qs:
        employees = department.employees.select_related("user").order_by(
            "user__name"
        )
        if emp_status in Employee.StatusChoices.values:
            employees = employees.filter(status=emp_status)
        rows.append(
            {
                "department": department,
                "employee_count": department.employee_count,
                "employees": employees,
                "active_count": employees.filter(
                    status=Employee.StatusChoices.ACTIVE
                ).count(),
            }
        )

    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(
        status=Employee.StatusChoices.ACTIVE
    ).count()
    total_departments = Department.objects.count()
    avg_headcount = (
        round(total_employees / total_departments, 1) if total_departments else 0
    )

    chart_labels = [row["department"].name for row in rows[:10]]
    chart_values = [row["employee_count"] for row in rows[:10]]

    context = _report_context("all", "reports_departments", "Department-wise Employee Report")
    context.update(
        {
            "rows": rows,
            "search": search,
            "emp_status": emp_status,
            "employee_statuses": Employee.StatusChoices.choices,
            "total_departments": total_departments,
            "total_employees": total_employees,
            "active_employees": active_employees,
            "avg_headcount": avg_headcount,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
        }
    )
    return render(request, "admin/reports_departments.html", context)


@admin_required
def admin_reports_performance_view(request):
    """
    Admin Reports - Employee Performance Report.

    Read-only analysis of performance reviews and warnings that HR recorded.
    Ratings, review periods, warnings and their statuses come straight from
    the existing performance models.
    """
    search = request.GET.get("q", "").strip()
    department_filter = request.GET.get("department", "").strip()
    min_rating = request.GET.get("min_rating", "").strip()
    warning_status = request.GET.get("warning_status", "").strip()

    reviews_qs = EmployeePerformance.objects.select_related(
        "employee", "employee__user", "employee__department", "reviewed_by"
    ).order_by("-created_at")
    warnings_qs = PerformanceWarning.objects.select_related(
        "employee", "employee__user", "employee__department"
    ).order_by("-created_at")

    if search:
        reviews_qs = reviews_qs.filter(
            Q(employee__user__name__icontains=search)
            | Q(employee__user__email__icontains=search)
        )
        warnings_qs = warnings_qs.filter(
            Q(employee__user__name__icontains=search)
            | Q(employee__user__email__icontains=search)
            | Q(title__icontains=search)
        )
    if department_filter.isdigit():
        reviews_qs = reviews_qs.filter(employee__department_id=int(department_filter))
        warnings_qs = warnings_qs.filter(employee__department_id=int(department_filter))
    if min_rating in {"3", "4", "4.5", "5"}:
        reviews_qs = reviews_qs.filter(rating__gte=float(min_rating))
    if warning_status in dict(PerformanceWarning.StatusChoices.choices):
        warnings_qs = warnings_qs.filter(status=warning_status)

    avg_rating = EmployeePerformance.objects.aggregate(avg=Avg("rating"))["avg"]

    context = _report_context("all", "reports_performance", "Employee Performance Report")
    context.update(
        {
            "reviews": reviews_qs,
            "warnings": warnings_qs,
            "departments": Department.objects.order_by("name"),
            "search": search,
            "department_filter": department_filter,
            "min_rating": min_rating,
            "warning_status": warning_status,
            "warning_statuses": PerformanceWarning.StatusChoices.choices,
            "total_reviews": EmployeePerformance.objects.count(),
            "avg_rating": round(avg_rating, 1) if avg_rating is not None else None,
            "open_warnings": PerformanceWarning.objects.filter(
                status__in=[
                    PerformanceWarning.StatusChoices.PENDING,
                    PerformanceWarning.StatusChoices.ACTIVE,
                ]
            ).count(),
            "resolved_warnings": PerformanceWarning.objects.filter(
                status__in=[
                    PerformanceWarning.StatusChoices.ACKNOWLEDGED,
                    PerformanceWarning.StatusChoices.RESOLVED,
                ]
            ).count(),
            "rated_employees": EmployeePerformance.objects.values("employee_id").distinct().count(),
        }
    )
    return render(request, "admin/reports_performance.html", context)


# =============================================================================
# Task 8: Admin Responsibilities (Performance Warnings & HR Recommendations)
# =============================================================================


@admin_required
def admin_responsibilities_warnings_view(request):
    """
    Admin Responsibilities - Performance Warnings Directory.

    Lists all performance warnings across employees, with filtering by status,
    department, recommendation presence, and search term. Displays employee details,
    department, reason, issue date, status, issuing HR Manager, and HR recommendation info.
    """
    from employees.models import PerformanceWarning as StandalonePerformanceWarning

    search = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    has_rec_filter = request.GET.get("has_rec", "").strip()

    warnings_qs = StandalonePerformanceWarning.objects.select_related(
        "employee__user", "employee__department", "issued_by__user", "decided_by"
    ).order_by("-warning_date", "-warning_id")

    if search:
        warnings_qs = warnings_qs.filter(
            Q(employee__user__name__icontains=search)
            | Q(employee__user__email__icontains=search)
            | Q(employee__employee_code__icontains=search)
            | Q(employee__department__name__icontains=search)
            | Q(reason__icontains=search)
        )
    if status_filter in dict(StandalonePerformanceWarning.STATUS_CHOICES):
        warnings_qs = warnings_qs.filter(status=status_filter)
    if has_rec_filter == "yes":
        warnings_qs = warnings_qs.exclude(hr_recommendation="")
    elif has_rec_filter == "no":
        warnings_qs = warnings_qs.filter(hr_recommendation="")

    total_warnings = StandalonePerformanceWarning.objects.count()
    open_warnings_count = StandalonePerformanceWarning.objects.filter(status="OPEN").count()
    sent_to_admin_count = StandalonePerformanceWarning.objects.filter(status="SENT_TO_ADMIN").count()
    resolved_warnings_count = StandalonePerformanceWarning.objects.filter(status="RESOLVED").count()
    with_recs_count = StandalonePerformanceWarning.objects.exclude(hr_recommendation="").count()

    context = get_sidebar_context()
    context.update(
        {
            "current_page": "admin_responsibilities_warnings",
            "page_title": "Performance Warnings - Admin Responsibilities",
            "warnings": warnings_qs,
            "search": search,
            "status_filter": status_filter,
            "has_rec_filter": has_rec_filter,
            "status_choices": StandalonePerformanceWarning.STATUS_CHOICES,
            "total_warnings": total_warnings,
            "open_warnings_count": open_warnings_count,
            "sent_to_admin_count": sent_to_admin_count,
            "resolved_warnings_count": resolved_warnings_count,
            "with_recs_count": with_recs_count,
        }
    )
    return render(request, "admin/responsibilities_warnings.html", context)


@admin_required
def admin_responsibilities_warning_detail_view(request, warning_id):
    """
    Admin Responsibilities - Warning Details View.

    Detailed view of a single warning, including issuing HR Manager, employee profile,
    warning details, attached HR recommendation (if any), Admin decision (if resolved),
    and complete historical warnings for this employee.
    """
    from employees.models import PerformanceWarning as StandalonePerformanceWarning

    warning = get_object_or_404(
        StandalonePerformanceWarning.objects.select_related(
            "employee__user", "employee__department", "issued_by__user", "decided_by"
        ),
        pk=warning_id,
    )

    history = StandalonePerformanceWarning.objects.filter(
        employee=warning.employee
    ).exclude(pk=warning.pk).select_related(
        "issued_by__user", "decided_by"
    ).order_by("-warning_date", "-warning_id")

    context = get_sidebar_context()
    context.update(
        {
            "current_page": "admin_responsibilities_warnings",
            "page_title": f"Warning #{warning.warning_id} Details - Admin Responsibilities",
            "warning": warning,
            "history": history,
            "employee": warning.employee,
        }
    )
    return render(request, "admin/responsibilities_warning_detail.html", context)


@admin_required
def admin_responsibilities_recommendations_view(request):
    """
    Admin Responsibilities - HR Recommendations Directory.

    Lists all warnings containing HR recommendations requiring Admin review or previously decided.
    Allows filtering by status (Pending Review vs Decided) and searching by employee.
    """
    from employees.models import PerformanceWarning as StandalonePerformanceWarning

    status_tab = request.GET.get("tab", "pending").strip()
    search = request.GET.get("q", "").strip()

    recs_qs = StandalonePerformanceWarning.objects.exclude(
        hr_recommendation=""
    ).select_related(
        "employee__user", "employee__department", "issued_by__user", "decided_by"
    ).order_by("-warning_date", "-warning_id")

    if status_tab == "resolved":
        recs_qs = recs_qs.filter(status="RESOLVED")
    else:
        # Default: pending admin review
        recs_qs = recs_qs.filter(status__in=["OPEN", "SENT_TO_ADMIN"])

    if search:
        recs_qs = recs_qs.filter(
            Q(employee__user__name__icontains=search)
            | Q(employee__user__email__icontains=search)
            | Q(employee__employee_code__icontains=search)
            | Q(hr_recommendation__icontains=search)
            | Q(reason__icontains=search)
        )

    pending_count = StandalonePerformanceWarning.objects.exclude(
        hr_recommendation=""
    ).filter(status__in=["OPEN", "SENT_TO_ADMIN"]).count()

    resolved_count = StandalonePerformanceWarning.objects.exclude(
        hr_recommendation=""
    ).filter(status="RESOLVED").count()

    context = get_sidebar_context()
    context.update(
        {
            "current_page": "admin_responsibilities_recommendations",
            "page_title": "HR Recommendations - Admin Responsibilities",
            "recommendations": recs_qs,
            "status_tab": status_tab,
            "search": search,
            "pending_count": pending_count,
            "resolved_count": resolved_count,
            "total_count": pending_count + resolved_count,
        }
    )
    return render(request, "admin/responsibilities_recommendations.html", context)


@admin_required
def admin_responsibilities_review_view(request, warning_id):
    """
    Admin Responsibilities - HR Recommendation Review & Final Decision Interface.

    Presents the complete review context:
    - Employee Information & Current Employment Status
    - Warning Details & Progression Timeline (Warning -> HR Rec -> Admin Review -> Admin Decision)
    - HR Recommendation clearly distinguished from Admin Final Decision
    - Performance & Warning History
    - Admin Final Decision Form (Continue Employment, Give Another Warning, Issue Termination Letter with confirmation)
    """
    from employees.models import PerformanceWarning as StandalonePerformanceWarning

    warning = get_object_or_404(
        StandalonePerformanceWarning.objects.select_related(
            "employee__user", "employee__department", "issued_by__user", "decided_by"
        ),
        pk=warning_id,
    )

    employee = warning.employee
    warning_history = StandalonePerformanceWarning.objects.filter(
        employee=employee
    ).select_related("issued_by__user", "decided_by").order_by("-warning_date", "-warning_id")

    performance_reviews = employee.performance_reviews.select_related("reviewed_by__user").order_by("-review_date")

    initial_data = {}
    if warning.admin_decision:
        initial_data["decision"] = warning.admin_decision
        initial_data["admin_comments"] = warning.admin_comments

    form = AdminDecisionForm(initial=initial_data)

    context = get_sidebar_context()
    context.update(
        {
            "current_page": "admin_responsibilities_recommendations",
            "page_title": f"Review Recommendation: {employee.user.name or employee.user.email} - Admin Responsibilities",
            "warning": warning,
            "employee": employee,
            "warning_history": warning_history,
            "performance_reviews": performance_reviews,
            "form": form,
        }
    )
    return render(request, "admin/responsibilities_review.html", context)


@admin_required
def admin_responsibilities_decision_view(request, warning_id):
    """
    Admin Responsibilities - Process Admin Final Decision.

    Handles form submission for:
    1. Continue Employment: sets admin decision, resolves warning, employee remains Active.
    2. Give Another Warning: sets admin decision, resolves warning, creates a new warning record preserving history.
    3. Issue Termination Letter: requires confirmation! Updates employment status to Terminated,
       deactivates user account (blocks login), records termination notice document, never deletes employee record.
    """
    from django.core.files.base import ContentFile
    from employees.models import EmployeeDocument
    from employees.models import PerformanceWarning as StandalonePerformanceWarning

    warning = get_object_or_404(
        StandalonePerformanceWarning.objects.select_related(
            "employee__user", "employee__department", "issued_by__user"
        ),
        pk=warning_id,
    )
    employee = warning.employee

    if request.method != "POST":
        return redirect("hrms:admin_responsibilities_review", warning_id=warning.pk)

    form = AdminDecisionForm(request.POST)
    if not form.is_valid():
        warning_history = StandalonePerformanceWarning.objects.filter(
            employee=employee
        ).select_related("issued_by__user", "decided_by").order_by("-warning_date", "-warning_id")
        performance_reviews = employee.performance_reviews.select_related("reviewed_by__user").order_by("-review_date")

        context = get_sidebar_context()
        context.update(
            {
                "current_page": "admin_responsibilities_recommendations",
                "page_title": f"Review Recommendation: {employee.user.name or employee.user.email} - Admin Responsibilities",
                "warning": warning,
                "employee": employee,
                "warning_history": warning_history,
                "performance_reviews": performance_reviews,
                "form": form,
            }
        )
        return render(request, "admin/responsibilities_review.html", context)

    decision = form.cleaned_data["decision"]
    admin_comments = form.cleaned_data["admin_comments"]
    new_warning_reason = form.cleaned_data.get("new_warning_reason", "")
    now = timezone.now()

    # Update current warning with admin decision
    warning.admin_decision = decision
    warning.admin_comments = admin_comments
    warning.decided_by = request.user
    warning.decision_date = now
    warning.status = "RESOLVED"
    warning.save()

    emp_name = employee.user.name or employee.user.email

    if decision == "CONTINUE":
        messages.success(
            request,
            f"Decision recorded: Continued employment for {emp_name}. Records and active status maintained.",
        )
    elif decision == "ANOTHER_WARNING":
        # Create new warning record to continue tracking without overwriting history
        StandalonePerformanceWarning.objects.create(
            employee=employee,
            performance=warning.performance,
            issued_by=warning.issued_by,
            reason=new_warning_reason or admin_comments,
            hr_recommendation="",
            status="OPEN",
        )
        messages.success(
            request,
            f"Decision recorded: Subsequent warning issued to {emp_name}. Warning progression preserved.",
        )
    elif decision == "TERMINATION":
        # 1. Update employee employment status to TERMINATED
        employee.employment_status = "TERMINATED"
        employee.save(update_fields=["employment_status", "updated_at"])

        # 2. Deactivate employee user account (lockout at authentication level)
        emp_user = employee.user
        emp_user.status = User.StatusChoices.INACTIVE
        emp_user.is_active = False
        emp_user.save(update_fields=["status", "is_active"])

        # 3. Synchronize hrms.Employee profile if present
        Employee.objects.filter(user=emp_user).update(status=Employee.StatusChoices.TERMINATED)

        # 4. Generate and store official termination letter document under EmployeeDocument
        try:
            dept_name = employee.department.name if employee.department else "N/A"
            letter_text = (
                f"OFFICIAL NOTICE OF TERMINATION OF EMPLOYMENT\n"
                f"{'='*50}\n\n"
                f"Date of Decision: {now.strftime('%B %d, %Y at %H:%M')}\n"
                f"Employee Name:    {emp_name}\n"
                f"Employee Code:    {employee.employee_code}\n"
                f"Department:       {dept_name}\n"
                f"Designation:      {employee.designation}\n\n"
                f"Prior HR Recommendation:\n"
                f"------------------------\n"
                f"{warning.hr_recommendation or 'N/A'}\n\n"
                f"Administrator Final Directive:\n"
                f"------------------------------\n"
                f"{admin_comments}\n\n"
                f"Authorized by System Administrator: {request.user.name or request.user.email}\n"
                f"Status: TERMINATED - Access Revoked\n"
            )
            filename = f"termination_letter_{employee.employee_code}_{now.strftime('%Y%m%d%H%M%S')}.txt"
            EmployeeDocument.objects.create(
                employee=employee,
                document_type="OTHER",
                document=ContentFile(letter_text.encode("utf-8"), name=filename),
            )
        except Exception:
            pass

        messages.warning(
            request,
            f"Termination letter issued for {emp_name}. Employment status marked as Terminated and account deactivated.",
        )

    return redirect("hrms:admin_responsibilities_warning_detail", warning_id=warning.pk)


# ============================================================================
# ANNOUNCEMENT MANAGEMENT VIEWS
# ============================================================================


def sync_to_admin_module_announcement(announcement, is_delete=False):
    """Synchronize hrms.models.Announcement with admin_module.models.Announcement."""
    try:
        from admin_module.models import Announcement as AdminModuleAnnouncement

        if is_delete:
            AdminModuleAnnouncement.objects.filter(title=announcement.title).delete()
            return

        adm_ann, _ = AdminModuleAnnouncement.objects.get_or_create(
            title=announcement.title,
            defaults={
                "content": announcement.content,
                "announcement_type": getattr(announcement, "announcement_type", "GENERAL") or "GENERAL",
                "created_by": announcement.created_by,
                "is_published": announcement.is_published,
                "published_at": announcement.published_at,
            },
        )
        adm_ann.content = announcement.content
        adm_ann.announcement_type = getattr(announcement, "announcement_type", "GENERAL") or "GENERAL"
        adm_ann.created_by = announcement.created_by
        adm_ann.is_published = announcement.is_published
        adm_ann.published_at = announcement.published_at
        adm_ann.save()
    except Exception:
        pass


@admin_required
def admin_announcements_management_view(request):
    """List and manage announcements from the admin portal."""
    announcements = Announcement.objects.select_related("created_by").order_by("-created_at")

    # Optional query filter by status (all, published, draft)
    status_filter = request.GET.get("status", "").strip().lower()
    if status_filter == "published":
        announcements = announcements.filter(is_published=True)
    elif status_filter == "draft":
        announcements = announcements.filter(is_published=False)

    audience_filter = request.GET.get("audience", "").strip()
    if audience_filter:
        announcements = announcements.filter(target_audience=audience_filter)

    search_query = request.GET.get("q", "").strip()
    if search_query:
        announcements = announcements.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )

    context = get_sidebar_context()
    context.update({
        "page_title": "Manage Announcements - Smart HRMS Admin",
        "current_page": "announcements",
        "announcements": announcements,
        "show_add_button": True,
        "status_filter": status_filter,
        "audience_filter": audience_filter,
        "search_query": search_query,
        "published_count": Announcement.objects.filter(is_published=True).count(),
        "draft_count": Announcement.objects.filter(is_published=False).count(),
    })
    return render(request, "admin/manage_announcements.html", context)


@admin_required
def admin_announcement_create_view(request):
    """Create a new announcement."""
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            publish_action = request.POST.get("action")

            if publish_action == "publish" or form.cleaned_data.get("is_published"):
                announcement.is_published = True
                announcement.published_at = timezone.now()
                announcement.is_active = True
            else:
                announcement.is_published = False
                announcement.published_at = None

            announcement.save()
            sync_to_admin_module_announcement(announcement)

            messages.success(
                request,
                f"Announcement '{announcement.title}' was created successfully."
                + (" and published immediately." if announcement.is_published else " as a draft."),
            )
            return redirect("hrms:announcements_list")
        messages.error(request, "Please correct the errors below to create the announcement.")
    else:
        form = AnnouncementForm()

    context = get_sidebar_context()
    context.update({
        "page_title": "Add Announcement - Smart HRMS Admin",
        "current_page": "announcements",
        "form": form,
        "title": "Add Announcement",
        "submit_label": "Create Announcement",
        "back_url": "hrms:announcements_list",
    })
    return render(request, "admin/announcement_form.html", context)


@admin_required
def admin_announcement_detail_view(request, announcement_id):
    """View announcement details."""
    announcement = get_object_or_404(Announcement, pk=announcement_id)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Announcement: {announcement.title}",
        "current_page": "announcements",
        "announcement": announcement,
    })
    return render(request, "admin/announcement_detail.html", context)


@admin_required
def admin_announcement_edit_view(request, announcement_id):
    """Edit an existing announcement."""
    announcement = get_object_or_404(Announcement, pk=announcement_id)

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            ann = form.save(commit=False)
            publish_action = request.POST.get("action")

            if publish_action == "publish":
                ann.is_published = True
                if not ann.published_at:
                    ann.published_at = timezone.now()
                ann.is_active = True
            elif publish_action == "draft":
                ann.is_published = False
                ann.published_at = None
            else:
                now_published = form.cleaned_data.get("is_published")
                if now_published:
                    ann.is_published = True
                    if not ann.published_at:
                        ann.published_at = timezone.now()
                    ann.is_active = True
                else:
                    ann.is_published = False
                    ann.published_at = None

            ann.save()
            sync_to_admin_module_announcement(ann)

            messages.success(request, f"Announcement '{ann.title}' was updated successfully.")
            return redirect("hrms:announcements_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AnnouncementForm(instance=announcement)

    context = get_sidebar_context()
    context.update({
        "page_title": f"Edit Announcement: {announcement.title}",
        "current_page": "announcements",
        "form": form,
        "announcement": announcement,
        "title": "Edit Announcement",
        "submit_label": "Update Announcement",
        "back_url": "hrms:announcements_list",
    })
    return render(request, "admin/announcement_form.html", context)


@admin_required
def admin_announcement_delete_view(request, announcement_id):
    """Delete an announcement after confirmation."""
    announcement = get_object_or_404(Announcement, pk=announcement_id)

    if request.method == "POST":
        announcement_title = announcement.title
        sync_to_admin_module_announcement(announcement, is_delete=True)
        announcement.delete()
        messages.success(request, f"Announcement '{announcement_title}' has been deleted.")
        return redirect("hrms:announcements_list")

    context = get_sidebar_context()
    context.update({
        "page_title": f"Delete Announcement: {announcement.title}",
        "current_page": "announcements",
        "object_type": "Announcement",
        "object_name": announcement.title,
        "object_id": announcement_id,
        "delete_url": "hrms:announcement_delete",
        "back_url": "hrms:announcements_list",
        "warning_message": (
            "This announcement is currently PUBLISHED and visible to users. Deleting it will remove it from all feeds."
            if announcement.is_published
            else None
        ),
    })
    return render(request, "admin/confirm_delete.html", context)


@admin_required
def admin_announcement_publish_view(request, announcement_id):
    """Publish a draft announcement or toggle its publication status."""
    announcement = get_object_or_404(Announcement, pk=announcement_id)

    if request.method in ["POST", "GET"]:
        if announcement.is_published:
            announcement.unpublish()
            messages.info(request, f"Announcement '{announcement.title}' has been unpublished and moved to draft.")
        else:
            announcement.publish()
            messages.success(request, f"Announcement '{announcement.title}' has been published successfully.")

        sync_to_admin_module_announcement(announcement)

    next_url = request.META.get("HTTP_REFERER") or "hrms:announcements_list"
    if "delete" in str(next_url):
        return redirect("hrms:announcements_list")
    return redirect(next_url)


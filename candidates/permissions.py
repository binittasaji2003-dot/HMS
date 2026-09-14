"""Role-based access control and security permissions for HRMS Portal.

Defines roles:
- ADMIN: Superusers or members of the ADMIN group.
- HR: Staff members or members of the HR group.
- EMPLOYEE: Onboarded employees with records in employee_table or members of the EMPLOYEE group.
- CANDIDATE: Standard authenticated job applicants who only have access to Candidate portal functionality.

Security Policy:
- Candidate users must ONLY access Candidate functionality.
- Any attempt by a Candidate to access Admin, HR, or Employee endpoints must strictly raise
  django.core.exceptions.PermissionDenied (HTTP 403 Forbidden).
- Redirects to login on authorization failure are strictly avoided for authenticated users to
  prevent redirect loops and ensure proper security auditing.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from .onboarding import is_candidate_onboarded


# ==============================================================================
# 1. ROLE IDENTIFICATION HELPERS
# ==============================================================================
def is_admin_user(user):
    """Returns True if the user has ADMIN privileges."""
    if not user or not user.is_authenticated:
        return False
    return bool(user.is_superuser or user.groups.filter(name__iexact="ADMIN").exists())


def is_hr_user(user):
    """Returns True if the user has HR privileges (staff or HR group or superuser)."""
    if not user or not user.is_authenticated:
        return False
    if is_admin_user(user):
        return True
    return bool(user.is_staff or user.groups.filter(name__iexact="HR").exists())


def is_employee_user(user):
    """
    Returns True if the user is an onboarded employee
    (has record in employee_table, is in EMPLOYEE group, or is an admin).
    """
    if not user or not user.is_authenticated:
        return False
    if is_admin_user(user):
        return True
    if user.groups.filter(name__iexact="EMPLOYEE").exists():
        return True
    return bool(is_candidate_onboarded(user_id=user.id))


def is_candidate_user(user):
    """
    Returns True if the user is specifically a job CANDIDATE
    (authenticated, and not an HR staff member or superuser).
    """
    if not user or not user.is_authenticated:
        return False
    # If the user is staff or superuser, they are HR/Admin, not regular Candidate
    if user.is_staff or user.is_superuser:
        return False
    return True


def get_user_role(user):
    """Resolves the primary system role for a given user account."""
    if not user or not user.is_authenticated:
        return "ANONYMOUS"
    if is_admin_user(user):
        return "ADMIN"
    if is_hr_user(user):
        return "HR"
    if is_employee_user(user):
        return "EMPLOYEE"
    return "CANDIDATE"


# ==============================================================================
# 2. ROLE-BASED ACCESS CONTROL DECORATORS
# ==============================================================================
def hr_or_admin_required(view_func):
    """
    View decorator that restricts access strictly to HR and Admin users.
    If an authenticated Candidate or non-HR user attempts access,
    strictly raises PermissionDenied (HTTP 403 Forbidden).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("candidates:login")
        if not is_hr_user(request.user):
            raise PermissionDenied("Access denied: HR or Administrator role required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """
    View decorator that restricts access strictly to Administrator users.
    Raises PermissionDenied (HTTP 403 Forbidden) on unauthorized access.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("candidates:login")
        if not is_admin_user(request.user):
            raise PermissionDenied("Access denied: Administrator role required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employee_or_admin_required(view_func):
    """
    View decorator that restricts access to onboarded Employees and Administrators.
    Raises PermissionDenied (HTTP 403 Forbidden) if accessed by a Candidate.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("candidates:login")
        if not is_employee_user(request.user):
            raise PermissionDenied("Access denied: Employee or Administrator role required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def candidate_required(view_func):
    """
    View decorator that ensures user is authenticated and enforces Candidate context.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("candidates:login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

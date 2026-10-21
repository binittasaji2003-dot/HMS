from django.conf import settings
from django.utils import timezone


def allauth_settings(request):
    """Expose some settings from django-allauth in templates."""
    return {
        "ACCOUNT_ALLOW_REGISTRATION": settings.ACCOUNT_ALLOW_REGISTRATION,
    }


def birthday_greeting(request):
    """
    Check if the authenticated user should receive a birthday greeting popup today.
    Conditions:
    1. User is authenticated.
    2. User is NOT Admin (or superuser / staff).
    3. User is an Employee or HR Manager.
    4. User has filled their profile with date_of_birth.
    5. TODAY is their birthday (same month and day).
    6. User has not already dismissed the birthday popup today in this session.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"show_birthday_popup": False}

    # Admin is strictly excluded
    role = getattr(user, "role", None)
    if role == "Admin" or getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return {"show_birthday_popup": False}

    # Only Employee and HR roles
    if role not in ["Employee", "HR"]:
        return {"show_birthday_popup": False}

    # Extract date_of_birth from profile
    dob = None
    if role == "Employee":
        emp = getattr(user, "employee_profile", None)
        if emp:
            dob = emp.date_of_birth or (getattr(emp, "candidate", None) and emp.candidate.date_of_birth)
    elif role == "HR":
        hr = getattr(user, "hr_profile", None)
        if hr:
            dob = hr.date_of_birth

    if not dob:
        return {"show_birthday_popup": False}

    today = timezone.localdate()
    is_bday = (dob.month == today.month and dob.day == today.day)
    if not is_bday:
        return {"show_birthday_popup": False}

    # Check if already dismissed today
    today_str = today.isoformat()
    if request.session.get("birthday_dismissed_date") == today_str:
        return {"show_birthday_popup": False}

    name = user.name or user.email.split("@")[0]
    if hasattr(user, "employee_profile") and getattr(user.employee_profile, "candidate", None):
        cand = user.employee_profile.candidate
        if cand.first_name:
            name = f"{cand.first_name} {cand.last_name}".strip()

    return {
        "show_birthday_popup": True,
        "birthday_user_name": name,
    }

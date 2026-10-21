from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import resolve_url

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from hr_management_system.users.models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def get_login_redirect_url(self, request: HttpRequest) -> str:
        user = request.user
        role = getattr(user, "role", "")

        # 1. Administrator
        if role == "Admin" or (user.is_superuser and role != "HR"):
            return resolve_url("admin_module:admin_dashboard")

        # 2. HR Manager
        if role == "HR" or hasattr(user, "hr_profile"):
            return resolve_url("hr:dashboard")

        # 3. Employee
        if role == "Employee" or (hasattr(user, "employee_profile") and role != "Candidate"):
            return resolve_url("employees:dashboard")

        # 4. Candidate
        if role == "Candidate" or hasattr(user, "candidate_profile"):
            return resolve_url("candidates:dashboard")

        # Fallback for staff / superuser
        if user.is_superuser or user.is_staff:
            return resolve_url("admin_module:admin_dashboard")

        if hasattr(user, "employee_profile"):
            return resolve_url("employees:dashboard")

        return resolve_url("home")


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def get_login_redirect_url(self, request: HttpRequest) -> str:
        user = request.user
        role = getattr(user, "role", "")

        # 1. Administrator
        if role == "Admin" or (user.is_superuser and role != "HR"):
            return resolve_url("admin_module:admin_dashboard")

        # 2. HR Manager
        if role == "HR" or hasattr(user, "hr_profile"):
            return resolve_url("hr:dashboard")

        # 3. Employee
        if role == "Employee" or (hasattr(user, "employee_profile") and role != "Candidate"):
            return resolve_url("employees:dashboard")

        # 4. Candidate
        if role == "Candidate" or hasattr(user, "candidate_profile"):
            return resolve_url("candidates:dashboard")

        # Fallback for staff / superuser
        if user.is_superuser or user.is_staff:
            return resolve_url("admin_module:admin_dashboard")

        if hasattr(user, "employee_profile"):
            return resolve_url("employees:dashboard")

        return resolve_url("home")

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user

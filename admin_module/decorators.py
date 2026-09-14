from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse


User = get_user_model()


def admin_required(view_func):
    """
    Require the current user to be an authenticated,
    active System Administrator.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(
                request,
                "Please log in with your Admin credentials "
                "to access the Admin Dashboard.",
            )
            return redirect(
                f"{reverse('admin_module:admin_login')}?next={request.path}"
            )

        user_role = getattr(request.user, "role", None)
        user_status = getattr(request.user, "status", None)

        if user_role != User.RoleChoices.ADMIN:
            messages.error(
                request,
                "Access denied: You do not have Administrator permissions.",
            )
            return redirect("admin_module:admin_login")

        if (
            user_status != User.StatusChoices.ACTIVE
            or not request.user.is_active
        ):
            messages.error(
                request,
                "Access denied: Your Administrator account is not active.",
            )
            return redirect("admin_module:admin_login")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


class AdminRequiredMixin(AccessMixin):
    """
    Verify that the current user is authenticated,
    has the Admin role, and has an active account.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(
                request,
                "Please log in with your Admin credentials "
                "to continue.",
            )
            return redirect(
                f"{reverse('admin_module:admin_login')}?next={request.path}"
            )

        user_role = getattr(request.user, "role", None)
        user_status = getattr(request.user, "status", None)

        if (
            user_role != User.RoleChoices.ADMIN
            or user_status != User.StatusChoices.ACTIVE
            or not request.user.is_active
        ):
            messages.error(
                request,
                "Access restricted to active Administrators only.",
            )
            return redirect("admin_module:admin_login")

        return super().dispatch(request, *args, **kwargs)
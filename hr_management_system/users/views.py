from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from hr_management_system.users.models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        user = self.request.user
        if user.is_superuser or user.is_staff or getattr(user, "role", "") == User.RoleChoices.ADMIN:
            return reverse("admin:index")
        if getattr(user, "role", "") == User.RoleChoices.HR or hasattr(user, "hr_profile"):
            return reverse("hr:dashboard")
        if getattr(user, "role", "") == User.RoleChoices.CANDIDATE or hasattr(user, "candidate_profile"):
            return reverse("candidates:dashboard")
        if hasattr(user, "employee_profile") or getattr(user, "role", "") == User.RoleChoices.EMPLOYEE:
            return reverse("employees:dashboard")
        return reverse("users:detail", kwargs={"pk": user.pk})


user_redirect_view = UserRedirectView.as_view()

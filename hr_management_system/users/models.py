from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models import EmailField
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for HR Management System.
    """

    class RoleChoices(models.TextChoices):
        ADMIN = "Admin", _("Admin")
        HR = "HR", _("HR Manager")
        EMPLOYEE = "Employee", _("Employee")
        CANDIDATE = "Candidate", _("Candidate")

    class StatusChoices(models.TextChoices):
        ACTIVE = "Active", _("Active")
        INACTIVE = "Inactive", _("Inactive")
        PENDING = "Pending", _("Pending")

    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
    )
    status = CharField(
        _("Status"),
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = _("user")
        verbose_name_plural = _("users")

        constraints = [
            models.UniqueConstraint(
                fields=["role"],
                condition=Q(role="Admin"),
                name="only_one_admin_user",
            ),
        ]

    @property
    def is_birthday_today(self) -> bool:
        """Check if today is the user's birthday.
        - Strictly excluded for Admin.
        - Applicable only for Employee and HR roles with date_of_birth set.
        - True only on their actual birthday.
        """
        if not self.is_authenticated:
            return False
        if self.role == self.RoleChoices.ADMIN or self.is_superuser or self.is_staff:
            return False
        if self.role not in [self.RoleChoices.EMPLOYEE, self.RoleChoices.HR]:
            return False

        dob = None
        if self.role == self.RoleChoices.EMPLOYEE:
            emp = getattr(self, "employee_profile", None)
            if emp:
                dob = emp.date_of_birth or (getattr(emp, "candidate", None) and emp.candidate.date_of_birth)
        elif self.role == self.RoleChoices.HR:
            hr = getattr(self, "hr_profile", None)
            if hr:
                dob = hr.date_of_birth

        if not dob:
            return False

        from django.utils import timezone
        today = timezone.localdate()
        return bool(dob.month == today.month and dob.day == today.day)

    def is_admin_role(self) -> bool:
        return self.role == self.RoleChoices.ADMIN and self.status == self.StatusChoices.ACTIVE

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})

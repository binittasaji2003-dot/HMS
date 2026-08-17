from django.conf import settings
from django.db import models


class Department(models.Model):
    department_id = models.AutoField(primary_key=True)

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_departments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.name


class Announcement(models.Model):
    ANNOUNCEMENT_TYPES = [
        ("GENERAL", "General"),
        ("HOLIDAY", "Holiday"),
        ("NOTICE", "Notice"),
        ("HR", "HR Notice"),
    ]

    announcement_id = models.AutoField(primary_key=True)

    title = models.CharField(
        max_length=200,
    )

    content = models.TextField()

    announcement_type = models.CharField(
        max_length=20,
        choices=ANNOUNCEMENT_TYPES,
        default="GENERAL",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_announcements",
    )

    is_published = models.BooleanField(
        default=False,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.title


class EmployeeApproval(models.Model):
    """
    Admin approval of an employee created from a selected candidate.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    approval_id = models.AutoField(primary_key=True)

    employee = models.OneToOneField(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="admin_approval",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_approvals",
    )

    comments = models.TextField(
        blank=True,
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.employee.employee_code} - {self.status}"
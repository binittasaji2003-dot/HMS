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
        blank=True,
        related_name="created_departments",
    )

    department_leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_departments",
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

    target_audience = models.CharField(
        max_length=50,
        default="All",
)

    is_active = models.BooleanField(
        default=True,
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

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_employee_approvals",
    )

    comments = models.TextField(
        blank=True,
    )

    rejection_reason = models.TextField(
        blank=True,
        default="",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.employee.employee_code} - {self.status}"


class Holiday(models.Model):
    HOLIDAY_TYPE_CHOICES = [
        ("PUBLIC", "Public Holiday"),
        ("RESTRICTED", "Restricted Holiday"),
        ("COMPANY", "Company Holiday"),
    ]

    holiday_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    date = models.DateField()
    holiday_type = models.CharField(max_length=30, choices=HOLIDAY_TYPE_CHOICES, default="PUBLIC")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return f"{self.name} ({self.date})"


class AdminNotification(models.Model):
    NOTIFICATION_TYPES = [
        ("HR_REPORT_SUBMITTED", "HR Weekly Report Submitted"),
        ("EMPLOYEE_APPROVAL", "New Employee Approval Pending"),
        ("HR_RECOMMENDATION", "HR Recommendation Submitted"),
        ("GENERAL", "General Notification"),
    ]

    notification_id = models.AutoField(primary_key=True)
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="admin_notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=40,
        choices=NOTIFICATION_TYPES,
        default="GENERAL",
    )
    link_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Admin Notification: {self.title}"


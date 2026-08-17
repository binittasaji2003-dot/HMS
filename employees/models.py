from django.conf import settings
from django.db import models


class Employee(models.Model):
    EMPLOYMENT_STATUS = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("ON_LEAVE", "On Leave"),
        ("TERMINATED", "Terminated"),
    ]

    employee_id = models.AutoField(
        primary_key=True,
    )

    # Employee login account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )

    # Original candidate who was selected
    candidate = models.OneToOneField(
        "candidates.Candidate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_record",
    )

    employee_code = models.CharField(
        max_length=30,
        unique=True,
    )

    # These are company/employment details
    department = models.ForeignKey(
        "admin_module.Department",
        on_delete=models.PROTECT,
        related_name="employees",
    )

    designation = models.CharField(
        max_length=100,
    )

    joining_date = models.DateField()

    employment_status = models.CharField(
        max_length=30,
        choices=EMPLOYMENT_STATUS,
        default="ACTIVE",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_employees",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.employee_code} - {self.user.get_username()}"


class EmployeeDocument(models.Model):
    DOCUMENT_TYPES = [
        ("ID_PROOF", "ID Proof"),
        ("TENTH_CERTIFICATE", "10th Certificate"),
        ("TENTH_MARKLIST", "10th Marklist"),
        ("TWELFTH_CERTIFICATE", "12th Certificate"),
        ("TWELFTH_MARKLIST", "12th Marklist"),
        ("EXPERIENCE_CERTIFICATE", "Experience Certificate"),
        ("OTHER", "Other"),
    ]

    document_id = models.AutoField(
        primary_key=True,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
    )

    document = models.FileField(
        upload_to="employees/documents/",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.employee.employee_code} - "
            f"{self.get_document_type_display()}"
        )


class EmployeeReport(models.Model):
    REPORT_STATUS = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("REVIEWED", "Reviewed"),
        ("NEEDS_CORRECTION", "Needs Correction"),
    ]

    report_id = models.AutoField(
        primary_key=True,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    week_start_date = models.DateField()

    week_end_date = models.DateField()

    work_summary = models.TextField()

    tasks_completed = models.TextField()

    achievements = models.TextField(
        blank=True,
    )

    challenges = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=REPORT_STATUS,
        default="SUBMITTED",
    )

    reviewed_by = models.ForeignKey(
        "hr.HRManager",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_employee_reports",
    )

    hr_comments = models.TextField(
        blank=True,
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.employee.employee_code} - "
            f"{self.week_start_date}"
        )


class EmployeePerformance(models.Model):
    RATING_CHOICES = [
        ("EXCELLENT", "Excellent"),
        ("GOOD", "Good"),
        ("AVERAGE", "Average"),
        ("NEEDS_IMPROVEMENT", "Needs Improvement"),
    ]

    performance_id = models.AutoField(
        primary_key=True,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="performance_reviews",
    )

    reviewed_by = models.ForeignKey(
        "hr.HRManager",
        on_delete=models.SET_NULL,
        null=True,
        related_name="employee_performance_reviews",
    )

    review_period = models.CharField(
        max_length=50,
    )

    rating = models.CharField(
        max_length=30,
        choices=RATING_CHOICES,
    )

    comments = models.TextField(
        blank=True,
    )

    review_date = models.DateField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.employee.employee_code} - "
            f"{self.get_rating_display()}"
        )


class PerformanceWarning(models.Model):
    ADMIN_DECISION_CHOICES = [
        ("CONTINUE", "Continue Employment"),
        ("ANOTHER_WARNING", "Another Warning"),
        ("TERMINATION", "Termination"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("SENT_TO_ADMIN", "Sent to Admin"),
        ("RESOLVED", "Resolved"),
    ]

    warning_id = models.AutoField(
        primary_key=True,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="performance_warnings",
    )

    performance = models.ForeignKey(
        EmployeePerformance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="warnings",
    )

    issued_by = models.ForeignKey(
        "hr.HRManager",
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_warnings",
    )

    warning_date = models.DateField(
        auto_now_add=True,
    )

    reason = models.TextField()

    hr_recommendation = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    admin_decision = models.CharField(
        max_length=30,
        choices=ADMIN_DECISION_CHOICES,
        null=True,
        blank=True,
    )

    admin_comments = models.TextField(
        blank=True,
    )

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_warning_decisions",
    )

    decision_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Warning - {self.employee.employee_code}"
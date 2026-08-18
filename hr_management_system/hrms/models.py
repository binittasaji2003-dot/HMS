from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """Departments table representing organizational units."""

    name = models.CharField(_("Department Name"), max_length=150, unique=True)
    description = models.TextField(_("Description"), blank=True, default="")
    status = models.CharField(
        _("Status"),
        max_length=50,
        choices=[("Active", "Active"), ("Inactive", "Inactive")],
        default="Active",
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "departments"
        ordering = ["name"]
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def __str__(self) -> str:
        return self.name


class HRManager(models.Model):
    """HR Managers profile table linking user accounts with department management."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hrms_hr_profile",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_managers",
    )
    phone = models.CharField(_("Phone Number"), max_length=30, blank=True, default="")
    office_location = models.CharField(_("Office Location"), max_length=150, blank=True, default="")
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "hr_managers"
        verbose_name = _("HR Manager")
        verbose_name_plural = _("HR Managers")

    def __str__(self) -> str:
        return f"{self.user.name or self.user.email} (HR)"


class JobVacancy(models.Model):
    """Job Vacancies table for hiring and job postings."""

    class StatusChoices(models.TextChoices):
        OPEN = "Open", _("Open")
        CLOSED = "Closed", _("Closed")
        DRAFT = "Draft", _("Draft")
        ON_HOLD = "On Hold", _("On Hold")

    title = models.CharField(_("Job Title"), max_length=200)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="vacancies",
    )
    description = models.TextField(_("Job Description"))
    requirements = models.TextField(_("Requirements"), blank=True, default="")
    openings_count = models.PositiveIntegerField(_("Openings Count"), default=1)
    status = models.CharField(
        _("Status"),
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_vacancies",
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "job_vacancies"
        ordering = ["-created_at"]
        verbose_name = _("Job Vacancy")
        verbose_name_plural = _("Job Vacancies")

    def __str__(self) -> str:
        return f"{self.title} - {self.department.name} ({self.status})"


class Candidate(models.Model):
    """Candidates table for applicant tracking."""

    class StatusChoices(models.TextChoices):
        APPLIED = "Applied", _("Applied")
        SHORTLISTED = "Shortlisted", _("Shortlisted")
        INTERVIEWING = "Interviewing", _("Interviewing")
        SELECTED = "Selected", _("Selected")
        REJECTED = "Rejected", _("Rejected")
        HIRED = "Hired", _("Hired")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidate_applications",
    )
    job_vacancy = models.ForeignKey(
        JobVacancy,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    full_name = models.CharField(_("Full Name"), max_length=200)
    email = models.EmailField(_("Email Address"))
    phone = models.CharField(_("Phone Number"), max_length=30, blank=True, default="")
    resume = models.FileField(_("Resume Document"), upload_to="resumes/", blank=True, null=True)
    experience_years = models.DecimalField(_("Experience (Years)"), max_digits=4, decimal_places=1, default=0.0)
    status = models.CharField(
        _("Status"),
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.APPLIED,
    )
    applied_at = models.DateTimeField(_("Applied At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "candidates"
        ordering = ["-applied_at"]
        verbose_name = _("Candidate")
        verbose_name_plural = _("Candidates")

    def __str__(self) -> str:
        return f"{self.full_name} - {self.job_vacancy.title} ({self.status})"


class Employee(models.Model):
    """Employees table for internal company workforce."""

    class StatusChoices(models.TextChoices):
        ACTIVE = "Active", _("Active")
        PENDING_APPROVAL = "Pending Approval", _("Pending Approval")
        INACTIVE = "Inactive", _("Inactive")
        ON_LEAVE = "On Leave", _("On Leave")
        TERMINATED = "Terminated", _("Terminated")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hrms_employee_profile",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    designation = models.CharField(_("Designation"), max_length=150)
    date_of_joining = models.DateField(_("Date of Joining"), null=True, blank=True)
    salary = models.DecimalField(_("Salary"), max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "employees"
        ordering = ["-created_at"]
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")

    def __str__(self) -> str:
        return f"{self.user.name or self.user.email} - {self.designation}"


class EmployeePerformance(models.Model):
    """Employee Performance appraisals and scoring."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="performance_reviews",
    )
    review_period = models.CharField(_("Review Period"), max_length=100)
    rating = models.DecimalField(_("Performance Rating (1-5)"), max_digits=3, decimal_places=1)
    feedback = models.TextField(_("Review Feedback"))
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="given_performance_reviews",
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "employee_performance"
        ordering = ["-created_at"]
        verbose_name = _("Employee Performance")
        verbose_name_plural = _("Employee Performances")

    def __str__(self) -> str:
        return f"{self.employee.user.name or self.employee.user.email} - {self.review_period}: {self.rating}/5"


class PerformanceWarning(models.Model):
    """Performance Warnings issued to employees."""

    class SeverityChoices(models.TextChoices):
        LOW = "Low", _("Low")
        MEDIUM = "Medium", _("Medium")
        HIGH = "High", _("High")
        CRITICAL = "Critical", _("Critical")

    class StatusChoices(models.TextChoices):
        PENDING = "Pending", _("Pending")
        ACTIVE = "Active", _("Active")
        ACKNOWLEDGED = "Acknowledged", _("Acknowledged")
        RESOLVED = "Resolved", _("Resolved")

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="warnings",
    )
    title = models.CharField(_("Warning Subject"), max_length=200)
    reason = models.TextField(_("Reason / Details"))
    severity = models.CharField(
        _("Severity"),
        max_length=50,
        choices=SeverityChoices.choices,
        default=SeverityChoices.MEDIUM,
    )
    status = models.CharField(
        _("Status"),
        max_length=50,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_warnings",
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "performance_warnings"
        ordering = ["-created_at"]
        verbose_name = _("Performance Warning")
        verbose_name_plural = _("Performance Warnings")

    def __str__(self) -> str:
        return f"Warning: {self.title} - {self.employee.user.name or self.employee.user.email} ({self.status})"


class Announcement(models.Model):
    """Announcements table for organization-wide or role-specific broadcast messages."""

    class AudienceChoices(models.TextChoices):
        ALL = "All", _("All")
        HR = "HR", _("HR Managers")
        EMPLOYEES = "Employees", _("Employees")
        CANDIDATES = "Candidates", _("Candidates")

    title = models.CharField(_("Announcement Title"), max_length=200)
    content = models.TextField(_("Content"))
    target_audience = models.CharField(
        _("Target Audience"),
        max_length=50,
        choices=AudienceChoices.choices,
        default=AudienceChoices.ALL,
    )
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="announcements",
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        db_table = "announcements"
        ordering = ["-created_at"]
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")

    def __str__(self) -> str:
        return f"{self.title} ({self.target_audience})"

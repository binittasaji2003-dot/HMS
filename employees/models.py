from django.conf import settings
from django.db import models


class Team(models.Model):
    team_id = models.AutoField(primary_key=True)
    team_name = models.CharField(max_length=100)
    department = models.ForeignKey(
        "admin_module.Department",
        on_delete=models.CASCADE,
        related_name="teams",
    )
    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["team_name"]

    def __str__(self):
        return f"{self.team_name} ({self.department.name})"


class Employee(models.Model):
    EMPLOYMENT_STATUS = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("ON_LEAVE", "On Leave"),
        ("TERMINATED", "Terminated"),
    ]

    EMPLOYMENT_TYPES = [
        ("FULL_TIME", "Full Time"),
        ("PART_TIME", "Part Time"),
        ("CONTRACT", "Contract"),
        ("INTERN", "Intern"),
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

    profile_photo = models.ImageField(
        upload_to="employees/profile_photos/",
        null=True,
        blank=True,
    )

    # Personal details
    first_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )
    gender = models.CharField(
        max_length=20,
        choices=[("MALE", "Male"), ("FEMALE", "Female"), ("OTHER", "Other")],
        blank=True,
        default="",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
    )
    personal_email = models.EmailField(
        blank=True,
        default="",
    )
    address = models.TextField(
        blank=True,
        default="",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    pincode = models.CharField(
        max_length=20,
        blank=True,
        default="",
    )

    # Employment details
    department = models.ForeignKey(
        "admin_module.Department",
        on_delete=models.PROTECT,
        related_name="employees",
    )

    team = models.ForeignKey(
        "employees.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )

    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_employees",
    )

    designation = models.CharField(
        max_length=100,
    )

    joining_date = models.DateField()

    employment_type = models.CharField(
        max_length=30,
        choices=EMPLOYMENT_TYPES,
        default="FULL_TIME",
    )

    employment_status = models.CharField(
        max_length=30,
        choices=EMPLOYMENT_STATUS,
        default="ACTIVE",
    )

    work_location = models.CharField(
        max_length=150,
        blank=True,
        default="",
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
        return f"{self.employee_code} - {self.full_name}"

    @property
    def full_name(self):
        name = f"{self.first_name} {self.middle_name} {self.last_name}".replace("  ", " ").strip()
        if name:
            return name
        if self.user:
            return getattr(self.user, "name", "") or self.user.email
        return f"Employee {self.employee_code}"

    @property
    def team_lead_name(self):
        if self.team_lead:
            return getattr(self.team_lead, "name", "") or self.team_lead.get_username()
        if self.team and self.team.team_lead:
            return getattr(self.team.team_lead, "name", "") or self.team.team_lead.get_username()
        return "Not Assigned"

    def sync_from_candidate_if_empty(self):
        if self.candidate:
            changed = False
            if not self.first_name and self.candidate.first_name:
                self.first_name = self.candidate.first_name
                changed = True
            if not self.middle_name and self.candidate.middle_name:
                self.middle_name = self.candidate.middle_name
                changed = True
            if not self.last_name and self.candidate.last_name:
                self.last_name = self.candidate.last_name
                changed = True
            if not self.date_of_birth and self.candidate.date_of_birth:
                self.date_of_birth = self.candidate.date_of_birth
                changed = True
            if not self.phone and self.candidate.phone:
                self.phone = self.candidate.phone
                changed = True
            if not self.address and self.candidate.address:
                self.address = self.candidate.address
                changed = True
            if not self.profile_photo and self.candidate.profile_photo:
                self.profile_photo = self.candidate.profile_photo
                changed = True
            if changed:
                self.save()

    @property
    def is_team_lead(self):
        """Check if this employee leads any active team or active employees."""
        if not self.user:
            return False
        return (
            self.user.led_employees.filter(employment_status="ACTIVE").exclude(pk=self.pk).exists()
            or self.user.led_teams.filter(is_active=True).exists()
            or Employee.objects.filter(team_lead=self.user, employment_status="ACTIVE").exclude(pk=self.pk).exists()
        )

    def get_or_create_leave_balance(self, year=None):
        if not year:
            from django.utils import timezone
            year = timezone.now().year
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=self,
            leave_year=year,
            defaults={"total_entitlement": 15},
        )
        return balance

    @property
    def educations(self):
        return self.education_records.all()

    @property
    def experiences(self):
        return self.experience_records.all()


class EmployeeEducation(models.Model):
    education_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="education_records",
    )
    degree = models.CharField(
        max_length=150,
        help_text="Degree / Qualification (e.g. MCA, BCA, B.Tech, MBA)",
    )
    institution = models.CharField(
        max_length=200,
        help_text="School / College / Institute Name",
    )
    university_board = models.CharField(
        max_length=200,
        help_text="University or Board Name",
    )
    year_of_passing = models.PositiveIntegerField(
        help_text="Passing Year (e.g. 2025)",
    )
    grade_percentage = models.CharField(
        max_length=50,
        help_text="Grade / Percentage / CGPA (e.g. 8.5 CGPA or 85%)",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-year_of_passing", "-created_at"]

    def __str__(self):
        return f"{self.degree} - {self.institution} ({self.year_of_passing})"


class EmployeeExperience(models.Model):
    experience_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="experience_records",
    )
    company_name = models.CharField(
        max_length=200,
    )
    designation = models.CharField(
        max_length=150,
    )
    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
    )
    is_current = models.BooleanField(
        default=False,
    )
    responsibilities = models.TextField(
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return f"{self.designation} at {self.company_name}"


class EmployeeDocument(models.Model):
    DOCUMENT_TYPES = [
        ("ID_PROOF", "ID Proof"),
        ("TENTH_CERTIFICATE", "10th Certificate"),
        ("TENTH_MARKLIST", "10th Marklist"),
        ("TWELFTH_CERTIFICATE", "12th Certificate"),
        ("TWELFTH_MARKLIST", "12th Marklist"),
        ("DEGREE_CERTIFICATE", "Degree Certificate"),
        ("EXPERIENCE_CERTIFICATE", "Experience Certificate"),
        ("RESUME", "Resume / CV"),
        ("OTHER", "Other Document"),
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
        return f"{self.employee.employee_code} - {self.get_document_type_display()}"


class EmployeeReport(models.Model):
    REPORT_STATUS = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("REVIEWED", "Reviewed"),
        ("NEEDS_CORRECTION", "Needs Improvement"),
    ]
    PROGRESS_STATUS_CHOICES = [
        ("ON_TRACK", "On Track"),
        ("AHEAD", "Ahead of Schedule"),
        ("DELAYED", "Delayed"),
        ("BLOCKED", "Blocked"),
        ("COMPLETED", "Completed"),
        ("IN_PROGRESS", "In Progress"),
        ("NOT_STARTED", "Not Started"),
        ("MOSTLY_COMPLETED", "Mostly Completed"),
    ]

    report_id = models.AutoField(
        primary_key=True,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    title = models.CharField(
        max_length=200,
        default="Weekly Work Report",
    )

    week_start_date = models.DateField()

    week_end_date = models.DateField()

    work_summary = models.TextField()

    tasks_completed = models.TextField()

    achievements = models.TextField(
        blank=True,
        default="",
    )

    challenges = models.TextField(
        blank=True,
        default="",
    )

    challenges_handling = models.TextField(
        blank=True,
        default="",
    )

    pending_tasks = models.TextField(
        blank=True,
        default="",
    )

    next_week_plan = models.TextField(
        blank=True,
        default="",
    )

    skills_technologies_used = models.TextField(
        blank=True,
        default="",
    )

    additional_comments = models.TextField(
        blank=True,
        default="",
    )

    progress_status = models.CharField(
        max_length=30,
        choices=PROGRESS_STATUS_CHOICES,
        default="COMPLETED",
    )

    declaration_accepted = models.BooleanField(
        default=False,
        help_text="Employee declaration of accurate work reporting",
    )

    status = models.CharField(
        max_length=30,
        choices=REPORT_STATUS,
        default="DRAFT",
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
        default="",
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.employee.employee_code} - {self.title} ({self.week_start_date})"


class PerformanceReview(models.Model):
    review_id = models.AutoField(
        primary_key=True,
    )

    employee_report = models.OneToOneField(
        EmployeeReport,
        on_delete=models.CASCADE,
        related_name="performance_review",
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="evaluation_reviews",
    )

    reviewed_by = models.ForeignKey(
        "hr.HRManager",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_performance_reviews",
    )

    # 8 Performance Criteria (1-5 Star Ratings) + Remarks
    task_completion = models.PositiveSmallIntegerField(
        default=5,
    )
    task_completion_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    quality_of_work = models.PositiveSmallIntegerField(
        default=5,
    )
    quality_of_work_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    technical_skills = models.PositiveSmallIntegerField(
        default=5,
    )
    technical_skills_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    problem_solving = models.PositiveSmallIntegerField(
        default=5,
    )
    problem_solving_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    timeliness = models.PositiveSmallIntegerField(
        default=5,
    )
    timeliness_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    team_collaboration = models.PositiveSmallIntegerField(
        default=5,
    )
    team_collaboration_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    communication = models.PositiveSmallIntegerField(
        default=5,
    )
    communication_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    goal_achievement = models.PositiveSmallIntegerField(
        default=5,
    )
    goal_achievement_remarks = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    # Calculated Scores
    total_score = models.PositiveSmallIntegerField(
        default=40,
    )
    average_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=5.00,
    )
    performance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
    )

    # Qualitative Written Feedback
    overall_feedback = models.TextField(
        blank=True,
        default="",
    )
    strengths = models.TextField(
        blank=True,
        default="",
    )
    areas_for_improvement = models.TextField(
        blank=True,
        default="",
    )
    recommendations = models.TextField(
        blank=True,
        default="",
    )
    next_week_expectations = models.TextField(
        blank=True,
        default="",
    )

    reviewed_at = models.DateTimeField(
        auto_now_add=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-reviewed_at"]

    def calculate_scores(self):
        ratings = [
            self.task_completion,
            self.quality_of_work,
            self.technical_skills,
            self.problem_solving,
            self.timeliness,
            self.team_collaboration,
            self.communication,
            self.goal_achievement,
        ]
        self.total_score = sum(ratings)
        self.average_score = round(sum(ratings) / 8.0, 2)
        self.performance_percentage = round((self.total_score / 40.0) * 100.0, 2)

    def save(self, *args, **kwargs):
        self.calculate_scores()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review #{self.review_id} for {self.employee.employee_code} ({self.average_score}/5)"


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

    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=4.3,
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
        return f"{self.employee.employee_code} - {self.get_rating_display()}"


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


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("REPORT_REMINDER", "Weekly Report Reminder"),
        ("HR_FEEDBACK", "HR Feedback"),
        ("WARNING", "Performance Warning"),
        ("ANNOUNCEMENT", "Company Announcement"),
        ("PROFILE_UPDATE", "Profile Update"),
        ("LEAVE_REQUEST", "Leave Request"),
        ("LEAVE_APPROVED", "Leave Approved"),
        ("LEAVE_REJECTED", "Leave Rejected"),
        ("LEAVE_CANCELLED", "Leave Cancelled"),
    ]

    notification_id = models.AutoField(
        primary_key=True,
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    title = models.CharField(
        max_length=200,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default="REPORT_REMINDER",
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.employee.employee_code} - {self.title}"


class LeaveType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_balances",
    )
    leave_year = models.PositiveIntegerField(
        help_text="Calendar year for leave entitlement (e.g. 2026)",
    )
    total_entitlement = models.PositiveIntegerField(
        default=15,
        help_text="Annual leave entitlement (default 15 days)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-leave_year"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "leave_year"],
                name="unique_employee_leave_year",
            )
        ]

    def __str__(self):
        return f"{self.employee.employee_code} ({self.leave_year}) - {self.remaining_days}/{self.total_entitlement} Days"

    @property
    def approved_requests(self):
        return self.employee.leave_requests.filter(
            start_date__year=self.leave_year,
            status="APPROVED",
        )

    @property
    def taken_days(self):
        from django.db.models import Sum
        val = self.approved_requests.aggregate(total=Sum("number_of_days"))["total"]
        return val or 0

    @property
    def pending_requests(self):
        return self.employee.leave_requests.filter(
            start_date__year=self.leave_year,
            status="PENDING",
        )

    @property
    def pending_requests_count(self):
        return self.pending_requests.count()

    @property
    def pending_days(self):
        from django.db.models import Sum
        val = self.pending_requests.aggregate(total=Sum("number_of_days"))["total"]
        return val or 0

    @property
    def rejected_requests(self):
        return self.employee.leave_requests.filter(
            start_date__year=self.leave_year,
            status="REJECTED",
        )

    @property
    def rejected_requests_count(self):
        return self.rejected_requests.count()

    @property
    def remaining_days(self):
        return max(0, self.total_entitlement - self.taken_days)


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="leave_requests",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_days = models.PositiveIntegerField()
    reason = models.TextField()
    declaration_accepted = models.BooleanField(
        default=False,
        help_text="Employee declaration agreement acceptance",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approver_leave_requests",
        help_text="Assigned Team Lead or Manager to review",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leave_requests",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_leave_requests",
    )
    rejection_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.employee.employee_code} - {self.leave_type.name} ({self.start_date} to {self.end_date}) [{self.get_status_display()}]"

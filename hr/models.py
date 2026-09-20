from django.conf import settings
from django.db import models


class HRManager(models.Model):
    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]

    hr_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hr_profile",
    )

    # Personal Information
    first_name = models.CharField(
        max_length=100,
        blank=True,
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
    )
    address = models.TextField(
        blank=True,
    )
    city = models.CharField(
        max_length=100,
        blank=True,
    )
    state = models.CharField(
        max_length=100,
        blank=True,
    )
    pincode = models.CharField(
        max_length=20,
        blank=True,
    )
    profile_photo = models.ImageField(
        upload_to="hr/profile_photos/",
        null=True,
        blank=True,
    )

    # Professional Information
    employee_code = models.CharField(
        max_length=30,
        unique=True,
    )
    designation = models.CharField(
        max_length=100,
        default="HR Manager",
        blank=True,
    )
    department = models.ForeignKey(
        "admin_module.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_managers",
    )
    joining_date = models.DateField(
        null=True,
        blank=True,
    )
    reporting_manager = models.CharField(
        max_length=150,
        blank=True,
        help_text="Reporting Manager / HR Lead",
    )

    # Experience & Completion Status
    has_no_experience = models.BooleanField(
        default=False,
        help_text="Indicates whether the HR Manager has no prior work experience (Fresher)",
    )
    profile_completed = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        combined = " ".join([p for p in parts if p]).strip()
        if combined:
            return combined
        if self.user:
            return self.user.name or self.user.email
        return f"HR Manager #{self.hr_id}"

    @property
    def completion_percentage(self):
        score = 0
        total_parts = 5
        # 1. Personal details
        if self.first_name and self.last_name and self.phone and self.date_of_birth:
            score += 1
        # 2. Address
        if self.address or self.city:
            score += 1
        # 3. Education
        if self.education_records.exists():
            score += 1
        # 4. Experience
        if self.has_no_experience or self.experience_records.exists():
            score += 1
        # 5. Documents
        if self.documents.exists():
            score += 1
        return int((score / total_parts) * 100)

    def update_profile_completion_status(self):
        """Calculates and updates profile_completed boolean flag."""
        has_personal = bool(self.first_name and self.last_name and self.phone and self.date_of_birth)
        has_address = bool(self.address or (self.city and self.state))
        has_education = self.education_records.exists()
        has_experience = self.has_no_experience or self.experience_records.exists()
        has_document = self.documents.exists()

        is_complete = bool(has_personal and has_address and has_education and has_experience and has_document)
        if self.profile_completed != is_complete:
            self.profile_completed = is_complete
            self.save(update_fields=["profile_completed"])
        return is_complete

    def __str__(self):
        return self.full_name or self.user.get_username()


class HREducation(models.Model):
    education_id = models.AutoField(primary_key=True)
    hr = models.ForeignKey(
        HRManager,
        on_delete=models.CASCADE,
        related_name="education_records",
    )
    degree = models.CharField(
        max_length=150,
        help_text="Degree / Qualification (e.g., MBA HR, B.Tech, BBA, M.Com)",
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
        help_text="Passing Year (e.g., 2021)",
    )
    grade_percentage = models.CharField(
        max_length=50,
        help_text="Grade / Percentage / CGPA (e.g., 85% or 8.5 CGPA)",
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


class HRExperience(models.Model):
    experience_id = models.AutoField(primary_key=True)
    hr = models.ForeignKey(
        HRManager,
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
        help_text="Key responsibilities and achievements",
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


class HRDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ("ID_PROOF", "ID Proof (Aadhaar / Passport / Voter ID / DL)"),
        ("EDUCATIONAL_CERTIFICATE", "Educational Certificate"),
        ("EXPERIENCE_CERTIFICATE", "Experience / Relieving Letter"),
        ("RESUME", "Resume / CV"),
        ("OTHER", "Other Document"),
    ]

    document_id = models.AutoField(primary_key=True)
    hr = models.ForeignKey(
        HRManager,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
        default="OTHER",
    )
    title = models.CharField(
        max_length=200,
        blank=True,
    )
    document_file = models.FileField(
        upload_to="hr/documents/",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.title or self.document_file.name}"



class AptitudeTest(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    test_id = models.AutoField(primary_key=True)

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Duration of the test in minutes",
    )

    total_questions = models.PositiveIntegerField(
        default=15,
        help_text="Number of questions presented to candidates across categories",
    )

    pass_percentage = models.PositiveIntegerField(
        default=50,
        help_text="Passing percentage required",
    )

    created_by = models.ForeignKey(
        HRManager,
        on_delete=models.SET_NULL,
        null=True,
        related_name="aptitude_tests",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.title


class AptitudeQuestion(models.Model):
    CATEGORY_CHOICES = [
        ("QUANTITATIVE", "Quantitative Aptitude"),
        ("LOGICAL", "Logical Reasoning"),
        ("VERBAL", "Verbal Ability"),
    ]

    question_id = models.AutoField(primary_key=True)

    test = models.ForeignKey(
        AptitudeTest,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="QUANTITATIVE",
    )

    question = models.TextField()

    option_a = models.CharField(
        max_length=255,
    )

    option_b = models.CharField(
        max_length=255,
    )

    option_c = models.CharField(
        max_length=255,
    )

    option_d = models.CharField(
        max_length=255,
    )

    correct_answer = models.CharField(
        max_length=1,
        help_text="Choice letter: A, B, C, or D",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["category", "-created_at", "question_id"]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.question[:50]}"

    @property
    def correct_option_text(self):
        mapping = {
            "A": self.option_a,
            "B": self.option_b,
            "C": self.option_c,
            "D": self.option_d,
        }
        return mapping.get(self.correct_answer.upper(), "")


class AptitudeAttempt(models.Model):
    SUBMISSION_TYPES = [
        ("CANDIDATE_SUBMITTED", "Candidate Submitted"),
        ("AUTO_SUBMITTED", "Auto Submitted"),
    ]

    attempt_id = models.AutoField(primary_key=True)

    test = models.ForeignKey(
        AptitudeTest,
        on_delete=models.CASCADE,
        related_name="attempts",
    )

    application = models.ForeignKey(
        "candidates.JobApplication",
        on_delete=models.CASCADE,
        related_name="aptitude_attempts",
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
    )

    expires_at = models.DateTimeField()

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_completed = models.BooleanField(
        default=False,
    )

    submission_type = models.CharField(
        max_length=30,
        choices=SUBMISSION_TYPES,
        default="CANDIDATE_SUBMITTED",
    )

    questions_data = models.JSONField(
        default=list,
        help_text="Randomized question and shuffled option snapshot for this attempt",
    )

    answers_data = models.JSONField(
        default=dict,
        help_text="Candidate submitted answers mapping {question_id: selected_key}",
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Attempt #{self.attempt_id} by {self.application.candidate} - {self.test.title}"


class AptitudeResult(models.Model):
    SUBMISSION_TYPES = [
        ("CANDIDATE_SUBMITTED", "Candidate Submitted"),
        ("AUTO_SUBMITTED", "Auto Submitted"),
    ]

    result_id = models.AutoField(primary_key=True)

    test = models.ForeignKey(
        AptitudeTest,
        on_delete=models.CASCADE,
        related_name="results",
    )

    application = models.ForeignKey(
        "candidates.JobApplication",
        on_delete=models.CASCADE,
        related_name="aptitude_results",
    )

    score = models.PositiveIntegerField()

    total_marks = models.PositiveIntegerField()

    percentage = models.FloatField(
        default=0.0,
    )

    passed = models.BooleanField(
        default=False,
    )

    correct_answers_count = models.PositiveIntegerField(
        default=0,
    )

    incorrect_answers_count = models.PositiveIntegerField(
        default=0,
    )

    unanswered_count = models.PositiveIntegerField(
        default=0,
    )

    submission_type = models.CharField(
        max_length=30,
        choices=SUBMISSION_TYPES,
        default="CANDIDATE_SUBMITTED",
    )

    hr_comments = models.TextField(
        blank=True,
    )

    hr_decision = models.CharField(
        max_length=30,
        blank=True,
    )

    completed_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.application} - {self.score}/{self.total_marks} ({'Pass' if self.passed else 'Fail'})"


class InterviewLocation(models.Model):
    location_id = models.AutoField(primary_key=True)
    location_name = models.CharField(
        max_length=150,
        help_text="e.g. Kochi Office, Trivandrum Office, Bangalore Office",
    )
    address = models.TextField(
        help_text="Full physical street address / floor details",
    )
    city = models.CharField(
        max_length=100,
        default="Kochi",
    )
    state = models.CharField(
        max_length=100,
        default="Kerala",
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    @property
    def name(self):
        return self.location_name

    class Meta:
        ordering = ["location_name"]

    def __str__(self):
        return f"{self.location_name} ({self.city})"


class InterviewSlot(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ("TECHNICAL", "Technical Interview"),
        ("HR", "HR Interview"),
        ("FINAL", "Final Interview"),
    ]

    SLOT_STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("BOOKED", "Booked"),
        ("CANCELLED", "Cancelled"),
    ]

    slot_id = models.AutoField(primary_key=True)

    vacancy = models.ForeignKey(
        "candidates.JobVacancy",
        on_delete=models.CASCADE,
        related_name="interview_slots",
        null=True,
        blank=True,
    )

    interviewer = models.ForeignKey(
        HRManager,
        on_delete=models.CASCADE,
        related_name="interview_slots",
    )

    location = models.ForeignKey(
        InterviewLocation,
        on_delete=models.CASCADE,
        related_name="interview_slots",
    )

    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES,
        default="TECHNICAL",
    )

    interview_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    instructions = models.TextField(
        blank=True,
        help_text="Special instructions for offline venue reporting",
    )

    status = models.CharField(
        max_length=20,
        choices=SLOT_STATUS_CHOICES,
        default="AVAILABLE",
    )

    booked_by = models.ForeignKey(
        "candidates.Candidate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_slots",
    )

    booked_application = models.ForeignKey(
        "candidates.JobApplication",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_slots",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["interview_date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["interviewer", "interview_date", "start_time"],
                name="unique_interviewer_slot",
            )
        ]

    def __str__(self):
        return f"{self.interview_date} {self.start_time.strftime('%I:%M %p')}-{self.end_time.strftime('%I:%M %p')} at {self.location.location_name} ({self.status})"

    @property
    def formatted_time_range(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class Interview(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    ATTENDANCE_CHOICES = [
        ("NOT_MARKED", "Not Marked"),
        ("ATTENDED", "Attended"),
        ("NO_SHOW", "No Show"),
    ]

    INTERVIEW_TYPE_CHOICES = [
        ("TECHNICAL", "Technical Interview"),
        ("HR", "HR Interview"),
        ("FINAL", "Final Interview"),
    ]

    interview_id = models.AutoField(primary_key=True)

    application = models.ForeignKey(
        "candidates.JobApplication",
        on_delete=models.CASCADE,
        related_name="interviews",
    )

    slot = models.ForeignKey(
        InterviewSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interviews",
    )

    location = models.ForeignKey(
        InterviewLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interviews",
    )

    interviewer = models.ForeignKey(
        HRManager,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interviews",
    )

    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES,
        default="TECHNICAL",
    )

    interview_date = models.DateField()

    interview_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SCHEDULED",
    )

    attendance = models.CharField(
        max_length=20,
        choices=ATTENDANCE_CHOICES,
        default="NOT_MARKED",
    )

    instructions = models.TextField(
        blank=True,
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.application} - {self.interview_date} ({self.get_attendance_display()})"

    @property
    def venue_name(self):
        if self.location:
            return self.location.location_name
        return "Corporate Office"

    @property
    def venue(self):
        return self.venue_name


class InterviewEvaluation(models.Model):
    RESULT_CHOICES = [
        ("PASS", "Pass / Proceed to Selection"),
        ("FAIL", "Fail / Not Selected"),
    ]

    evaluation_id = models.AutoField(primary_key=True)

    interview = models.OneToOneField(
        Interview,
        on_delete=models.CASCADE,
        related_name="evaluation",
    )

    technical_rating = models.PositiveIntegerField(
        default=3,
        help_text="Score 1-5 for technical competency",
    )

    communication_rating = models.PositiveIntegerField(
        default=3,
        help_text="Score 1-5 for communication & interpersonal skills",
    )

    problem_solving_rating = models.PositiveIntegerField(
        default=3,
        help_text="Score 1-5 for problem solving & analytical skills",
    )

    role_skill_rating = models.PositiveIntegerField(
        default=3,
        help_text="Score 1-5 for role-specific expertise",
    )

    professionalism_rating = models.PositiveIntegerField(
        default=3,
        help_text="Score 1-5 for attitude & professionalism",
    )

    overall_rating = models.FloatField(
        default=3.0,
        help_text="Calculated average rating out of 5",
    )

    comments = models.TextField(
        blank=True,
        help_text="Confidential HR / Interviewer evaluation feedback",
    )

    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default="PASS",
    )

    evaluated_by = models.ForeignKey(
        HRManager,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interview_evaluations",
    )

    evaluated_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"Evaluation for {self.interview} - {self.result} ({self.overall_rating:.1f}/5)"


#My new contribution for the job portal feature :

class JobVacancy(models.Model):
    JOB_TYPE_CHOICES = [
        ("FULL_TIME", "Full Time"),
        ("PART_TIME", "Part Time"),
        ("CONTRACT", "Contract"),
        ("INTERNSHIP", "Internship"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    vacancy_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    department_name = models.CharField(
        max_length=100, 
        help_text="Designated department name for the position"
    )
    job_type = models.CharField(
        max_length=20, 
        choices=JOB_TYPE_CHOICES, 
        default="FULL_TIME"
    )
    experience_required = models.CharField(
        max_length=100, 
        help_text="e.g., 2+ years, Entry Level"
    )
    description = models.TextField()
    requirements = models.TextField(help_text="Key skills and qualifications required")
    openings_count = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="OPEN"
    )
    posted_by = models.ForeignKey(
        HRManager,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posted_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class HRWeeklyReport(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("REVIEWED", "Reviewed"),
        ("NEEDS_IMPROVEMENT", "Needs Improvement"),
    ]

    report_id = models.AutoField(primary_key=True)
    hr_manager = models.ForeignKey(
        HRManager,
        on_delete=models.CASCADE,
        related_name="weekly_reports",
    )
    week_start_date = models.DateField()
    week_end_date = models.DateField()

    # Work Summary
    work_summary = models.TextField(help_text="Overview of weekly HR responsibilities and activities")
    tasks_completed = models.TextField(help_text="Key tasks completed during the week")
    achievements = models.TextField(blank=True, help_text="Major accomplishments and milestones")
    challenges = models.TextField(blank=True, help_text="Obstacles and challenges encountered")
    pending_tasks = models.TextField(blank=True, help_text="Carried-over or ongoing tasks")
    next_week_plan = models.TextField(blank=True, help_text="Planned initiatives and schedule for next week")

    # Supporting Recruitment Metrics
    vacancies_worked = models.PositiveIntegerField(default=0, help_text="Number of job vacancies worked on")
    candidates_screened = models.PositiveIntegerField(default=0, help_text="Resumes/candidates screened")
    candidates_shortlisted = models.PositiveIntegerField(default=0, help_text="Candidates shortlisted")
    aptitude_tests = models.PositiveIntegerField(default=0, help_text="Aptitude tests coordinated")
    interviews = models.PositiveIntegerField(default=0, help_text="Interviews coordinated/conducted")
    candidates_selected = models.PositiveIntegerField(default=0, help_text="Candidates selected/onboarded")

    # Workflow & Audit
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-week_start_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["hr_manager", "week_start_date", "week_end_date"],
                name="unique_hr_weekly_report_period",
            )
        ]

    def __str__(self):
        return f"{self.hr_manager.full_name} ({self.week_display}) - {self.get_status_display()}"

    @property
    def is_editable(self):
        return self.status in ["DRAFT", "NEEDS_IMPROVEMENT"]

    @property
    def week_display(self):
        if self.week_start_date and self.week_end_date:
            return f"{self.week_start_date.strftime('%b %d')} - {self.week_end_date.strftime('%b %d, %Y')}"
        return f"Report #{self.report_id}"


class HRPerformanceReview(models.Model):
    RATING_CHOICES = [
        (1, "1 - Needs Significant Improvement"),
        (2, "2 - Needs Improvement"),
        (3, "3 - Meets Expectations"),
        (4, "4 - Good"),
        (5, "5 - Excellent"),
    ]

    PERFORMANCE_STATUS_CHOICES = [
        ("EXCELLENT", "Excellent (85-100%)"),
        ("GOOD", "Good (70-84%)"),
        ("NEEDS_IMPROVEMENT", "Needs Improvement (50-69%)"),
        ("UNSATISFACTORY", "Unsatisfactory (Below 50%)"),
    ]

    review_id = models.AutoField(primary_key=True)
    report = models.OneToOneField(
        HRWeeklyReport,
        on_delete=models.CASCADE,
        related_name="performance_review",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_hr_reviews",
    )

    # 8 Criteria Ratings (1-5)
    task_completion = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)
    quality_of_work = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)
    recruitment_coordination = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)
    timeliness = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)
    documentation = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)
    communication = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)
    problem_solving = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)
    weekly_goal_achievement = models.PositiveSmallIntegerField(default=3, choices=RATING_CHOICES)

    # Remarks per criterion
    task_completion_remarks = models.CharField(max_length=255, blank=True)
    quality_of_work_remarks = models.CharField(max_length=255, blank=True)
    recruitment_coordination_remarks = models.CharField(max_length=255, blank=True)
    timeliness_remarks = models.CharField(max_length=255, blank=True)
    documentation_remarks = models.CharField(max_length=255, blank=True)
    communication_remarks = models.CharField(max_length=255, blank=True)
    problem_solving_remarks = models.CharField(max_length=255, blank=True)
    weekly_goal_achievement_remarks = models.CharField(max_length=255, blank=True)

    # Calculated metrics (computed automatically)
    total_score = models.PositiveIntegerField(default=0, help_text="Sum of all 8 criteria ratings (out of 40)")
    average_score = models.DecimalField(max_digits=4, decimal_places=2, default=0.00, help_text="Average rating (out of 5)")
    performance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Performance score percentage")
    performance_status = models.CharField(
        max_length=30,
        choices=PERFORMANCE_STATUS_CHOICES,
        default="GOOD",
    )

    # Overall Qualitative Feedback
    overall_feedback = models.TextField(blank=True, help_text="Executive summary of HR weekly performance")
    strengths = models.TextField(blank=True, help_text="Key strengths observed")
    areas_for_improvement = models.TextField(blank=True, help_text="Areas needing enhancement")
    recommendations = models.TextField(blank=True, help_text="Action points and recommendations")
    next_week_expectations = models.TextField(blank=True, help_text="Target expectations for upcoming week")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review for {self.report} - {self.performance_percentage}% ({self.get_performance_status_display()})"

    def calculate_scores(self):
        ratings = [
            self.task_completion or 0,
            self.quality_of_work or 0,
            self.recruitment_coordination or 0,
            self.timeliness or 0,
            self.documentation or 0,
            self.communication or 0,
            self.problem_solving or 0,
            self.weekly_goal_achievement or 0,
        ]
        total = sum(ratings)
        avg = round(total / 8.0, 2)
        pct = round((total / 40.0) * 100.0, 2)

        if pct >= 85.0:
            status = "EXCELLENT"
        elif pct >= 70.0:
            status = "GOOD"
        elif pct >= 50.0:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "UNSATISFACTORY"

        self.total_score = total
        self.average_score = avg
        self.performance_percentage = pct
        self.performance_status = status

    def save(self, *args, **kwargs):
        self.calculate_scores()
        super().save(*args, **kwargs)


# Alias PerformanceReview for naming compatibility
PerformanceReview = HRPerformanceReview


class HRNotification(models.Model):
    NOTIFICATION_TYPES = [
        ("PERFORMANCE_REVIEWED", "Weekly Report Reviewed"),
        ("REPORT_NEEDS_IMPROVEMENT", "Report Needs Improvement"),
        ("PROFILE_UPDATE", "Profile Update Notice"),
        ("GENERAL", "General Notification"),
    ]

    notification_id = models.AutoField(primary_key=True)
    hr_manager = models.ForeignKey(
        HRManager,
        on_delete=models.CASCADE,
        related_name="notifications",
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
        return f"{self.hr_manager.full_name} - {self.title}"

from django.conf import settings
from django.db import models


class Candidate(models.Model):
    candidate_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )

    first_name = models.CharField(
        max_length=100,
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    last_name = models.CharField(
        max_length=100,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    profile_photo = models.ImageField(
        upload_to="candidates/profile_photos/",
        blank=True,
        null=True,
    )

    resume = models.FileField(
        upload_to="candidates/resumes/",
        blank=True,
        null=True,
    )

    id_proof = models.FileField(
        upload_to="candidates/documents/",
        blank=True,
        null=True,
    )

    tenth_certificate = models.FileField(
        upload_to="candidates/documents/",
        blank=True,
        null=True,
    )

    twelfth_certificate = models.FileField(
        upload_to="candidates/documents/",
        blank=True,
        null=True,
    )

    tenth_marklist = models.FileField(
        upload_to="candidates/documents/",
        blank=True,
        null=True,
    )

    twelfth_marklist = models.FileField(
        upload_to="candidates/documents/",
        blank=True,
        null=True,
    )

    policy_agreement = models.BooleanField(
        default=False,
    )

    profile_completed = models.BooleanField(
        default=False,
    )

    # 10th School Education
    tenth_board = models.CharField(
        max_length=150,
        blank=True,
    )
    tenth_school = models.CharField(
        max_length=200,
        blank=True,
    )
    tenth_percentage = models.CharField(
        max_length=20,
        blank=True,
    )
    tenth_passing_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # 12th School Education
    twelfth_board = models.CharField(
        max_length=150,
        blank=True,
    )
    twelfth_school = models.CharField(
        max_length=200,
        blank=True,
    )
    twelfth_stream = models.CharField(
        max_length=100,
        blank=True,
    )
    twelfth_percentage = models.CharField(
        max_length=20,
        blank=True,
    )
    twelfth_passing_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # Experience Details
    is_fresher = models.BooleanField(
        default=True,
    )
    total_experience_years = models.PositiveIntegerField(
        default=0,
    )
    total_experience_months = models.PositiveIntegerField(
        default=0,
    )
    current_employment_status = models.CharField(
        max_length=50,
        blank=True,
        default="Not Currently Employed",
        choices=[
            ("Currently Employed", "Currently Employed"),
            ("Not Currently Employed", "Not Currently Employed"),
            ("Self Employed", "Self Employed"),
            ("Internship", "Internship"),
            ("Other", "Other"),
        ],
    )
    current_organization = models.CharField(
        max_length=200,
        blank=True,
    )
    current_designation = models.CharField(
        max_length=150,
        blank=True,
    )
    joining_date = models.DateField(
        null=True,
        blank=True,
    )
    # Skills & Location
    skills = models.TextField(
        blank=True,
        help_text="Comma-separated skills, e.g. Python, Django, SQL, React",
    )
    state = models.CharField(
        max_length=100,
        blank=True,
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default="India",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def calculate_profile_completion(self):
        """
        Calculates dynamic profile completion percentage (0% to 100%)
        based on 7 essential profile sections. Middle Name is strictly optional.
        """
        sections = {}
        missing_fields = []

        # 1. Personal Details (Weight: 20%)
        # Required: first_name, last_name, phone, date_of_birth, address
        personal_missing = []
        if not self.first_name:
            personal_missing.append("First Name")
        if not self.last_name:
            personal_missing.append("Last Name")
        if not self.phone:
            personal_missing.append("Phone Number")
        if not self.date_of_birth:
            personal_missing.append("Date of Birth")
        if not self.address:
            personal_missing.append("Residential Address")
        personal_complete = len(personal_missing) == 0
        sections["personal"] = {
            "label": "Personal Information",
            "weight": 20,
            "complete": personal_complete,
            "missing": personal_missing,
        }
        if not personal_complete:
            missing_fields.extend(personal_missing)

        # 2. Profile Photo (Weight: 10%)
        photo_complete = bool(self.profile_photo)
        sections["photo"] = {
            "label": "Profile Photo",
            "weight": 10,
            "complete": photo_complete,
            "missing": [] if photo_complete else ["Profile Photo"],
        }
        if not photo_complete:
            missing_fields.append("Profile Photo")

        # 3. 10th Details (Weight: 15%)
        tenth_missing = []
        if not self.tenth_board:
            tenth_missing.append("10th Board")
        if not self.tenth_percentage:
            tenth_missing.append("10th Percentage / CGPA")
        if not self.tenth_passing_year:
            tenth_missing.append("10th Passing Year")
        tenth_complete = len(tenth_missing) == 0
        sections["tenth"] = {
            "label": "10th Education",
            "weight": 15,
            "complete": tenth_complete,
            "missing": tenth_missing,
        }
        if not tenth_complete:
            missing_fields.extend(tenth_missing)

        # 4. 12th Details (Weight: 15%)
        twelfth_missing = []
        if not self.twelfth_board:
            twelfth_missing.append("12th Board")
        if not self.twelfth_percentage:
            twelfth_missing.append("12th Percentage / CGPA")
        if not self.twelfth_passing_year:
            twelfth_missing.append("12th Passing Year")
        twelfth_complete = len(twelfth_missing) == 0
        sections["twelfth"] = {
            "label": "12th Education",
            "weight": 15,
            "complete": twelfth_complete,
            "missing": twelfth_missing,
        }
        if not twelfth_complete:
            missing_fields.extend(twelfth_missing)

        # 5. Higher Education (Weight: 15%)
        has_higher_ed = self.education_records.exists() if self.pk else False
        sections["higher_education"] = {
            "label": "Higher Education (Degree / Diploma)",
            "weight": 15,
            "complete": has_higher_ed,
            "missing": [] if has_higher_ed else ["Higher Education (Degree / Diploma)"],
        }
        if not has_higher_ed:
            missing_fields.append("Higher Education (Degree / Diploma)")

        # 6. Experience (Weight: 10%)
        experience_missing = []
        if not self.is_fresher:
            if not self.total_experience_years and not self.total_experience_months:
                experience_missing.append("Total Experience (Years/Months)")
            if self.current_employment_status == "Currently Employed":
                if not self.current_organization:
                    experience_missing.append("Current Organization")
                if not self.current_designation:
                    experience_missing.append("Current Designation")
        exp_complete = len(experience_missing) == 0
        sections["experience"] = {
            "label": "Work Experience Status",
            "weight": 10,
            "complete": exp_complete,
            "missing": experience_missing,
        }
        if not exp_complete:
            missing_fields.extend(experience_missing)

        # 7. Resume (Weight: 15%)
        resume_complete = bool(self.resume)
        sections["resume"] = {
            "label": "Resume Upload",
            "weight": 15,
            "complete": resume_complete,
            "missing": [] if resume_complete else ["Resume Document"],
        }
        if not resume_complete:
            missing_fields.append("Resume Document")

        # Sum percentage
        total_percentage = sum(s["weight"] for s in sections.values() if s["complete"])
        is_complete = total_percentage >= 100

        if self.pk and self.profile_completed != is_complete:
            self.profile_completed = is_complete
            Candidate.objects.filter(pk=self.pk).update(profile_completed=is_complete)

        return {
            "percentage": total_percentage,
            "is_complete": is_complete,
            "missing_fields": missing_fields,
            "sections": sections,
        }

    @property
    def highest_education_record(self):
        return self.education_records.first() if self.pk else None

    @property
    def highest_education_display(self):
        highest = self.highest_education_record
        if highest:
            return f"{highest.education_level} - {highest.degree_program}"
        if self.twelfth_board:
            return f"12th Standard ({self.twelfth_stream or 'Higher Secondary'})"
        if self.tenth_board:
            return "10th Standard"
        return "Not Specified"

    @property
    def experience_display(self):
        if self.is_fresher:
            return "Fresher"
        parts = []
        if self.total_experience_years:
            parts.append(f"{self.total_experience_years} yr{'s' if self.total_experience_years > 1 else ''}")
        if self.total_experience_months:
            parts.append(f"{self.total_experience_months} mo{'s' if self.total_experience_months > 1 else ''}")
        exp_str = " ".join(parts) if parts else "Experienced"
        if self.current_organization:
            exp_str += f" ({self.current_designation or 'Employee'} at {self.current_organization})"
        return exp_str

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CandidateEducation(models.Model):
    EDUCATION_LEVELS = [
        ("Diploma", "Diploma / Polytechnic"),
        ("Bachelor's", "Bachelor's Degree"),
        ("Master's", "Master's Degree"),
        ("M.Phil", "M.Phil"),
        ("Doctorate / PhD", "Doctorate / PhD"),
        ("Other", "Other"),
    ]

    EDUCATION_STATUSES = [
        ("Currently Studying", "Currently Studying / Pursuing"),
        ("Graduated", "Graduated"),
        ("Completed", "Completed"),
        ("Discontinued", "Discontinued"),
    ]

    FIELD_OF_STUDY_CHOICES = [
        ("Computer Applications", "Computer Applications (BCA, MCA, etc.)"),
        ("Computer Science", "Computer Science / CS Engineering"),
        ("Information Technology", "Information Technology (IT)"),
        ("Engineering", "Engineering (Civil, Mech, Electrical, Electronics, etc.)"),
        ("Business Administration", "Business Administration (BBA, MBA)"),
        ("Commerce", "Commerce / Accounting (B.Com, M.Com, CA)"),
        ("Mathematics", "Mathematics / Statistics"),
        ("Physics", "Physics"),
        ("Chemistry", "Chemistry"),
        ("Agriculture", "Agriculture / Agro-Sciences"),
        ("Biology", "Biology / Life Sciences"),
        ("Other", "Other"),
    ]

    education_id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="education_records",
    )
    education_level = models.CharField(
        max_length=50,
        choices=EDUCATION_LEVELS,
    )
    degree_program = models.CharField(
        max_length=150,
        help_text="e.g. BCA, MCA, B.Tech, B.Sc, M.Sc, MBA, etc.",
    )
    field_of_study = models.CharField(
        max_length=150,
        choices=FIELD_OF_STUDY_CHOICES,
        default="Computer Applications",
        blank=True,
    )
    institution = models.CharField(
        max_length=200,
        help_text="School / College / Institute name",
    )
    university_board = models.CharField(
        max_length=200,
        blank=True,
        help_text="University or Board name",
    )
    education_status = models.CharField(
        max_length=50,
        choices=EDUCATION_STATUSES,
        default="Graduated",
    )
    completion_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Passing or expected completion year",
    )
    percentage_or_cgpa = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. 8.5 CGPA or 85%",
    )
    certificate = models.FileField(
        upload_to="candidates/education_certificates/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-completion_year", "-created_at"]

    def __str__(self):
        return f"{self.candidate} - {self.education_level} ({self.degree_program})"


class JobVacancy(models.Model):
    EMPLOYMENT_TYPES = [
        ("FULL_TIME", "Full Time"),
        ("PART_TIME", "Part Time"),
        ("INTERNSHIP", "Internship"),
        ("CONTRACT", "Contract"),
    ]

    WORK_MODES = [
        ("ON_SITE", "On-site"),
        ("REMOTE", "Remote"),
        ("HYBRID", "Hybrid"),
    ]

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    CLOSED_REASONS = [
        ("MANUALLY_CLOSED", "Manually Closed by HR"),
        ("DEADLINE_EXPIRED", "Deadline Expired"),
    ]

    vacancy_id = models.AutoField(primary_key=True)

    # Basic Job Info
    title = models.CharField(
        max_length=150,
    )
    role_designation = models.CharField(
        max_length=150,
        blank=True,
        help_text="Job Role or Designation (e.g. Backend Developer, HR Executive)",
    )
    department = models.ForeignKey(
        "admin_module.Department",
        on_delete=models.PROTECT,
        related_name="job_vacancies",
    )
    description = models.TextField()
    responsibilities = models.TextField(
        blank=True,
    )
    skills_required = models.TextField(
        blank=True,
        help_text="Mandatory / core technical & professional skills (comma-separated)",
    )
    preferred_skills = models.TextField(
        blank=True,
        help_text="Preferred / nice-to-have skills (comma-separated)",
    )
    qualifications = models.TextField(
        blank=True,
        help_text="General qualifications summary / description",
    )

    # Educational Requirements
    minimum_qualification = models.CharField(
        max_length=50,
        choices=CandidateEducation.EDUCATION_LEVELS,
        default="Bachelor's",
        help_text="Minimum required qualification level",
    )
    required_field_of_study = models.CharField(
        max_length=150,
        choices=CandidateEducation.FIELD_OF_STUDY_CHOICES,
        blank=True,
        help_text="Required / preferred field of study (optional)",
    )
    graduation_year_min = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum graduation year eligible (optional)",
    )
    graduation_year_max = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum graduation year eligible (optional)",
    )

    # Experience Requirements
    experience_required_bool = models.BooleanField(
        default=False,
        verbose_name="Experience Required",
        help_text="Specify whether professional experience is mandatory",
    )
    minimum_experience = models.FloatField(
        default=0.0,
        help_text="Minimum experience in years (0 for freshers)",
    )
    maximum_experience = models.FloatField(
        null=True,
        blank=True,
        help_text="Maximum experience in years (optional)",
    )
    experience_required = models.CharField(
        max_length=100,
        blank=True,
        help_text="Text representation of experience requirements (e.g., 2-4 Years)",
    )

    # Employment Type, Location & Openings
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default="FULL_TIME",
    )
    location = models.CharField(
        max_length=150,
        default="Headquarters",
        help_text="City or primary location",
    )
    state = models.CharField(
        max_length=100,
        blank=True,
        help_text="State / Province",
    )
    country = models.CharField(
        max_length=100,
        default="India",
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WORK_MODES,
        default="ON_SITE",
    )
    number_of_openings = models.PositiveIntegerField(
        default=1,
        help_text="Number of open vacancies",
    )

    # Status, Posting & Closure
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )
    closing_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last date to apply / deadline",
    )
    closed_reason = models.CharField(
        max_length=30,
        choices=CLOSED_REASONS,
        null=True,
        blank=True,
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_vacancies",
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posted_jobs",
    )
    posted_date = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-posted_date"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def is_deadline_passed(self):
        if not self.closing_date:
            return False
        from django.utils import timezone
        return self.closing_date < timezone.localdate()

    def check_and_update_status(self):
        """If status is OPEN and deadline has passed, automatically transition to CLOSED with DEADLINE_EXPIRED and run screening."""
        from django.utils import timezone
        if self.status == "OPEN" and self.is_deadline_passed():
            self.status = "CLOSED"
            self.closed_reason = "DEADLINE_EXPIRED"
            self.closed_at = timezone.now()
            JobVacancy.objects.filter(pk=self.pk, status="OPEN").update(
                status="CLOSED",
                closed_reason="DEADLINE_EXPIRED",
                closed_at=self.closed_at,
            )
            # Automatically screen applications submitted before closure
            try:
                from .screening_service import run_resume_screening
                run_resume_screening(self, force_rescreen=False)
            except Exception:
                pass
            return True
        return False

    @classmethod
    def update_all_expired(cls):
        """Batch update all open vacancies whose deadlines have passed and screen applications."""
        from django.utils import timezone
        today = timezone.localdate()
        now = timezone.now()
        expired_vacancies = list(cls.objects.filter(
            status="OPEN",
            closing_date__isnull=False,
            closing_date__lt=today,
        ))
        for v in expired_vacancies:
            v.status = "CLOSED"
            v.closed_reason = "DEADLINE_EXPIRED"
            v.closed_at = now
            v.save(update_fields=["status", "closed_reason", "closed_at"])
            try:
                from .screening_service import run_resume_screening
                run_resume_screening(v, force_rescreen=False)
            except Exception:
                pass
        return len(expired_vacancies)

    @property
    def is_open(self):
        return self.status == "OPEN" and not self.is_deadline_passed()

    @property
    def experience_display(self):
        if not self.experience_required_bool or (self.minimum_experience == 0 and not self.maximum_experience):
            return "Fresher / No Experience Required"
        if self.maximum_experience:
            return f"{self.minimum_experience:g} - {self.maximum_experience:g} Years"
        return f"{self.minimum_experience:g}+ Years"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("RESUME_REVIEW", "Resume Under Review"),
        ("SHORTLISTED", "Shortlisted"),
        ("APTITUDE_TEST_SCHEDULED", "Aptitude Test Scheduled"),
        ("APTITUDE", "Aptitude In Progress"),
        ("APTITUDE_REVIEW", "Aptitude Review"),
        ("INTERVIEW_SCHEDULING", "Interview Slot Selection"),
        ("INTERVIEW_SCHEDULED", "Interview Scheduled"),
        ("INTERVIEW", "Interview In Progress"),
        ("INTERVIEW_REVIEW", "Interview Evaluation"),
        ("SELECTED", "Selected"),
        ("FORWARDED_TO_ADMIN", "Forwarded to Admin"),
        ("HIRED", "Hired"),
        ("REJECTED", "Rejected"),
    ]

    application_id = models.AutoField(primary_key=True)

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    vacancy = models.ForeignKey(
        JobVacancy,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    applied_resume = models.FileField(
        upload_to="applications/resumes/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="APPLIED",
    )

    # Aptitude Test Scheduling
    aptitude_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled date for aptitude assessment",
    )

    aptitude_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Scheduled time for aptitude assessment",
    )

    aptitude_duration_minutes = models.PositiveIntegerField(
        default=30,
        null=True,
        blank=True,
        help_text="Duration of test in minutes",
    )

    aptitude_start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timezone-aware test start datetime",
    )

    aptitude_end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timezone-aware test end datetime",
    )

    aptitude_passing_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional passing score threshold",
    )

    aptitude_test = models.ForeignKey(
        "hr.AptitudeTest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_applications",
    )

    aptitude_remarks = models.TextField(
        blank=True,
        help_text="HR instructions or notes for aptitude round",
    )

    def get_aptitude_start_datetime(self):
        if self.aptitude_start_datetime:
            return self.aptitude_start_datetime
        if self.aptitude_date and self.aptitude_time:
            from django.utils import timezone
            import datetime
            combined = datetime.datetime.combine(self.aptitude_date, self.aptitude_time)
            return timezone.make_aware(combined) if timezone.is_naive(combined) else combined
        return None

    def get_aptitude_end_datetime(self):
        if self.aptitude_end_datetime:
            return self.aptitude_end_datetime
        start_dt = self.get_aptitude_start_datetime()
        if start_dt:
            import datetime
            duration = self.aptitude_duration_minutes or (self.aptitude_test.duration_minutes if self.aptitude_test else 30)
            return start_dt + datetime.timedelta(minutes=duration)
        return None

    def is_aptitude_window_open(self):
        start_dt = self.get_aptitude_start_datetime()
        end_dt = self.get_aptitude_end_datetime()
        if not start_dt or not end_dt:
            return False
        from django.utils import timezone
        now = timezone.now()
        return start_dt <= now < end_dt

    def is_aptitude_window_passed(self):
        end_dt = self.get_aptitude_end_datetime()
        if not end_dt:
            return False
        from django.utils import timezone
        return timezone.now() >= end_dt

    def is_aptitude_upcoming(self):
        start_dt = self.get_aptitude_start_datetime()
        if not start_dt:
            return False
        from django.utils import timezone
        return timezone.now() < start_dt

    INFORMATION_SOURCES = [
        ("PROFILE", "Use My Profile"),
        ("RESUME", "Autofill From Resume"),
        ("MANUAL", "Enter Manually"),
    ]

    ELIGIBILITY_STATUSES = [
        ("ELIGIBLE", "Eligible to Apply"),
        ("NOT_ELIGIBLE", "Not Eligible"),
        ("UNDER_REVIEW", "Under Review"),
    ]

    information_source = models.CharField(
        max_length=20,
        choices=INFORMATION_SOURCES,
        default="PROFILE",
    )

    eligibility_status = models.CharField(
        max_length=30,
        choices=ELIGIBILITY_STATUSES,
        default="ELIGIBLE",
    )

    eligibility_details = models.JSONField(
        default=dict,
        blank=True,
    )

    # Section 4: Current / Past Employment
    is_currently_employed = models.BooleanField(
        default=False,
    )
    is_past_employee = models.BooleanField(
        default=False,
    )
    past_employee_id = models.CharField(
        max_length=50,
        blank=True,
    )
    past_designation = models.CharField(
        max_length=150,
        blank=True,
    )
    past_employment_period = models.CharField(
        max_length=100,
        blank=True,
    )

    # Section 5: Location & Relocation
    current_state = models.CharField(
        max_length=100,
        blank=True,
    )
    current_country = models.CharField(
        max_length=100,
        blank=True,
        default="India",
    )
    willing_to_relocate = models.BooleanField(
        default=True,
    )

    # Section 6: Work Authorization / Visa
    legally_authorized = models.BooleanField(
        default=True,
    )
    requires_visa_sponsorship = models.BooleanField(
        default=False,
    )
    visa_status = models.CharField(
        max_length=100,
        blank=True,
    )

    # Section 7: Salary / CTC
    current_salary = models.CharField(
        max_length=50,
        blank=True,
    )
    expected_salary = models.CharField(
        max_length=50,
        blank=True,
    )

    # Section 8: Scholarship / Financial Assistance
    receiving_scholarship = models.BooleanField(
        default=False,
    )
    scholarship_details = models.CharField(
        max_length=200,
        blank=True,
    )

    # Section 9: Job-Specific Questions
    willing_to_work_location = models.BooleanField(
        default=True,
    )
    work_mode_preference = models.CharField(
        max_length=50,
        blank=True,
        default="Any",
    )
    available_joining_days = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    why_interested = models.TextField(
        blank=True,
    )
    additional_info = models.TextField(
        blank=True,
    )
    applied_skills = models.TextField(
        blank=True,
    )

    # Admin Forwarding
    is_forwarded_to_admin = models.BooleanField(
        default=False,
        help_text="Whether selected candidate details have been forwarded to Admin for employee processing",
    )
    forwarded_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    forwarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forwarded_applications",
    )

    applied_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "vacancy"],
                name="unique_candidate_vacancy",
            ),
        ]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate} - {self.vacancy}"

    @property
    def latest_interview(self):
        return self.interviews.order_by("-interview_date", "-interview_time").first()

    @property
    def latest_booked_slot(self):
        return self.booked_slots.order_by("-interview_date", "-start_time").first()


class CandidateNotification(models.Model):
    NOTIFICATION_TYPES = [
        ("APPLICATION_SUBMITTED", "Application Submitted"),
        ("APPLICATION_UNDER_REVIEW", "Application Under Review"),
        ("SHORTLISTED", "Resume Shortlisted"),
        ("NOT_SHORTLISTED", "Application Update"),
        ("STATUS_UPDATE", "Application Status Updated"),
        ("APTITUDE_SCHEDULED", "Aptitude Test Scheduled"),
        ("APTITUDE_RESCHEDULED", "Aptitude Test Rescheduled"),
        ("APTITUDE_CANCELLED", "Aptitude Test Cancelled"),
        ("APTITUDE_RESULT", "Aptitude Test Result"),
        ("INTERVIEW_ELIGIBLE", "Interview Slot Selection Open"),
        ("INTERVIEW_SCHEDULED", "Interview Scheduled"),
        ("INTERVIEW_RESCHEDULED", "Interview Rescheduled"),
        ("INTERVIEW_CANCELLED", "Interview Cancelled"),
        ("INTERVIEW_ATTENDED", "Interview Attended"),
        ("INTERVIEW_NO_SHOW", "Interview No Show"),
        ("INTERVIEW_PASSED", "Selected for Position"),
        ("INTERVIEW_FAILED", "Interview Result"),
        ("INTERVIEW_UPDATE", "Interview Updated"),
        ("EMPLOYEE_CONVERTED", "Employee Onboarding Complete"),
        ("GENERAL", "General Notification"),
    ]

    notification_id = models.AutoField(primary_key=True)

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="candidate_notifications",
    )

    title = models.CharField(
        max_length=200,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default="STATUS_UPDATE",
    )

    link_url = models.CharField(
        max_length=255,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.candidate} - {self.title}"


def send_candidate_notification(
    candidate,
    title,
    message,
    notification_type="STATUS_UPDATE",
    application=None,
    link_url="",
):
    """
    Utility helper to dispatch a targeted notification to a specific candidate.
    Prevents duplicate notifications for Candidate + JobApplication + Notification Type.
    """
    if not candidate:
        return None

    if application and notification_type in [
        "APPLICATION_SUBMITTED",
        "APPLICATION_UNDER_REVIEW",
        "SHORTLISTED",
        "NOT_SHORTLISTED",
        "APTITUDE_SCHEDULED",
        "INTERVIEW_ELIGIBLE",
        "INTERVIEW_SCHEDULED",
        "INTERVIEW_PASSED",
        "INTERVIEW_FAILED",
        "EMPLOYEE_CONVERTED",
    ]:
        existing = CandidateNotification.objects.filter(
            candidate=candidate,
            application=application,
            notification_type=notification_type,
        ).first()
        if existing:
            return existing

    return CandidateNotification.objects.create(
        candidate=candidate,
        application=application,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url,
    )


class ResumeScreening(models.Model):
    STATUS_CHOICES = [
        ("SHORTLISTED", "Shortlisted"),
        ("NOT_SHORTLISTED", "Not Shortlisted"),
        ("MANUAL_REVIEW", "Manual Review"),
        ("EXTRACTION_FAILED", "Extraction Failed"),
    ]

    screening_id = models.AutoField(primary_key=True)

    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="screening_result",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="NOT_SHORTLISTED",
    )

    match_score = models.FloatField(
        default=0.0,
        help_text="Overall screening match percentage score (0 - 100)",
    )

    # Required Skills
    required_skills_total = models.PositiveIntegerField(
        default=0,
    )
    required_skills_matched = models.PositiveIntegerField(
        default=0,
    )
    required_skills_data = models.JSONField(
        default=list,
        help_text="List of required skills with match status: [{'skill': 'Python', 'matched': True}]",
    )

    # Preferred Skills
    preferred_skills_total = models.PositiveIntegerField(
        default=0,
    )
    preferred_skills_matched = models.PositiveIntegerField(
        default=0,
    )
    preferred_skills_data = models.JSONField(
        default=list,
        help_text="List of preferred skills with match status: [{'skill': 'Docker', 'matched': True}]",
    )

    # Extracted Skills from Resume / Application
    extracted_skills = models.JSONField(
        default=list,
        help_text="List of skills extracted from candidate resume/application",
    )

    # Educational Match Breakdown
    education_matched = models.BooleanField(
        default=False,
    )
    required_education = models.CharField(
        max_length=150,
        blank=True,
    )
    candidate_education = models.CharField(
        max_length=150,
        blank=True,
    )
    education_remarks = models.TextField(
        blank=True,
    )

    # Field of Study Match Breakdown
    field_of_study_matched = models.BooleanField(
        default=True,
    )
    required_field_of_study = models.CharField(
        max_length=150,
        blank=True,
    )
    candidate_field_of_study = models.CharField(
        max_length=150,
        blank=True,
    )

    # Graduation Year Match Breakdown
    graduation_year_matched = models.BooleanField(
        default=True,
    )
    required_graduation_range = models.CharField(
        max_length=100,
        blank=True,
    )
    candidate_graduation_year = models.CharField(
        max_length=50,
        blank=True,
    )
    graduation_remarks = models.TextField(
        blank=True,
    )

    # Experience Match Breakdown
    experience_matched = models.BooleanField(
        default=False,
    )
    required_experience = models.CharField(
        max_length=100,
        blank=True,
    )
    candidate_experience = models.CharField(
        max_length=100,
        blank=True,
    )
    experience_remarks = models.TextField(
        blank=True,
    )

    # Summary & Decision Reasons
    decision_reason = models.TextField(
        blank=True,
        help_text="Clear explanation for shortlisted or not shortlisted outcome",
    )
    missing_requirements = models.JSONField(
        default=list,
        help_text="List of missing mandatory requirements/skills",
    )

    screened_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    screened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_screenings",
    )
    is_manual_override = models.BooleanField(
        default=False,
    )
    override_notes = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-screened_at"]

    def __str__(self):
        return f"Screening #{self.screening_id} - {self.application.candidate} for {self.application.vacancy.title} ({self.get_status_display()})"

    @property
    def candidate(self):
        return self.application.candidate

    @property
    def vacancy(self):
        return self.application.vacancy

    @property
    def required_skills_ratio_display(self):
        return f"{self.required_skills_matched}/{self.required_skills_total}"



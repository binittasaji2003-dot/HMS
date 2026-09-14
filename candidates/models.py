"""Database models for the Candidate / Job Portal Module.

Architecture follows Cookiecutter Django enterprise HRMS standards.
Supports Candidate Profile, Education, Skills, Documents, Vacancies, Applications,
Aptitude Tests, Questions, Results, Interviews, and Notifications.
"""
from django.conf import settings
from django.db import models


# ==============================================================================
# 1. DEPARTMENT MODEL
# ==============================================================================
class Department(models.Model):
    department_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, help_text="Department name, e.g., IT & Engineering")
    code = models.CharField(max_length=20, unique=True, help_text="Short department code, e.g., IT, HR, DESIGN")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "department"
        ordering = ["name"]
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name


# ==============================================================================
# 2. JOB VACANCY MODEL
# ==============================================================================
class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full Time"
        PART_TIME = "PART_TIME", "Part Time"
        CONTRACT = "CONTRACT", "Contract"
        INTERNSHIP = "INTERNSHIP", "Internship"
        REMOTE = "REMOTE", "Remote"
        HYBRID = "HYBRID", "Hybrid"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        DRAFT = "DRAFT", "Draft"

    job_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, help_text="Job title, e.g., Python Developer")
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="jobs",
        help_text="Department offering this vacancy",
    )
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    experience_required = models.CharField(max_length=50, default="0-2 Years")
    location = models.CharField(max_length=150, default="Kochi, Kerala (Hybrid)")
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_display = models.CharField(max_length=50, blank=True, help_text="e.g. ₹6.0 - 8.5 LPA")
    description = models.TextField(help_text="Job overview and details")
    responsibilities = models.TextField(blank=True, help_text="Key responsibilities")
    requirements = models.TextField(blank=True, help_text="Minimum qualifications & skills")
    skills_required = models.CharField(max_length=255, blank=True, help_text="Comma-separated skill tags")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    deadline = models.DateField(null=True, blank=True, help_text="Application deadline date")
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_active(self):
        from django.utils import timezone
        if self.status != self.Status.OPEN:
            return False
        if self.deadline and self.deadline < timezone.now().date():
            return False
        return True

    class Meta:

        db_table = "job_vacancy"
        ordering = ["-posted_at"]
        verbose_name = "Job Vacancy"
        verbose_name_plural = "Job Vacancies"
        indexes = [
            models.Index(fields=["status", "department"]),
            models.Index(fields=["job_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.department.name})"


# ==============================================================================
# 3. CANDIDATE PROFILE MODEL
# ==============================================================================
class Candidate(models.Model):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    candidate_id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
        help_text="Underlying Django User account",
    )
    candidate_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        db_index=True,
        help_text="Unique Candidate Reference ID (e.g. #CAN-2026-884)",
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to="candidates/photos/", null=True, blank=True)
    experience_level = models.CharField(max_length=100, blank=True, default="Fresher / 0-1 Years")
    preferred_job_type = models.CharField(max_length=100, blank=True, default="Full Time")
    preferred_locations = models.CharField(max_length=255, blank=True, default="Kochi, Bangalore, Remote")
    notice_period = models.CharField(max_length=50, blank=True, default="Immediate Joiner (0 Days)")
    profile_completion_pct = models.PositiveIntegerField(default=0, help_text="Percentage completion (0-100)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate"
        ordering = ["-created_at"]
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"

    @property
    def initials(self):
        if not self.full_name:
            return "CA"
        parts = self.full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return parts[0][:2].upper()

    def calculate_profile_completion(self):
        """Dynamically calculates candidate profile completion percentage (0-100) and advice."""
        score = 0
        advice = "Complete your profile to increase visibility to recruiters."

        # 1. Personal Information (30 points)
        if self.full_name:
            score += 5
        if self.phone:
            score += 5
        if self.date_of_birth:
            score += 5
        if self.gender:
            score += 5
        if self.address:
            score += 3
        if self.city:
            score += 3
        if self.state:
            score += 2
        if self.pincode:
            score += 2

        # 2. Education (30 points)
        educations = list(self.educations.all())
        edu_score = 0
        has_degree = False
        has_12th = False
        has_10th = False

        for edu in educations:
            q = (edu.qualification_type or "").lower()
            if any(k in q for k in ["degree", "bachelor", "master", "mca", "b.sc", "b.tech", "btech", "m.tech", "be", "b.e", "bba", "bcom", "b.com", "mba"]):
                has_degree = True
            elif any(k in q for k in ["12th", "higher secondary", "hsc", "plus two", "+2", "intermediate"]):
                has_12th = True
            elif any(k in q for k in ["10th", "sslc", "secondary", "matric", "high school"]):
                has_10th = True

        if has_degree:
            edu_score += 10
        if has_12th:
            edu_score += 10
        if has_10th:
            edu_score += 10

        # Fallback if custom titles used
        if edu_score < 30 and len(educations) > 0:
            edu_score = max(edu_score, min(30, len(educations) * 10))

        score += edu_score

        # 3. Skills (15 points)
        skill_count = self.skills.count()
        if skill_count >= 3:
            score += 15
        elif skill_count > 0:
            score += skill_count * 5

        # 4. Documents (25 points)
        doc_score = 0
        has_docs = hasattr(self, "documents") and self.documents is not None
        has_resume = False
        has_degree_cert = False

        if has_docs:
            d = self.documents
            if d.resume:
                doc_score += 10
                has_resume = True
            if d.id_proof:
                doc_score += 5
            if d.degree_certificate or d.graduation_certificate:
                doc_score += 5
                has_degree_cert = True
            if (
                d.tenth_certificate
                or d.tenth_marklist
                or d.twelfth_certificate
                or d.twelfth_marklist
                or d.experience_certificate
                or d.other_document
            ):
                doc_score += 5

        score += doc_score
        score = min(100, max(0, score))

        # Dynamic advice
        if not has_resume:
            advice = "Upload your Resume / CV to reach 100% profile completion."
        elif not has_degree_cert:
            advice = "Add your Degree Provisional certificate to reach 100%."
        elif skill_count < 3:
            advice = "Add at least 3 technical skills to boost recruiter visibility."
        elif edu_score < 30:
            advice = "Complete your 10th, 12th, and Degree academic records."
        elif score < 100:
            advice = "Add any remaining certificates or contact info to reach 100%."
        else:
            advice = "Profile is 100% complete and fully verified!"

        return score, advice

    def update_profile_completion(self):
        score, _ = self.calculate_profile_completion()
        self.profile_completion_pct = score
        Candidate.objects.filter(pk=self.pk).update(profile_completion_pct=score)
        return score

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.candidate_code:
            self.candidate_code = f"CAN-2026-{self.candidate_id:04d}"
            super().save(update_fields=["candidate_code"])

    @property
    def is_selected(self):
        """Returns True if candidate has at least one application with status = 'SELECTED'."""
        return self.applications.filter(status="SELECTED").exists()

    @property
    def is_onboarded(self):
        """Returns True if candidate has been onboarded into employee_table."""
        from .onboarding import is_candidate_onboarded
        return is_candidate_onboarded(candidate_id=self.candidate_id, user_id=self.user_id)

    @property
    def employee_record(self):
        """Returns the dictionary representation of the candidate's row in employee_table, if present."""
        from .onboarding import get_employee_record
        return get_employee_record(candidate_id=self.candidate_id, user_id=self.user_id)

    @property
    def lifecycle_stage(self):
        """Returns the current talent lifecycle stage."""
        from .onboarding import get_candidate_lifecycle_stage
        return get_candidate_lifecycle_stage(self)

    def __str__(self):
        return f"{self.full_name} ({self.candidate_code or self.candidate_id})"




# ==============================================================================
# 4. CANDIDATE EDUCATION MODEL
# ==============================================================================
class CandidateEducation(models.Model):
    education_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="educations",
    )
    qualification_type = models.CharField(
        max_length=100,
        help_text="e.g. Master of Computer Applications (MCA), B.Sc CS, 12th, 10th",
    )
    institution = models.CharField(max_length=255, help_text="School / College / Institute name")
    board_or_university = models.CharField(max_length=255, blank=True, help_text="University / Board name")
    year = models.CharField(max_length=50, help_text="Graduation year / duration, e.g., 2024 - 2026")
    percentage_or_cgpa = models.CharField(max_length=50, help_text="e.g., 8.8 CGPA or 86.5%")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_education"
        ordering = ["-education_id"]
        verbose_name = "Candidate Education"
        verbose_name_plural = "Candidate Educations"

    def __str__(self):
        return f"{self.qualification_type} - {self.candidate.full_name}"


# ==============================================================================
# 5. CANDIDATE SKILLS MODEL
# ==============================================================================
class CandidateSkill(models.Model):
    skill_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill_name = models.CharField(max_length=100, help_text="e.g. Python, Django, PostgreSQL, REST APIs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "candidate_skill"
        unique_together = [("candidate", "skill_name")]
        ordering = ["skill_name"]
        verbose_name = "Candidate Skill"
        verbose_name_plural = "Candidate Skills"

    def __str__(self):
        return f"{self.skill_name} ({self.candidate.full_name})"


# ==============================================================================
# 6. CANDIDATE DOCUMENTS MODEL
# ==============================================================================
class CandidateDocument(models.Model):
    """
    Documents uploaded by Candidate during portal usage.
    NOTE: These belong strictly to the Candidate module.
    When candidate is hired, verified documents flow to employee_documents.
    """
    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    document_id = models.BigAutoField(primary_key=True)
    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    resume = models.FileField(upload_to="candidates/documents/resumes/", blank=True, null=True)
    profile_photo = models.ImageField(upload_to="candidates/documents/photos/", blank=True, null=True)
    id_proof = models.FileField(upload_to="candidates/documents/id_proofs/", blank=True, null=True)
    tenth_certificate = models.FileField(
        upload_to="candidates/documents/certificates/",
        blank=True,
        null=True,
        db_column="10th_certificate",
    )
    tenth_marklist = models.FileField(
        upload_to="candidates/documents/marklists/",
        blank=True,
        null=True,
        db_column="10th_marklist",
    )
    twelfth_certificate = models.FileField(
        upload_to="candidates/documents/certificates/",
        blank=True,
        null=True,
        db_column="12th_certificate",
    )
    twelfth_marklist = models.FileField(
        upload_to="candidates/documents/marklists/",
        blank=True,
        null=True,
        db_column="12th_marklist",
    )
    degree_certificate = models.FileField(upload_to="candidates/documents/degrees/", blank=True, null=True)
    graduation_certificate = models.FileField(upload_to="candidates/documents/degrees/", blank=True, null=True)
    experience_certificate = models.FileField(upload_to="candidates/documents/experience/", blank=True, null=True)
    other_document = models.FileField(upload_to="candidates/documents/other/", blank=True, null=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    uploaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_document"
        verbose_name = "Candidate Document"
        verbose_name_plural = "Candidate Documents"

    DOCUMENT_DEFINITIONS = [

        ("resume", "Resume / Curriculum Vitae", "PDF"),
        ("id_proof", "Identity Proof (Aadhaar / Passport)", "PDF, JPG, PNG"),
        ("tenth_certificate", "10th Standard Certificate", "PDF, JPG, PNG"),
        ("tenth_marklist", "10th Standard Marksheet", "PDF, JPG, PNG"),
        ("twelfth_certificate", "12th Standard Certificate", "PDF, JPG, PNG"),
        ("twelfth_marklist", "12th Standard Marksheet", "PDF, JPG, PNG"),
        ("degree_certificate", "Degree Certificate / Provisional", "PDF, JPG, PNG"),
        ("graduation_certificate", "Graduation Certificate / Consolidated", "PDF, JPG, PNG"),
        ("experience_certificate", "Experience Certificate / Relieving Letter", "PDF, JPG, PNG"),
        ("other_document", "Other Supporting Document / Certifications", "PDF, JPG, PNG"),
    ]

    def get_document_items(self):
        """Returns structured metadata for all 10 candidate document categories."""
        import os
        items = []
        for field_name, label, allowed_types in self.DOCUMENT_DEFINITIONS:
            file_field = getattr(self, field_name, None)
            has_file = bool(file_field and file_field.name)
            filename = os.path.basename(file_field.name) if has_file else ""
            file_size_display = ""
            file_ext = ""
            if has_file:
                try:
                    size = file_field.size
                    if size >= 1024 * 1024:
                        file_size_display = f"{size / (1024 * 1024):.1f} MB"
                    else:
                        file_size_display = f"{max(1, size // 1024)} KB"
                except Exception:
                    file_size_display = "Uploaded"
                _, ext = os.path.splitext(filename)
                file_ext = ext.lstrip(".").upper() or "DOC"

            items.append({
                "field_name": field_name,
                "label": label,
                "allowed_types": allowed_types,
                "has_file": has_file,
                "file": file_field,
                "filename": filename,
                "file_size": file_size_display,
                "file_ext": file_ext,
                "verification_status": self.verification_status,
                "uploaded_at": self.uploaded_at,
            })
        return items

    def __str__(self):
        return f"Documents of {self.candidate.full_name} ({self.verification_status})"



# ==============================================================================
# 7. JOB APPLICATION MODEL
# ==============================================================================
class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        RESUME_REVIEW = "RESUME_REVIEW", "Resume Under Review"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        APTITUDE_TEST = "APTITUDE_TEST", "Aptitude Test"
        INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED", "Interview Scheduled"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"

    application_id = models.BigAutoField(primary_key=True)
    application_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        db_index=True,
        help_text="Unique Application Ref, e.g., #APP-2026-8841",
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    resume = models.FileField(
        upload_to="applications/resumes/",
        blank=True,
        null=True,
        help_text="Specific resume attached for this application",
    )
    cover_note = models.TextField(blank=True, help_text="Why candidate is a good fit")
    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.APPLIED,
        db_index=True,
    )
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job_application"
        ordering = ["-applied_at"]
        verbose_name = "Job Application"
        verbose_name_plural = "Job Applications"
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"],
                name="unique_candidate_job_application",
            )
        ]
        indexes = [
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["job", "status"]),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.application_code:
            self.application_code = f"APP-2026-{self.application_id:04d}"
            super().save(update_fields=["application_code"])

    def __str__(self):
        return f"{self.application_code or self.application_id} - {self.candidate.full_name} for {self.job.title} ({self.status})"


# ==============================================================================
# 8. APTITUDE TEST MODEL
# ==============================================================================
class AptitudeTest(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        UPCOMING = "UPCOMING", "Upcoming"
        ARCHIVED = "ARCHIVED", "Archived"

    test_id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="aptitude_tests",
        null=True,
        blank=True,
        help_text="Optional link to specific job vacancy",
    )
    title = models.CharField(max_length=255, help_text="e.g. Python Developer Aptitude Assessment")
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    total_questions = models.PositiveIntegerField(default=20)
    passing_percentage = models.PositiveIntegerField(default=60)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="Current test status (Active, Upcoming, Archived)",
    )
    assigned_candidates = models.ManyToManyField(
        Candidate,
        related_name="assigned_tests",
        blank=True,
        help_text="Candidates specifically assigned to take this assessment",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "aptitude_test"
        ordering = ["-created_at"]
        verbose_name = "Aptitude Test"
        verbose_name_plural = "Aptitude Tests"

    def __str__(self):
        return self.title

    @property
    def duration(self):
        return self.duration_minutes

    @duration.setter
    def duration(self, value):
        self.duration_minutes = value

    @property
    def passing_score(self):
        return self.passing_percentage

    @passing_score.setter
    def passing_score(self, value):
        self.passing_percentage = value


# ==============================================================================
# 9. APTITUDE QUESTION MODEL
# ==============================================================================
class Question(models.Model):
    class CorrectOption(models.TextChoices):
        A = "A", "Option A"
        B = "B", "Option B"
        C = "C", "Option C"
        D = "D", "Option D"

    question_id = models.BigAutoField(primary_key=True)
    test = models.ForeignKey(
        AptitudeTest,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=2, choices=CorrectOption.choices)
    marks = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "aptitude_question"
        ordering = ["question_id"]
        verbose_name = "Aptitude Question"
        verbose_name_plural = "Aptitude Questions"

    def __str__(self):
        return f"Q{self.question_id}: {self.question_text[:60]}"

    @property
    def correct_answer(self):
        return self.correct_option

    @correct_answer.setter
    def correct_answer(self, value):
        self.correct_option = value


# ==============================================================================
# 10. APTITUDE TEST RESULT MODEL
# ==============================================================================
class TestResult(models.Model):
    result_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="test_results",
    )
    test = models.ForeignKey(
        AptitudeTest,
        on_delete=models.CASCADE,
        related_name="results",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="test_results",
    )
    total_questions = models.PositiveIntegerField(default=20)
    correct_answers = models.PositiveIntegerField(default=0)
    incorrect_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_passed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "aptitude_result"
        ordering = ["-completed_at"]
        verbose_name = "Aptitude Test Result"
        verbose_name_plural = "Aptitude Test Results"
        indexes = [
            models.Index(fields=["candidate", "test"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["candidate", "test"], name="unique_candidate_test_result")
        ]

    def __str__(self):
        return f"{self.candidate.full_name} - {self.test.title}: {self.score_percentage}% ({'PASSED' if self.is_passed else 'FAILED'})"

    @property
    def score(self):
        return self.correct_answers

    @score.setter
    def score(self, value):
        self.correct_answers = value

    @property
    def percentage(self):
        return self.score_percentage

    @percentage.setter
    def percentage(self, value):
        self.score_percentage = value

    @property
    def passed(self):
        return self.is_passed

    @passed.setter
    def passed(self, value):
        self.is_passed = value

    @property
    def submitted_at(self):
        return self.completed_at


# ==============================================================================
# 11. INTERVIEW MODEL
# ==============================================================================
class Interview(models.Model):
    class Mode(models.TextChoices):
        ONLINE = "ONLINE", "Online Video Call"
        OFFLINE = "OFFLINE", "In-person Interview"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"

    interview_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interviews",
    )
    interview_round = models.CharField(max_length=100, default="Round 1 - Technical Interview")
    date = models.DateField(db_index=True)
    time = models.TimeField()
    mode = models.CharField(max_length=15, choices=Mode.choices, default=Mode.ONLINE)
    interviewer = models.CharField(max_length=255, default="HR Team & Senior Tech Lead")
    meeting_link = models.URLField(blank=True, help_text="e.g. Google Meet / Zoom link")
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "interview"
        ordering = ["-date", "-time"]
        verbose_name = "Interview"
        verbose_name_plural = "Interviews"
        indexes = [
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["job", "status"]),
        ]

    def __str__(self):
        return f"{self.interview_round} - {self.candidate.full_name} ({self.date})"


# ==============================================================================
# 12. NOTIFICATION MODEL
# ==============================================================================
class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPLICATION = "APPLICATION", "Application Update"
        INTERVIEW = "INTERVIEW", "Interview Schedule"
        APTITUDE = "APTITUDE", "Aptitude Test"
        GENERAL = "GENERAL", "General Announcement"
        REGISTRATION = "REGISTRATION", "Registration"

    notification_id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        db_index=True,
    )
    link = models.CharField(max_length=255, blank=True, help_text="Target URL or action link")
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["candidate", "is_read"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.candidate.full_name} ({'Read' if self.is_read else 'Unread'})"

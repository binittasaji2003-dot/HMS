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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class JobVacancy(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    vacancy_id = models.AutoField(primary_key=True)

    title = models.CharField(
        max_length=150,
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

    qualifications = models.TextField(
        blank=True,
    )

    skills_required = models.TextField(
        blank=True,
    )

    experience_required = models.CharField(
        max_length=100,
        blank=True,
    )

    location = models.CharField(
        max_length=150,
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

    closing_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("RESUME_REVIEW", "Resume Under Review"),
        ("SHORTLISTED", "Shortlisted"),
        ("APTITUDE", "Aptitude Test Scheduled"),
        ("INTERVIEW", "Interview Scheduled"),
        ("SELECTED", "Selected"),
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
            )
        ]

    def __str__(self):
        return f"{self.candidate} - {self.vacancy}"
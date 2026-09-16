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


class CandidateNotification(models.Model):
    NOTIFICATION_TYPES = [
        ("STATUS_UPDATE", "Application Status Updated"),
        ("APTITUDE_SCHEDULED", "Aptitude Test Scheduled"),
        ("APTITUDE_RESULT", "Aptitude Test Result"),
        ("INTERVIEW_SCHEDULED", "Interview Scheduled"),
        ("INTERVIEW_UPDATE", "Interview Updated"),
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
    """Utility helper to dispatch a targeted notification to a specific candidate."""
    if not candidate:
        return None
    return CandidateNotification.objects.create(
        candidate=candidate,
        application=application,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url,
    )


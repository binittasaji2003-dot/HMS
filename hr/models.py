from django.conf import settings
from django.db import models


class HRManager(models.Model):
    hr_id = models.AutoField(primary_key=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hr_profile",
    )

    department = models.ForeignKey(
        "admin_module.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_managers",
    )

    employee_code = models.CharField(
        max_length=30,
        unique=True,
    )

    joining_date = models.DateField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.user.get_username()


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

    duration_minutes = models.PositiveIntegerField()

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
    question_id = models.AutoField(primary_key=True)

    test = models.ForeignKey(
        AptitudeTest,
        on_delete=models.CASCADE,
        related_name="questions",
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
    )

    def __str__(self):
        return self.question[:50]


class AptitudeResult(models.Model):
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

    completed_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.application} - {self.score}/{self.total_marks}"


class Interview(models.Model):
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    interview_id = models.AutoField(primary_key=True)

    application = models.ForeignKey(
        "candidates.JobApplication",
        on_delete=models.CASCADE,
        related_name="interviews",
    )

    interviewer = models.ForeignKey(
        HRManager,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interviews",
    )

    interview_date = models.DateField()

    interview_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SCHEDULED",
    )

    remarks = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.application} - {self.interview_date}"
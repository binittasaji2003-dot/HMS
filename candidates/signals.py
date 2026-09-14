"""Django signals for Candidate notifications and recruitment emails."""
import logging
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import Application, Candidate, Interview, Notification
from .emails import (
    send_shortlisted_email,
    send_aptitude_test_email,
    send_interview_scheduled_email,
    send_selected_email,
    send_rejected_email,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. CANDIDATE REGISTRATION NOTIFICATION
# ==============================================================================
@receiver(post_save, sender=Candidate)
def notify_candidate_on_registration(sender, instance, created, **kwargs):
    """
    Automatically creates a welcome notification when a new candidate registers.
    """
    if created:
        try:
            link = reverse("candidates:profile")
        except Exception:
            link = "/profile/"

        Notification.objects.create(
            candidate=instance,
            title="Welcome to HRMS Portal",
            message="Your candidate account has been successfully created. Complete your profile and explore open job vacancies.",
            notification_type=Notification.NotificationType.REGISTRATION,
            link=link,
        )


# ==============================================================================
# 2. APPLICATION STATUS CHANGE NOTIFICATIONS & EMAILS
# ==============================================================================
@receiver(pre_save, sender=Application)
def track_application_status_change(sender, instance, **kwargs):
    """
    Detects if the Application status has changed prior to saving to database.
    """
    if instance.pk:
        try:
            old_status = Application.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
            if old_status and old_status != instance.status:
                instance._status_changed_from = old_status
                instance._status_changed_to = instance.status
        except Exception:
            pass


@receiver(post_save, sender=Application)
def notify_candidate_on_status_change(sender, instance, created, **kwargs):
    """
    Automatically creates a Candidate Notification and dispatches emails
    whenever HR changes the application status.
    Supported statuses:
    - RESUME_REVIEW -> "Resume Under Review"
    - SHORTLISTED -> "Application Shortlisted" (+ Email)
    - APTITUDE_TEST -> "Aptitude Test Assigned" (+ Email)
    - INTERVIEW_SCHEDULED -> "Interview Scheduled" (+ Email)
    - SELECTED -> "Application Selected" (+ Email)
    - REJECTED -> "Application Decision" (+ Email)
    """
    if created:
        return  # Initial application creation notification and email handled in apply view

    if hasattr(instance, "_status_changed_to"):
        new_status = instance._status_changed_to
        job_title = instance.job.title if instance.job else "Position"

        notification_templates = {
            Application.Status.RESUME_REVIEW: {
                "title": "Resume Under Review",
                "message": f"Your application for {job_title} is now under review by the recruitment team.",
                "type": Notification.NotificationType.APPLICATION,
            },
            Application.Status.SHORTLISTED: {
                "title": "Application Shortlisted",
                "message": f"Congratulations! Your application for {job_title} has been shortlisted for further evaluation.",
                "type": Notification.NotificationType.APPLICATION,
            },
            Application.Status.APTITUDE_TEST: {
                "title": "Aptitude Test Assigned",
                "message": f"An aptitude assessment has been assigned for your application for {job_title}.",
                "type": Notification.NotificationType.APTITUDE,
            },
            Application.Status.INTERVIEW_SCHEDULED: {
                "title": "Interview Scheduled",
                "message": f"An interview round has been scheduled for your application for {job_title}.",
                "type": Notification.NotificationType.INTERVIEW,
            },
            Application.Status.SELECTED: {
                "title": "Application Selected",
                "message": f"Congratulations! You have been selected for the position of {job_title}.",
                "type": Notification.NotificationType.APPLICATION,
            },
            Application.Status.REJECTED: {
                "title": "Application Decision",
                "message": f"Your application for {job_title} has been reviewed and will not be proceeding further.",
                "type": Notification.NotificationType.APPLICATION,
            },
        }

        template_info = notification_templates.get(new_status)
        if template_info:
            try:
                link = reverse("candidates:application_details", kwargs={"application_id": instance.application_id})
            except Exception:
                link = f"/applications/{instance.application_id}/"

            Notification.objects.create(
                candidate=instance.candidate,
                title=template_info["title"],
                message=template_info["message"],
                notification_type=template_info["type"],
                link=link,
            )

        # Dispatch emails based on recruitment milestones
        try:
            if new_status == Application.Status.SHORTLISTED:
                send_shortlisted_email(instance)
            elif new_status == Application.Status.APTITUDE_TEST:
                send_aptitude_test_email(instance)
            elif new_status == Application.Status.INTERVIEW_SCHEDULED:
                # Check for existing scheduled interview
                interview = instance.interviews.filter(status=Interview.Status.SCHEDULED).order_by("-date").first()
                send_interview_scheduled_email(instance, interview=interview)
            elif new_status == Application.Status.SELECTED:
                send_selected_email(instance)
                # Dispatch signal for existing HR/Admin onboarding integration
                try:
                    from .onboarding import candidate_selected_for_onboarding
                    candidate_selected_for_onboarding.send(
                        sender=Application,
                        application=instance,
                        candidate=instance.candidate,
                        job=instance.job,
                        department=instance.job.department if instance.job else None,
                    )
                except Exception as exc:
                    logger.error("Error dispatching candidate_selected_for_onboarding: %s", exc)
            elif new_status == Application.Status.REJECTED:
                send_rejected_email(instance)
        except Exception as exc:
            logger.error("Failed to send status update email for application %s: %s", instance.pk, exc)

        # Clear state tracking to prevent duplicate triggers
        delattr(instance, "_status_changed_to")
        if hasattr(instance, "_status_changed_from"):
            delattr(instance, "_status_changed_from")


# ==============================================================================
# 3. INTERVIEW RECORD CREATION & UPDATE NOTIFICATIONS
# ==============================================================================
@receiver(pre_save, sender=Interview)
def track_interview_status_change(sender, instance, **kwargs):
    """
    Detects if an Interview status, date, or time has changed.
    """
    if instance.pk:
        try:
            old = Interview.objects.filter(pk=instance.pk).values("status", "date", "time").first()
            if old:
                if old["status"] != instance.status or old["date"] != instance.date or old["time"] != instance.time:
                    instance._interview_changed = True
                    instance._old_status = old["status"]
        except Exception:
            pass


@receiver(post_save, sender=Interview)
def notify_candidate_on_interview_creation(sender, instance, created, **kwargs):
    """
    When an interview is scheduled or rescheduled directly by HR/admin, ensures notification
    and interview invitation email are sent.
    """
    try:
        link = reverse("candidates:interview_details", kwargs={"interview_id": instance.interview_id})
    except Exception:
        link = f"/interviews/{instance.interview_id}/"

    date_str = instance.date.strftime("%d %b %Y") if hasattr(instance.date, "strftime") else str(instance.date)
    time_str = instance.time.strftime("%I:%M %p") if hasattr(instance.time, "strftime") else str(instance.time)

    if created and instance.status == Interview.Status.SCHEDULED:
        notif_exists = Notification.objects.filter(
            candidate=instance.candidate,
            title__icontains="Interview Scheduled",
            link=link,
        ).exists()

        if not notif_exists:
            Notification.objects.create(
                candidate=instance.candidate,
                title="Interview Scheduled",
                message=f"Your {instance.interview_round} has been scheduled for {date_str} at {time_str}.",
                notification_type=Notification.NotificationType.INTERVIEW,
                link=link,
            )
            try:
                send_interview_scheduled_email(instance.application, interview=instance)
            except Exception as exc:
                logger.error("Failed to send interview email for %s: %s", instance.pk, exc)

    elif not created and getattr(instance, "_interview_changed", False):
        if instance.status == Interview.Status.RESCHEDULED:
            Notification.objects.create(
                candidate=instance.candidate,
                title="Interview Rescheduled",
                message=f"Your {instance.interview_round} has been rescheduled to {date_str} at {time_str}.",
                notification_type=Notification.NotificationType.INTERVIEW,
                link=link,
            )
            try:
                send_interview_scheduled_email(instance.application, interview=instance)
            except Exception as exc:
                logger.error("Failed to send rescheduled interview email for %s: %s", instance.pk, exc)


# ==============================================================================
# 4. BROADCAST ANNOUNCEMENTS HELPER
# ==============================================================================
def broadcast_announcement(title, message, candidate=None, link="/"):
    """
    Broadcasts an announcement notification to a specific candidate or all candidates.
    """
    if candidate:
        candidates = [candidate]
    else:
        candidates = list(Candidate.objects.all())

    notifications = [
        Notification(
            candidate=c,
            title=title,
            message=message,
            notification_type=Notification.NotificationType.GENERAL,
            link=link,
        )
        for c in candidates
    ]
    return Notification.objects.bulk_create(notifications)


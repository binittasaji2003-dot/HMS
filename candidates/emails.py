"""Email notification dispatcher for Candidate portal recruitment workflows."""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_candidate_email(candidate, subject, message_text, fail_silently=True):
    """
    Sends an email to a candidate using Django's email system.
    Never hardcodes passwords or SMTP credentials; uses configured EMAIL_BACKEND.
    """
    recipient_email = None
    if hasattr(candidate, "user") and candidate.user and candidate.user.email:
        recipient_email = candidate.user.email
    elif isinstance(candidate, str) and "@" in candidate:
        recipient_email = candidate

    if not recipient_email:
        logger.warning("No recipient email available for candidate %s", candidate)
        return False

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "recruitment@company.com")

    try:
        send_mail(
            subject=subject,
            message=message_text,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=fail_silently,
        )
        return True
    except Exception as exc:
        logger.error("Failed to dispatch email to %s: %s", recipient_email, exc)
        if not fail_silently:
            raise
        return False


def send_application_submitted_email(application):
    """Dispatches application confirmation email to the candidate."""
    candidate = application.candidate
    job = application.job
    subject = f"Application Confirmation: {job.title} [{application.application_code}]"
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"Thank you for applying for the position of {job.title} at our organization.\n"
        f"We have successfully received your application.\n\n"
        f"Application Details:\n"
        f"--------------------\n"
        f"Application ID: {application.application_code}\n"
        f"Position: {job.title}\n"
        f"Department: {job.department.name if job.department else 'N/A'}\n"
        f"Applied Date: {application.applied_at.strftime('%d %B %Y')}\n"
        f"Current Status: Applied\n\n"
        f"You can monitor the progress of your application and upcoming recruitment milestones "
        f"anytime on your HRMS Candidate Portal.\n\n"
        f"Best regards,\n"
        f"HR Recruitment Team\n"
        f"HRMS Portal"
    )
    return send_candidate_email(candidate, subject, body)


def send_shortlisted_email(application):
    """Dispatches email notification when a candidate's application is shortlisted."""
    candidate = application.candidate
    job = application.job
    subject = f"Application Shortlisted: {job.title}"
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"Congratulations! We are pleased to inform you that your application for the position of "
        f"{job.title} (Ref: {application.application_code}) has been shortlisted by our recruitment team.\n\n"
        f"Our team was impressed by your credentials and experience. The next stage of the evaluation "
        f"process will be communicated to you shortly via your Candidate Portal.\n\n"
        f"Please check your notifications and application details regularly for updates.\n\n"
        f"Best regards,\n"
        f"HR Recruitment Team\n"
        f"HRMS Portal"
    )
    return send_candidate_email(candidate, subject, body)


def send_aptitude_test_email(application, test=None):
    """Dispatches email notification when an aptitude test is assigned or scheduled."""
    candidate = application.candidate
    job = application.job
    test_title = test.title if test else "Candidate Competency Assessment"
    subject = f"Aptitude Assessment Scheduled: {job.title}"
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"An aptitude assessment ({test_title}) has been assigned for your application "
        f"for {job.title} (Ref: {application.application_code}).\n\n"
        f"Assessment Details:\n"
        f"-------------------\n"
        f"Assessment: {test_title}\n"
        f"Position: {job.title}\n\n"
        f"Please log in to your Candidate Portal to review assessment guidelines and complete the test.\n\n"
        f"Best regards,\n"
        f"Talent Acquisition & Assessment Team\n"
        f"HRMS Portal"
    )
    return send_candidate_email(candidate, subject, body)


def send_interview_scheduled_email(application=None, interview=None):
    """Dispatches email notification when an interview round is scheduled."""
    if application:
        candidate = application.candidate
        job = application.job
        app_code = application.application_code
    elif interview:
        candidate = interview.candidate
        job = interview.job
        app_code = interview.application.application_code if interview.application else "Direct Schedule"
    else:
        return False

    round_name = interview.interview_round if interview else "Technical Interview"
    date_str = interview.date.strftime("%d %B %Y") if (interview and hasattr(interview.date, "strftime")) else str(getattr(interview, "date", "To be announced"))
    time_str = interview.time.strftime("%I:%M %p") if (interview and hasattr(interview.time, "strftime")) else str(getattr(interview, "time", "TBA"))
    mode_str = interview.get_mode_display() if interview else "Online Video Call"
    meeting_info = interview.meeting_link if (interview and interview.meeting_link) else "Link provided in portal"

    job_title = job.title if job else "Position"
    subject = f"Interview Scheduled: {job_title} - {round_name}"
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"We are pleased to invite you for an interview for the {job_title} position.\n\n"
        f"Interview Details:\n"
        f"------------------\n"
        f"Application Reference: {app_code}\n"
        f"Round: {round_name}\n"
        f"Date: {date_str}\n"
        f"Time: {time_str}\n"
        f"Mode: {mode_str}\n"
        f"Meeting Link / Venue: {meeting_info}\n\n"
        f"Instructions:\n"
        f"Please ensure a quiet environment with stable internet connectivity. "
        f"Join the session 5 minutes prior to the scheduled time.\n\n"
        f"Best regards,\n"
        f"HR Recruitment & Interview Panel\n"
        f"HRMS Portal"
    )
    return send_candidate_email(candidate, subject, body)


def send_selected_email(application):
    """Dispatches job offer and selection notification email."""
    candidate = application.candidate
    job = application.job
    subject = f"Congratulations! Selection Offer: {job.title}"
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"Heartiest congratulations! Following your interviews and assessments, we are thrilled to offer "
        f"you the position of {job.title} ({job.department.name if job.department else 'Engineering'}).\n\n"
        f"Our HR Operations team will reach out with the formal offer letter, salary breakdown, and onboarding "
        f"schedule shortly.\n\n"
        f"We are excited about the prospect of you joining our team!\n\n"
        f"Warm regards,\n"
        f"Head of Human Resources\n"
        f"HRMS Portal"
    )
    return send_candidate_email(candidate, subject, body)


def send_rejected_email(application):
    """Dispatches recruitment decision notification email."""
    candidate = application.candidate
    job = application.job
    subject = f"Application Status Update: {job.title}"
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"Thank you for taking the time to apply for the position of {job.title} and for your interest "
        f"in joining our organization.\n\n"
        f"After careful consideration and review of all candidates, we regret to inform you that we will "
        f"not be proceeding further with your application for this specific opening.\n\n"
        f"We sincerely appreciate your interest and time, and we wish you every success in your "
        f"professional endeavors.\n\n"
        f"Best regards,\n"
        f"Talent Acquisition Team\n"
        f"HRMS Portal"
    )
    return send_candidate_email(candidate, subject, body)

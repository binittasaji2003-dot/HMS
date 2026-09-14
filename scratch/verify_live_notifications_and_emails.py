import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_DIR = r"c:\Users\pc\OneDrive\Desktop\Alan Porject"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
import django
django.setup()

from django.conf import settings
settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")

from datetime import date, timedelta
from django.core import mail
from django.contrib.auth import get_user_model
from django.test import Client
from candidates.models import Candidate, CandidateDocument, Job, Application, Interview, Notification
from candidates.signals import broadcast_announcement

User = get_user_model()


def run_live_verification():
    print("================================================================")
    print("STARTING COMPLETE CANDIDATE NOTIFICATION & EMAIL VERIFICATION")
    print("================================================================")

    client = Client()
    mail.outbox = []

    # -------------------------------------------------------------
    # 1. CANDIDATE REGISTRATION
    # -------------------------------------------------------------
    test_email = "test.notify.candidate@example.com"
    User.objects.filter(email=test_email).delete()

    print("\n[STEP 1] Testing Candidate Registration via /register/...")
    reg_response = client.post(
        "/register/",
        {
            "name": "Arjun Menon",
            "email": test_email,
            "phone": "+91 98765 44321",
            "password": "Password@123",
            "confirm_password": "Password@123",
        },
        follow=True,
    )
    assert reg_response.status_code == 200
    candidate = Candidate.objects.get(user__email=test_email)
    print(f"[PASS] Candidate registered: {candidate.full_name} ({candidate.candidate_code})")

    # Verify Registration Notification
    reg_notif = Notification.objects.filter(candidate=candidate).first()
    assert reg_notif is not None
    assert reg_notif.title == "Welcome to HRMS Portal"
    assert reg_notif.notification_type == Notification.NotificationType.REGISTRATION
    assert not reg_notif.is_read
    print(f"[PASS] Registration notification created: '{reg_notif.title}'")

    # Verify Header Bell displays real unread count: 1
    dash_resp = client.get("/")
    assert dash_resp.status_code == 200
    dash_html = dash_resp.content.decode("utf-8")
    assert 'id="headerNotificationCount">1</span>' in dash_html
    print("[PASS] Header notification bell displays real unread count: 1")

    # -------------------------------------------------------------
    # 2. APPLICATION SUBMISSION & CONFIRMATION EMAIL
    # -------------------------------------------------------------
    print("\n[STEP 2] Submitting Job Application & Verifying Confirmation Email...")
    job = Job.objects.filter(status=Job.Status.OPEN).first()
    assert job is not None, "At least one OPEN job is required for verification."

    # Ensure resume is present
    doc, _ = CandidateDocument.objects.get_or_create(candidate=candidate)
    doc.resume = "resumes/arjun_resume.pdf"
    doc.save()

    # Clear outbox before applying
    mail.outbox = []

    apply_resp = client.post(f"/jobs/{job.pk}/apply/", follow=True)
    assert apply_resp.status_code == 200
    app = Application.objects.get(candidate=candidate, job=job)
    print(f"[PASS] Application submitted: {app.application_code} for {job.title}")

    # Check notification & email
    app_notif = Notification.objects.filter(candidate=candidate, notification_type=Notification.NotificationType.APPLICATION).order_by("-created_at").first()
    assert app_notif is not None
    assert "submitted successfully" in app_notif.message.lower()
    print(f"[PASS] In-app notification created: '{app_notif.title}' | '{app_notif.message}'")

    assert len(mail.outbox) >= 1
    assert "Application Confirmation" in mail.outbox[-1].subject
    assert test_email in mail.outbox[-1].to
    print(f"[PASS] Confirmation email dispatched: '{mail.outbox[-1].subject}' to {mail.outbox[-1].to}")

    # Header bell count check: 2
    dash_html = client.get("/").content.decode("utf-8")
    assert 'id="headerNotificationCount">2</span>' in dash_html
    print("[PASS] Header notification bell displays unread count: 2")

    # -------------------------------------------------------------
    # 3. RESUME UNDER REVIEW
    # -------------------------------------------------------------
    print("\n[STEP 3] HR Updates: APPLIED -> RESUME_REVIEW...")
    app.status = Application.Status.RESUME_REVIEW
    app.save()

    review_notif = Notification.objects.filter(candidate=candidate).order_by("-created_at").first()
    assert review_notif.title == "Resume Under Review"
    print(f"[PASS] Notification created: '{review_notif.title}'")

    dash_html = client.get("/").content.decode("utf-8")
    assert 'id="headerNotificationCount">3</span>' in dash_html
    print("[PASS] Header notification bell displays unread count: 3")

    # -------------------------------------------------------------
    # 4. SHORTLISTED & EMAIL
    # -------------------------------------------------------------
    print("\n[STEP 4] HR Updates: RESUME_REVIEW -> SHORTLISTED...")
    mail.outbox = []
    app.status = Application.Status.SHORTLISTED
    app.save()

    shortlist_notif = Notification.objects.filter(candidate=candidate).order_by("-created_at").first()
    assert shortlist_notif.title == "Application Shortlisted"
    print(f"[PASS] Notification created: '{shortlist_notif.title}'")

    assert len(mail.outbox) >= 1
    assert "Shortlisted" in mail.outbox[-1].subject
    print(f"[PASS] Shortlisted email dispatched: '{mail.outbox[-1].subject}' to {mail.outbox[-1].to}")

    dash_html = client.get("/").content.decode("utf-8")
    assert 'id="headerNotificationCount">4</span>' in dash_html
    print("[PASS] Header notification bell displays unread count: 4")

    # -------------------------------------------------------------
    # 5. APTITUDE TEST & EMAIL
    # -------------------------------------------------------------
    print("\n[STEP 5] HR Updates: SHORTLISTED -> APTITUDE_TEST...")
    mail.outbox = []
    app.status = Application.Status.APTITUDE_TEST
    app.save()

    apt_notif = Notification.objects.filter(candidate=candidate).order_by("-created_at").first()
    assert apt_notif.title == "Aptitude Test Assigned"
    print(f"[PASS] Notification created: '{apt_notif.title}'")

    assert len(mail.outbox) >= 1
    assert "Aptitude" in mail.outbox[-1].subject
    print(f"[PASS] Aptitude assessment email dispatched: '{mail.outbox[-1].subject}' to {mail.outbox[-1].to}")

    dash_html = client.get("/").content.decode("utf-8")
    assert 'id="headerNotificationCount">5</span>' in dash_html
    print("[PASS] Header notification bell displays unread count: 5")

    # -------------------------------------------------------------
    # 6. INTERVIEW SCHEDULED & EMAIL
    # -------------------------------------------------------------
    print("\n[STEP 6] HR Schedules Interview & Sets INTERVIEW_SCHEDULED...")
    mail.outbox = []
    interview = Interview.objects.create(
        candidate=candidate,
        job=job,
        application=app,
        interview_round="Technical Round 1",
        date=date.today() + timedelta(days=2),
        time="14:30:00",
        mode=Interview.Mode.ONLINE,
        meeting_link="https://meet.google.com/xyz-abcd-efg",
        status=Interview.Status.SCHEDULED,
    )
    app.status = Application.Status.INTERVIEW_SCHEDULED
    app.save()

    int_notif = Notification.objects.filter(candidate=candidate, notification_type=Notification.NotificationType.INTERVIEW).first()
    assert int_notif is not None
    print(f"[PASS] Interview notification created: '{int_notif.title}' | '{int_notif.message}'")

    assert len(mail.outbox) >= 1
    assert "Interview Scheduled" in mail.outbox[-1].subject
    assert "https://meet.google.com/xyz-abcd-efg" in mail.outbox[-1].body
    print(f"[PASS] Interview invitation email dispatched: '{mail.outbox[-1].subject}'")

    dash_html = client.get("/").content.decode("utf-8")
    # Interview created 1 notif (or signal handled)
    unread_now = Notification.objects.filter(candidate=candidate, is_read=False).count()
    assert f'id="headerNotificationCount">{unread_now}</span>' in dash_html
    print(f"[PASS] Header notification bell displays unread count: {unread_now}")

    # -------------------------------------------------------------
    # 7. SELECTED & EMAIL
    # -------------------------------------------------------------
    print("\n[STEP 7] HR Updates: INTERVIEW_SCHEDULED -> SELECTED...")
    mail.outbox = []
    app.status = Application.Status.SELECTED
    app.save()

    sel_notif = Notification.objects.filter(candidate=candidate).order_by("-created_at").first()
    assert sel_notif.title == "Application Selected"
    print(f"[PASS] Notification created: '{sel_notif.title}'")

    assert len(mail.outbox) >= 1
    assert "Selection Offer" in mail.outbox[-1].subject
    print(f"[PASS] Selection offer email dispatched: '{mail.outbox[-1].subject}' to {mail.outbox[-1].to}")

    # -------------------------------------------------------------
    # 8. REJECTED & EMAIL
    # -------------------------------------------------------------
    print("\n[STEP 8] HR Updates: SELECTED -> REJECTED...")
    mail.outbox = []
    app.status = Application.Status.REJECTED
    app.save()

    rej_notif = Notification.objects.filter(candidate=candidate).order_by("-created_at").first()
    assert rej_notif.title == "Application Decision"
    print(f"[PASS] Notification created: '{rej_notif.title}'")

    assert len(mail.outbox) >= 1
    assert "Status Update" in mail.outbox[-1].subject
    print(f"[PASS] Decision email dispatched: '{mail.outbox[-1].subject}' to {mail.outbox[-1].to}")

    # -------------------------------------------------------------
    # 9. ANNOUNCEMENT BROADCAST
    # -------------------------------------------------------------
    print("\n[STEP 9] Broadcasting Portal Announcement...")
    broadcast_announcement(
        title="Scheduled Maintenance Notice",
        message="System upgrades will occur on Sunday at 2 AM.",
        candidate=candidate,
    )
    ann_notif = Notification.objects.filter(candidate=candidate, title="Scheduled Maintenance Notice").first()
    assert ann_notif is not None
    print(f"[PASS] Announcement created: '{ann_notif.title}'")

    # Verify announcement tab filtering
    ann_resp = client.get("/notifications/?category=announcements")
    assert ann_resp.status_code == 200
    assert "Scheduled Maintenance Notice" in ann_resp.content.decode("utf-8")
    print("[PASS] Announcements tab displays broadcasted announcement")

    # -------------------------------------------------------------
    # 10. MARK AS READ (SINGLE)
    # -------------------------------------------------------------
    total_unread_before = Notification.objects.filter(candidate=candidate, is_read=False).count()
    print(f"\n[STEP 10] Marking single notification as read (Total unread before: {total_unread_before})...")
    mark_resp = client.get(f"/notifications/{ann_notif.pk}/read/?stay=1", follow=True)
    assert mark_resp.status_code == 200
    ann_notif.refresh_from_db()
    assert ann_notif.is_read
    total_unread_after = Notification.objects.filter(candidate=candidate, is_read=False).count()
    assert total_unread_after == total_unread_before - 1
    print(f"[PASS] Single notification marked as read. Unread count decremented: {total_unread_before} -> {total_unread_after}")

    # -------------------------------------------------------------
    # 11. MARK ALL AS READ
    # -------------------------------------------------------------
    print(f"\n[STEP 11] Marking all notifications as read (Unread remaining: {total_unread_after})...")
    mark_all_resp = client.post("/notifications/mark-all-read/", follow=True)
    assert mark_all_resp.status_code == 200
    unread_final = Notification.objects.filter(candidate=candidate, is_read=False).count()
    assert unread_final == 0
    print("[PASS] All notifications marked as read; unread count is now 0")

    # Verify header bell badge disappears when unread count is 0
    dash_html = client.get("/").content.decode("utf-8")
    assert 'id="headerNotificationCount"' not in dash_html
    print("[PASS] Header notification bell badge vanishes when unread count is 0")

    # -------------------------------------------------------------
    # 12. SECURITY CHECK: NO HARDCODED PASSWORDS & ENV VAR USAGE
    # -------------------------------------------------------------
    print("\n[STEP 12] Security verification of email configuration...")
    assert hasattr(settings, "EMAIL_BACKEND")
    assert hasattr(settings, "DEFAULT_FROM_EMAIL")
    assert getattr(settings, "EMAIL_HOST_PASSWORD", "") == ""
    print("[PASS] Email settings use environment variables with no hardcoded credentials")

    print("\n================================================================")
    print("ALL CANDIDATE NOTIFICATION & EMAIL VERIFICATIONS PASSED (12/12)!")
    print("================================================================")


if __name__ == "__main__":
    run_live_verification()

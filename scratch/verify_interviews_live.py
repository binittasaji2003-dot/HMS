import os
import sys
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
import django
django.setup()

from django.conf import settings
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")
settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

from django.test import Client
from django.urls import reverse
from django.core import mail
if not hasattr(mail, "outbox"):
    mail.outbox = []
from django.contrib.auth import get_user_model
from candidates.models import Interview, Candidate, Job, Department, Notification

User = get_user_model()

def run_interview_live_verification():
    print("=== STARTING INTERVIEW BACKEND LIVE VERIFICATION ===")
    client = Client()

    # 1. Setup Candidates
    user_a, _ = User.objects.get_or_create(username="live_cand_interview_a", defaults={"email": "cand_a@example.com"})
    user_a.set_password("pass123")
    user_a.save()
    cand_a, _ = Candidate.objects.get_or_create(user=user_a, defaults={"full_name": "Alice Candidate"})

    user_b, _ = User.objects.get_or_create(username="live_cand_interview_b", defaults={"email": "cand_b@example.com"})
    user_b.set_password("pass123")
    user_b.save()
    cand_b, _ = Candidate.objects.get_or_create(user=user_b, defaults={"full_name": "Bob Candidate"})

    # 2. Setup Job
    dept, _ = Department.objects.get_or_create(code="ENG", defaults={"name": "Engineering"})
    job, _ = Job.objects.get_or_create(
        title="Full Stack Python Engineer",
        defaults={
            "department": dept,
            "description": "Full Stack developer",
            "job_type": Job.JobType.FULL_TIME,
            "status": Job.Status.OPEN,
        }
    )

    # 3. Schedule Interview via HR simulation
    mail.outbox.clear()
    today = date.today()
    upcoming_interview = Interview.objects.create(
        candidate=cand_a,
        job=job,
        interview_round="Technical Round 1",
        date=today + timedelta(days=2),
        time="10:30:00",
        mode=Interview.Mode.ONLINE,
        interviewer="Rajesh Menon (Tech Lead)",
        meeting_link="https://meet.google.com/live-demo-room",
        instructions="Prepare system design and live Python coding.",
        status=Interview.Status.SCHEDULED,
    )
    print(f"[1] HR scheduled interview created: ID {upcoming_interview.interview_id}")

    # Verify notification generated
    notif = Notification.objects.filter(candidate=cand_a, notification_type=Notification.NotificationType.INTERVIEW).order_by("-created_at").first()
    assert notif is not None, "In-app notification was not generated"
    assert "Technical Round 1" in notif.message
    assert str(upcoming_interview.interview_id) in notif.link
    print(f"[2] In-app notification confirmed: '{notif.title}' -> '{notif.message}' (Link: {notif.link})")

    # Verify email dispatched
    assert len(mail.outbox) >= 1, "Interview email was not dispatched"
    email = mail.outbox[-1]
    assert "Interview Scheduled" in email.subject
    assert "Technical Round 1" in email.body
    print(f"[3] Interview email confirmed: '{email.subject}' to {email.to}")

    # 4. Previous completed interview
    previous_interview = Interview.objects.create(
        candidate=cand_a,
        job=job,
        interview_round="HR Initial Screening",
        date=today - timedelta(days=5),
        time="15:00:00",
        mode=Interview.Mode.ONLINE,
        interviewer="Pooja Sharma (Talent Lead)",
        status=Interview.Status.COMPLETED,
    )
    print(f"[4] Previous interview created: ID {previous_interview.interview_id}")

    # 5. Candidate A views interview list
    client.login(username="live_cand_interview_a", password="pass123")
    resp_list = client.get(reverse("candidates:interview_list"))
    assert resp_list.status_code == 200, f"Expected 200, got {resp_list.status_code}"
    html = resp_list.content.decode()
    assert "Technical Round 1" in html
    assert "HR Initial Screening" in html
    assert "https://meet.google.com/live-demo-room" in html
    assert "Rajesh Menon (Tech Lead)" in html
    print("[5] Interview list view rendered with both Upcoming & Previous interviews successfully.")

    # 6. Candidate A views interview details
    resp_details = client.get(reverse("candidates:interview_details", args=[upcoming_interview.interview_id]))
    assert resp_details.status_code == 200, f"Expected 200, got {resp_details.status_code}"
    details_html = resp_details.content.decode()
    assert "Technical Round 1" in details_html
    assert "Prepare system design and live Python coding." in details_html
    assert "https://meet.google.com/live-demo-room" in details_html
    print("[6] Interview details view rendered with meeting link, instructions, and panel.")

    # 7. Candidate B unauthorized access check
    client_b = Client()
    client_b.login(username="live_cand_interview_b", password="pass123")
    resp_unauth = client_b.get(reverse("candidates:interview_details", args=[upcoming_interview.interview_id]))
    assert resp_unauth.status_code == 403, f"Expected 403 Forbidden, got {resp_unauth.status_code}"
    print("[7] Cross-candidate isolation confirmed: Candidate B blocked with 403 PermissionDenied.")

    # 8. Candidate cannot edit interview via POST
    resp_post = client.post(
        reverse("candidates:interview_details", args=[upcoming_interview.interview_id]),
        {"date": "2026-12-31", "interviewer": "Hacked Interviewer"},
    )
    # The view is read-only (renders template or rejects POST, does not mutate DB)
    upcoming_interview.refresh_from_db()
    assert upcoming_interview.interviewer == "Rajesh Menon (Tech Lead)"
    print("[8] Read-only integrity verified: interview fields cannot be modified by candidate.")

    print("=== ALL INTERVIEW VERIFICATION CHECKS PASSED PERFECTLY ===")

if __name__ == "__main__":
    run_interview_live_verification()

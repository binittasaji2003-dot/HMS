import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
import django
django.setup()

from django.conf import settings
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append("testserver")

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from candidates.models import AptitudeTest, Question, TestResult, Candidate, Job, Department, Notification
import json

User = get_user_model()

def run_live_verification():
    print("=== STARTING APTITUDE TEST LIVE VERIFICATION ===")
    client = Client()

    # 1. Setup or retrieve live candidate
    user, _ = User.objects.get_or_create(
        username="live_aptitude_candidate",
        defaults={"email": "aptitude_candidate@example.com", "first_name": "Alan", "last_name": "Candidate"},
    )
    user.set_password("SecurePass2026!")
    user.save()
    candidate, _ = Candidate.objects.get_or_create(user=user, defaults={"full_name": "Alan Candidate"})

    # 2. Setup Department and Job
    dept, _ = Department.objects.get_or_create(code="ENG", defaults={"name": "Engineering"})
    job, _ = Job.objects.get_or_create(
        title="Senior Python Engineer",
        defaults={
            "department": dept,
            "description": "Senior Python role",
            "job_type": Job.JobType.FULL_TIME,
            "status": Job.Status.OPEN,
        }
    )

    # 3. Create or reset Test & Questions
    test, _ = AptitudeTest.objects.get_or_create(
        title="Python Live Assessment",
        defaults={
            "job": job,
            "description": "End-to-end live verification test",
            "duration_minutes": 25,
            "total_questions": 3,
            "passing_percentage": 66,
            "status": AptitudeTest.Status.ACTIVE,
            "is_active": True,
        }
    )
    test.assigned_candidates.add(candidate)
    test.questions.all().delete()
    TestResult.objects.filter(candidate=candidate, test=test).delete()

    q1 = Question.objects.create(
        test=test,
        question_text="What is the output of bool([])?",
        option_a="True",
        option_b="False",
        option_c="None",
        option_d="Error",
        correct_option=Question.CorrectOption.B,
    )
    q2 = Question.objects.create(
        test=test,
        question_text="Which keyword creates an anonymous function?",
        option_a="def",
        option_b="anon",
        option_c="lambda",
        option_d="func",
        correct_option=Question.CorrectOption.C,
    )
    q3 = Question.objects.create(
        test=test,
        question_text="Which collection is unindexed and contains unique elements?",
        option_a="List",
        option_b="Tuple",
        option_c="Dictionary",
        option_d="Set",
        correct_option=Question.CorrectOption.D,
    )

    print("[1] Test & Questions created successfully.")
    print(f"    Test duration property: {test.duration}m | passing_score property: {test.passing_score}%")
    assert test.duration == 25
    assert test.passing_score == 66
    assert q1.correct_answer == "B"

    # 4. Authenticate
    client.login(username="live_aptitude_candidate", password="SecurePass2026!")

    # 5. GET /aptitude/
    resp = client.get(reverse("candidates:aptitude_list"))
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert "Python Live Assessment" in resp.content.decode()
    print("[2] Aptitude list view rendered available tests successfully.")

    # 6. GET /aptitude/<id>/
    resp_test = client.get(reverse("candidates:aptitude_test", args=[test.test_id]))
    assert resp_test.status_code == 200, f"Expected 200, got {resp_test.status_code}"
    content_str = resp_test.content.decode()
    # SECURITY ASSERTION: Correct answers are never sent to client
    assert "correct_option" not in content_str
    assert "correct_answer" not in content_str
    assert '"correct":' not in content_str
    print("[3] Test environment rendered cleanly. Verified: zero correct answer exposure in payload.")

    # 7. POST /aptitude/<id>/submit/ with 2 correct, 1 wrong (66.67% >= 66% -> PASS)
    submitted_answers = {
        str(q1.question_id): "B",  # Correct
        str(q2.question_id): "C",  # Correct
        str(q3.question_id): "A",  # Wrong (correct is D)
    }
    submit_resp = client.post(
        reverse("candidates:aptitude_submit", args=[test.test_id]),
        {"answers_json": json.dumps(submitted_answers), "fake_client_score": "100"},
        follow=True,
    )
    assert submit_resp.status_code == 200
    print("[4] Assessment submitted.")

    # 8. Verify TestResult in DB
    result = TestResult.objects.filter(candidate=candidate, test=test).first()
    assert result is not None, "TestResult was not created"
    assert result.correct_answers == 2, f"Expected 2 correct, got {result.correct_answers}"
    assert result.incorrect_answers == 1, f"Expected 1 incorrect, got {result.incorrect_answers}"
    assert result.is_passed is True, "Expected is_passed to be True"
    assert float(result.score_percentage) == 66.67
    assert result.score == 2
    assert result.percentage == result.score_percentage
    assert result.passed is True
    print(f"[5] Score verified strictly by backend: {result.score_percentage}% - Status: {'PASSED' if result.is_passed else 'FAILED'}")

    # 9. Verify Notification created
    notif = Notification.objects.filter(
        candidate=candidate,
        notification_type=Notification.NotificationType.APTITUDE,
    ).order_by("-created_at").first()
    assert notif is not None, "Notification not created"
    assert "Python Live Assessment" in notif.message
    print(f"[6] In-app notification generated: '{notif.title}' -> '{notif.message}'")

    # 10. Verify Duplicate Prevention
    dup_resp = client.post(
        reverse("candidates:aptitude_submit", args=[test.test_id]),
        {"answers_json": json.dumps(submitted_answers)},
        follow=True,
    )
    assert dup_resp.status_code == 200
    assert TestResult.objects.filter(candidate=candidate, test=test).count() == 1
    print("[7] Duplicate submission locked out safely; redirected to existing result.")

    # 11. Verify Result Card Access Control
    other_user, _ = User.objects.get_or_create(username="unauthorized_cand", defaults={"email": "unauth@example.com"})
    other_user.set_password("pass123")
    other_user.save()
    Candidate.objects.get_or_create(user=other_user, defaults={"full_name": "Unauthorized User"})

    other_client = Client()
    other_client.login(username="unauthorized_cand", password="pass123")
    forbidden_resp = other_client.get(reverse("candidates:aptitude_result", args=[result.result_id]))
    assert forbidden_resp.status_code == 403, f"Expected 403 Forbidden, got {forbidden_resp.status_code}"
    print("[8] Unauthorized candidate blocked from viewing other's result (403 PermissionDenied).")

    # 12. Verify Completed Tab in Aptitude List
    list_completed_resp = client.get(reverse("candidates:aptitude_list") + "?tab=completed")
    assert list_completed_resp.status_code == 200
    assert "PASSED" in list_completed_resp.content.decode()
    print("[9] Completed assessment tab displays verified score card.")

    print("=== ALL LIVE VERIFICATION CHECKS PASSED PERFECTLY ===")

if __name__ == "__main__":
    run_live_verification()

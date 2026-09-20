import datetime
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth import get_user_model
from admin_module.models import Department
from candidates.models import Candidate, JobVacancy, JobApplication, CandidateNotification
from hr.models import HRManager, AptitudeTest, AptitudeQuestion, AptitudeAttempt, AptitudeResult

User = get_user_model()


class AptitudeRecruitmentFlowTests(TestCase):
    """
    Comprehensive test suite covering all 27 test cases for the Aptitude Scheduling,
    Timed Test, Auto-Submission, Score Privacy, HR-Only Score Review, and Recruitment Flow.
    """

    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Human Resources", is_active=True)

        # Create HR User & Profile
        self.hr_user = User.objects.create_user(
            email="hr_manager@example.com",
            password="hrpassword123",
            role=User.RoleChoices.HR,
            name="HR Manager",
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR-001",
        )

        # Create Candidate User & Profile
        self.candidate_user = User.objects.create_user(
            email="candidate@example.com",
            password="candpassword123",
            role=User.RoleChoices.CANDIDATE,
            name="Jane Doe",
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            first_name="Jane",
            last_name="Doe",
            phone="1234567890",
        )

        # Create Other Candidate for security checks
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="otherpassword123",
            role=User.RoleChoices.CANDIDATE,
            name="Other Person",
            is_active=True,
        )
        self.other_candidate = Candidate.objects.create(
            user=self.other_user,
            first_name="Other",
            last_name="Person",
        )

        # Create Vacancy
        self.vacancy = JobVacancy.objects.create(
            title="Senior Python Developer",
            department=self.dept,
            description="Python & Django developer position",
            experience_required="3+ years",
            status="OPEN",
            closing_date=timezone.now().date() + datetime.timedelta(days=30),
        )

        # Create Aptitude Test & Questions
        self.test = AptitudeTest.objects.create(
            title="Python & Core Aptitude Assessment",
            duration_minutes=30,
            pass_percentage=60.0,
            total_questions=6,
            status="ACTIVE",
        )

        # 2 Quantitative, 2 Logical, 2 Verbal
        self.q1 = AptitudeQuestion.objects.create(
            test=self.test,
            category="QUANTITATIVE",
            question="What is 15 * 4?",
            option_a="60",
            option_b="50",
            option_c="70",
            option_d="80",
            correct_answer="A",
            is_active=True,
        )
        self.q2 = AptitudeQuestion.objects.create(
            test=self.test,
            category="QUANTITATIVE",
            question="What is the square root of 81?",
            option_a="8",
            option_b="9",
            option_c="7",
            option_d="6",
            correct_answer="B",
            is_active=True,
        )
        self.q3 = AptitudeQuestion.objects.create(
            test=self.test,
            category="LOGICAL",
            question="If all roses are flowers and some flowers fade quickly, do all roses fade quickly?",
            option_a="Cannot be determined",
            option_b="Yes",
            option_c="No",
            option_d="Never",
            correct_answer="A",
            is_active=True,
        )
        self.q4 = AptitudeQuestion.objects.create(
            test=self.test,
            category="LOGICAL",
            question="Which number completes the sequence: 2, 4, 8, 16, ...?",
            option_a="32",
            option_b="24",
            option_c="30",
            option_d="64",
            correct_answer="A",
            is_active=True,
        )
        self.q5 = AptitudeQuestion.objects.create(
            test=self.test,
            category="VERBAL",
            question="Choose the synonym for 'Candid':",
            option_a="Frank",
            option_b="Deceptive",
            option_c="Shy",
            option_d="Hostile",
            correct_answer="A",
            is_active=True,
        )
        self.q6 = AptitudeQuestion.objects.create(
            test=self.test,
            category="VERBAL",
            question="Choose the antonym for 'Vague':",
            option_a="Precise",
            option_b="Ambiguous",
            option_c="Unclear",
            option_d="Doubtful",
            correct_answer="A",
            is_active=True,
        )

        # Create Shortlisted Application
        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.vacancy,
            status="SHORTLISTED",
        )

    # 1. HR Schedules Aptitude Test
    def test_01_hr_schedules_aptitude_test(self):
        self.client.force_login(self.hr_user)
        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        response = self.client.post(
            reverse("hr:schedule_aptitude", kwargs={"pk": self.application.pk}),
            {
                "aptitude_test_id": self.test.pk,
                "aptitude_date": tomorrow.strftime("%Y-%m-%d"),
                "aptitude_time": "10:00",
                "aptitude_duration_minutes": "45",
                "aptitude_passing_score": "65",
                "aptitude_remarks": "Please have your webcam ready and ensure stable internet.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()

        # 2. Status is APTITUDE_TEST_SCHEDULED
        self.assertEqual(self.application.status, "APTITUDE_TEST_SCHEDULED")

        # 3. Schedule fields recorded properly
        self.assertEqual(self.application.aptitude_date, tomorrow)
        self.assertEqual(self.application.aptitude_time, datetime.time(10, 0))
        self.assertEqual(self.application.aptitude_duration_minutes, 45)
        self.assertEqual(self.application.aptitude_passing_score, 65.0)
        self.assertEqual(self.application.aptitude_remarks, "Please have your webcam ready and ensure stable internet.")
        self.assertIsNotNone(self.application.aptitude_start_datetime)
        self.assertIsNotNone(self.application.aptitude_end_datetime)

        # 4. Notification generated
        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="APTITUDE_SCHEDULED",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("45 Minutes", notif.message)
        self.assertIn(self.vacancy.title, notif.message)

    # 5. Candidate Popup Notification for Aptitude Scheduled
    def test_05_candidate_popup_notification_present(self):
        # Create scheduled state
        self.application.status = "APTITUDE_TEST_SCHEDULED"
        self.application.aptitude_date = timezone.now().date() + datetime.timedelta(days=1)
        self.application.aptitude_time = datetime.time(14, 30)
        self.application.aptitude_duration_minutes = 30
        self.application.save()

        notif = CandidateNotification.objects.create(
            candidate=self.candidate,
            application=self.application,
            title="Aptitude Test Scheduled",
            message="Your aptitude test has been scheduled.",
            notification_type="APTITUDE_SCHEDULED",
            is_read=False,
        )

        self.client.force_login(self.candidate_user)
        response = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aptitude Test Scheduled")
        self.assertContains(response, "candidateDecisionModal")

    # 6. Test Window Validation: Early Access Blocked
    def test_06_early_access_blocked(self):
        # Scheduled tomorrow
        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        self.application.status = "APTITUDE_TEST_SCHEDULED"
        self.application.aptitude_test = self.test
        self.application.aptitude_date = tomorrow
        self.application.aptitude_time = datetime.time(10, 0)
        self.application.aptitude_duration_minutes = 30
        self.application.aptitude_start_datetime = timezone.make_aware(datetime.datetime.combine(tomorrow, datetime.time(10, 0)))
        self.application.aptitude_end_datetime = self.application.aptitude_start_datetime + datetime.timedelta(minutes=30)
        self.application.save()

        self.client.force_login(self.candidate_user)
        response = self.client.get(reverse("candidates:take_aptitude_test", kwargs={"application_id": self.application.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("candidates:applications"))

    # 7. Test Window Validation: Late Access Blocked
    def test_07_late_access_blocked(self):
        # Scheduled yesterday
        yesterday = timezone.now().date() - datetime.timedelta(days=1)
        self.application.status = "APTITUDE_TEST_SCHEDULED"
        self.application.aptitude_test = self.test
        self.application.aptitude_date = yesterday
        self.application.aptitude_time = datetime.time(10, 0)
        self.application.aptitude_duration_minutes = 30
        self.application.aptitude_start_datetime = timezone.make_aware(datetime.datetime.combine(yesterday, datetime.time(10, 0)))
        self.application.aptitude_end_datetime = self.application.aptitude_start_datetime + datetime.timedelta(minutes=30)
        self.application.save()

        self.client.force_login(self.candidate_user)
        response = self.client.get(reverse("candidates:take_aptitude_test", kwargs={"application_id": self.application.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("candidates:applications"))

    # 8-13. Active Window: Start Test, Question Shuffling, Privacy & Balanced Pool
    def test_08_to_13_start_test_active_window(self):
        # Set window starting 5 minutes ago, ending in 25 minutes
        now = timezone.now()
        start = now - datetime.timedelta(minutes=5)
        end = now + datetime.timedelta(minutes=25)
        self.application.status = "APTITUDE_TEST_SCHEDULED"
        self.application.aptitude_test = self.test
        self.application.aptitude_date = start.date()
        self.application.aptitude_time = start.time()
        self.application.aptitude_duration_minutes = 30
        self.application.aptitude_start_datetime = start
        self.application.aptitude_end_datetime = end
        self.application.save()

        self.client.force_login(self.candidate_user)
        response = self.client.get(reverse("candidates:take_aptitude_test", kwargs={"application_id": self.application.pk}))
        self.assertEqual(response.status_code, 200)

        # 9. Check AptitudeAttempt created and application status is APTITUDE
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "APTITUDE")

        attempt = AptitudeAttempt.objects.filter(application=self.application).first()
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.test, self.test)
        self.assertFalse(attempt.is_completed)

        # 10. Check balanced categories
        categories = [q["category"] for q in attempt.questions_data]
        self.assertIn("QUANTITATIVE", categories)
        self.assertIn("LOGICAL", categories)
        self.assertIn("VERBAL", categories)

        # 11-12. Shuffling options
        for q in attempt.questions_data:
            keys = [opt["key"] for opt in q["options"]]
            self.assertEqual(sorted(keys), ["A", "B", "C", "D"])

        # 13. Security check: correct_key MUST NOT appear in rendered HTML context
        for q_display in response.context["questions"]:
            self.assertNotIn("correct_key", q_display)
        self.assertNotContains(response, "correct_key")

    # 14. Incremental AJAX Answer Saving
    def test_14_incremental_ajax_answer_saving(self):
        # Create attempt
        now = timezone.now()
        attempt = AptitudeAttempt.objects.create(
            test=self.test,
            application=self.application,
            expires_at=now + datetime.timedelta(minutes=30),
            questions_data=[
                {"question_id": self.q1.pk, "correct_key": "A", "question": "Q1", "options": []},
                {"question_id": self.q2.pk, "correct_key": "B", "question": "Q2", "options": []},
            ],
            answers_data={},
        )
        self.application.status = "APTITUDE"
        self.application.save()

        self.client.force_login(self.candidate_user)
        response = self.client.post(
            reverse("candidates:save_aptitude_answer_ajax", kwargs={"application_id": self.application.pk}),
            {
                "question_id": str(self.q1.pk),
                "selected_option": "A",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["question_id"], str(self.q1.pk))

        attempt.refresh_from_db()
        self.assertEqual(attempt.answers_data.get(str(self.q1.pk)), "A")

    # 15-20. Manual Candidate Submission, Score Privacy, Counts Breakdown & Stage Update
    def test_15_to_20_manual_candidate_submission_and_privacy(self):
        now = timezone.now()
        attempt = AptitudeAttempt.objects.create(
            test=self.test,
            application=self.application,
            expires_at=now + datetime.timedelta(minutes=30),
            questions_data=[
                {"question_id": self.q1.pk, "correct_key": "A", "question": "Q1", "options": []},
                {"question_id": self.q2.pk, "correct_key": "B", "question": "Q2", "options": []},
                {"question_id": self.q3.pk, "correct_key": "A", "question": "Q3", "options": []},
                {"question_id": self.q4.pk, "correct_key": "A", "question": "Q4", "options": []},
            ],
            answers_data={str(self.q1.pk): "A"},  # 1 pre-saved
        )
        self.application.status = "APTITUDE"
        self.application.aptitude_passing_score = 50.0
        self.application.save()

        self.client.force_login(self.candidate_user)
        # Submit Q1: A (Correct), Q2: B (Correct), Q3: C (Incorrect), Q4: Unanswered
        response = self.client.post(
            reverse("candidates:submit_aptitude_test", kwargs={"application_id": self.application.pk}),
            {
                f"question_{self.q1.pk}": "A",
                f"question_{self.q2.pk}": "B",
                f"question_{self.q3.pk}": "C",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("candidates:aptitude_result", kwargs={"application_id": self.application.pk}))

        # 16. Verify submission_type and attempt completion
        attempt.refresh_from_db()
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.submission_type, "CANDIDATE_SUBMITTED")

        # 17. Application status updated to APTITUDE_REVIEW
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "APTITUDE_REVIEW")

        # 15. Verify AptitudeResult score and counts
        result = AptitudeResult.objects.get(application=self.application, test=self.test)
        self.assertEqual(result.score, 2)
        self.assertEqual(result.total_marks, 4)
        self.assertEqual(result.percentage, 50.0)
        self.assertTrue(result.passed)
        self.assertEqual(result.correct_answers_count, 2)
        self.assertEqual(result.incorrect_answers_count, 1)
        self.assertEqual(result.unanswered_count, 1)
        self.assertEqual(result.submission_type, "CANDIDATE_SUBMITTED")

        # 18. Candidate Notification must NOT expose score, percentage or pass/fail
        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="APTITUDE_RESULT",
        ).first()
        self.assertIsNotNone(notif)
        self.assertNotIn("Score", notif.message)
        self.assertNotIn("50", notif.message)
        self.assertNotIn("Passed", notif.message)
        self.assertIn("under review", notif.message)

        # 19. Candidate result view must NOT expose score or pass/fail
        res_page = self.client.get(reverse("candidates:aptitude_result", kwargs={"application_id": self.application.pk}))
        self.assertEqual(res_page.status_code, 200)
        self.assertNotContains(res_page, "Score")
        self.assertNotContains(res_page, "50%")
        self.assertNotContains(res_page, "Passed")
        self.assertContains(res_page, "Aptitude Assessment Submitted")
        self.assertContains(res_page, "Under HR Review")

        # 20. Candidate Applications list must NOT expose score
        apps_page = self.client.get(reverse("candidates:applications"))
        self.assertEqual(apps_page.status_code, 200)
        self.assertContains(apps_page, "Aptitude Assessment Submitted")
        self.assertNotContains(apps_page, "Detailed Scorecard")

    # 21-22. Auto-Submission on Timer Expiration
    def test_21_22_auto_submission_on_expiry(self):
        past = timezone.now() - datetime.timedelta(minutes=10)
        attempt = AptitudeAttempt.objects.create(
            test=self.test,
            application=self.application,
            expires_at=past,
            questions_data=[
                {"question_id": self.q1.pk, "correct_key": "A", "question": "Q1", "options": []},
                {"question_id": self.q2.pk, "correct_key": "B", "question": "Q2", "options": []},
            ],
            answers_data={str(self.q1.pk): "A"},
        )
        self.application.status = "APTITUDE"
        self.application.save()

        self.client.force_login(self.candidate_user)
        # Hitting take_aptitude_test with expired attempt triggers auto-submit
        response = self.client.get(reverse("candidates:take_aptitude_test", kwargs={"application_id": self.application.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("candidates:aptitude_result", kwargs={"application_id": self.application.pk}))

        attempt.refresh_from_db()
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.submission_type, "AUTO_SUBMITTED")

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "APTITUDE_REVIEW")

        result = AptitudeResult.objects.get(application=self.application)
        self.assertEqual(result.submission_type, "AUTO_SUBMITTED")
        self.assertEqual(result.score, 1)
        self.assertEqual(result.unanswered_count, 1)

    # 23. HR-Only Scorecard Review Page
    def test_23_hr_scorecard_review_page(self):
        now = timezone.now()
        attempt = AptitudeAttempt.objects.create(
            test=self.test,
            application=self.application,
            expires_at=now,
            is_completed=True,
            completed_at=now,
            submission_type="CANDIDATE_SUBMITTED",
            questions_data=[
                {
                    "question_id": self.q1.pk,
                    "category": "QUANTITATIVE",
                    "category_display": "Quantitative Aptitude",
                    "question": "What is 15 * 4?",
                    "correct_key": "A",
                    "options": [{"key": "A", "text": "60"}, {"key": "B", "text": "50"}],
                }
            ],
            answers_data={str(self.q1.pk): "A"},
        )
        result = AptitudeResult.objects.create(
            test=self.test,
            application=self.application,
            score=1,
            total_marks=1,
            percentage=100.0,
            passed=True,
            correct_answers_count=1,
            incorrect_answers_count=0,
            unanswered_count=0,
            submission_type="CANDIDATE_SUBMITTED",
        )
        self.application.status = "APTITUDE_REVIEW"
        self.application.save()

        self.client.force_login(self.hr_user)
        response = self.client.get(reverse("hr:aptitude_review", kwargs={"pk": self.application.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100%")
        self.assertContains(response, "Candidate Submitted")
        self.assertContains(response, "Quantitative Aptitude")
        self.assertContains(response, "Proceed to Interview")

    # 24. HR Decision: Proceed to Interview
    def test_24_hr_decision_proceed_to_interview(self):
        self.application.status = "APTITUDE_REVIEW"
        self.application.save()

        self.client.force_login(self.hr_user)
        response = self.client.post(
            reverse("hr:aptitude_decision", kwargs={"pk": self.application.pk}),
            {
                "decision": "INTERVIEW",
                "hr_comments": "Strong analytical performance. Proceeding to technical interview.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertIn(self.application.status, ["INTERVIEW", "INTERVIEW_SCHEDULING"])

    # 25. HR Decision: Reject
    def test_25_hr_decision_reject(self):
        self.application.status = "APTITUDE_REVIEW"
        self.application.save()

        self.client.force_login(self.hr_user)
        response = self.client.post(
            reverse("hr:aptitude_decision", kwargs={"pk": self.application.pk}),
            {
                "decision": "REJECT",
                "hr_comments": "Did not meet required cutoff score.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "REJECTED")

    # 26. HR Reschedules Aptitude Test
    def test_26_hr_reschedule_aptitude_test(self):
        self.application.status = "APTITUDE_TEST_SCHEDULED"
        self.application.aptitude_test = self.test
        self.application.aptitude_date = timezone.now().date() + datetime.timedelta(days=1)
        self.application.aptitude_time = datetime.time(10, 0)
        self.application.save()

        new_date = timezone.now().date() + datetime.timedelta(days=3)
        self.client.force_login(self.hr_user)
        response = self.client.post(
            reverse("hr:reschedule_aptitude", kwargs={"pk": self.application.pk}),
            {
                "aptitude_date": new_date.strftime("%Y-%m-%d"),
                "aptitude_time": "15:00",
                "aptitude_duration_minutes": "40",
                "reschedule_reason": "Candidate requested alternative afternoon slot.",
                "aptitude_remarks": "Updated session remarks.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "APTITUDE_TEST_SCHEDULED")
        self.assertEqual(self.application.aptitude_date, new_date)
        self.assertEqual(self.application.aptitude_time, datetime.time(15, 0))

        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="APTITUDE_RESCHEDULED",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Candidate requested alternative afternoon slot", notif.message)

    # 27. HR Cancels Aptitude Test
    def test_27_hr_cancel_aptitude_test(self):
        self.application.status = "APTITUDE_TEST_SCHEDULED"
        self.application.aptitude_test = self.test
        self.application.aptitude_date = timezone.now().date() + datetime.timedelta(days=1)
        self.application.aptitude_time = datetime.time(10, 0)
        self.application.save()

        self.client.force_login(self.hr_user)
        response = self.client.post(
            reverse("hr:cancel_aptitude", kwargs={"pk": self.application.pk}),
            {
                "cancellation_reason": "Internal assessment restructuring.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "SHORTLISTED")
        self.assertIsNone(self.application.aptitude_date)
        self.assertIsNone(self.application.aptitude_time)

        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="APTITUDE_CANCELLED",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Internal assessment restructuring", notif.message)

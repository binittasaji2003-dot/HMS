import datetime
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from admin_module.models import Department
from employees.models import (
    Employee,
    EmployeeReport,
    Notification,
    PerformanceReview,
)
from hr.models import HRManager

User = get_user_model()


class HREmployeeEvaluationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(
            name="Product Engineering",
            description="Software Engineering",
            is_active=True,
        )

        # HR Manager User & Profile
        self.hr_user = User.objects.create_user(
            email="hr@company.com",
            password="hrpassword123",
            name="Alice Smith",
            role="HR",
            is_staff=True,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            employee_code="HR001",
            department=self.department,
            designation="Senior HR Manager",
            first_name="Alice",
            last_name="Smith",
            is_active=True,
        )

        # Employee User & Profile
        self.emp_user = User.objects.create_user(
            email="bob@company.com",
            password="password123",
            name="Bob Miller",
            role="Employee",
            is_active=True,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            employee_code="EMP0088",
            department=self.department,
            designation="Full Stack Developer",
            joining_date=datetime.date(2024, 1, 10),
            employment_status="ACTIVE",
            first_name="Bob",
            last_name="Miller",
        )

        # Employee Weekly Report
        self.start_date = datetime.date(2026, 9, 7)
        self.end_date = datetime.date(2026, 9, 11)
        self.report = EmployeeReport.objects.create(
            employee=self.employee,
            title="Sprint 36 Work Report",
            week_start_date=self.start_date,
            week_end_date=self.end_date,
            progress_status="ON_TRACK",
            work_summary="Implemented core feature sets and conducted peer code reviews.",
            tasks_completed="1. API endpoints\n2. Frontend components\n3. Unit tests",
            achievements="Zero production defect leakage.",
            challenges="None encountered.",
            challenges_handling="Proactive sprint grooming.",
            next_week_plan="Deliver sprint 37 items.",
            skills_technologies_used="Python, Django, PostgreSQL",
            declaration_accepted=True,
            status="SUBMITTED",
            submitted_at=timezone.now(),
        )

    def test_hr_evaluates_employee_report_with_8_criteria_matrix(self):
        """Test HR reviewing employee report, evaluating 8 criteria matrix, and calculating score."""
        self.client.force_login(self.hr_user, backend="django.contrib.auth.backends.ModelBackend")

        # GET review page
        get_res = self.client.get(reverse("hr:employee_report_review", kwargs={"pk": self.report.pk}))
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "Bob Miller")
        self.assertContains(get_res, "Sprint 36 Work Report")
        self.assertContains(get_res, "Task Completion")
        self.assertContains(get_res, "Goal Achievement")

        # Report transitions to UNDER_REVIEW
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "UNDER_REVIEW")

        # POST evaluation matrix data
        eval_data = {
            "task_completion": 5,
            "task_completion_remarks": "Completed all planned user stories ahead of time",
            "quality_of_work": 5,
            "quality_of_work_remarks": "High code quality and test coverage",
            "technical_skills": 4,
            "technical_skills_remarks": "Strong architectural understanding",
            "problem_solving": 5,
            "problem_solving_remarks": "Proactively resolved edge cases",
            "timeliness": 5,
            "timeliness_remarks": "All deliverables delivered on schedule",
            "team_collaboration": 4,
            "team_collaboration_remarks": "Great teamwork and helpful in reviews",
            "communication": 5,
            "communication_remarks": "Clear, concise standup and weekly reporting",
            "goal_achievement": 4,
            "goal_achievement_remarks": "Met sprint milestone targets",
            "overall_feedback": "Outstanding work this week Bob. Your dedication to code quality is exemplary.",
            "strengths": "Fast turnaround and high attention to detail.",
            "areas_for_improvement": "Continue mentoring junior engineers.",
            "recommendations": "Explore advanced PostgreSQL query optimization techniques.",
            "next_week_expectations": "Lead the database migration sprint next week.",
            "status_decision": "REVIEWED",
        }

        post_res = self.client.post(reverse("hr:employee_report_review", kwargs={"pk": self.report.pk}), eval_data)
        self.assertEqual(post_res.status_code, 302)

        # Verify PerformanceReview record
        review = PerformanceReview.objects.filter(employee_report=self.report).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.employee, self.employee)
        self.assertEqual(review.reviewed_by, self.hr_manager)

        # Total: 5 + 5 + 4 + 5 + 5 + 4 + 5 + 4 = 37
        self.assertEqual(review.total_score, 37)
        # Average: 37 / 8 = 4.625 -> 4.62 (banker's rounding)
        self.assertAlmostEqual(float(review.average_score), 4.62, places=2)
        # Percentage: (37 / 40) * 100 = 92.5%
        self.assertAlmostEqual(float(review.performance_percentage), 92.5, places=1)

        # Verify report status and notification
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "REVIEWED")
        self.assertEqual(self.report.reviewed_by, self.hr_manager)

        notif = Notification.objects.filter(employee=self.employee, notification_type="REPORT_FEEDBACK").first()
        self.assertIsNotNone(notif)
        self.assertIn("92.5%", notif.message)

    def test_hr_requests_correction_on_employee_report(self):
        """Test HR returning employee report for correction."""
        self.client.force_login(self.hr_user, backend="django.contrib.auth.backends.ModelBackend")

        eval_data = {
            "task_completion": 2,
            "task_completion_remarks": "Missing sprint task breakdown",
            "quality_of_work": 3,
            "quality_of_work_remarks": "Average quality",
            "technical_skills": 3,
            "technical_skills_remarks": "Standard",
            "problem_solving": 2,
            "problem_solving_remarks": "Blockers were left unresolved",
            "timeliness": 3,
            "timeliness_remarks": "Delivered on time",
            "team_collaboration": 3,
            "team_collaboration_remarks": "Satisfactory",
            "communication": 2,
            "communication_remarks": "Insufficient detail in task descriptions",
            "goal_achievement": 2,
            "goal_achievement_remarks": "Milestones partially unaddressed",
            "overall_feedback": "Please expand on the blockers and specify the exact user stories completed.",
            "status_decision": "NEEDS_CORRECTION",
        }

        res = self.client.post(reverse("hr:employee_report_review", kwargs={"pk": self.report.pk}), eval_data)
        self.assertEqual(res.status_code, 302)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "NEEDS_CORRECTION")

        # Employee can now edit the report
        self.client.force_login(self.emp_user, backend="django.contrib.auth.backends.ModelBackend")
        edit_page_res = self.client.get(reverse("employees:edit_report", kwargs={"report_id": self.report.report_id}))
        self.assertEqual(edit_page_res.status_code, 200)

    def test_employee_performance_view_and_report_detail(self):
        """Test that employee sees evaluation matrix and performance metrics."""
        # Create completed review
        review = PerformanceReview.objects.create(
            employee_report=self.report,
            employee=self.employee,
            reviewed_by=self.hr_manager,
            task_completion=5,
            quality_of_work=5,
            technical_skills=5,
            problem_solving=5,
            timeliness=5,
            team_collaboration=5,
            communication=5,
            goal_achievement=5,
            overall_feedback="Flawless week.",
        )
        review.calculate_scores()
        review.save()
        self.report.status = "REVIEWED"
        self.report.save()

        self.client.force_login(self.emp_user, backend="django.contrib.auth.backends.ModelBackend")

        # Check Report Detail page
        res_detail = self.client.get(reverse("employees:report_detail", kwargs={"report_id": self.report.report_id}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, "40/40")
        self.assertContains(res_detail, "100.00%")
        self.assertContains(res_detail, "Flawless week.")

        # Check Performance page
        res_perf = self.client.get(reverse("employees:performance"))
        self.assertEqual(res_perf.status_code, 200)
        self.assertContains(res_perf, "5.0")
        self.assertContains(res_perf, "100.00%")
        self.assertContains(res_perf, "View Evaluation Matrix")

    def test_hr_performance_analysis_matrix_view(self):
        """Test HR performance analysis page and filtering."""
        self.client.force_login(self.hr_user, backend="django.contrib.auth.backends.ModelBackend")

        res_analytics = self.client.get(reverse("hr:employee_performance_analysis"))
        self.assertEqual(res_analytics.status_code, 200)
        self.assertContains(res_analytics, "Performance Analytics Matrix")
        self.assertContains(res_analytics, "Filter by Employee")
        self.assertContains(res_analytics, "Filter by Department")


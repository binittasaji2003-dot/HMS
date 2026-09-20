import datetime
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from admin_module.models import Department
from employees.models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeExperience,
    EmployeeReport,
    Notification,
    PerformanceReview,
)

User = get_user_model()


class EmployeeProfileAndReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.department = Department.objects.create(
            name="Engineering",
            description="Engineering Department",
            is_active=True,
        )

        # Team Lead User & Profile
        self.lead_user = User.objects.create_user(
            email="lead@company.com",
            password="leadpassword123",
            name="Sarah Connor",
            role="Employee",
            is_active=True,
        )
        self.lead_employee = Employee.objects.create(
            user=self.lead_user,
            employee_code="EMP0010",
            department=self.department,
            designation="Tech Lead",
            joining_date=datetime.date(2023, 1, 15),
            employment_status="ACTIVE",
            first_name="Sarah",
            last_name="Connor",
            phone="9876543210",
        )

        # Subordinate Employee User & Profile
        self.emp_user = User.objects.create_user(
            email="john@company.com",
            password="password123",
            name="John Doe",
            role="Employee",
            is_active=True,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            employee_code="EMP0020",
            department=self.department,
            designation="Software Engineer",
            team_lead=self.lead_user,
            joining_date=datetime.date(2024, 3, 1),
            employment_status="ACTIVE",
            first_name="John",
            last_name="Doe",
            phone="9123456780",
        )

        # Unrelated Employee
        self.other_user = User.objects.create_user(
            email="other@company.com",
            password="password123",
            name="Jane Other",
            role="Employee",
            is_active=True,
        )
        self.other_employee = Employee.objects.create(
            user=self.other_user,
            employee_code="EMP0030",
            department=self.department,
            designation="QA Engineer",
            joining_date=datetime.date(2024, 5, 1),
            employment_status="ACTIVE",
        )

    def test_employee_profile_get_and_update(self):
        """Test profile page retrieval and personal information updating."""
        self.client.force_login(self.emp_user, backend="django.contrib.auth.backends.ModelBackend")
        response = self.client.get(reverse("employees:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "EMP0020")
        self.assertContains(response, "Sarah Connor")

        # Update personal information
        update_data = {
            "action": "update_profile",
            "first_name": "Johnny",
            "middle_name": "R",
            "last_name": "Doe",
            "email": "johnny.doe@company.com",
            "personal_email": "johnny.personal@gmail.com",
            "phone": "9998887776",
            "date_of_birth": "1996-08-15",
            "gender": "MALE",
            "address": "42 Tech Boulevard, Silicon Suite",
            "city": "Kochi",
            "state": "Kerala",
            "pincode": "682001",
        }
        post_response = self.client.post(reverse("employees:profile"), update_data)
        self.assertEqual(post_response.status_code, 302)

        self.employee.refresh_from_db()
        self.emp_user.refresh_from_db()
        self.assertEqual(self.employee.first_name, "Johnny")
        self.assertEqual(self.employee.middle_name, "R")
        self.assertEqual(self.employee.full_name, "Johnny R Doe")
        self.assertEqual(self.emp_user.name, "Johnny R Doe")
        self.assertEqual(self.emp_user.email, "johnny.doe@company.com")
        self.assertEqual(self.employee.city, "Kochi")

    def test_employee_education_crud(self):
        """Test adding and deleting education records."""
        self.client.force_login(self.emp_user, backend="django.contrib.auth.backends.ModelBackend")

        # Add Education
        edu_data = {
            "degree": "B.Tech in Computer Science",
            "institution": "National Institute of Technology",
            "university_board": "APJ Abdul Kalam Tech University",
            "year_of_passing": 2022,
            "grade_percentage": "8.8 CGPA / First Class",
        }
        response = self.client.post(reverse("employees:education_add"), edu_data)
        self.assertEqual(response.status_code, 302)

        edu = EmployeeEducation.objects.filter(employee=self.employee).first()
        self.assertIsNotNone(edu)
        self.assertEqual(edu.degree, "B.Tech in Computer Science")
        self.assertEqual(edu.year_of_passing, 2022)

        # Delete Education
        del_response = self.client.post(reverse("employees:education_delete", kwargs={"pk": edu.pk}))
        self.assertEqual(del_response.status_code, 302)
        self.assertEqual(EmployeeEducation.objects.filter(employee=self.employee).count(), 0)

    def test_employee_experience_crud(self):
        """Test adding and deleting work experience records."""
        self.client.force_login(self.emp_user, backend="django.contrib.auth.backends.ModelBackend")

        exp_data = {
            "company_name": "Acme Innovations Ltd",
            "designation": "Associate Python Engineer",
            "start_date": "2022-07-01",
            "end_date": "2024-02-28",
            "responsibilities": "Built REST APIs and optimized database queries.",
        }
        response = self.client.post(reverse("employees:experience_add"), exp_data)
        self.assertEqual(response.status_code, 302)

        exp = EmployeeExperience.objects.filter(employee=self.employee).first()
        self.assertIsNotNone(exp)
        self.assertEqual(exp.company_name, "Acme Innovations Ltd")
        self.assertFalse(exp.is_current)

        # Delete Experience
        del_response = self.client.post(reverse("employees:experience_delete", kwargs={"pk": exp.pk}))
        self.assertEqual(del_response.status_code, 302)
        self.assertEqual(EmployeeExperience.objects.filter(employee=self.employee).count(), 0)

    def test_team_lead_subordinate_profile_access(self):
        """Test that Team Lead can view subordinate's profile, but other employees cannot."""
        # Team Lead views assigned subordinate
        self.client.force_login(self.lead_user, backend="django.contrib.auth.backends.ModelBackend")
        res_lead = self.client.get(reverse("employees:subordinate_profile", kwargs={"employee_id": self.employee.pk}))
        self.assertEqual(res_lead.status_code, 200)
        self.assertContains(res_lead, "John Doe")
        self.assertContains(res_lead, "EMP0020")

        # Unrelated employee attempts to view subordinate
        self.client.force_login(self.other_user, backend="django.contrib.auth.backends.ModelBackend")
        res_other = self.client.get(reverse("employees:subordinate_profile", kwargs={"employee_id": self.employee.pk}))
        self.assertEqual(res_other.status_code, 302)

    def test_employee_weekly_report_draft_and_submission(self):
        """Test weekly report creation as Draft and full Submission with declaration and notifications."""
        self.client.force_login(self.emp_user, backend="django.contrib.auth.backends.ModelBackend")

        start = datetime.date(2026, 9, 14)
        end = datetime.date(2026, 9, 18)

        # 1. Save as Draft
        draft_data = {
            "action": "save_draft",
            "title": "Sprint 37 Engineering Report",
            "week_start_date": start.isoformat(),
            "week_end_date": end.isoformat(),
            "progress_status": "ON_TRACK",
            "work_summary": "Implemented authentication and profile features.",
            "tasks_completed": "Completed tasks 1 to 5.",
            "next_week_plan": "Start report evaluation matrix.",
        }
        res_draft = self.client.post(reverse("employees:submit_report"), draft_data)
        self.assertEqual(res_draft.status_code, 302)

        report = EmployeeReport.objects.filter(employee=self.employee, week_start_date=start).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.status, "DRAFT")

        # 2. Edit & Submit Report
        submit_data = {
            "action": "submit_report",
            "title": "Sprint 37 Engineering Report - Final",
            "week_start_date": start.isoformat(),
            "week_end_date": end.isoformat(),
            "progress_status": "AHEAD",
            "work_summary": "Implemented authentication, profile features and automated test suite.",
            "tasks_completed": "Delivered 8 user stories with 100% test coverage.",
            "achievements": "Sprint closed 1 day early.",
            "challenges": "Docker port contention during tests.",
            "challenges_handling": "Used isolated test database containers.",
            "pending_tasks": "None.",
            "next_week_plan": "Performance matrix review integration.",
            "skills_technologies_used": "Django, PostgreSQL, Docker, Bootstrap 5",
            "declaration_accepted": "on",
        }
        res_submit = self.client.post(reverse("employees:edit_report", kwargs={"report_id": report.report_id}), submit_data)
        self.assertEqual(res_submit.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.status, "SUBMITTED")
        self.assertEqual(report.progress_status, "AHEAD")
        self.assertTrue(report.declaration_accepted)
        self.assertIsNotNone(report.submitted_at)

        # Notification verification
        emp_notif = Notification.objects.filter(employee=self.employee, notification_type="REPORT_REMINDER").first()
        self.assertIsNotNone(emp_notif)
        self.assertIn("Sprint 37", emp_notif.message)

    def test_duplicate_weekly_report_prevention(self):
        """Test that overlapping/duplicate weekly reports for the same employee are rejected."""
        self.client.force_login(self.emp_user, backend="django.contrib.auth.backends.ModelBackend")
        start = datetime.date(2026, 10, 5)
        end = datetime.date(2026, 10, 9)

        # Create first report
        EmployeeReport.objects.create(
            employee=self.employee,
            title="First Report",
            week_start_date=start,
            week_end_date=end,
            status="SUBMITTED",
            work_summary="Summary",
            tasks_completed="Tasks",
            next_week_plan="Plan",
        )

        # Attempt to create duplicate for same dates
        dup_data = {
            "action": "submit_report",
            "title": "Duplicate Report",
            "week_start_date": start.isoformat(),
            "week_end_date": end.isoformat(),
            "progress_status": "ON_TRACK",
            "work_summary": "Summary 2",
            "tasks_completed": "Tasks 2",
            "next_week_plan": "Plan 2",
            "declaration_accepted": "on",
        }
        res_dup = self.client.post(reverse("employees:submit_report"), dup_data)
        self.assertEqual(res_dup.status_code, 200) # Form re-rendered with error
        self.assertContains(res_dup, "already exists")


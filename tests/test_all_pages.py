from datetime import date
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from admin_module.models import Announcement, Department, EmployeeApproval
from candidates.models import Candidate, JobApplication, JobVacancy
from employees.models import (
    Employee,
    EmployeePerformance,
    EmployeeReport,
    Notification,
    PerformanceWarning,
)
from hr.models import AptitudeQuestion, AptitudeResult, AptitudeTest, HRManager, Interview

User = get_user_model()


class AllPagesAvailabilityTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Department
        self.department = Department.objects.create(
            name="Information Technology",
            description="IT & Software Development",
            is_active=True,
        )

        # 2. Admin User
        self.admin_user = User.objects.create_superuser(
            email="admin.test@company.com",
            password="AdminPassword123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
        )

        # 3. HR User & Profile
        self.hr_user = User.objects.create_user(
            email="hr.test@company.com",
            password="HRPassword123!",
            name="HR Manager",
            role=User.RoleChoices.HR,
            is_active=True,
        )
        self.hr_profile = HRManager.objects.create(
            user=self.hr_user,
            department=self.department,
            employee_code="HR-0001",
            joining_date=date(2024, 1, 1),
            is_active=True,
        )

        # 4. Employee User & Profile
        self.emp_user = User.objects.create_user(
            email="employee.test@company.com",
            password="EmpPassword123!",
            name="Test Employee",
            role=User.RoleChoices.EMPLOYEE,
            is_active=True,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            employee_code="EMP-0001",
            department=self.department,
            designation="Software Engineer",
            joining_date=date(2024, 6, 1),
            employment_status="ACTIVE",
        )

        # 5. Candidate User & Profile
        self.cand_user = User.objects.create_user(
            email="candidate.test@example.com",
            password="CandPassword123!",
            name="Jane Candidate",
            role=User.RoleChoices.CANDIDATE,
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user,
            first_name="Jane",
            last_name="Candidate",
            phone="9876543210",
            profile_completed=True,
        )

        # 6. Job Vacancy & Application
        self.vacancy = JobVacancy.objects.create(
            title="Senior Python Developer",
            department=self.department,
            description="Build modern backend systems with Django.",
            responsibilities="Design APIs and integrate modules.",
            qualifications="Python, Django, PostgreSQL",
            skills_required="Django, Docker, PostgreSQL",
            experience_required="3+ years",
            location="Bangalore / Remote",
            posted_by=self.hr_user,
            status="OPEN",
        )
        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.vacancy,
            status="APPLIED",
        )

        # 7. Employee Reports, Warnings, Performance, Announcements, Notifications
        self.report = EmployeeReport.objects.create(
            employee=self.employee,
            title="Weekly Development Status",
            week_start_date=date(2026, 9, 1),
            week_end_date=date(2026, 9, 7),
            work_summary="Integrated modules and conducted test suite runs.",
            tasks_completed="Completed authentication and module integration.",
            challenges="None",
            status="SUBMITTED",
        )
        self.warning = PerformanceWarning.objects.create(
            employee=self.employee,
            issued_by=self.hr_profile,
            reason="Unresolved code review latency.",
            hr_recommendation="Provide 1-on-1 coaching.",
            status="OPEN",
        )
        self.performance = EmployeePerformance.objects.create(
            employee=self.employee,
            reviewed_by=self.hr_profile,
            review_period="Q3-2026",
            rating="EXCELLENT",
            comments="Outstanding contribution to system integration.",
        )
        self.announcement = Announcement.objects.create(
            title="Quarterly All-Hands Meeting",
            content="Join us this Friday for our organizational updates.",
            announcement_type="GENERAL",
            is_active=True,
            is_published=True,
            created_by=self.admin_user,
        )
        self.notification = Notification.objects.create(
            employee=self.employee,
            title="Report Submitted",
            message="Your weekly work report has been logged.",
            notification_type="REPORT",
        )
        self.approval = EmployeeApproval.objects.create(
            employee=self.employee,
            status="PENDING",
        )
        self.aptitude_test = AptitudeTest.objects.create(
            title="Django & Backend Aptitude",
            description="Evaluate core backend architecture skills.",
            duration_minutes=30,
            created_by=self.hr_profile,
            status="ACTIVE",
        )

    # -------------------------------------------------------------------------
    # PUBLIC PAGES
    # -------------------------------------------------------------------------
    def test_public_home_page(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_public_about_page(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_allauth_login_page(self):
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)

    def test_role_select_page(self):
        response = self.client.get(reverse("role_select"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select Your Portal Role")
        self.assertContains(response, "Administrator")
        self.assertContains(response, "HR Manager")
        self.assertContains(response, "Employee")
        self.assertContains(response, "Candidate")

    # -------------------------------------------------------------------------
    # ADMIN PORTAL PAGES
    # -------------------------------------------------------------------------
    def test_admin_portal_pages(self):
        self.client.login(username=self.admin_user.email, password="AdminPassword123!")

        urls = [
            reverse("admin_module:admin_dashboard"),
            reverse("admin_module:employees_list"),
            reverse("admin_module:employee_create"),
            reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk}),
            reverse("admin_module:hr_managers_list"),
            reverse("admin_module:hr_manager_create"),
            reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_profile.pk}),
            reverse("admin_module:departments_list"),
            reverse("admin_module:department_create"),
            reverse("admin_module:department_detail", kwargs={"department_id": self.department.pk}),
            reverse("admin_module:announcements_list"),
            reverse("admin_module:announcement_create"),
            reverse("admin_module:announcement_detail", kwargs={"announcement_id": self.announcement.pk}),
            reverse("admin_module:recruitment_jobs"),
            reverse("admin_module:recruitment_status"),
            reverse("admin_module:recruitment_selected"),
            reverse("admin_module:recruitment_approvals"),
            reverse("admin_module:reports_hr_weekly"),
            reverse("admin_module:reports_employee_weekly"),
            reverse("admin_module:reports_recruitment"),
            reverse("admin_module:reports_departments"),
            reverse("admin_module:reports_performance"),
            reverse("admin_module:candidates_list"),
            reverse("admin_module:admin_responsibilities_warnings"),
            reverse("admin_module:admin_responsibilities_recommendations"),
        ]

        for url in urls:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Failed on Admin URL: {url}")

    # -------------------------------------------------------------------------
    # HR PORTAL PAGES
    # -------------------------------------------------------------------------
    def test_hr_portal_pages(self):
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        urls = [
            reverse("hr:dashboard"),
            reverse("hr:profile"),
            reverse("hr:profile_edit"),
            reverse("hr:change_password"),
            reverse("hr:job_list"),
            reverse("hr:job_create"),
            reverse("hr:application_list"),
            reverse("hr:application_detail", kwargs={"pk": self.application.pk}),
            reverse("hr:aptitude_test_list"),
            reverse("hr:aptitude_test_create"),
            reverse("hr:aptitude_test_edit", kwargs={"pk": self.aptitude_test.pk}),
            reverse("hr:aptitude_questions", kwargs={"test_id": self.aptitude_test.pk}),
            reverse("hr:aptitude_results"),
            reverse("hr:interview_list"),
            reverse("hr:employee_report_list"),
            reverse("hr:warning_list"),
            reverse("hr:performance_list"),
        ]

        for url in urls:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Failed on HR URL: {url}")

    # -------------------------------------------------------------------------
    # EMPLOYEE PORTAL PAGES
    # -------------------------------------------------------------------------
    def test_employee_portal_pages(self):
        self.client.login(username=self.emp_user.email, password="EmpPassword123!")

        urls = [
            reverse("employees:dashboard"),
            reverse("employees:profile"),
            reverse("employees:reports_list"),
            reverse("employees:submit_report"),
            reverse("employees:edit_report", kwargs={"report_id": self.report.report_id}),
            reverse("employees:performance"),
            reverse("employees:announcements"),
            reverse("employees:notifications"),
        ]

        for url in urls:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Failed on Employee URL: {url}")

    # -------------------------------------------------------------------------
    # CANDIDATE PORTAL PAGES
    # -------------------------------------------------------------------------
    def test_candidate_portal_pages(self):
        self.client.login(username=self.cand_user.email, password="CandPassword123!")

        urls = [
            reverse("candidates:dashboard"),
            reverse("candidates:job_list"),
            reverse("candidates:job_detail", kwargs={"vacancy_id": self.vacancy.vacancy_id}),
            reverse("candidates:applications"),
            reverse("candidates:profile"),
        ]

        for url in urls:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Failed on Candidate URL: {url}")

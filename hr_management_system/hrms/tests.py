from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from admin_module.models import Department as AdminModuleDepartment
from employees.models import Employee as StandaloneEmployee
from employees.models import EmployeeDocument
from employees.models import EmployeeReport
from employees.models import PerformanceWarning as StandalonePerformanceWarning
from hr.models import HRManager as StandaloneHRManager
from hr_management_system.hrms.forms import EmployeeCreateForm, HRManagerCreateForm
from hr_management_system.hrms.models import (
    Candidate,
    Department,
    Employee,
    EmployeePerformance,
    HRManager,
    JobVacancy,
    PerformanceWarning,
)

User = get_user_model()


class AdminManagementFormsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Engineering")

    def test_employee_form_creates_active_user_and_employee_record(self):
        form = EmployeeCreateForm(
            data={
                "username": "jdoe",
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": "9876543210",
                "password": "StrongPass123!",
                "department": self.department.pk,
                "designation": "Software Engineer",
                "hire_date": "2024-01-15",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        user = form.save(admin_user=self.admin)

        self.assertEqual(user.role, User.RoleChoices.EMPLOYEE)
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertTrue(Employee.objects.filter(user=user, designation="Software Engineer").exists())
        self.assertEqual(Employee.objects.get(user=user).status, Employee.StatusChoices.ACTIVE)

    def test_hr_manager_form_rejects_duplicate_email(self):
        User.objects.create_user(
            email="hr@example.com",
            password="ExistingPass123!",
            name="Existing HR",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
        )

        form = HRManagerCreateForm(
            data={
                "username": "hrmanager",
                "full_name": "HR Manager",
                "email": "hr@example.com",
                "phone": "9988776655",
                "password": "StrongPass123!",
                "department": self.department.pk,
                "hired_date": "2024-02-01",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

        hr_manager = HRManager.objects.filter(user__email="hr@example.com").first()
        self.assertIsNone(hr_manager)

    def test_employee_and_hr_roles_are_inactive_until_admin_created(self):
        employee_user = User.objects.create_user(
            email="employee_default@example.com",
            password="StrongPass123!",
            name="Employee Default",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
        )
        hr_user = User.objects.create_user(
            email="hr_default@example.com",
            password="StrongPass123!",
            name="HR Default",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
        )

        self.assertFalse(employee_user.is_active)
        self.assertFalse(hr_user.is_active)

        employee_form = EmployeeCreateForm(
            data={
                "username": "newemployee",
                "full_name": "New Employee",
                "email": "newemployee@example.com",
                "phone": "9898989898",
                "password": "StrongPass123!",
                "department": self.department.pk,
                "designation": "Analyst",
                "hire_date": "2024-05-01",
            }
        )
        self.assertTrue(employee_form.is_valid(), employee_form.errors)
        employee_user = employee_form.save(admin_user=self.admin)
        self.assertTrue(employee_user.is_active)

    def test_department_dropdown_has_default_department_options(self):
        Department.objects.all().delete()

        form = EmployeeCreateForm()
        self.assertGreater(form.fields["department"].queryset.count(), 0)

        hr_form = HRManagerCreateForm()
        self.assertGreater(hr_form.fields["department"].queryset.count(), 0)


class RecruitmentMonitoringAccessTests(TestCase):
    """Security: only authenticated, active Admin users may monitor recruitment."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.department = Department.objects.create(name="Engineering")
        self.vacancy = JobVacancy.objects.create(
            title="Senior Backend Engineer",
            department=self.department,
            description="Build robust services.",
            status=JobVacancy.StatusChoices.OPEN,
        )

    def test_anonymous_users_redirected_to_admin_login(self):
        for url_name in [
            "hrms:recruitment_jobs",
            "hrms:recruitment_status",
            "hrms:recruitment_selected",
            "hrms:recruitment_approvals",
        ]:
            url = reverse(url_name)
            response = self.client.get(url)
            expected = f"{reverse('hrms:admin_login')}?next={url}"
            self.assertRedirects(response, expected, fetch_redirect_response=False)

    def test_non_admin_users_blocked_from_monitoring_pages(self):
        roles = [
            (User.RoleChoices.HR, "hr@example.com", True),
            (User.RoleChoices.EMPLOYEE, "employee@example.com", True),
            (User.RoleChoices.CANDIDATE, "candidate@example.com", True),
        ]
        for role, email, is_active in roles:
            user = User.objects.create_user(
                email=email,
                password="Pass1234!",
                name=email,
                role=role,
                status=User.StatusChoices.ACTIVE,
                is_active=is_active,
            )
            self.client.force_login(user)
            for url_name in [
                "hrms:recruitment_jobs",
                "hrms:recruitment_status",
                "hrms:recruitment_selected",
                "hrms:recruitment_approvals",
            ]:
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 302, f"{role} reached {url_name}")
                self.assertRedirects(
                    response, reverse("hrms:admin_login"), fetch_redirect_response=False
                )
            self.client.logout()

    def test_non_admin_user_cannot_approve_employee(self):
        candidate_user = User.objects.create_user(
            email="newhire@example.com",
            password="Pass1234!",
            name="New Hire",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.INACTIVE,
            is_active=False,
        )
        employee = Employee.objects.create(
            user=candidate_user,
            department=self.department,
            designation="Backend Engineer",
            date_of_joining="2026-09-10",
            status=Employee.StatusChoices.PENDING_APPROVAL,
        )

        hr_user = User.objects.create_user(
            email="hr@example.com",
            password="Pass1234!",
            name="HR Manager",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.client.force_login(hr_user)
        response = self.client.post(
            reverse("hrms:recruitment_approval_approve", args=[employee.pk])
        )
        self.assertEqual(response.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.status, Employee.StatusChoices.PENDING_APPROVAL)

    def test_inactive_admin_cannot_access_monitoring(self):
        self.admin.status = User.StatusChoices.INACTIVE
        self.admin.save(update_fields=["status"])
        self.client.force_login(self.admin)
        response = self.client.get(reverse("hrms:recruitment_jobs"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("hrms:admin_login"), fetch_redirect_response=False
        )


class RecruitmentMonitoringDataTests(TestCase):
    """Monitoring pages display real recruitment data from the database."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.client.force_login(self.admin)

        self.hr_user = User.objects.create_user(
            email="hr@example.com",
            password="HrPass123!",
            name="Priya HR",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.department = Department.objects.create(name="Engineering")
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.department,
            phone="1234567890",
            office_location="HQ",
        )
        self.vacancy = JobVacancy.objects.create(
            title="Senior Backend Engineer",
            department=self.department,
            description="Build robust services.",
            requirements="Python & Django",
            openings_count=2,
            created_by=self.hr_user,
            status=JobVacancy.StatusChoices.OPEN,
        )
        self.vacancy_two = JobVacancy.objects.create(
            title="QA Analyst",
            department=self.department,
            description="Ensure quality.",
            status=JobVacancy.StatusChoices.OPEN,
        )

    def _candidate(self, full_name, email, status, vacancy=None):
        return Candidate.objects.create(
            job_vacancy=vacancy or self.vacancy,
            full_name=full_name,
            email=email,
            phone="9988776655",
            experience_years=4,
            status=status,
        )

    def test_jobs_page_lists_job_postings_with_real_details(self):
        self._candidate("Arjun Nair", "arjun@example.com", Candidate.StatusChoices.APPLIED)
        self._candidate("Beena Mathew", "beena@example.com", Candidate.StatusChoices.SHORTLISTED)
        self._candidate("Chirag Shah", "chirag@example.com", Candidate.StatusChoices.SELECTED)

        response = self.client.get(reverse("hrms:recruitment_jobs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Backend Engineer")
        self.assertContains(response, "QA Analyst")
        self.assertContains(response, "Engineering")
        self.assertContains(response, "Priya HR")
        self.assertContains(response, "HR Manager")

        # Real applicant counts and summary values are passed to the template.
        job_rows = {row["vacancy"].pk: row for row in response.context["job_rows"]}
        self.assertEqual(job_rows[self.vacancy.pk]["applicants_count"], 3)
        self.assertEqual(job_rows[self.vacancy_two.pk]["applicants_count"], 0)
        self.assertEqual(response.context["total_applications"], 3)
        self.assertEqual(response.context["open_jobs"], 2)
        self.assertEqual(response.context["selections_count"], 1)

    def test_jobs_page_filters_by_search_and_status(self):
        response = self.client.get(reverse("hrms:recruitment_jobs"), {"q": "QA"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QA Analyst")
        self.assertNotContains(response, "Senior Backend Engineer")

        self.vacancy.status = JobVacancy.StatusChoices.CLOSED
        self.vacancy.save(update_fields=["status"])
        response = self.client.get(reverse("hrms:recruitment_jobs"), {"status": "Closed"})
        self.assertContains(response, "Senior Backend Engineer")
        self.assertNotContains(response, "QA Analyst")

    def test_recruitment_status_page_shows_stage_counts_per_job(self):
        self._candidate("Arjun Nair", "arjun@example.com", Candidate.StatusChoices.APPLIED)
        self._candidate("Beena Mathew", "beena@example.com", Candidate.StatusChoices.SHORTLISTED)
        self._candidate("Beena2 Mathew", "beena2@example.com", Candidate.StatusChoices.INTERVIEWING)
        self._candidate("Chirag Shah", "chirag@example.com", Candidate.StatusChoices.SELECTED)
        self._candidate("Dinesh Rao", "dinesh@example.com", Candidate.StatusChoices.HIRED)
        self._candidate("Eva K", "eva@example.com", Candidate.StatusChoices.REJECTED)
        self._candidate("QA Person", "qa@example.com", Candidate.StatusChoices.SELECTED, self.vacancy_two)

        response = self.client.get(reverse("hrms:recruitment_status"))
        self.assertEqual(response.status_code, 200)
        job_rows = {row["vacancy"].pk: row for row in response.context["job_rows"]}
        self.assertEqual(job_rows[self.vacancy.pk]["applicants_count"], 6)
        self.assertEqual(job_rows[self.vacancy.pk]["stages"]["Applied"], 1)
        self.assertEqual(job_rows[self.vacancy.pk]["stages"]["Shortlisted"], 1)
        self.assertEqual(job_rows[self.vacancy.pk]["stages"]["Interviewing"], 1)
        self.assertEqual(job_rows[self.vacancy.pk]["stages"]["Selected"], 1)
        self.assertEqual(job_rows[self.vacancy.pk]["stages"]["Hired"], 1)
        self.assertEqual(job_rows[self.vacancy.pk]["stages"]["Rejected"], 1)
        self.assertEqual(job_rows[self.vacancy_two.pk]["stages"]["Selected"], 1)

        totals = response.context["global_totals"]
        self.assertEqual(totals["Applied"], 1)
        self.assertEqual(totals["Selected"], 2)
        self.assertEqual(response.context["total_applications"], 7)

    def test_recruitment_status_page_renders_stage_table(self):
        self._candidate("Arjun Nair", "arjun@example.com", Candidate.StatusChoices.SELECTED)
        response = self.client.get(reverse("hrms:recruitment_status"))
        self.assertContains(response, "Senior Backend Engineer")
        self.assertContains(response, "Recruitment Progress by Job")
        self.assertContains(response, "Selected")

    def test_job_pipeline_detail_page(self):
        candidate = self._candidate(
            "Arjun Nair", "arjun@example.com", Candidate.StatusChoices.SELECTED
        )
        response = self.client.get(
            reverse("hrms:recruitment_job_status", args=[self.vacancy.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Backend Engineer")
        self.assertContains(response, "Arjun Nair")
        self.assertContains(response, "Priya HR")
        self.assertEqual(response.context["total_applicants"], 1)
        self.assertEqual(response.context["stage_counts"]["Selected"], 1)

        # Stage filtering works.
        response = self.client.get(
            reverse("hrms:recruitment_job_status", args=[self.vacancy.pk]),
            {"stage": Candidate.StatusChoices.APPLIED},
        )
        self.assertNotContains(response, "Arjun Nair")

    def test_selected_candidates_page_lists_only_selected_or_hired(self):
        selected = self._candidate(
            "Chirag Shah", "chirag@example.com", Candidate.StatusChoices.SELECTED
        )
        hired = self._candidate(
            "Dinesh Rao", "dinesh@example.com", Candidate.StatusChoices.HIRED
        )
        self._candidate("Eva K", "eva@example.com", Candidate.StatusChoices.REJECTED)
        self._candidate(
            "Arjun Nair", "arjun@example.com", Candidate.StatusChoices.APPLIED
        )

        response = self.client.get(reverse("hrms:recruitment_selected"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chirag Shah")
        self.assertContains(response, "Dinesh Rao")
        self.assertNotContains(response, "Eva K")
        self.assertNotContains(response, "Arjun Nair")
        self.assertEqual(response.context["total_count"], 2)
        self.assertEqual(response.context["selected_count"], 1)
        self.assertEqual(response.context["hired_count"], 1)

        # Filtering by vacancy keeps only that job's selections.
        response = self.client.get(
            reverse("hrms:recruitment_selected"), {"vacancy": self.vacancy.pk}
        )
        self.assertContains(response, "Chirag Shah")
        self.assertContains(response, "Dinesh Rao")
        _ = selected
        _ = hired

    def test_candidate_detail_page_is_read_only_and_complete(self):
        candidate = self._candidate(
            "Chirag Shah", "chirag@example.com", Candidate.StatusChoices.SELECTED
        )
        response = self.client.get(
            reverse("hrms:recruitment_candidate_detail", args=[candidate.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chirag Shah")
        self.assertContains(response, "chirag@example.com")
        self.assertContains(response, "Senior Backend Engineer")
        self.assertContains(response, "Engineering")
        self.assertContains(response, "Read-only")
        self.assertContains(response, "Selected")

    def test_candidate_detail_missing_record_redirects(self):
        response = self.client.get(
            reverse("hrms:recruitment_candidate_detail", args=[99999])
        )
        self.assertRedirects(
            response, reverse("hrms:recruitment_selected"), fetch_redirect_response=False
        )


class EmployeeApprovalWorkflowTests(TestCase):
    """Approving new employee records, with duplicate-approval protection."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.client.force_login(self.admin)

        self.department = Department.objects.create(name="Engineering")
        self.hr_user = User.objects.create_user(
            email="hr@example.com",
            password="HrPass123!",
            name="Priya HR",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )

    def _pending_employee(self, name="Fathima Khan", email="fathima@example.com"):
        user = User.objects.create_user(
            email=email,
            password="HirePass123!",
            name=name,
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.INACTIVE,
            is_active=False,
        )
        return Employee.objects.create(
            user=user,
            department=self.department,
            designation="Software Engineer",
            date_of_joining="2026-09-15",
            status=Employee.StatusChoices.PENDING_APPROVAL,
        )

    def test_approvals_list_shows_pending_records(self):
        employee = self._pending_employee()
        response = self.client.get(reverse("hrms:recruitment_approvals"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fathima Khan")
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Pending")
        self.assertContains(response, "Awaiting Approval")
        self.assertEqual(response.context["pending_count"], 1)
        self.assertIn(employee, response.context["pending_list"])

    def test_approval_review_screen_loads(self):
        employee = self._pending_employee()
        response = self.client.get(
            reverse("hrms:recruitment_approval_review", args=[employee.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fathima Khan")
        self.assertContains(response, "fathima@example.com")
        self.assertContains(response, "Approve &amp; Activate Employee")
        self.assertContains(response, "Pending Approval")

    def test_approve_flow_activates_employee_and_user(self):
        employee = self._pending_employee()
        url = reverse("hrms:recruitment_approval_approve", args=[employee.pk])

        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "approved")

        employee.refresh_from_db()
        self.assertEqual(employee.status, Employee.StatusChoices.ACTIVE)
        employee.user.refresh_from_db()
        self.assertEqual(employee.user.status, User.StatusChoices.ACTIVE)
        self.assertTrue(employee.user.is_active)

    def test_duplicate_approval_is_prevented(self):
        employee = self._pending_employee()
        url = reverse("hrms:recruitment_approval_approve", args=[employee.pk])

        first = self.client.post(url)
        self.assertEqual(first.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.status, Employee.StatusChoices.ACTIVE)

        second = self.client.post(url, follow=True)
        self.assertEqual(second.status_code, 200)
        employee.refresh_from_db()
        self.assertEqual(employee.status, Employee.StatusChoices.ACTIVE)
        self.assertContains(second, "already been processed")
        # Exactly one employee record exists for the hire.
        self.assertEqual(
            Employee.objects.filter(user=employee.user).count(), 1
        )

    def test_approve_via_get_is_not_allowed(self):
        employee = self._pending_employee()
        response = self.client.get(
            reverse("hrms:recruitment_approval_approve", args=[employee.pk])
        )
        self.assertRedirects(
            response, reverse("hrms:recruitment_approvals"), fetch_redirect_response=False
        )
        employee.refresh_from_db()
        self.assertEqual(employee.status, Employee.StatusChoices.PENDING_APPROVAL)

    def test_review_of_already_processed_record_redirects(self):
        employee = self._pending_employee()
        employee.status = Employee.StatusChoices.ACTIVE
        employee.save(update_fields=["status"])

        response = self.client.get(
            reverse("hrms:recruitment_approval_review", args=[employee.pk])
        )
        self.assertRedirects(
            response, reverse("hrms:recruitment_approvals"), fetch_redirect_response=False
        )

    def test_approve_missing_record_redirects_with_error(self):
        response = self.client.post(
            reverse("hrms:recruitment_approval_approve", args=[99999]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already been processed")

    def test_previous_admin_module_pages_still_work(self):
        # Sanity checks: Tasks 1-4 pages render for an admin after Task 5 changes.
        self._pending_employee()
        for url_name in [
            "hrms:admin_dashboard",
            "hrms:employees_list",
            "hrms:hr_managers_list",
            "hrms:departments_list",
            "hrms:candidates_list",
        ]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)

        # Sidebar still receives the approval count badge context.
        response = self.client.get(reverse("hrms:admin_dashboard"))
        self.assertEqual(response.context["approvals_pending_count"], 1)


class ReportsAccessTests(TestCase):
    """Security: only authenticated, active Admin users may access the Reports section."""

    REPORT_URLS = [
        "hrms:reports_hr_weekly",
        "hrms:reports_employee_weekly",
        "hrms:reports_recruitment",
        "hrms:reports_departments",
        "hrms:reports_performance",
    ]

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )

    def test_anonymous_users_redirected_to_admin_login(self):
        for url_name in self.REPORT_URLS:
            url = reverse(url_name)
            response = self.client.get(url)
            expected = f"{reverse('hrms:admin_login')}?next={url}"
            self.assertRedirects(response, expected, fetch_redirect_response=False)

    def test_non_admin_users_blocked_from_reports(self):
        roles = [
            (User.RoleChoices.HR, "hr@example.com"),
            (User.RoleChoices.EMPLOYEE, "employee@example.com"),
            (User.RoleChoices.CANDIDATE, "candidate@example.com"),
        ]
        for role, email in roles:
            user = User.objects.create_user(
                email=email,
                password="Pass1234!",
                name=email,
                role=role,
                status=User.StatusChoices.ACTIVE,
                is_active=True,
            )
            self.client.force_login(user)
            for url_name in self.REPORT_URLS:
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 302, f"{role} reached {url_name}")
                self.assertRedirects(
                    response, reverse("hrms:admin_login"), fetch_redirect_response=False
                )
            self.client.logout()

    def test_inactive_admin_blocked_from_reports(self):
        self.admin.status = User.StatusChoices.INACTIVE
        self.admin.save(update_fields=["status"])
        self.client.force_login(self.admin)
        for url_name in self.REPORT_URLS:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302, url_name)


class ReportsDataTests(TestCase):
    """Each report renders real database data and its filters work."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.client.force_login(self.admin)

        self.hr_user = User.objects.create_user(
            email="hr@example.com",
            password="HrPass123!",
            name="Priya Nair",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.engineering = Department.objects.create(name="Engineering")
        self.finance = Department.objects.create(name="Finance")
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.engineering,
            phone="1234567890",
            office_location="HQ",
        )
        self.vacancy = JobVacancy.objects.create(
            title="Senior Backend Engineer",
            department=self.engineering,
            description="Build robust services.",
            requirements="Python & Django",
            openings_count=2,
            created_by=self.hr_user,
            status=JobVacancy.StatusChoices.OPEN,
        )

    def _employee(self, name, email, department, designation="Engineer", status=None):
        user = User.objects.create_user(
            email=email,
            password="EmpPass123!",
            name=name,
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        return Employee.objects.create(
            user=user,
            department=department,
            designation=designation,
            date_of_joining="2026-01-05",
            status=status or Employee.StatusChoices.ACTIVE,
        )

    def test_hr_weekly_report_counts_and_period_filter(self):
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Arjun Nair",
            email="arjun@example.com",
            status=Candidate.StatusChoices.APPLIED,
        )
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Beena Mathew",
            email="beena@example.com",
            status=Candidate.StatusChoices.SHORTLISTED,
        )
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Chirag Shah",
            email="chirag@example.com",
            status=Candidate.StatusChoices.SELECTED,
        )
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Ebin Roy",
            email="ebin@example.com",
            status=Candidate.StatusChoices.REJECTED,
        )
        # One application older than the 7-day window.
        old_candidate = Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Old Applicant",
            email="old@example.com",
            status=Candidate.StatusChoices.APPLIED,
        )
        Candidate.objects.filter(pk=old_candidate.pk).update(
            applied_at=timezone.now() - timedelta(days=40)
        )

        response = self.client.get(reverse("hrms:reports_hr_weekly"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Priya Nair")
        self.assertContains(response, "Engineering")
        self.assertEqual(response.context["total_applications"], 5)
        self.assertEqual(response.context["total_selections"], 1)
        row = response.context["rows"][0]
        self.assertEqual(row["applications"], 5)
        self.assertEqual(row["shortlisted"], 1)
        self.assertEqual(row["selected"], 1)
        self.assertEqual(row["rejected"], 1)

        # 7-day period excludes the old application.
        response = self.client.get(
            reverse("hrms:reports_hr_weekly"), {"period": "7d"}
        )
        self.assertEqual(response.context["total_applications"], 4)
        self.assertEqual(response.context["rows"][0]["applications"], 4)

    def test_hr_weekly_report_empty_state(self):
        HRManager.objects.all().delete()
        response = self.client.get(reverse("hrms:reports_hr_weekly"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No HR Managers Found")

    def test_employee_weekly_reports_from_existing_model(self):
        admin_module_dept = AdminModuleDepartment.objects.create(name="Operations")
        emp_user = User.objects.create_user(
            email="weekly@example.com",
            password="EmpPass123!",
            name="Weekly Employee",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        standalone_employee = StandaloneEmployee.objects.create(
            user=emp_user,
            department=admin_module_dept,
            employee_code="EMP-WK1",
            designation="Operations Analyst",
            joining_date="2026-01-05",
            employment_status="ACTIVE",
        )
        EmployeeReport.objects.create(
            employee=standalone_employee,
            week_start_date="2026-08-31",
            week_end_date="2026-09-06",
            work_summary="Completed sprint deliverables and updated runbooks.",
            tasks_completed="Task A; Task B",
            status="SUBMITTED",
        )

        response = self.client.get(reverse("hrms:reports_employee_weekly"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weekly Employee")
        self.assertContains(response, "Operations")
        self.assertContains(response, "Completed sprint deliverables")
        self.assertContains(response, "Submitted")
        self.assertEqual(response.context["total_reports"], 1)

        # Status filter narrows the list.
        response = self.client.get(
            reverse("hrms:reports_employee_weekly"), {"status": "REVIEWED"}
        )
        self.assertNotContains(response, "Weekly Employee")
        self.assertContains(response, "No Weekly Reports Found")

        # Date range filter also works.
        response = self.client.get(
            reverse("hrms:reports_employee_weekly"),
            {"from": "2026-09-07", "to": "2026-09-20"},
        )
        self.assertNotContains(response, "Weekly Employee")

    def test_recruitment_report_statistics(self):
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Arjun Nair",
            email="arjun@example.com",
            status=Candidate.StatusChoices.APPLIED,
        )
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Beena Mathew",
            email="beena@example.com",
            status=Candidate.StatusChoices.SHORTLISTED,
        )
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Chirag Shah",
            email="chirag@example.com",
            status=Candidate.StatusChoices.SELECTED,
        )
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Dinesh Rao",
            email="dinesh@example.com",
            status=Candidate.StatusChoices.HIRED,
        )
        Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Eva K",
            email="eva@example.com",
            status=Candidate.StatusChoices.REJECTED,
        )

        response = self.client.get(reverse("hrms:reports_recruitment"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Backend Engineer")
        self.assertEqual(response.context["applications"], 5)
        self.assertEqual(response.context["shortlisted"], 1)
        self.assertEqual(response.context["selected"], 1)
        self.assertEqual(response.context["hired"], 1)
        self.assertEqual(response.context["rejected"], 1)
        self.assertEqual(response.context["total_jobs"], 1)
        self.assertEqual(response.context["open_jobs"], 1)
        self.assertEqual(response.context["chart_values"], [5])

        # Period filter counts only recent applications.
        old = Candidate.objects.create(
            job_vacancy=self.vacancy,
            full_name="Old Applicant",
            email="old@example.com",
            status=Candidate.StatusChoices.APPLIED,
        )
        Candidate.objects.filter(pk=old.pk).update(
            applied_at=timezone.now() - timedelta(days=40)
        )
        response = self.client.get(
            reverse("hrms:reports_recruitment"), {"period": "7d"}
        )
        self.assertEqual(response.context["applications"], 5)

    def test_department_wise_employee_report(self):
        self._employee("Ana Thomas", "ana@example.com", self.engineering, "Engineer")
        self._employee("Ben Jose", "ben@example.com", self.engineering, "Engineer")
        self._employee(
            "Cyril Paul",
            "cyril@example.com",
            self.finance,
            "Analyst",
            status=Employee.StatusChoices.ON_LEAVE,
        )

        response = self.client.get(reverse("hrms:reports_departments"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Thomas")
        self.assertContains(response, "Ben Jose")
        self.assertContains(response, "Cyril Paul")

        rows = {row["department"].pk: row for row in response.context["rows"]}
        self.assertEqual(rows[self.engineering.pk]["employee_count"], 2)
        self.assertEqual(rows[self.finance.pk]["employee_count"], 1)
        self.assertEqual(response.context["total_employees"], 3)
        self.assertEqual(response.context["active_employees"], 2)
        self.assertEqual(response.context["avg_headcount"], 1.5)

        # Search filter narrows departments.
        response = self.client.get(
            reverse("hrms:reports_departments"), {"q": "Finance"}
        )
        self.assertContains(response, "Cyril Paul")
        self.assertNotContains(response, "Ana Thomas")

    def test_performance_report_reviews_and_warnings(self):
        employee = self._employee("Ana Thomas", "ana@example.com", self.engineering)
        EmployeePerformance.objects.create(
            employee=employee,
            review_period="Q3 2026",
            rating="4.5",
            feedback="Consistent delivery and strong ownership.",
            reviewed_by=self.hr_user,
        )
        EmployeePerformance.objects.create(
            employee=employee,
            review_period="Q2 2026",
            rating="2.5",
            feedback="Missed several deadlines.",
            reviewed_by=self.hr_user,
        )
        PerformanceWarning.objects.create(
            employee=employee,
            title="Missed delivery deadline",
            reason="Deliverable slipped by a week.",
            severity="Medium",
            status="Pending",
            issued_by=self.hr_user,
        )

        response = self.client.get(reverse("hrms:reports_performance"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Thomas")
        self.assertContains(response, "Q3 2026")
        self.assertContains(response, "Missed delivery deadline")
        self.assertEqual(response.context["total_reviews"], 2)
        self.assertEqual(response.context["avg_rating"], 3.5)
        self.assertEqual(response.context["open_warnings"], 1)
        self.assertEqual(response.context["rated_employees"], 1)

        # Rating filter keeps only high-rated reviews.
        response = self.client.get(
            reverse("hrms:reports_performance"), {"min_rating": "4"}
        )
        self.assertContains(response, "Q3 2026")
        self.assertNotContains(response, "Q2 2026")

        # Warning status filter.
        response = self.client.get(
            reverse("hrms:reports_performance"), {"warning_status": "Resolved"}
        )
        self.assertNotContains(response, "Missed delivery deadline")

    def test_all_report_pages_render_for_admin(self):
        for url_name in ReportsAccessTests.REPORT_URLS:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)

    def test_previous_tasks_pages_still_work_after_reports(self):
        for url_name in [
            "hrms:admin_dashboard",
            "hrms:employees_list",
            "hrms:hr_managers_list",
            "hrms:departments_list",
            "hrms:candidates_list",
            "hrms:recruitment_jobs",
            "hrms:recruitment_status",
            "hrms:recruitment_selected",
            "hrms:recruitment_approvals",
        ]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)

        # Sidebar exposes all five report links with the new section.
        response = self.client.get(reverse("hrms:admin_dashboard"))
        for text in [
            "HR Weekly Reports",
            "Employee Weekly Reports",
            "Recruitment Reports",
            "Department Employees",
            "Performance Reports",
        ]:
            self.assertContains(response, text)


class AdminResponsibilitiesWorkflowTests(TestCase):
    """
    Task 8: Admin Responsibilities Test Suite.
    Verifies performance warnings, HR recommendations, Admin decisions (Continue, Another Warning, Termination),
    confirmation enforcement, decision history, and security.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@company.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.client.force_login(self.admin)

        self.dept = AdminModuleDepartment.objects.create(name="Engineering")
        self.hrms_dept = Department.objects.create(name="Engineering")

        self.hr_user = User.objects.create_user(
            email="hrmanager@company.com",
            password="HrPass123!",
            name="Sarah HR",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_manager = StandaloneHRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR-001",
        )

        self.emp_user = User.objects.create_user(
            email="employee@company.com",
            password="EmpPass123!",
            name="Alex Dev",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.employee = StandaloneEmployee.objects.create(
            user=self.emp_user,
            department=self.dept,
            employee_code="EMP-001",
            designation="Backend Engineer",
            joining_date="2025-06-01",
            employment_status="ACTIVE",
        )
        self.hrms_employee = Employee.objects.create(
            user=self.emp_user,
            department=self.hrms_dept,
            designation="Backend Engineer",
            date_of_joining="2025-06-01",
            status=Employee.StatusChoices.ACTIVE,
        )

        self.warning = StandalonePerformanceWarning.objects.create(
            employee=self.employee,
            issued_by=self.hr_manager,
            reason="Consistently failing to meet sprint commitments and unexcused absences.",
            hr_recommendation="Recommend formal disciplinary warning or transition review.",
            status="SENT_TO_ADMIN",
        )

    def test_admin_can_view_warnings_list(self):
        response = self.client.get(reverse("hrms:admin_responsibilities_warnings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Performance Warnings")
        self.assertContains(response, "Alex Dev")
        self.assertContains(response, "EMP-001")
        self.assertContains(response, "Engineering")

    def test_admin_can_view_warning_detail(self):
        url = reverse("hrms:admin_responsibilities_warning_detail", args=[self.warning.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Warning #{self.warning.pk}")
        self.assertContains(response, "Consistently failing to meet sprint commitments")
        self.assertContains(response, "Sarah HR")
        self.assertContains(response, "HR Recommendation on Record")

    def test_admin_can_view_hr_recommendations(self):
        response = self.client.get(reverse("hrms:admin_responsibilities_recommendations"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HR Recommendations")
        self.assertContains(response, "Recommend formal disciplinary warning")
        self.assertContains(response, "Alex Dev")

    def test_admin_can_review_hr_recommendation_page(self):
        url = reverse("hrms:admin_responsibilities_review", args=[self.warning.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Review HR Recommendation")
        self.assertContains(response, "HR ADVISORY")
        self.assertContains(response, "ADMIN RULING")
        self.assertContains(response, "Decision Progression Lifecycle")

    def test_admin_decision_continue_employment(self):
        url = reverse("hrms:admin_responsibilities_decision", args=[self.warning.pk])
        response = self.client.post(
            url,
            {
                "decision": "CONTINUE",
                "admin_comments": "Performance has improved over the past two weeks. Continue employment with mentoring.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.warning.refresh_from_db()
        self.assertEqual(self.warning.admin_decision, "CONTINUE")
        self.assertEqual(self.warning.status, "RESOLVED")
        self.assertEqual(self.warning.decided_by, self.admin)
        self.assertIsNotNone(self.warning.decision_date)

        # Employee remains Active
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.employment_status, "ACTIVE")
        self.emp_user.refresh_from_db()
        self.assertTrue(self.emp_user.is_active)

    def test_admin_decision_give_another_warning(self):
        url = reverse("hrms:admin_responsibilities_decision", args=[self.warning.pk])
        response = self.client.post(
            url,
            {
                "decision": "ANOTHER_WARNING",
                "admin_comments": "Give one final 30-day warning before escalating to termination.",
                "new_warning_reason": "Final 30-day notice for sprint deliverables.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        # Current warning is resolved with decision
        self.warning.refresh_from_db()
        self.assertEqual(self.warning.admin_decision, "ANOTHER_WARNING")
        self.assertEqual(self.warning.status, "RESOLVED")

        # New warning is created for employee without overwriting previous history
        all_warnings = StandalonePerformanceWarning.objects.filter(employee=self.employee)
        self.assertEqual(all_warnings.count(), 2)

        new_warning = all_warnings.exclude(pk=self.warning.pk).first()
        self.assertIsNotNone(new_warning)
        self.assertEqual(new_warning.reason, "Final 30-day notice for sprint deliverables.")
        self.assertEqual(new_warning.status, "OPEN")
        self.assertIsNone(new_warning.admin_decision)

    def test_admin_decision_termination_requires_confirmation(self):
        url = reverse("hrms:admin_responsibilities_decision", args=[self.warning.pk])
        response = self.client.post(
            url,
            {
                "decision": "TERMINATION",
                "admin_comments": "Repeated policy violations. Immediate termination.",
                # Notice: confirm_termination is missing
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confirmation is required before issuing a termination letter")

        # Warning is NOT resolved
        self.warning.refresh_from_db()
        self.assertIsNone(self.warning.admin_decision)
        self.assertEqual(self.warning.status, "SENT_TO_ADMIN")

        # Employee is NOT terminated
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.employment_status, "ACTIVE")

    def test_admin_decision_termination_executed_with_confirmation(self):
        url = reverse("hrms:admin_responsibilities_decision", args=[self.warning.pk])
        response = self.client.post(
            url,
            {
                "decision": "TERMINATION",
                "admin_comments": "Repeated infractions confirmed. Immediate termination of employment.",
                "confirm_termination": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        # Warning updated
        self.warning.refresh_from_db()
        self.assertEqual(self.warning.admin_decision, "TERMINATION")
        self.assertEqual(self.warning.status, "RESOLVED")

        # Employee employment status updated to TERMINATED (record NOT deleted)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.employment_status, "TERMINATED")

        # User account deactivated
        self.emp_user.refresh_from_db()
        self.assertFalse(self.emp_user.is_active)
        self.assertEqual(self.emp_user.status, User.StatusChoices.INACTIVE)

        # hrms.Employee synchronized
        self.hrms_employee.refresh_from_db()
        self.assertEqual(self.hrms_employee.status, Employee.StatusChoices.TERMINATED)

        # Official termination document created under EmployeeDocument
        doc = EmployeeDocument.objects.filter(employee=self.employee).first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_type, "OTHER")

        # Ensure employee record is NOT deleted
        self.assertTrue(StandaloneEmployee.objects.filter(pk=self.employee.pk).exists())

    def test_role_security_for_admin_responsibilities(self):
        # HR user cannot access
        self.client.force_login(self.hr_user)
        for url_name in [
            "hrms:admin_responsibilities_warnings",
            "hrms:admin_responsibilities_recommendations",
        ]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)

        # Employee cannot access
        self.client.force_login(self.emp_user)
        for url_name in [
            "hrms:admin_responsibilities_warnings",
            "hrms:admin_responsibilities_recommendations",
        ]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)

        # Unauthenticated cannot access
        self.client.logout()
        for url_name in [
            "hrms:admin_responsibilities_warnings",
            "hrms:admin_responsibilities_recommendations",
        ]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)

    def test_sidebar_displays_admin_responsibilities_links(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("hrms:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Responsibilities")
        self.assertContains(response, "Performance Warnings")
        self.assertContains(response, "HR Recommendations")

    def test_previous_tasks_pages_still_work_with_task_8(self):
        self.client.force_login(self.admin)
        for url_name in [
            "hrms:admin_dashboard",
            "hrms:employees_list",
            "hrms:hr_managers_list",
            "hrms:departments_list",
            "hrms:candidates_list",
            "hrms:recruitment_jobs",
            "hrms:recruitment_status",
            "hrms:recruitment_selected",
            "hrms:recruitment_approvals",
            "hrms:reports_hr_weekly",
            "hrms:reports_employee_weekly",
            "hrms:reports_recruitment",
            "hrms:reports_departments",
            "hrms:reports_performance",
        ]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)


class AdminAnnouncementTests(TestCase):
    """Test suite verifying Admin Announcement management: Add, Edit, Delete, Publish, and Access Control."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin_ann@example.com",
            password="AdminPass123!",
            name="Admin Announcer",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_user = User.objects.create_user(
            email="hr_ann@example.com",
            password="HrPass123!",
            name="HR Announcer",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.employee_user = User.objects.create_user(
            email="emp_ann@example.com",
            password="EmpPass123!",
            name="Emp Announcer",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )

    def test_admin_can_view_announcements_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("hrms:announcements_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Announcement Management")
        self.assertContains(response, "Broadcast Registry")

    def test_admin_can_create_draft_announcement(self):
        self.client.force_login(self.admin)
        create_url = reverse("hrms:announcement_create")
        data = {
            "title": "Quarterly Town Hall",
            "announcement_type": "GENERAL",
            "target_audience": "All",
            "content": "Join us for the all-hands town hall this Friday.",
        }
        response = self.client.post(create_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quarterly Town Hall")

        from hr_management_system.hrms.models import Announcement
        ann = Announcement.objects.get(title="Quarterly Town Hall")
        self.assertFalse(ann.is_published)
        self.assertIsNone(ann.published_at)
        self.assertEqual(ann.created_by, self.admin)

    def test_admin_can_create_published_announcement(self):
        self.client.force_login(self.admin)
        create_url = reverse("hrms:announcement_create")
        data = {
            "title": "Holiday Notice",
            "announcement_type": "HOLIDAY",
            "target_audience": "Employees",
            "content": "Offices are closed on Monday.",
            "is_published": "on",
        }
        response = self.client.post(create_url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        from hr_management_system.hrms.models import Announcement
        ann = Announcement.objects.get(title="Holiday Notice")
        self.assertTrue(ann.is_published)
        self.assertIsNotNone(ann.published_at)

    def test_admin_can_view_announcement_detail(self):
        from hr_management_system.hrms.models import Announcement
        ann = Announcement.objects.create(
            title="System Maintenance",
            content="Scheduled downtime Sunday 2am-4am.",
            announcement_type="NOTICE",
            target_audience="All",
            created_by=self.admin,
            is_published=False,
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("hrms:announcement_detail", args=[ann.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Maintenance")
        self.assertContains(response, "Scheduled downtime Sunday 2am-4am.")

    def test_admin_can_edit_announcement(self):
        from hr_management_system.hrms.models import Announcement
        ann = Announcement.objects.create(
            title="Old Policy",
            content="Old policy guidelines.",
            announcement_type="HR",
            target_audience="Employees",
            created_by=self.admin,
            is_published=False,
        )
        self.client.force_login(self.admin)
        edit_url = reverse("hrms:announcement_edit", args=[ann.pk])
        edit_data = {
            "title": "Updated Policy 2026",
            "announcement_type": "HR",
            "target_audience": "Employees",
            "content": "Brand new guidelines for remote work.",
            "is_published": "on",
        }
        response = self.client.post(edit_url, edit_data, follow=True)
        self.assertEqual(response.status_code, 200)

        ann.refresh_from_db()
        self.assertEqual(ann.title, "Updated Policy 2026")
        self.assertEqual(ann.content, "Brand new guidelines for remote work.")
        self.assertTrue(ann.is_published)
        self.assertIsNotNone(ann.published_at)

    def test_admin_can_publish_announcement(self):
        from hr_management_system.hrms.models import Announcement
        ann = Announcement.objects.create(
            title="Draft Notice for Review",
            content="Draft content awaiting executive signoff.",
            announcement_type="NOTICE",
            target_audience="HR",
            created_by=self.admin,
            is_published=False,
            published_at=None,
        )
        self.client.force_login(self.admin)
        publish_url = reverse("hrms:announcement_publish", args=[ann.pk])

        # Publish
        response = self.client.post(publish_url, follow=True)
        self.assertEqual(response.status_code, 200)

        ann.refresh_from_db()
        self.assertTrue(ann.is_published)
        self.assertIsNotNone(ann.published_at)

        # Unpublish (toggle)
        response = self.client.post(publish_url, follow=True)
        self.assertEqual(response.status_code, 200)

        ann.refresh_from_db()
        self.assertFalse(ann.is_published)
        self.assertIsNone(ann.published_at)

    def test_admin_can_delete_announcement(self):
        from hr_management_system.hrms.models import Announcement
        ann = Announcement.objects.create(
            title="Announcement To Delete",
            content="This announcement should be deleted.",
            created_by=self.admin,
        )
        self.client.force_login(self.admin)
        delete_url = reverse("hrms:announcement_delete", args=[ann.pk])

        # GET shows confirmation
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete Announcement?")
        self.assertContains(response, "Announcement To Delete")

        # POST performs deletion
        response = self.client.post(delete_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Announcement.objects.filter(pk=ann.pk).exists())

    def test_non_admin_cannot_access_announcement_views(self):
        from hr_management_system.hrms.models import Announcement
        ann = Announcement.objects.create(
            title="Secret Admin Notice",
            content="Restricted message.",
            created_by=self.admin,
        )

        urls = [
            reverse("hrms:announcements_list"),
            reverse("hrms:announcement_create"),
            reverse("hrms:announcement_detail", args=[ann.pk]),
            reverse("hrms:announcement_edit", args=[ann.pk]),
            reverse("hrms:announcement_delete", args=[ann.pk]),
            reverse("hrms:announcement_publish", args=[ann.pk]),
        ]

        # 1. Unauthenticated users are redirected
        self.client.logout()
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

        # 2. HR manager cannot access admin announcement views
        self.client.force_login(self.hr_user)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

        # 3. Employee cannot access admin announcement views
        self.client.force_login(self.employee_user)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_sidebar_and_dashboard_display_announcements(self):
        self.client.force_login(self.admin)

        # Sidebar has link
        response = self.client.get(reverse("hrms:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Announcements")
        self.assertContains(response, "Recent Announcements")


from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from admin_module.forms import (
    AdminDecisionForm,
    AnnouncementForm,
    DepartmentForm,
    EmployeeCreateForm,
    HRManagerCreateForm,
    ensure_default_departments,
)
from admin_module.models import Announcement, Department, EmployeeApproval
from candidates.models import Candidate, JobApplication, JobVacancy
from employees.models import (
    Employee,
    EmployeePerformance,
    EmployeeReport,
    PerformanceWarning,
)
from hr.models import AptitudeTest, HRManager, Interview

User = get_user_model()


class AdminManagementFormsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@company.com",
            password="AdminPass123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Engineering", description="Tech team")

    def test_department_dropdown_has_default_department_options(self):
        depts = ensure_default_departments()
        self.assertTrue(depts.filter(name="Engineering").exists())

    def test_employee_form_creates_active_user_and_employee_record(self):
        form = EmployeeCreateForm(
            data={
                "full_name": "John Doe",
                "email": "john.doe@company.com",
                "password": "StrongPassword123!",
                "employee_code": "EMP-001",
                "department": self.department.pk,
                "designation": "Software Engineer",
                "joining_date": "2024-01-15",
                "employment_status": "ACTIVE",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        employee = form.save(admin_user=self.admin)

        self.assertEqual(employee.user.role, User.RoleChoices.EMPLOYEE)
        self.assertTrue(employee.user.check_password("StrongPassword123!"))
        self.assertEqual(employee.employee_code, "EMP-001")
        self.assertEqual(employee.employment_status, "ACTIVE")
        self.assertEqual(employee.designation, "Software Engineer")

    def test_hr_manager_form_rejects_duplicate_email(self):
        User.objects.create_user(
            email="hr.manager@company.com",
            password="Password123!",
            name="HR One",
            role=User.RoleChoices.HR,
        )
        form = HRManagerCreateForm(
            data={
                "full_name": "HR Manager Two",
                "email": "hr.manager@company.com",
                "password": "Password123!",
                "employee_code": "HR-002",
                "department": self.department.pk,
                "joining_date": "2024-02-01",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_hr_manager_form_creates_active_manager(self):
        form = HRManagerCreateForm(
            data={
                "full_name": "HR Specialist",
                "email": "specialist@company.com",
                "password": "SecurePass123!",
                "employee_code": "HR-009",
                "department": self.department.pk,
                "joining_date": "2024-03-01",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        manager = form.save(admin_user=self.admin)
        self.assertEqual(manager.employee_code, "HR-009")
        self.assertTrue(manager.is_active)
        self.assertEqual(manager.user.role, User.RoleChoices.HR)


class AdminAccessControlTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="AdminPass123!",
            name="Admin User",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.employee_user = User.objects.create_user(
            email="emp@test.com",
            password="UserPass123!",
            name="Normal Employee",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
        )

    def test_anonymous_users_redirected_to_admin_login(self):
        urls = [
            reverse("admin_module:admin_dashboard"),
            reverse("admin_module:employees_list"),
            reverse("admin_module:hr_managers_list"),
            reverse("admin_module:departments_list"),
            reverse("admin_module:announcements_list"),
            reverse("admin_module:recruitment_jobs"),
            reverse("admin_module:recruitment_approvals"),
            reverse("admin_module:reports_departments"),
            reverse("admin_module:admin_responsibilities_warnings"),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("admin_module:admin_login"), response.url)

    def test_non_admin_users_blocked(self):
        self.client.force_login(self.employee_user)
        response = self.client.get(reverse("admin_module:admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)

    def test_inactive_admin_blocked(self):
        self.admin.status = User.StatusChoices.INACTIVE
        self.admin.save()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_module:admin_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)
        self.admin.status = User.StatusChoices.ACTIVE
        self.admin.save()

    def test_authenticated_admin_allowed(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin_module:admin_dashboard"))
        self.assertEqual(response.status_code, 200)


class AdminDepartmentManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@dept.com",
            password="AdminPass123!",
            name="Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.client.force_login(self.admin)

    def test_create_department(self):
        response = self.client.post(
            reverse("admin_module:department_create"),
            {"name": "Marketing", "description": "Growth and brand", "is_active": True},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(name="Marketing").exists())

    def test_edit_department(self):
        dept = Department.objects.create(name="Finance", description="Old desc")
        response = self.client.post(
            reverse("admin_module:department_edit", kwargs={"department_id": dept.pk}),
            {"name": "Finance & Accounting", "description": "New desc", "is_active": True},
        )
        self.assertEqual(response.status_code, 302)
        dept.refresh_from_db()
        self.assertEqual(dept.name, "Finance & Accounting")
        self.assertEqual(dept.description, "New desc")

    def test_delete_department(self):
        dept = Department.objects.create(name="Temp Dept")
        response = self.client.post(
            reverse("admin_module:department_delete", kwargs={"department_id": dept.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Department.objects.filter(pk=dept.pk).exists())


class AdminEmployeeManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@emp.com",
            password="AdminPass123!",
            name="Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Operations")
        self.client.force_login(self.admin)

    def test_employee_list_view(self):
        user = User.objects.create_user(email="alice@emp.com", name="Alice", role=User.RoleChoices.EMPLOYEE)
        Employee.objects.create(
            user=user,
            employee_code="EMP-100",
            department=self.department,
            designation="Dev",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )
        response = self.client.get(reverse("admin_module:employees_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice")
        self.assertContains(response, "EMP-100")

    def test_employee_detail_view(self):
        user = User.objects.create_user(email="bob@emp.com", name="Bob", role=User.RoleChoices.EMPLOYEE)
        emp = Employee.objects.create(
            user=user,
            employee_code="EMP-101",
            department=self.department,
            designation="QA",
            joining_date=date(2024, 2, 1),
            employment_status="ACTIVE",
        )
        response = self.client.get(reverse("admin_module:employee_detail", kwargs={"employee_id": emp.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bob")
        self.assertContains(response, "QA")

    def test_employee_edit_view(self):
        user = User.objects.create_user(email="carol@emp.com", name="Carol", role=User.RoleChoices.EMPLOYEE)
        emp = Employee.objects.create(
            user=user,
            employee_code="EMP-102",
            department=self.department,
            designation="Junior Dev",
            joining_date=date(2024, 3, 1),
            employment_status="ACTIVE",
        )
        response = self.client.post(
            reverse("admin_module:employee_edit", kwargs={"employee_id": emp.pk}),
            {
                "full_name": "Carol Danvers",
                "email": "carol@emp.com",
                "department": self.department.pk,
                "designation": "Senior Dev",
                "employment_status": "ACTIVE",
                "joining_date": "2024-03-01",
            },
        )
        self.assertEqual(response.status_code, 302)
        emp.refresh_from_db()
        self.assertEqual(emp.designation, "Senior Dev")
        self.assertEqual(emp.user.name, "Carol Danvers")


class AdminAnnouncementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@ann.com",
            password="AdminPass123!",
            name="Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.client.force_login(self.admin)

    def test_admin_creates_announcement_always_published_immediately(self):
        response = self.client.post(
            reverse("admin_module:announcement_create"),
            {
                "title": "Town Hall Meeting",
                "announcement_type": "GENERAL",
                "target_audience": "All",
                "content": "Quarterly town hall next Friday.",
            },
        )
        self.assertEqual(response.status_code, 302)
        ann = Announcement.objects.get(title="Town Hall Meeting")
        self.assertTrue(ann.is_published)
        self.assertIsNotNone(ann.published_at)
        self.assertTrue(ann.is_active)
        self.assertEqual(ann.created_by, self.admin)
        self.assertEqual(ann.target_audience, "All")

    def test_admin_can_edit_announcement(self):
        ann = Announcement.objects.create(
            title="Holiday Notice",
            content="Office closed on Monday.",
            announcement_type="HOLIDAY",
            target_audience="Employees",
            created_by=self.admin,
            is_published=True,
            published_at=timezone.now(),
        )
        response = self.client.post(
            reverse("admin_module:announcement_edit", kwargs={"announcement_id": ann.pk}),
            {
                "title": "Updated Holiday Notice",
                "announcement_type": "HOLIDAY",
                "target_audience": "All",
                "content": "Office closed on Monday and Tuesday.",
            },
        )
        self.assertEqual(response.status_code, 302)
        ann.refresh_from_db()
        self.assertEqual(ann.title, "Updated Holiday Notice")
        self.assertEqual(ann.target_audience, "All")
        self.assertTrue(ann.is_published)

    def test_admin_can_delete_announcement(self):
        ann = Announcement.objects.create(
            title="Temporary Notice",
            content="Will be deleted.",
            announcement_type="NOTICE",
            created_by=self.admin,
            is_published=True,
            published_at=timezone.now(),
        )
        response = self.client.post(
            reverse("admin_module:announcement_delete", kwargs={"announcement_id": ann.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Announcement.objects.filter(pk=ann.pk).exists())


class RecruitmentMonitoringAndApprovalTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@rec.com",
            password="AdminPass123!",
            name="Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Product")
        self.vacancy = JobVacancy.objects.create(
            title="Product Manager",
            department=self.department,
            description="Manage product lifecycle",
            status="OPEN",
            posted_by=self.admin,
        )
        self.cand_user = User.objects.create_user(
            email="cand@test.com",
            name="Jane Candidate",
            role=User.RoleChoices.CANDIDATE,
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user,
            first_name="Jane",
            last_name="Candidate",
            phone="1234567890",
        )
        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.vacancy,
            status="SELECTED",
        )
        self.client.force_login(self.admin)

    def test_jobs_page_lists_job_postings_with_real_details(self):
        response = self.client.get(reverse("admin_module:recruitment_jobs"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Manager")

    def test_recruitment_status_page_renders_stage_table(self):
        response = self.client.get(reverse("admin_module:recruitment_status"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Manager")

    def test_selected_candidates_page_lists_only_selected(self):
        response = self.client.get(reverse("admin_module:recruitment_selected"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Candidate")

    def test_candidate_detail_page(self):
        response = self.client.get(
            reverse("admin_module:recruitment_candidate_detail", kwargs={"candidate_id": self.candidate.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Candidate")

    def test_approve_flow_activates_employee_and_user(self):
        emp_user = User.objects.create_user(
            email="new.hire@company.com",
            name="New Hire",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.PENDING,
            is_active=False,
        )
        employee = Employee.objects.create(
            user=emp_user,
            candidate=self.candidate,
            employee_code="EMP-999",
            department=self.department,
            designation="Associate PM",
            joining_date=date(2024, 4, 1),
            employment_status="INACTIVE",
        )
        approval = EmployeeApproval.objects.create(
            employee=employee,
            status="PENDING",
        )

        response = self.client.get(reverse("admin_module:recruitment_approvals"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Hire")

        # Execute approval
        post_response = self.client.post(
            reverse("admin_module:recruitment_approval_approve", kwargs={"employee_id": employee.pk}),
            {"comments": "Approved after great interviews."},
        )
        self.assertEqual(post_response.status_code, 302)

        approval.refresh_from_db()
        employee.refresh_from_db()
        emp_user.refresh_from_db()

        self.assertEqual(approval.status, "APPROVED")
        self.assertEqual(approval.approved_by, self.admin)
        self.assertEqual(employee.employment_status, "ACTIVE")
        self.assertTrue(emp_user.is_active)
        self.assertEqual(emp_user.status, User.StatusChoices.ACTIVE)


class AdminReportsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@rep.com",
            password="AdminPass123!",
            name="Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Analytics")
        self.client.force_login(self.admin)

    def test_all_report_pages_render_for_admin(self):
        report_urls = [
            reverse("admin_module:reports_hr_weekly"),
            reverse("admin_module:reports_employee_weekly"),
            reverse("admin_module:reports_recruitment"),
            reverse("admin_module:reports_departments"),
            reverse("admin_module:reports_performance"),
        ]
        for url in report_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


class AdminResponsibilitiesWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@resp.com",
            password="AdminPass123!",
            name="Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Support")
        self.emp_user = User.objects.create_user(
            email="emp.resp@company.com",
            name="Support Agent",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            employee_code="EMP-SUPP",
            department=self.department,
            designation="Support Specialist",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )
        self.hr_user = User.objects.create_user(
            email="hr.resp@company.com",
            name="HR Specialist",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            employee_code="HR-SUPP",
            department=self.department,
            joining_date=date(2024, 1, 1),
            is_active=True,
        )
        self.warning = PerformanceWarning.objects.create(
            employee=self.employee,
            issued_by=self.hr_manager,
            reason="Unresolved customer escalation backlog.",
            hr_recommendation="Recommend issuing a final warning or reassignment.",
            status="SENT_TO_ADMIN",
        )
        self.client.force_login(self.admin)

    def test_admin_can_view_warnings_list(self):
        response = self.client.get(reverse("admin_module:admin_responsibilities_warnings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Support Agent")

    def test_admin_can_view_hr_recommendations(self):
        response = self.client.get(reverse("admin_module:admin_responsibilities_recommendations"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommend issuing a final warning")

    def test_admin_decision_continue_employment(self):
        response = self.client.post(
            reverse("admin_module:admin_responsibilities_decision", kwargs={"warning_id": self.warning.pk}),
            {
                "decision": "CONTINUE",
                "admin_comments": "Performance has improved this week, continue employment with mentoring.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.warning.refresh_from_db()
        self.assertEqual(self.warning.status, "RESOLVED")
        self.assertEqual(self.warning.admin_decision, "CONTINUE")
        self.assertEqual(self.warning.decided_by, self.admin)

    def test_admin_decision_termination_executed(self):
        response = self.client.post(
            reverse("admin_module:admin_responsibilities_decision", kwargs={"warning_id": self.warning.pk}),
            {
                "decision": "TERMINATION",
                "admin_comments": "Repeated protocol violations, proceed with immediate termination.",
                "confirm_termination": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.warning.refresh_from_db()
        self.employee.refresh_from_db()
        self.emp_user.refresh_from_db()

        self.assertEqual(self.warning.status, "RESOLVED")
        self.assertEqual(self.warning.admin_decision, "TERMINATION")
        self.assertEqual(self.employee.employment_status, "TERMINATED")
        self.assertFalse(self.emp_user.is_active)
        self.assertEqual(self.emp_user.status, User.StatusChoices.INACTIVE)

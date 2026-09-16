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
    EmployeeDocument,
    EmployeePerformance,
    EmployeeReport,
    Notification,
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

    def test_department_records_loads_actual_database_data_and_headcounts(self):
        """Department records directory renders actual DB departments and computed employee headcounts."""
        dept_tech = Department.objects.create(name="Cloud Engineering", description="Cloud architecture team", is_active=True)
        dept_empty = Department.objects.create(name="Legal Compliance", description="Legal affairs", is_active=False)

        # Add 2 employees to Cloud Engineering
        for i in range(1, 3):
            u = User.objects.create_user(
                email=f"cloud.dev{i}@company.com",
                name=f"Cloud Dev {i}",
                role=User.RoleChoices.EMPLOYEE,
            )
            Employee.objects.create(
                user=u,
                employee_code=f"CLD-00{i}",
                department=dept_tech,
                designation="Cloud Engineer",
                joining_date=date(2024, 1, 1),
                employment_status="ACTIVE",
            )

        response = self.client.get(reverse("admin_module:departments_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cloud Engineering")
        self.assertContains(response, "Cloud architecture team")
        self.assertContains(response, "2 personnel")
        self.assertContains(response, "Legal Compliance")
        self.assertContains(response, "0 personnel")

    def test_empty_department_records_handled_gracefully(self):
        """Empty department queryset displays a clean 'No Departments Found' state."""
        # Ensure no departments exist
        Department.objects.all().delete()
        response = self.client.get(reverse("admin_module:departments_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Departments Found")

    def test_department_detail_view_renders_actual_data(self):
        """Department detail view renders employees, HR leads, and vacancy records."""
        dept = Department.objects.create(name="Cyber Security", description="SecOps team", is_active=True)
        u = User.objects.create_user(email="sec.dev@company.com", name="Security Dev", role=User.RoleChoices.EMPLOYEE)
        Employee.objects.create(
            user=u,
            employee_code="SEC-001",
            department=dept,
            designation="Security Specialist",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )
        hr_u = User.objects.create_user(email="sec.hr@company.com", name="Security HR Lead", role=User.RoleChoices.HR)
        HRManager.objects.create(
            user=hr_u,
            employee_code="SEC-HR",
            department=dept,
            joining_date=date(2024, 1, 1),
        )

        response = self.client.get(reverse("admin_module:department_detail", kwargs={"department_id": dept.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cyber Security")
        self.assertContains(response, "Security Specialist")
        self.assertContains(response, "Security HR Lead")
        self.assertContains(response, "1 Members")

    def test_department_auth_protection(self):
        """Anonymous and non-admin users cannot access department views."""
        self.client.logout()
        response = self.client.get(reverse("admin_module:departments_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)



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

    def test_employee_edit_view_and_status_sync(self):
        user = User.objects.create_user(
            email="carol@emp.com",
            name="Carol",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        emp = Employee.objects.create(
            user=user,
            employee_code="EMP-102",
            department=self.department,
            designation="Junior Dev",
            joining_date=date(2024, 3, 1),
            employment_status="ACTIVE",
        )
        # Edit employee to INACTIVE status
        response = self.client.post(
            reverse("admin_module:employee_edit", kwargs={"employee_id": emp.pk}),
            {
                "full_name": "Carol Danvers",
                "email": "carol@emp.com",
                "department": self.department.pk,
                "designation": "Senior Dev",
                "employment_status": "INACTIVE",
                "joining_date": "2024-03-01",
            },
        )
        self.assertEqual(response.status_code, 302)
        emp.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(emp.designation, "Senior Dev")
        self.assertEqual(emp.user.name, "Carol Danvers")
        self.assertEqual(emp.employment_status, "INACTIVE")
        self.assertFalse(user.is_active)
        self.assertEqual(user.status, User.StatusChoices.INACTIVE)

    def test_employee_termination_preserves_all_historical_records(self):
        """Verify normal admin removal terminates/deactivates rather than physically deleting."""
        user = User.objects.create_user(
            email="dan@emp.com",
            name="Dan",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        emp = Employee.objects.create(
            user=user,
            employee_code="EMP-103",
            department=self.department,
            designation="Analyst",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )
        hr_user = User.objects.create_user(
            email="hr.manager@test.com",
            name="HR Manager",
            role=User.RoleChoices.HR,
        )
        hr_mgr = HRManager.objects.create(
            user=hr_user,
            department=self.department,
            employee_code="HR-010",
        )

        # Create historical records
        report = EmployeeReport.objects.create(
            employee=emp,
            title="Sprint 1 Report",
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            work_summary="Completed sprint items",
            tasks_completed="Task 1, Task 2",
            status="REVIEWED",
            reviewed_by=hr_mgr,
        )
        perf = EmployeePerformance.objects.create(
            employee=emp,
            review_period="Q1 2024",
            score=4.5,
            rating="EXCELLENT",
            comments="Great performance",
            review_date=date(2024, 3, 31),
            reviewed_by=hr_mgr,
        )
        warning = PerformanceWarning.objects.create(
            employee=emp,
            warning_date=date(2024, 2, 15),
            reason="Late submission",
            status="ISSUED",
            issued_by=hr_mgr,
        )
        doc = EmployeeDocument.objects.create(
            employee=emp,
            document_type="ID_PROOF",
            document="employees/documents/test_id.pdf",
        )
        notif = Notification.objects.create(
            employee=emp,
            title="System Alert",
            message="Welcome to HRMS",
        )

        # GET confirm delete view
        get_resp = self.client.get(reverse("admin_module:employee_delete", kwargs={"employee_id": emp.pk}))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, "Terminate Employee")

        # POST to terminate employee
        post_resp = self.client.post(
            reverse("admin_module:employee_delete", kwargs={"employee_id": emp.pk})
        )
        self.assertEqual(post_resp.status_code, 302)

        # Assert no physical deletion occurred
        self.assertTrue(Employee.objects.filter(pk=emp.pk).exists())
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

        # Assert status updated to TERMINATED and User deactivated
        emp.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(emp.employment_status, "TERMINATED")
        self.assertFalse(user.is_active)
        self.assertEqual(user.status, User.StatusChoices.INACTIVE)

        # Assert department relation remains intact
        self.assertEqual(emp.department, self.department)

        # Assert all historical records remain intact
        self.assertTrue(EmployeeReport.objects.filter(pk=report.pk).exists())
        self.assertEqual(report.employee, emp)
        self.assertTrue(EmployeePerformance.objects.filter(pk=perf.pk).exists())
        self.assertEqual(perf.employee, emp)
        self.assertTrue(PerformanceWarning.objects.filter(pk=warning.pk).exists())
        self.assertEqual(warning.employee, emp)
        self.assertTrue(EmployeeDocument.objects.filter(pk=doc.pk).exists())
        self.assertEqual(doc.employee, emp)
        self.assertTrue(Notification.objects.filter(pk=notif.pk).exists())
        self.assertEqual(notif.employee, emp)

    def test_already_terminated_employee_handled_safely(self):
        user = User.objects.create_user(
            email="erin@emp.com",
            name="Erin",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.INACTIVE,
            is_active=False,
        )
        emp = Employee.objects.create(
            user=user,
            employee_code="EMP-104",
            department=self.department,
            designation="Contractor",
            joining_date=date(2024, 1, 1),
            employment_status="TERMINATED",
        )
        response = self.client.post(
            reverse("admin_module:employee_delete", kwargs={"employee_id": emp.pk})
        )
        self.assertEqual(response.status_code, 302)
        emp.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(emp.employment_status, "TERMINATED")
        self.assertFalse(user.is_active)

    def test_anonymous_user_cannot_terminate_employee(self):
        user = User.objects.create_user(email="frank@emp.com", name="Frank", role=User.RoleChoices.EMPLOYEE)
        emp = Employee.objects.create(
            user=user,
            employee_code="EMP-105",
            department=self.department,
            designation="Dev",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )
        self.client.logout()
        response = self.client.post(
            reverse("admin_module:employee_delete", kwargs={"employee_id": emp.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)
        emp.refresh_from_db()
        self.assertEqual(emp.employment_status, "ACTIVE")

    def test_non_admin_user_cannot_terminate_employee(self):
        user = User.objects.create_user(email="grace@emp.com", name="Grace", role=User.RoleChoices.EMPLOYEE)
        emp = Employee.objects.create(
            user=user,
            employee_code="EMP-106",
            department=self.department,
            designation="Dev",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )
        normal_employee_user = User.objects.create_user(
            email="other.emp@emp.com",
            name="Other Employee",
            role=User.RoleChoices.EMPLOYEE,
        )
        self.client.force_login(normal_employee_user)
        response = self.client.post(
            reverse("admin_module:employee_delete", kwargs={"employee_id": emp.pk})
        )
        self.assertEqual(response.status_code, 302)
        emp.refresh_from_db()
        self.assertEqual(emp.employment_status, "ACTIVE")


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

    def test_candidates_list_has_no_add_candidate_action(self):
        response = self.client.get(reverse("admin_module:candidates_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "New Candidate Application")
        self.assertNotContains(response, "Register First Candidate")
        self.assertNotContains(response, "Add Candidate")

    def test_candidate_create_url_is_removed(self):
        response = self.client.get("/admin-portal/candidates/add/")
        self.assertEqual(response.status_code, 404)



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
            password="EmpPass123!",
            name="Support Agent",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
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

    def test_admin_can_open_issue_warning_form(self):
        """Admin can open the Issue Warning form; employee and original report are automatically bound."""
        url = reverse("admin_module:admin_responsibilities_issue_warning", kwargs={"warning_id": self.warning.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Support Agent")
        self.assertContains(response, "EMP-SUPP")
        self.assertContains(response, "Unresolved customer escalation backlog.")
        self.assertContains(response, "Issue Formal Warning")

    def test_warning_message_is_required(self):
        """Warning message cannot be empty."""
        url = reverse("admin_module:admin_responsibilities_issue_warning", kwargs={"warning_id": self.warning.pk})
        response = self.client.post(url, {"warning_message": "   "})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Warning message cannot be empty.")
        self.warning.refresh_from_db()
        self.assertNotEqual(self.warning.status, "RESOLVED")

    def test_admin_issues_warning_and_notifies_only_target_employee(self):
        """Admin issues warning: updates PerformanceWarning, notifies exact employee, excludes other employees and HR."""
        # Create another employee
        other_user = User.objects.create_user(
            email="other.emp@company.com",
            name="Other Employee",
            role=User.RoleChoices.EMPLOYEE,
        )
        other_employee = Employee.objects.create(
            user=other_user,
            employee_code="EMP-OTHER",
            department=self.department,
            designation="Developer",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )

        url = reverse("admin_module:admin_responsibilities_issue_warning", kwargs={"warning_id": self.warning.pk})
        directive = "Clear all backlog tickets within 24 hours. Failure will lead to escalation."
        response = self.client.post(url, {"warning_message": directive})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("admin_module:admin_responsibilities_warnings"))

        # 1. Check PerformanceWarning updated
        self.warning.refresh_from_db()
        self.assertEqual(self.warning.status, "RESOLVED")
        self.assertEqual(self.warning.admin_decision, "ANOTHER_WARNING")
        self.assertEqual(self.warning.admin_comments, directive)
        self.assertEqual(self.warning.decided_by, self.admin)
        self.assertIsNotNone(self.warning.decision_date)

        # 2. Check Target Employee Notification
        target_notifs = Notification.objects.filter(employee=self.employee)
        self.assertTrue(target_notifs.exists())
        notif = target_notifs.last()
        self.assertIn(directive, notif.message)
        self.assertIn(self.warning.reason, notif.message)
        self.assertEqual(notif.notification_type, "WARNING")

        # 3. Check other employee received NO notification
        self.assertFalse(Notification.objects.filter(employee=other_employee).exists())

        # 4. Check employee can view notification in Employee Portal
        self.client.logout()
        self.client.login(username=self.emp_user.email, password="EmpPass123!")
        notif_resp = self.client.get(reverse("employees:notifications"))
        self.assertEqual(notif_resp.status_code, 200)
        self.assertContains(notif_resp, "Performance Warning Notice")
        self.assertContains(notif_resp, directive)

    def test_anonymous_user_cannot_issue_warning(self):
        """Anonymous user is redirected to admin login."""
        self.client.logout()
        url = reverse("admin_module:admin_responsibilities_issue_warning", kwargs={"warning_id": self.warning.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)

    def test_non_admin_user_cannot_issue_warning(self):
        """Non-admin user cannot access issue warning endpoint."""
        self.client.force_login(self.emp_user)
        url = reverse("admin_module:admin_responsibilities_issue_warning", kwargs={"warning_id": self.warning.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)



class AdminHRManagerDetailViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin.hrdetail@test.com",
            password="AdminPassword123!",
            name="Super Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Human Resources", description="HR Operations")
        self.hr_user = User.objects.create_user(
            email="jane.hr@company.com",
            password="HRSecretPass999!",
            name="Jane HR Officer",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            employee_code="HR-100",
            department=self.department,
            joining_date=date(2023, 6, 15),
            is_active=True,
        )
        self.client.force_login(self.admin)

    def test_admin_sees_all_existing_hr_profile_fields(self):
        """Admin detail view aggregates all HR profile, account, and professional fields."""
        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane HR Officer")
        self.assertContains(response, "jane.hr@company.com")
        self.assertContains(response, "HR-100")
        self.assertContains(response, "Human Resources")
        self.assertContains(response, "Personal Information")
        self.assertContains(response, "Professional Information")
        self.assertContains(response, "Account Information")
        self.assertContains(response, "Documents")
        self.assertContains(response, "HR Operations Activity")

    def test_hr_updated_information_appears_immediately_on_admin_detail_page(self):
        """When HR updates profile information, the Admin detail view immediately reflects changes."""
        self.hr_user.name = "Jane Updated Name"
        self.hr_user.email = "jane.updated@company.com"
        self.hr_user.save()

        new_dept = Department.objects.create(name="Global Talent Acquisition")
        self.hr_manager.department = new_dept
        self.hr_manager.employee_code = "HR-999"
        self.hr_manager.save()

        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Updated Name")
        self.assertContains(response, "jane.updated@company.com")
        self.assertContains(response, "HR-999")
        self.assertContains(response, "Global Talent Acquisition")

    def test_missing_optional_information_shows_appropriate_message(self):
        """Missing optional fields display clean fallback messages instead of blank/None."""
        user_empty = User.objects.create_user(
            email="blank.hr@company.com",
            password="Password123!",
            name="",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
        )
        manager_empty = HRManager.objects.create(
            user=user_empty,
            employee_code="",
            department=None,
            joining_date=None,
            is_active=True,
        )

        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": manager_empty.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not provided")
        self.assertContains(response, "Unassigned")
        self.assertContains(response, "Not uploaded")
        self.assertContains(response, "Never logged in")

    def test_profile_photo_and_documents_display_correctly(self):
        """Profile photo and documents linked to the HR user appear with valid links."""
        emp = Employee.objects.create(
            user=self.hr_user,
            employee_code="HR-100",
            department=self.department,
            designation="HR Manager",
            joining_date=date(2023, 6, 15),
            employment_status="ACTIVE",
            profile_photo="employees/profile_photos/jane_avatar.png",
        )
        doc = EmployeeDocument.objects.create(
            employee=emp,
            document_type="ID_PROOF",
            document="employees/documents/passport.pdf",
        )

        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "employees/profile_photos/jane_avatar.png")
        self.assertContains(response, "employees/documents/passport.pdf")
        self.assertContains(response, "ID Proof")
        self.assertContains(response, "View / Download")

    def test_password_and_hash_never_displayed(self):
        """Ensure neither raw password nor password hash appears anywhere on the profile page."""
        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "HRSecretPass999!")
        self.assertNotContains(response, self.hr_user.password)
        self.assertContains(response, "Encrypted (Hidden)")

    def test_anonymous_user_cannot_access_hr_manager_detail_page(self):
        """Unauthenticated requests are redirected to the admin login."""
        self.client.logout()
        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)

    def test_non_admin_user_cannot_access_hr_manager_detail_page(self):
        """Non-admin users cannot access the Admin HR Manager detail page."""
        self.client.force_login(self.hr_user)
        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)

    def test_hr_manager_detail_data_isolation(self):
        """Viewing HR Manager A displays only A's data, not HR Manager B's data."""
        other_hr_user = User.objects.create_user(
            email="other.hr@company.com",
            name="Other HR Manager",
            role=User.RoleChoices.HR,
        )
        other_hr_manager = HRManager.objects.create(
            user=other_hr_user,
            employee_code="HR-9999",
            department=self.department,
            joining_date=date(2024, 1, 1),
        )

        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane HR Officer")
        self.assertContains(response, "jane.hr@company.com")
        self.assertNotContains(response, "Other HR Manager")
        self.assertNotContains(response, "other.hr@company.com")
        self.assertNotContains(response, "HR-9999")

    def test_admin_details_not_present_in_hr_manager_detail_page(self):
        """Admin account sections and 'Created By' do not appear in HR Manager detail content."""
        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hr_user.email)
        self.assertNotContains(response, "Created By")
        self.assertNotContains(response, "System Admin / Direct Hire")



class AdminEmployeeDetailViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin.empdetail@test.com",
            password="AdminPassword123!",
            name="Super Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="Engineering", description="Software Development")
        self.emp_user = User.objects.create_user(
            email="john.smith@company.com",
            password="EmpSecretPass456!",
            name="John Smith",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            employee_code="EMP-200",
            department=self.department,
            designation="Fullstack Engineer",
            joining_date=date(2023, 5, 10),
            employment_status="ACTIVE",
        )
        self.client.force_login(self.admin)

    def test_admin_sees_all_existing_employee_profile_fields(self):
        """Admin detail view aggregates all personal, employment, account, and document sections."""
        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Smith")
        self.assertContains(response, "john.smith@company.com")
        self.assertContains(response, "EMP-200")
        self.assertContains(response, "Fullstack Engineer")
        self.assertContains(response, "Engineering")
        self.assertContains(response, "Personal Information")
        self.assertContains(response, "Employment Information")
        self.assertContains(response, "Account Information")
        self.assertContains(response, "Documents")
        self.assertContains(response, "Work & Performance Summary")

    def test_employee_updated_information_appears_correctly(self):
        """When an employee updates their profile, changes immediately reflect on the admin detail page."""
        self.emp_user.name = "Johnathan Smith"
        self.emp_user.email = "johnathan.smith@company.com"
        self.emp_user.save()

        self.employee.designation = "Lead Architect"
        self.employee.save()

        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Johnathan Smith")
        self.assertContains(response, "johnathan.smith@company.com")
        self.assertContains(response, "Lead Architect")

    def test_missing_optional_information_shows_appropriate_messages(self):
        """Missing optional fields cleanly display fallback labels."""
        empty_user = User.objects.create_user(
            email="blank.emp@company.com",
            password="Password123!",
            name="",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
        )
        empty_emp = Employee.objects.create(
            user=empty_user,
            employee_code="",
            department=self.department,
            designation="",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )

        url = reverse("admin_module:employee_detail", kwargs={"employee_id": empty_emp.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not provided")
        self.assertContains(response, "Not uploaded")
        self.assertContains(response, "Never logged in")

    def test_profile_photo_and_documents_display_when_available(self):
        """Profile photo and uploaded documents display with links and types."""
        self.employee.profile_photo = "employees/profile_photos/john_avatar.png"
        self.employee.save()

        doc = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type="EXPERIENCE_CERTIFICATE",
            document="employees/documents/exp_cert.pdf",
        )

        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "employees/profile_photos/john_avatar.png")
        self.assertContains(response, "employees/documents/exp_cert.pdf")
        self.assertContains(response, "Experience Certificate")
        self.assertContains(response, "View / Download")

    def test_candidate_information_displayed_when_present(self):
        """When an employee is linked to a recruited candidate, contact and address info appear."""
        cand_user = User.objects.create_user(
            email="cand.emp@test.com",
            password="CandPassword123!",
            name="Candidate John",
            role=User.RoleChoices.EMPLOYEE,
        )
        candidate = Candidate.objects.create(
            user=cand_user,
            first_name="Candidate",
            last_name="John",
            phone="+1234567890",
            address="123 Tech Boulevard, Silicon Valley",
            date_of_birth=date(1995, 8, 20),
        )
        emp = Employee.objects.create(
            user=cand_user,
            candidate=candidate,
            employee_code="EMP-CAND",
            department=self.department,
            designation="Developer",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )

        url = reverse("admin_module:employee_detail", kwargs={"employee_id": emp.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "+1234567890")
        self.assertContains(response, "123 Tech Boulevard, Silicon Valley")
        self.assertContains(response, "August 20, 1995")

    def test_password_and_hash_never_displayed(self):
        """Ensure neither raw password nor password hash is ever rendered on the employee detail page."""
        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "EmpSecretPass456!")
        self.assertNotContains(response, self.emp_user.password)
        self.assertContains(response, "Encrypted (Hidden)")

    def test_anonymous_user_cannot_access_employee_detail_page(self):
        """Unauthenticated requests are redirected to the admin login."""
        self.client.logout()
        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)

    def test_non_admin_user_cannot_access_employee_detail_page(self):
        """Non-admin users cannot access the Admin Employee detail page."""
        self.client.force_login(self.emp_user)
        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin_module:admin_login"), response.url)

    def test_employee_detail_data_isolation(self):
        """Viewing Employee A displays only A's data, not Employee B's data."""
        other_user = User.objects.create_user(
            email="other.emp@company.com",
            name="Other Employee",
            role=User.RoleChoices.EMPLOYEE,
        )
        other_employee = Employee.objects.create(
            user=other_user,
            employee_code="EMP-9999",
            department=self.department,
            designation="Mobile Developer",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )

        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Smith")
        self.assertContains(response, "john.smith@company.com")
        self.assertNotContains(response, "Other Employee")
        self.assertNotContains(response, "other.emp@company.com")
        self.assertNotContains(response, "EMP-9999")

    def test_admin_details_not_present_in_employee_detail_page(self):
        """Admin account info and 'Created By' do not appear in Employee detail page content."""
        self.employee.created_by = self.admin
        self.employee.save()

        url = reverse("admin_module:employee_detail", kwargs={"employee_id": self.employee.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.emp_user.email)
        self.assertNotContains(response, "Created By")
        self.assertNotContains(response, "System Admin / Direct Hire")


class AdminHRManagerDataIsolationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="binittasaji2003@gmail.com",
            password="AdminPass123!",
            name="Binitta Saji",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )
        self.department = Department.objects.create(name="HR Operations", description="HR Dept")

        # Create actual HR Manager
        self.hr_user = User.objects.create_user(
            email="hr.manager@company.com",
            password="HRPass123!",
            name="Alice Walker",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.department,
            employee_code="HR-101",
            joining_date=date(2023, 5, 10),
            is_active=True,
        )

        # Create accidental HRManager record linked to Admin (simulating legacy/accidental get_or_create)
        self.admin_hrmanager = HRManager.objects.create(
            user=self.admin,
            department=self.department,
            employee_code="ADMIN-HR-001",
            joining_date=date(2023, 1, 1),
            is_active=True,
        )

    def test_admin_user_excluded_from_hr_managers_list(self):
        """Admin user must never appear in the HR Managers directory."""
        self.client.force_login(self.admin)
        url = reverse("admin_module:hr_managers_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Alice Walker should be present in the HR list
        self.assertContains(response, "Alice Walker")
        self.assertContains(response, "hr.manager@company.com")
        # Admin details must NOT appear in the HR table
        self.assertNotContains(response, "ADMIN-HR-001")
        self.assertEqual(len(response.context["hr_managers"]), 1)
        self.assertEqual(response.context["hr_managers"][0].user, self.hr_user)

    def test_admin_user_excluded_from_sidebar_and_dashboard_counts(self):
        """Sidebar count and dashboard recent HR list must only include actual HR managers."""
        self.client.force_login(self.admin)
        url = reverse("admin_module:admin_dashboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["hr_managers_count"], 1)
        recent_hrs = response.context["recent_hr_managers"]
        self.assertEqual(len(recent_hrs), 1)
        self.assertEqual(recent_hrs[0].user, self.hr_user)

    def test_admin_hrmanager_record_cannot_be_viewed_via_detail(self):
        """Accessing HR Manager detail for an Admin returns 404."""
        self.client.force_login(self.admin)
        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.admin_hrmanager.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Valid HR Manager returns 200
        valid_url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        valid_response = self.client.get(valid_url)
        self.assertEqual(valid_response.status_code, 200)
        self.assertContains(valid_response, "Alice Walker")

    def test_admin_hrmanager_record_cannot_be_edited_or_deleted(self):
        """Edit, delete, and toggle status for Admin HRManager record return 404."""
        self.client.force_login(self.admin)

        edit_url = reverse("admin_module:hr_manager_edit", kwargs={"manager_id": self.admin_hrmanager.pk})
        self.assertEqual(self.client.get(edit_url).status_code, 404)

        del_url = reverse("admin_module:hr_manager_delete", kwargs={"manager_id": self.admin_hrmanager.pk})
        self.assertEqual(self.client.get(del_url).status_code, 404)

        toggle_url = reverse("admin_module:hr_manager_toggle_status", kwargs={"manager_id": self.admin_hrmanager.pk})
        self.assertEqual(self.client.post(toggle_url).status_code, 404)

    def test_empty_state_when_no_real_hr_managers(self):
        """When no real HR managers exist, empty state is displayed."""
        self.hr_manager.delete()
        self.hr_user.delete()

        self.client.force_login(self.admin)
        url = reverse("admin_module:hr_managers_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["hr_managers"]), 0)
        self.assertContains(response, "No HR Managers Found")

    def test_department_hr_metrics_exclude_admin(self):
        """Department HR counts and lists only include actual HR managers."""
        self.client.force_login(self.admin)

        # Department list
        url = reverse("admin_module:departments_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        dept = [d for d in response.context["departments"] if d.pk == self.department.pk][0]
        self.assertEqual(dept.hr_count, 1)

        # Department detail
        detail_url = reverse("admin_module:department_detail", kwargs={"department_id": self.department.pk})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.context["hr_managers"].count(), 1)
        self.assertEqual(detail_response.context["hr_managers"].first().user, self.hr_user)





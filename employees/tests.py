from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from admin_module.models import Department
from employees.models import Employee

User = get_user_model()


class EmployeeAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Engineering", is_active=True)
        self.email = "test.employee@company.com"
        self.password = "Secr3tPass!123"
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            name="Test Employee",
            is_active=True,
        )
        self.employee = Employee.objects.create(
            user=self.user,
            employee_code="EMP9999",
            department=self.dept,
            designation="Developer",
            joining_date=date(2025, 1, 1),
            employment_status="ACTIVE",
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse("employees:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Employee Login")

    def test_successful_employee_login_and_redirect(self):
        response = self.client.post(
            reverse("employees:login"),
            {"email": self.email, "password": self.password},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employees/dashboard.html")
        self.assertContains(response, "Test Employee")

    def test_invalid_login_credentials(self):
        response = self.client.post(
            reverse("employees:login"),
            {"email": self.email, "password": "WrongPassword"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid email/ID or password")

    def test_dashboard_login_required(self):
        response = self.client.get(reverse("employees:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_user_redirect_view_routes_to_dashboard(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(reverse("users:redirect"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employees/dashboard.html")

    def test_reviewed_report_popup_display_and_dismiss(self):
        from django.utils import timezone
        from employees.models import EmployeeReport
        from hr.models import HRManager

        hr_user = User.objects.create_user(
            email="hr.reviewer@company.com",
            password="Password123!",
            name="HR Reviewer",
            is_active=True,
        )
        hr_manager = HRManager.objects.create(
            user=hr_user,
            employee_code="HR001",
            department=self.dept,
        )
        report = EmployeeReport.objects.create(
            employee=self.employee,
            title="Weekly Work Report",
            week_start_date=date(2026, 9, 1),
            week_end_date=date(2026, 9, 7),
            work_summary="Completed sprint goals",
            tasks_completed="Task A, Task B",
            status="REVIEWED",
            reviewed_by=hr_manager,
            hr_comments="Outstanding work on sprint goals!",
            reviewed_at=timezone.now(),
        )

        self.client.login(username=self.email, password=self.password)
        response = self.client.get(reverse("employees:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weekly Report Reviewed")
        self.assertContains(response, "Outstanding work on sprint goals!")
        self.assertContains(response, "HR Reviewer")

        # Test dismiss endpoint
        dismiss_resp = self.client.post(
            reverse("employees:dismiss_report_popup", args=[report.pk])
        )
        self.assertEqual(dismiss_resp.status_code, 200)
        self.assertEqual(dismiss_resp.json(), {"status": "success"})

        # Subsequent dashboard visit should not trigger popup
        response2 = self.client.get(reverse("employees:dashboard"))
        self.assertEqual(response2.status_code, 200)
        self.assertNotContains(response2, "hrReviewPopupModal")

    def test_notifications_count_reduces_on_read(self):
        from employees.models import Notification

        self.client.login(username=self.email, password=self.password)
        # First visit auto-seeds 3 notifications
        resp = self.client.get(reverse("employees:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["unread_notifications_count"], 3)

        notif = self.employee.notifications.filter(is_read=False).first()
        read_resp = self.client.get(
            reverse("employees:mark_notification_read", args=[notif.notification_id]),
            follow=True,
        )
        self.assertEqual(read_resp.status_code, 200)
        self.assertEqual(read_resp.context["unread_notifications_count"], 2)

        # Dashboard also reflects updated unread count (2)
        dash_resp = self.client.get(reverse("employees:dashboard"))
        self.assertEqual(dash_resp.context["unread_notifications_count"], 2)

        # Mark all as read
        mark_all_resp = self.client.get(
            reverse("employees:mark_all_notifications_read"), follow=True
        )
        self.assertEqual(mark_all_resp.status_code, 200)
        self.assertEqual(mark_all_resp.context["unread_notifications_count"], 0)

        # Dashboard has 0 unread notifications
        dash_resp2 = self.client.get(reverse("employees:dashboard"))
        self.assertEqual(dash_resp2.context["unread_notifications_count"], 0)

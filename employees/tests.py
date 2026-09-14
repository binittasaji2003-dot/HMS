from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

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

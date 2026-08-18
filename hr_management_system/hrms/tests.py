from django.contrib.auth import get_user_model
from django.test import TestCase

from hr_management_system.hrms.forms import EmployeeCreateForm, HRManagerCreateForm
from hr_management_system.hrms.models import Department, Employee, HRManager

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

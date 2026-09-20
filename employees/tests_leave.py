import datetime
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from admin_module.models import Department
from employees.models import Employee, LeaveBalance, LeaveRequest, LeaveType, Notification, Team
from employees.views import ensure_default_leave_types

User = get_user_model()


class LeaveManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        ensure_default_leave_types()

        self.dept = Department.objects.create(
            name="Engineering",
            description="Engineering Dept",
            is_active=True,
        )

        # 1. Create Team Lead User & Employee Profile
        self.tl_user = User.objects.create_user(
            email="teamlead@company.com",
            password="password123",
            name="Lead Officer",
            role="Employee",
            is_active=True,
        )
        self.tl_emp = Employee.objects.create(
            user=self.tl_user,
            employee_code="TL001",
            department=self.dept,
            designation="Tech Lead",
            joining_date=datetime.date(2024, 1, 1),
            employment_status="ACTIVE",
        )

        # 2. Create Subordinate Employee User & Profile assigned to Team Lead
        self.sub_user = User.objects.create_user(
            email="subordinate@company.com",
            password="password123",
            name="Jane Doe",
            role="Employee",
            is_active=True,
        )
        self.sub_emp = Employee.objects.create(
            user=self.sub_user,
            employee_code="EMP002",
            department=self.dept,
            designation="Software Engineer",
            team_lead=self.tl_user,
            joining_date=datetime.date(2025, 1, 1),
            employment_status="ACTIVE",
        )

        # 3. Create Unrelated Employee User & Profile
        self.other_user = User.objects.create_user(
            email="other@company.com",
            password="password123",
            name="Other Person",
            role="Employee",
            is_active=True,
        )
        self.other_emp = Employee.objects.create(
            user=self.other_user,
            employee_code="EMP003",
            department=self.dept,
            designation="Analyst",
            joining_date=datetime.date(2025, 1, 1),
            employment_status="ACTIVE",
        )

        self.casual_type = LeaveType.objects.get(code="GENERAL")
        self.sick_type = LeaveType.objects.get(code="SICK")
        self.year = 2026

    def login_as(self, user):
        self.client.post(
            reverse("employees:login"),
            {"email": user.email, "password": "password123"},
            follow=True,
        )

    def test_01_leave_balance_initialization(self):
        """Test fresh balance has 15 total days, 0 taken, 0 pending, 15 remaining."""
        balance = self.sub_emp.get_or_create_leave_balance(self.year)
        self.assertEqual(balance.total_entitlement, 15)
        self.assertEqual(balance.taken_days, 0)
        self.assertEqual(balance.pending_days, 0)
        self.assertEqual(balance.remaining_days, 15)

    def test_02_apply_leave_success_and_pending_balance(self):
        """Test applying for 3 days leave creates PENDING request without deducting remaining balance."""
        self.login_as(self.sub_user)
        response = self.client.post(reverse("employees:leave_management"), {
            "leave_type": self.casual_type.id,
            "start_date": "2026-09-23",
            "end_date": "2026-09-25",
            "reason": "Personal family event",
            "declaration_accepted": "on",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        # Verify leave request created
        leave_req = LeaveRequest.objects.filter(employee=self.sub_emp).first()
        self.assertIsNotNone(leave_req)
        self.assertEqual(leave_req.number_of_days, 3)
        self.assertEqual(leave_req.status, "PENDING")
        self.assertEqual(leave_req.approver, self.tl_user)

        # Check balance calculations
        balance = self.sub_emp.get_or_create_leave_balance(2026)
        self.assertEqual(balance.total_entitlement, 15)
        self.assertEqual(balance.taken_days, 0) # Not deducted yet!
        self.assertEqual(balance.pending_days, 3)
        self.assertEqual(balance.remaining_days, 15)

        # Check notifications
        emp_notif = Notification.objects.filter(employee=self.sub_emp, notification_type="LEAVE_REQUEST").exists()
        tl_notif = Notification.objects.filter(employee=self.tl_emp, notification_type="LEAVE_REQUEST").exists()
        self.assertTrue(emp_notif)
        self.assertTrue(tl_notif)

    def test_03_team_lead_approval_deducts_balance(self):
        """Test Team Lead approving a request deducts the balance to 12 days remaining."""
        # Create pending request for 3 days
        leave_req = LeaveRequest.objects.create(
            employee=self.sub_emp,
            leave_type=self.casual_type,
            start_date=datetime.date(2026, 9, 23),
            end_date=datetime.date(2026, 9, 25),
            number_of_days=3,
            reason="Personal event",
            declaration_accepted=True,
            status="PENDING",
            approver=self.tl_user,
        )

        self.login_as(self.tl_user)
        response = self.client.post(reverse("employees:team_lead_leave_approve", args=[leave_req.id]), follow=True)
        self.assertEqual(response.status_code, 200)

        leave_req.refresh_from_db()
        self.assertEqual(leave_req.status, "APPROVED")
        self.assertEqual(leave_req.approved_by, self.tl_user)
        self.assertIsNotNone(leave_req.approved_at)

        # Balance check: 15 total, 3 taken, 12 remaining
        balance = self.sub_emp.get_or_create_leave_balance(2026)
        self.assertEqual(balance.taken_days, 3)
        self.assertEqual(balance.pending_days, 0)
        self.assertEqual(balance.remaining_days, 12)

        # Notification to subordinate
        approved_notif = Notification.objects.filter(employee=self.sub_emp, notification_type="LEAVE_APPROVED").exists()
        self.assertTrue(approved_notif)

    def test_04_over_balance_request_rejected(self):
        """Test requesting more than remaining balance fails."""
        # First approve a 14-day leave
        LeaveRequest.objects.create(
            employee=self.sub_emp,
            leave_type=self.casual_type,
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 14),
            number_of_days=14,
            reason="Long vacation",
            declaration_accepted=True,
            status="APPROVED",
            approver=self.tl_user,
            approved_by=self.tl_user,
            approved_at=timezone.now(),
        )

        balance = self.sub_emp.get_or_create_leave_balance(2026)
        self.assertEqual(balance.remaining_days, 1)

        # Now try to request 2 days
        self.login_as(self.sub_user)
        response = self.client.post(reverse("employees:leave_management"), {
            "leave_type": self.sick_type.id,
            "start_date": "2026-05-10",
            "end_date": "2026-05-11",
            "reason": "Illness",
            "declaration_accepted": "on",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        # Should not create new request
        self.assertEqual(LeaveRequest.objects.filter(employee=self.sub_emp, status="PENDING").count(), 0)

    def test_05_overlapping_leave_validation(self):
        """Test cannot create overlapping leave requests."""
        LeaveRequest.objects.create(
            employee=self.sub_emp,
            leave_type=self.casual_type,
            start_date=datetime.date(2026, 6, 10),
            end_date=datetime.date(2026, 6, 15),
            number_of_days=6,
            reason="Trip",
            declaration_accepted=True,
            status="APPROVED",
            approver=self.tl_user,
        )

        self.login_as(self.sub_user)
        # Attempt overlapping request (June 12 - June 14)
        response = self.client.post(reverse("employees:leave_management"), {
            "leave_type": self.sick_type.id,
            "start_date": "2026-06-12",
            "end_date": "2026-06-14",
            "reason": "Doctor visit",
            "declaration_accepted": "on",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LeaveRequest.objects.filter(employee=self.sub_emp, status="PENDING").count(), 0)

    def test_06_team_lead_rejection_requires_reason_and_no_deduction(self):
        """Test Team Lead rejecting a request requires a reason and does not deduct balance."""
        leave_req = LeaveRequest.objects.create(
            employee=self.sub_emp,
            leave_type=self.casual_type,
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 3),
            number_of_days=3,
            reason="Trip",
            declaration_accepted=True,
            status="PENDING",
            approver=self.tl_user,
        )

        self.login_as(self.tl_user)
        # Reject with reason
        response = self.client.post(reverse("employees:team_lead_leave_reject", args=[leave_req.id]), {
            "rejection_reason": "High project workload during sprint release.",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        leave_req.refresh_from_db()
        self.assertEqual(leave_req.status, "REJECTED")
        self.assertEqual(leave_req.rejection_reason, "High project workload during sprint release.")
        self.assertEqual(leave_req.rejected_by, self.tl_user)

        # Balance remains 15
        balance = self.sub_emp.get_or_create_leave_balance(2026)
        self.assertEqual(balance.taken_days, 0)
        self.assertEqual(balance.remaining_days, 15)

    def test_07_self_approval_strictly_prohibited(self):
        """Test Team Lead cannot approve their own leave request."""
        tl_req = LeaveRequest.objects.create(
            employee=self.tl_emp,
            leave_type=self.casual_type,
            start_date=datetime.date(2026, 7, 1),
            end_date=datetime.date(2026, 7, 2),
            number_of_days=2,
            reason="TL Vacation",
            declaration_accepted=True,
            status="PENDING",
        )

        self.login_as(self.tl_user)
        response = self.client.post(reverse("employees:team_lead_leave_approve", args=[tl_req.id]), follow=True)
        self.assertEqual(response.status_code, 200)

        tl_req.refresh_from_db()
        self.assertEqual(tl_req.status, "PENDING") # Must remain PENDING!

    def test_08_team_lead_scoping(self):
        """Test Team Lead can only see and review requests for their assigned subordinates."""
        unrelated_req = LeaveRequest.objects.create(
            employee=self.other_emp,
            leave_type=self.casual_type,
            start_date=datetime.date(2026, 9, 1),
            end_date=datetime.date(2026, 9, 2),
            number_of_days=2,
            reason="Other person leave",
            declaration_accepted=True,
            status="PENDING",
        )

        self.login_as(self.tl_user)
        # Attempt to approve unrelated employee request
        response = self.client.post(reverse("employees:team_lead_leave_approve", args=[unrelated_req.id]), follow=True)
        self.assertEqual(response.status_code, 200)

        unrelated_req.refresh_from_db()
        self.assertEqual(unrelated_req.status, "PENDING") # Denied permission!

    def test_09_employee_cancels_approved_request_restores_balance(self):
        """Test employee cancelling an approved request restores the leave balance."""
        leave_req = LeaveRequest.objects.create(
            employee=self.sub_emp,
            leave_type=self.casual_type,
            start_date=datetime.date(2026, 10, 1),
            end_date=datetime.date(2026, 10, 5),
            number_of_days=5,
            reason="Holiday",
            declaration_accepted=True,
            status="APPROVED",
            approver=self.tl_user,
            approved_by=self.tl_user,
            approved_at=timezone.now(),
        )

        balance = self.sub_emp.get_or_create_leave_balance(2026)
        self.assertEqual(balance.taken_days, 5)
        self.assertEqual(balance.remaining_days, 10)

        # Cancel request
        self.login_as(self.sub_user)
        response = self.client.post(reverse("employees:leave_cancel", args=[leave_req.id]), follow=True)
        self.assertEqual(response.status_code, 200)

        leave_req.refresh_from_db()
        self.assertEqual(leave_req.status, "CANCELLED")

        # Balance restored to 15!
        balance = self.sub_emp.get_or_create_leave_balance(2026)
        self.assertEqual(balance.taken_days, 0)
        self.assertEqual(balance.remaining_days, 15)


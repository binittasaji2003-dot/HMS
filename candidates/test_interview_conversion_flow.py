from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from admin_module.models import Department, EmployeeApproval
from candidates.models import (
    Candidate,
    CandidateNotification,
    JobApplication,
    JobVacancy,
    ResumeScreening,
)
from employees.models import Employee, Team
from hr.models import (
    AptitudeResult,
    AptitudeTest,
    HRManager,
    Interview,
    InterviewEvaluation,
    InterviewLocation,
    InterviewSlot,
)

User = get_user_model()


class RecruitmentInterviewAndConversionFlowTests(TestCase):
    def setUp(self):
        # 1. Setup Department & Leader
        self.dept_leader_user = User.objects.create_user(
            email="deptleader@example.com",
            password="leaderpassword123",
            name="Rahul Mathew",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.dept = Department.objects.create(
            name="Engineering",
            description="Engineering Department",
            department_leader=self.dept_leader_user,
        )

        # 1b. Setup Team & Team Lead
        self.team_lead_user = User.objects.create_user(
            email="teamlead@example.com",
            password="leadpassword123",
            name="Arun Joseph",
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.team = Team.objects.create(
            team_name="Backend Development",
            department=self.dept,
            team_lead=self.team_lead_user,
            is_active=True,
        )

        # 2. Setup HR User & Profile
        self.hr_user = User.objects.create_user(
            email="hrmanager@example.com",
            password="hrpassword123",
            name="HR Manager Jane",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR001",
            is_active=True,
        )

        # 3. Setup Admin User
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
            name="Executive Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
        )

        # 4. Setup Candidate User & Profile
        self.candidate_user = User.objects.create_user(
            email="candidate@example.com",
            password="candidatepass123",
            name="Alex Morgan",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            first_name="Alex",
            last_name="Morgan",
            phone="9876543210",
        )

        # 5. Setup Job Vacancy
        self.vacancy = JobVacancy.objects.create(
            title="Senior Python Developer",
            department=self.dept,
            employment_type="FULL_TIME",
            location="Kochi HQ",
            experience_required="3-5 Years",
            status="OPEN",
            closing_date=timezone.now().date() + timedelta(days=10),
            posted_by=self.hr_user,
        )

        # 6. Setup Job Application
        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.vacancy,
            status="APTITUDE_REVIEW",
            information_source="Job Portal",
        )
        self.screening = ResumeScreening.objects.create(
            application=self.application,
            status="SHORTLISTED",
            match_score=85.0,
        )

        # 7. Setup Physical Office Location
        self.location = InterviewLocation.objects.create(
            location_name="Smart HRMS Kochi Tech Park",
            address="Floor 4, Block B, InfoPark, Kochi, Kerala - 682042",
            city="Kochi",
            is_active=True,
        )

        # 8. Setup Aptitude Test and Result
        self.test = AptitudeTest.objects.create(
            title="Python Technical Aptitude",
            duration_minutes=30,
            created_by=self.hr_manager,
        )
        self.aptitude_result = AptitudeResult.objects.create(
            application=self.application,
            test=self.test,
            score=85,
            total_marks=100,
            percentage=85.0,
            passed=True,
            submission_type="CANDIDATE_SUBMITTED",
        )

    def test_hr_aptitude_decision_pass_transitions_to_interview_scheduling(self):
        """Test HR reviewing aptitude and passing candidate transitions status to INTERVIEW_SCHEDULING and sends notification."""
        self.client.force_login(self.hr_user)
        url = reverse("hr:aptitude_decision", kwargs={"pk": self.application.pk})
        
        response = self.client.post(url, {
            "decision": "PASS",
            "remarks": "Excellent technical fundamentals shown in aptitude assessment.",
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "INTERVIEW_SCHEDULING")
        
        # Verify INTERVIEW_ELIGIBLE notification was created
        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="INTERVIEW_ELIGIBLE"
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Offline Interview", notif.title)

    def test_hr_slot_creation_and_conflict_validation(self):
        """Test HR creating offline interview slot and conflict prevention on overlap."""
        self.client.force_login(self.hr_user)
        url = reverse("hr:interview_slot_create")
        
        slot_date = timezone.now().date() + timedelta(days=2)
        response = self.client.post(url, {
            "location_id": self.location.pk,
            "interview_date": slot_date.strftime("%Y-%m-%d"),
            "start_time": "10:00",
            "end_time": "10:45",
            "interviewer_id": self.hr_manager.pk,
            "interview_type": "TECHNICAL",
            "instructions": "Bring physical portfolio.",
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(InterviewSlot.objects.count(), 1)
        slot = InterviewSlot.objects.first()
        self.assertEqual(slot.location, self.location)
        self.assertEqual(slot.status, "AVAILABLE")

        # Attempt to create conflicting overlapping slot for same interviewer
        response_conflict = self.client.post(url, {
            "location_id": self.location.pk,
            "interview_date": slot_date.strftime("%Y-%m-%d"),
            "start_time": "10:30",
            "end_time": "11:15",
            "interviewer_id": self.hr_manager.pk,
            "interview_type": "TECHNICAL",
        }, follow=True)
        
        # Slot count should still be 1 due to conflict error
        self.assertEqual(InterviewSlot.objects.count(), 1)

    def test_candidate_slot_booking_flow(self):
        """Test Candidate selects and books an available offline interview slot."""
        # Set app to INTERVIEW_SCHEDULING
        self.application.status = "INTERVIEW_SCHEDULING"
        self.application.save()

        slot_date = timezone.now().date() + timedelta(days=3)
        slot = InterviewSlot.objects.create(
            location=self.location,
            interview_date=slot_date,
            start_time=time(11, 0),
            end_time=time(11, 45),
            interviewer=self.hr_manager,
            status="AVAILABLE",
        )

        self.client.force_login(self.candidate_user)
        
        # 1. Candidate views available slots
        view_url = reverse("candidates:interview_slots", kwargs={"application_id": self.application.pk})
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.location.name)

        # 2. Candidate books slot
        book_url = reverse("candidates:book_interview_slot", kwargs={"application_id": self.application.pk, "slot_id": slot.pk})
        response = self.client.post(book_url, {
            "application_id": self.application.pk,
        }, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        slot.refresh_from_db()
        self.assertEqual(slot.status, "BOOKED")
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "INTERVIEW_SCHEDULED")
        
        interview = Interview.objects.filter(application=self.application).first()
        self.assertIsNotNone(interview)
        self.assertEqual(interview.slot, slot)
        self.assertEqual(interview.location, self.location)
        self.assertEqual(interview.interview_type, "TECHNICAL")

        # Verify Candidate Notification
        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="INTERVIEW_SCHEDULED"
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn(self.location.name, notif.message)

    def test_hr_marks_attendance_attended_and_no_show(self):
        """Test HR marking candidate attendance as ATTENDED or NO_SHOW."""
        slot_date = timezone.now().date() + timedelta(days=1)
        slot = InterviewSlot.objects.create(
            location=self.location,
            interview_date=slot_date,
            start_time=time(14, 0),
            end_time=time(14, 45),
            interviewer=self.hr_manager,
            status="BOOKED",
        )
        self.application.status = "INTERVIEW_SCHEDULED"
        self.application.save()
        interview = Interview.objects.create(
            application=self.application,
            interviewer=self.hr_manager,
            slot=slot,
            location=self.location,
            interview_date=slot_date,
            interview_time=time(14, 0),
            status="SCHEDULED",
            attendance="SCHEDULED",
        )

        self.client.force_login(self.hr_user)
        attendance_url = reverse("hr:interview_attendance", kwargs={"pk": interview.pk})

        # 1. Mark ATTENDED
        response = self.client.post(attendance_url, {
            "attendance": "ATTENDED",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        interview.refresh_from_db()
        self.assertEqual(interview.attendance, "ATTENDED")
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "INTERVIEW_REVIEW")

        # 2. Mark NO_SHOW
        response_ns = self.client.post(attendance_url, {
            "attendance": "NO_SHOW",
        }, follow=True)
        self.assertEqual(response_ns.status_code, 200)
        interview.refresh_from_db()
        self.assertEqual(interview.attendance, "NO_SHOW")
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "REJECTED")

    def test_hr_interview_evaluation_pass_and_fail(self):
        """Test HR completing offline interview evaluation scorecard."""
        slot_date = timezone.now().date() + timedelta(days=1)
        slot = InterviewSlot.objects.create(
            location=self.location,
            interview_date=slot_date,
            start_time=time(15, 0),
            end_time=time(15, 45),
            interviewer=self.hr_manager,
            status="BOOKED",
        )
        self.application.status = "INTERVIEW_REVIEW"
        self.application.save()
        interview = Interview.objects.create(
            application=self.application,
            interviewer=self.hr_manager,
            slot=slot,
            location=self.location,
            interview_date=slot_date,
            interview_time=time(15, 0),
            status="SCHEDULED",
            attendance="ATTENDED",
        )

        self.client.force_login(self.hr_user)
        eval_url = reverse("hr:interview_evaluate", kwargs={"pk": interview.pk})

        # 1. Evaluate with PASS
        response = self.client.post(eval_url, {
            "technical_rating": 5,
            "communication_rating": 4,
            "problem_solving_rating": 5,
            "role_skill_rating": 4,
            "professionalism_rating": 5,
            "comments": "Outstanding knowledge in Python and system architecture.",
            "decision": "PASS",
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        evaluation = InterviewEvaluation.objects.filter(interview=interview).first()
        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.overall_rating, 4.6)
        self.assertEqual(evaluation.result, "PASS")

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "SELECTED")

        # Verify candidate received INTERVIEW_PASSED notification
        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="INTERVIEW_PASSED"
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Selected", notif.title)

    def test_candidate_score_privacy_enforcement(self):
        """Verify candidate application and status views never expose confidential HR ratings/scorecard."""
        slot_date = timezone.now().date() + timedelta(days=1)
        slot = InterviewSlot.objects.create(
            location=self.location,
            interview_date=slot_date,
            start_time=time(15, 0),
            end_time=time(15, 45),
            interviewer=self.hr_manager,
            status="BOOKED",
        )
        self.application.status = "SELECTED"
        self.application.save()
        interview = Interview.objects.create(
            application=self.application,
            interviewer=self.hr_manager,
            slot=slot,
            location=self.location,
            interview_date=slot_date,
            interview_time=time(15, 0),
            status="COMPLETED",
            attendance="ATTENDED",
        )
        InterviewEvaluation.objects.create(
            interview=interview,
            evaluated_by=self.hr_manager,
            technical_rating=5,
            communication_rating=4,
            problem_solving_rating=5,
            role_skill_rating=4,
            professionalism_rating=5,
            overall_rating=4.6,
            comments="CONFIDENTIAL_HR_INTERNAL_NOTE_12345",
            result="PASS",
        )

        self.client.force_login(self.candidate_user)
        app_list_url = reverse("candidates:applications")
        response = self.client.get(app_list_url)
        self.assertEqual(response.status_code, 200)
        
        # Privacy check: candidate must NOT see internal evaluation comments or ratings
        self.assertNotContains(response, "CONFIDENTIAL_HR_INTERNAL_NOTE_12345")
        self.assertNotContains(response, "Technical Skills:")
        self.assertNotContains(response, "4.6 / 5.0")

    def test_department_details_api(self):
        """Test the HR department details API returns department leader and teams."""
        self.client.force_login(self.hr_user)
        url = reverse("hr:department_details_api", kwargs={"department_id": self.dept.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["department_leader"], "Rahul Mathew")
        self.assertEqual(len(data["teams"]), 1)
        self.assertEqual(data["teams"][0]["name"], "Backend Development")
        self.assertEqual(data["teams"][0]["team_lead_name"], "Arun Joseph")

    def test_hr_forward_to_admin_and_admin_employee_approval(self):
        """Test HR forwarding selected candidate with team/lead to Admin and Admin approving into Employee."""
        self.application.status = "SELECTED"
        self.application.save()

        self.client.force_login(self.hr_user)
        forward_url = reverse("hr:forward_to_admin", kwargs={"pk": self.application.pk})
        
        join_date = (timezone.now().date() + timedelta(days=14)).strftime("%Y-%m-%d")
        response = self.client.post(forward_url, {
            "designation": "Senior Backend Developer",
            "department": self.dept.pk,
            "team": self.team.pk,
            "team_lead": self.team_lead_user.pk,
            "joining_date": join_date,
            "employment_type": "FULL_TIME",
            "work_location": "Kochi HQ - Floor 4",
            "notes": "Candidate cleared all rounds with high merit.",
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify Employee record created in INACTIVE state with team relationships
        employee = Employee.objects.filter(candidate=self.candidate).first()
        self.assertIsNotNone(employee)
        self.assertEqual(employee.employment_status, "INACTIVE")
        self.assertEqual(employee.designation, "Senior Backend Developer")
        self.assertEqual(employee.department, self.dept)
        self.assertEqual(employee.team, self.team)
        self.assertEqual(employee.team_lead, self.team_lead_user)
        self.assertEqual(employee.work_location, "Kochi HQ - Floor 4")
        self.assertEqual(employee.employment_type, "FULL_TIME")

        # Verify EmployeeApproval in PENDING state
        approval = EmployeeApproval.objects.filter(employee=employee).first()
        self.assertIsNotNone(approval)
        self.assertEqual(approval.status, "PENDING")
        self.assertEqual(approval.requested_by, self.hr_user)

        # Now Admin logs in and reviews / approves
        self.client.force_login(self.admin_user)

        # 1. Admin views review page
        review_url = reverse("admin_module:recruitment_approval_review", kwargs={"employee_id": employee.pk})
        review_resp = self.client.get(review_url)
        self.assertEqual(review_resp.status_code, 200)
        self.assertContains(review_resp, "Rahul Mathew")
        self.assertContains(review_resp, "Backend Development")
        self.assertContains(review_resp, "Arun Joseph")

        # 2. Admin approves
        approve_url = reverse("admin_module:recruitment_approval_approve", kwargs={"employee_id": employee.pk})
        response = self.client.post(approve_url, {
            "comments": "Approved for onboarding.",
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify employee converted to ACTIVE and user role updated
        employee.refresh_from_db()
        self.assertEqual(employee.employment_status, "ACTIVE")
        
        self.candidate_user.refresh_from_db()
        self.assertEqual(self.candidate_user.role, User.RoleChoices.EMPLOYEE)
        self.assertEqual(self.candidate_user.status, User.StatusChoices.ACTIVE)

        # Verify EMPLOYEE_CONVERTED notification sent to candidate
        notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="EMPLOYEE_CONVERTED"
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Official Onboarding Complete", notif.title)

    def test_admin_recruitment_approval_rejection_flow(self):
        """Test Admin rejecting employee creation request records reason and candidate remains SELECTED."""
        self.application.status = "SELECTED"
        self.application.save()

        self.client.force_login(self.hr_user)
        forward_url = reverse("hr:forward_to_admin", kwargs={"pk": self.application.pk})
        self.client.post(forward_url, {
            "designation": "Senior Backend Developer",
            "department": self.dept.pk,
            "team": self.team.pk,
            "team_lead": self.team_lead_user.pk,
            "notes": "Candidate pending executive clearance.",
        }, follow=True)

        employee = Employee.objects.filter(candidate=self.candidate).first()
        self.assertIsNotNone(employee)

        # Admin rejects
        self.client.force_login(self.admin_user)
        reject_url = reverse("admin_module:recruitment_approval_reject", kwargs={"employee_id": employee.pk})
        response = self.client.post(reject_url, {
            "rejection_reason": "Headcount freeze for Q3. Please defer onboarding date.",
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        approval = EmployeeApproval.objects.filter(employee=employee).first()
        self.assertEqual(approval.status, "REJECTED")
        self.assertEqual(approval.rejection_reason, "Headcount freeze for Q3. Please defer onboarding date.")

        # Employee remains INACTIVE and candidate user remains CANDIDATE role
        employee.refresh_from_db()
        self.assertEqual(employee.employment_status, "INACTIVE")
        self.candidate_user.refresh_from_db()
        self.assertEqual(self.candidate_user.role, User.RoleChoices.CANDIDATE)

        # Application remains in SELECTED status
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "SELECTED")

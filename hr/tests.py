from datetime import date, time
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from admin_module.models import AdminNotification, Department
from candidates.models import Candidate, JobApplication, JobVacancy
from employees.models import Employee, EmployeeDocument
from admin_module.models import AdminNotification, Department, EmployeeApproval
from candidates.models import Candidate, CandidateNotification, JobApplication, JobVacancy
from employees.models import Employee, EmployeeDocument, Notification, Team
from hr.models import (
    AptitudeResult,
    AptitudeTest,
    HRDocument,
    HREducation,
    HRExperience,
    HRManager,
    HRNotification,
    HRPerformanceReview,
    HRWeeklyReport,
    Interview,
)

User = get_user_model()


class HRModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Human Resources", is_active=True)
        self.engineering = Department.objects.create(name="Engineering", is_active=True)
        self.hr_user = User.objects.create_user(
            email="hr.manager@company.com",
            password="HRPassword123!",
            name="Alice Walker",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            first_name="Alice",
            last_name="Walker",
            phone="+1-555-123-4567",
            date_of_birth=date(1990, 5, 20),
            gender="FEMALE",
            address="123 Corporate Way, Cityville",
            city="Cityville",
            state="Kerala",
            pincode="682001",
            department=self.dept,
            employee_code="HRM-001",
            designation="HR Manager",
            joining_date=date(2024, 1, 1),
            is_active=True,
        )

        self.admin_user = User.objects.create_user(
            email="admin@company.com",
            password="AdminPassword123!",
            name="Super Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        # Linked education & experience
        self.edu = HREducation.objects.create(
            hr=self.hr_manager,
            degree="MBA Human Resources",
            institution="IIM Bangalore",
            university_board="Autonomous",
            year_of_passing=2018,
            grade_percentage="8.5 CGPA",
        )
        self.exp = HRExperience.objects.create(
            hr=self.hr_manager,
            company_name="TechCorp India",
            designation="HR Associate",
            start_date=date(2019, 1, 1),
            end_date=date(2023, 12, 31),
            responsibilities="Managed end-to-end tech hiring and onboarding.",
        )
        self.doc = HRDocument.objects.create(
            hr=self.hr_manager,
            document_type="ID_PROOF",
            title="Passport Document",
            document_file=SimpleUploadedFile("id_proof.pdf", b"pdf content", content_type="application/pdf"),
        )
        self.hr_manager.update_profile_completion_status()

    def test_hr_dashboard_view(self):
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        response = self.client.get(reverse("hr:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Walker")

    def test_hr_profile_view_displays_all_sections(self):
        """HR Profile view displays Account, Personal, Professional, Education, Experience, and Document info."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        response = self.client.get(reverse("hr:profile"))

        self.assertEqual(response.status_code, 200)

        # 1. Personal Info
        self.assertContains(response, "Alice Walker")
        self.assertContains(response, "+1-555-123-4567")
        self.assertContains(response, "123 Corporate Way, Cityville")
        self.assertContains(response, "May 20, 1990")

        # 2. Professional Info
        self.assertContains(response, "HRM-001")
        self.assertContains(response, "Human Resources")

        # 3. Education
        self.assertContains(response, "MBA Human Resources")
        self.assertContains(response, "IIM Bangalore")
        self.assertContains(response, "2018")

        # 4. Experience
        self.assertContains(response, "TechCorp India")
        self.assertContains(response, "HR Associate")

        # 5. Documents
        self.assertContains(response, "ID Proof")

        # 6. Account Info
        self.assertContains(response, "hr.manager@company.com")

        # Security check: Password hash must NEVER be present
        self.assertNotContains(response, self.hr_user.password)

    def test_hr_profile_completion_calculation(self):
        """Test profile completion percentage and boolean flag calculation."""
        self.assertTrue(self.hr_manager.profile_completed)
        self.assertEqual(self.hr_manager.completion_percentage, 100)

        # Incomplete HR profile
        user2 = User.objects.create_user(
            email="incomplete.hr@company.com",
            password="HRPassword123!",
            name="New HR",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        hr2 = HRManager.objects.create(
            user=user2,
            employee_code="HRM-002",
        )
        self.assertFalse(hr2.update_profile_completion_status())
        self.assertLess(hr2.completion_percentage, 100)

        # Verify dashboard banner appears for incomplete profile
        self.client.login(username=user2.email, password="HRPassword123!")
        dash_response = self.client.get(reverse("hr:dashboard"))
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, "Please complete your profile")

    def test_hr_profile_edit_view_get_and_post(self):
        """Edit profile form renders with data and updates HRManager."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        get_res = self.client.get(reverse("hr:profile_edit"))
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "Alice")
        self.assertContains(get_res, "Walker")

        post_data = {
            "first_name": "Alicia",
            "middle_name": "Marie",
            "last_name": "Walker",
            "email": "alicia.walker@company.com",
            "phone": "+1-555-999-8888",
            "date_of_birth": "1990-05-20",
            "gender": "FEMALE",
            "address": "456 Innovation Blvd",
            "city": "Kochi",
            "state": "Kerala",
            "pincode": "682030",
            "has_no_experience": False,
        }
        post_res = self.client.post(reverse("hr:profile_edit"), data=post_data)
        self.assertRedirects(post_res, reverse("hr:profile"))

        self.hr_manager.refresh_from_db()
        self.assertEqual(self.hr_manager.first_name, "Alicia")
        self.assertEqual(self.hr_manager.middle_name, "Marie")
        self.assertEqual(self.hr_manager.city, "Kochi")

        self.hr_user.refresh_from_db()
        self.assertEqual(self.hr_user.email, "alicia.walker@company.com")
        self.assertEqual(self.hr_user.name, "Alicia Marie Walker")

    def test_education_crud_actions(self):
        """HR can add, edit, and delete education records."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        # 1. Add Education
        add_res = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "add_education",
                "degree": "B.Tech Computer Science",
                "institution": "NIT Calicut",
                "university_board": "NIT",
                "year_of_passing": 2016,
                "grade_percentage": "8.8 CGPA",
            },
        )
        self.assertRedirects(add_res, reverse("hr:profile"))
        btech = HREducation.objects.filter(hr=self.hr_manager, degree="B.Tech Computer Science").first()
        self.assertIsNotNone(btech)

        # 2. Edit Education
        edit_res = self.client.post(
            reverse("hr:education_edit", kwargs={"pk": btech.pk}),
            data={
                "degree": "B.Tech CS Honours",
                "institution": "NIT Calicut",
                "university_board": "NIT",
                "year_of_passing": 2016,
                "grade_percentage": "9.0 CGPA",
            },
        )
        self.assertRedirects(edit_res, reverse("hr:profile"))
        btech.refresh_from_db()
        self.assertEqual(btech.degree, "B.Tech CS Honours")

        # 3. Delete Education
        del_res = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "delete_education",
                "education_id": btech.pk,
            },
        )
        self.assertRedirects(del_res, reverse("hr:profile"))
        self.assertFalse(HREducation.objects.filter(pk=btech.pk).exists())

    def test_experience_crud_actions(self):
        """HR can add, edit, and delete work experience records."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        # 1. Add Experience
        add_res = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "add_experience",
                "company_name": "Google",
                "designation": "People Ops Lead",
                "start_date": "2024-01-01",
                "is_current": True,
                "responsibilities": "Talent growth and people operations.",
            },
        )
        self.assertRedirects(add_res, reverse("hr:profile"))
        google_exp = HRExperience.objects.filter(hr=self.hr_manager, company_name="Google").first()
        self.assertIsNotNone(google_exp)
        self.assertTrue(google_exp.is_current)

        # 2. Edit Experience
        edit_res = self.client.post(
            reverse("hr:experience_edit", kwargs={"pk": google_exp.pk}),
            data={
                "company_name": "Google India",
                "designation": "Senior People Ops Lead",
                "start_date": "2024-01-01",
                "is_current": True,
                "responsibilities": "Global talent growth and HR strategy.",
            },
        )
        self.assertRedirects(edit_res, reverse("hr:profile"))
        google_exp.refresh_from_db()
        self.assertEqual(google_exp.company_name, "Google India")

        # 3. Delete Experience
        del_res = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "delete_experience",
                "experience_id": google_exp.pk,
            },
        )
        self.assertRedirects(del_res, reverse("hr:profile"))
        self.assertFalse(HRExperience.objects.filter(pk=google_exp.pk).exists())

    def test_document_upload_and_delete(self):
        """HR can upload and delete HRDocument records."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        file_data = SimpleUploadedFile("cert.pdf", b"Dummy Certificate Data", content_type="application/pdf")
        upload_res = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "upload_document",
                "document_type": "EDUCATIONAL_CERTIFICATE",
                "title": "MBA Certificate",
                "document_file": file_data,
            },
        )
        self.assertRedirects(upload_res, reverse("hr:profile"))
        new_doc = HRDocument.objects.filter(hr=self.hr_manager, title="MBA Certificate").first()
        self.assertIsNotNone(new_doc)

        # Delete
        del_res = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "delete_document",
                "document_id": new_doc.pk,
            },
        )
        self.assertRedirects(del_res, reverse("hr:profile"))
        self.assertFalse(HRDocument.objects.filter(pk=new_doc.pk).exists())

    def test_admin_hr_manager_profile_view(self):
        """Admin can view HR Manager details including education, experience, and documents."""
        self.client.login(username=self.admin_user.email, password="AdminPassword123!")
        url = reverse("admin_module:hr_manager_detail", kwargs={"manager_id": self.hr_manager.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Walker")
        self.assertContains(response, "MBA Human Resources")
        self.assertContains(response, "TechCorp India")
        self.assertContains(response, "Passport Document")
        self.assertContains(response, "Profile Complete")

    def test_unauthenticated_or_non_hr_cannot_access(self):
        """Unauthenticated or non-HR users cannot access HR profile or edit profile."""
        self.client.logout()
        res1 = self.client.get(reverse("hr:profile"))
        self.assertEqual(res1.status_code, 302)

        cand_user = User.objects.create_user(
            email="cand@test.com",
            password="CandPass123!",
            role=User.RoleChoices.CANDIDATE,
        )
        self.client.login(username="cand@test.com", password="CandPass123!")
        res2 = self.client.get(reverse("hr:profile"))
        self.assertEqual(res2.status_code, 302)
        res3 = self.client.get(reverse("hr:profile"))
        self.assertEqual(res3.status_code, 302)


class HRApplicationDetailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Software Engineering", is_active=True)
        self.hr_user = User.objects.create_user(
            email="hr.recruiter@company.com",
            password="HRPassword123!",
            name="HR Recruiter",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HRM-202",
            is_active=True,
        )

        self.vacancy = JobVacancy.objects.create(
            title="Backend Python Engineer",
            department=self.dept,
            description="Build modern APIs and services.",
            responsibilities="Develop robust backend systems.",
            qualifications="B.Tech in Computer Science or equivalent.",
            skills_required="Python, Django, PostgreSQL, Docker",
            experience_required="3+ years",
            location="Remote / Hybrid",
            status="OPEN",
        )

        # Candidate A
        self.user_a = User.objects.create_user(
            email="candidate.a@example.com",
            password="CandPass123!",
            name="John Robert Doe",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.candidate_a = Candidate.objects.create(
            user=self.user_a,
            first_name="John",
            middle_name="Robert",
            last_name="Doe",
            phone="+1-555-111-2222",
            date_of_birth=date(1995, 3, 15),
            address="789 Pine Street, Tech City",
            resume=SimpleUploadedFile("resume_a.pdf", b"Resume A content", content_type="application/pdf"),
            id_proof=SimpleUploadedFile("id_a.pdf", b"ID proof A", content_type="application/pdf"),
            tenth_certificate=SimpleUploadedFile("tenth_cert.pdf", b"10th Cert", content_type="application/pdf"),
            twelfth_certificate=SimpleUploadedFile("twelfth_cert.pdf", b"12th Cert", content_type="application/pdf"),
            policy_agreement=True,
            profile_completed=True,
        )
        self.app_a = JobApplication.objects.create(
            candidate=self.candidate_a,
            vacancy=self.vacancy,
            applied_resume=SimpleUploadedFile("app_resume_a.pdf", b"App Resume A", content_type="application/pdf"),
            status="APPLIED",
        )

        # Candidate B
        self.user_b = User.objects.create_user(
            email="candidate.b@example.com",
            password="CandPass123!",
            name="Sarah Smith",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.candidate_b = Candidate.objects.create(
            user=self.user_b,
            first_name="Sarah",
            last_name="Smith",
            phone="+1-555-333-4444",
            date_of_birth=date(1998, 8, 25),
            address="321 Oak Avenue, Metroville",
            policy_agreement=True,
            profile_completed=True,
        )
        self.app_b = JobApplication.objects.create(
            candidate=self.candidate_b,
            vacancy=self.vacancy,
            status="APPLIED",
        )

        # Evaluation for App A
        self.test_obj = AptitudeTest.objects.create(
            title="Python Assessment",
            duration_minutes=30,
            status="ACTIVE",
        )
        self.apt_result = AptitudeResult.objects.create(
            test=self.test_obj,
            application=self.app_a,
            score=85,
            total_marks=100,
        )
        self.interview = Interview.objects.create(
            application=self.app_a,
            interviewer=self.hr_manager,
            interview_date=date(2026, 10, 5),
            interview_time=time(14, 30),
            status="SCHEDULED",
            remarks="Strong coding background in Django.",
        )

    def test_application_detail_view_displays_complete_candidate_data(self):
        """Application detail page displays all candidate personal, account, education, and evaluation data."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        url = reverse("hr:application_detail", kwargs={"pk": self.app_a.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Personal details
        self.assertContains(response, "John Robert Doe")
        self.assertContains(response, "candidate.a@example.com")
        self.assertContains(response, "+1-555-111-2222")
        self.assertContains(response, "789 Pine Street, Tech City")
        self.assertContains(response, "March 15, 1995")

        # Job specs
        self.assertContains(response, "Backend Python Engineer")
        self.assertContains(response, "Software Engineering")
        self.assertContains(response, "Python, Django, PostgreSQL, Docker")

        # Documents
        self.assertContains(response, "Application Resume")
        self.assertContains(response, "10th Standard Certificate")
        self.assertContains(response, "12th Standard Certificate")
        self.assertContains(response, "Government ID Proof")

        # Evaluation history
        self.assertContains(response, "Python Assessment")
        self.assertContains(response, "85 / 100")
        self.assertContains(response, "October 05, 2026 at 14:30")
        self.assertContains(response, "Strong coding background in Django.")

        # Security check: Password hash must never be displayed
        self.assertNotContains(response, self.user_a.password)
        self.assertNotContains(response, self.hr_user.password)

    def test_application_detail_candidate_data_isolation(self):
        """Application A displays only Candidate A data; Application B displays only Candidate B data."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        # View Application A
        url_a = reverse("hr:application_detail", kwargs={"pk": self.app_a.pk})
        res_a = self.client.get(url_a)
        self.assertEqual(res_a.status_code, 200)
        self.assertContains(res_a, "John Robert Doe")
        self.assertContains(res_a, "candidate.a@example.com")
        self.assertNotContains(res_a, "Sarah Smith")
        self.assertNotContains(res_a, "candidate.b@example.com")

        # View Application B
        url_b = reverse("hr:application_detail", kwargs={"pk": self.app_b.pk})
        res_b = self.client.get(url_b)
        self.assertEqual(res_b.status_code, 200)
        self.assertContains(res_b, "Sarah Smith")
        self.assertContains(res_b, "candidate.b@example.com")
        self.assertNotContains(res_b, "John Robert Doe")
        self.assertNotContains(res_b, "candidate.a@example.com")

    def test_application_detail_handles_missing_optional_data_gracefully(self):
        """Minimal candidate applications render gracefully without errors."""
        # Minimal candidate without phone, dob, address, documents
        user_c = User.objects.create_user(
            email="minimal.cand@example.com",
            password="CandPass123!",
            name="Minimal Candidate",
            role=User.RoleChoices.CANDIDATE,
            is_active=True,
        )
        cand_c = Candidate.objects.create(
            user=user_c,
            first_name="Minimal",
            last_name="Candidate",
        )
        app_c = JobApplication.objects.create(
            candidate=cand_c,
            vacancy=self.vacancy,
            status="APPLIED",
        )

        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        url_c = reverse("hr:application_detail", kwargs={"pk": app_c.pk})
        res_c = self.client.get(url_c)

        self.assertEqual(res_c.status_code, 200)
        self.assertContains(res_c, "Minimal Candidate")
        self.assertContains(res_c, "minimal.cand@example.com")
        self.assertContains(res_c, "Not provided")
        self.assertContains(res_c, "Not uploaded")
        self.assertContains(res_c, "No interview sessions scheduled for this candidate yet.")

    def test_application_status_update_workflow(self):
        """HR Manager can transition application through recruitment stages."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        update_url = reverse("hr:application_status_update", kwargs={"pk": self.app_a.pk})

        # Update to SHORTLISTED
        res1 = self.client.post(update_url, data={"status": "SHORTLISTED"})
        self.assertRedirects(res1, reverse("hr:application_detail", kwargs={"pk": self.app_a.pk}))
        self.app_a.refresh_from_db()
        self.assertEqual(self.app_a.status, "SHORTLISTED")

        # Update to SELECTED
        res2 = self.client.post(update_url, data={"status": "SELECTED"})
        self.assertRedirects(res2, reverse("hr:application_detail", kwargs={"pk": self.app_a.pk}))
        self.app_a.refresh_from_db()
        self.assertEqual(self.app_a.status, "SELECTED")

        # Invalid status rejected
        res3 = self.client.post(update_url, data={"status": "INVALID_STAGE"})
        self.assertRedirects(res3, reverse("hr:application_detail", kwargs={"pk": self.app_a.pk}))
        self.app_a.refresh_from_db()
        self.assertEqual(self.app_a.status, "SELECTED")

    def test_application_list_displays_actual_applied_positions(self):
        """Application list displays the exact applied position and department for each candidate."""
        # Create second distinct vacancy
        vacancy_fe = JobVacancy.objects.create(
            title="Frontend React Developer",
            department=self.dept,
            description="Build interactive UIs.",
            location="Remote",
            status="OPEN",
        )
        self.app_b.vacancy = vacancy_fe
        self.app_b.save()

        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        url = reverse("hr:application_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Candidate A with Backend Python Engineer
        self.assertContains(response, "John Robert Doe")
        self.assertContains(response, "Backend Python Engineer")

        # Candidate B with Frontend React Developer
        self.assertContains(response, "Sarah Smith")
        self.assertContains(response, "Frontend React Developer")

    def test_application_list_search_by_position_and_candidate(self):
        """Application list search filters by candidate name and applied position title."""
        vacancy_fe = JobVacancy.objects.create(
            title="Frontend React Developer",
            department=self.dept,
            description="Build interactive UIs.",
            location="Remote",
            status="OPEN",
        )
        self.app_b.vacancy = vacancy_fe
        self.app_b.save()

        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        # Search for "React"
        res1 = self.client.get(reverse("hr:application_list") + "?q=React")
        self.assertEqual(res1.status_code, 200)
        self.assertContains(res1, "Frontend React Developer")
        self.assertContains(res1, "Sarah Smith")
        self.assertNotContains(res1, "Backend Python Engineer")

        # Search for "John"
        res2 = self.client.get(reverse("hr:application_list") + "?q=John")
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, "Backend Python Engineer")
        self.assertContains(res2, "John Robert Doe")
        self.assertNotContains(res2, "Frontend React Developer")


class AptitudeQuestionAndTestSystemTests(TestCase):
    """Comprehensive test suite for 3-category aptitude question management and randomized testing."""

    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Software Engineering", is_active=True)

        # HR User & Profile
        self.hr_user = User.objects.create_user(
            email="hr.lead@example.com",
            password="HRPassword123!",
            name="HR Specialist",
            role=User.RoleChoices.HR,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR777",
        )

        # Candidate User & Profile
        self.cand_user = User.objects.create_user(
            email="candidate.jane@example.com",
            password="CandPass123!",
            name="Jane Applicant",
            role=User.RoleChoices.CANDIDATE,
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user,
            first_name="Jane",
            last_name="Applicant",
            phone="+1-555-999-8888",
        )

        # Other Candidate User
        self.other_user = User.objects.create_user(
            email="other.cand@example.com",
            password="OtherPass123!",
            name="Bob Stranger",
            role=User.RoleChoices.CANDIDATE,
            is_active=True,
        )
        self.other_cand = Candidate.objects.create(
            user=self.other_user,
            first_name="Bob",
            last_name="Stranger",
        )

        # Vacancy & Applications
        self.vacancy = JobVacancy.objects.create(
            title="Full Stack Python Developer",
            department=self.dept,
            description="Build scalable web apps",
            location="Remote",
            status="OPEN",
        )
        self.app = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.vacancy,
            status="APTITUDE",
        )
        self.other_app = JobApplication.objects.create(
            candidate=self.other_cand,
            vacancy=self.vacancy,
            status="APTITUDE",
        )

        # Aptitude Test
        from hr.models import AptitudeAttempt, AptitudeQuestion, AptitudeResult, AptitudeTest
        from hr.question_bank import seed_default_questions

        self.test_obj = AptitudeTest.objects.create(
            title="General IT Aptitude Test",
            duration_minutes=30,
            total_questions=15,
            pass_percentage=50,
            status="ACTIVE",
            created_by=self.hr_manager,
        )

        # Seed questions
        seed_default_questions(test=self.test_obj)

    def test_predefined_questions_exist_in_all_three_categories(self):
        """Question bank contains valid questions across Quantitative, Logical, and Verbal categories."""
        from hr.models import AptitudeQuestion

        quant_qs = AptitudeQuestion.objects.filter(test=self.test_obj, category="QUANTITATIVE")
        logical_qs = AptitudeQuestion.objects.filter(test=self.test_obj, category="LOGICAL")
        verbal_qs = AptitudeQuestion.objects.filter(test=self.test_obj, category="VERBAL")

        self.assertGreaterEqual(quant_qs.count(), 10)
        self.assertGreaterEqual(logical_qs.count(), 10)
        self.assertGreaterEqual(verbal_qs.count(), 10)

        # Verify options and correct answers for sample questions
        for q in quant_qs[:3]:
            self.assertTrue(q.question)
            self.assertTrue(q.option_a)
            self.assertTrue(q.option_b)
            self.assertTrue(q.option_c)
            self.assertTrue(q.option_d)
            self.assertIn(q.correct_answer, ["A", "B", "C", "D"])
            self.assertTrue(q.is_active)

    def test_hr_can_view_and_filter_questions_by_category(self):
        """HR can view question bank and filter questions by category."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        url = reverse("hr:aptitude_questions", kwargs={"test_id": self.test_obj.pk})

        # All questions
        res_all = self.client.get(url)
        self.assertEqual(res_all.status_code, 200)
        self.assertContains(res_all, "General IT Aptitude Test")
        self.assertContains(res_all, "Quantitative")
        self.assertContains(res_all, "Logical")
        self.assertContains(res_all, "Verbal")

        # Filter by Quantitative
        res_quant = self.client.get(url + "?category=QUANTITATIVE")
        self.assertEqual(res_quant.status_code, 200)
        self.assertContains(res_quant, "Quantitative Aptitude")

        # Filter by Logical
        res_logical = self.client.get(url + "?category=LOGICAL")
        self.assertEqual(res_logical.status_code, 200)
        self.assertContains(res_logical, "Logical Reasoning")

        # Filter by Verbal
        res_verbal = self.client.get(url + "?category=VERBAL")
        self.assertEqual(res_verbal.status_code, 200)
        self.assertContains(res_verbal, "Verbal Ability")

    def test_hr_can_add_custom_question(self):
        """HR can add a custom MCQ question with validation."""
        from hr.models import AptitudeQuestion

        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        url = reverse("hr:aptitude_questions", kwargs={"test_id": self.test_obj.pk})

        data = {
            "category": "LOGICAL",
            "question": "What is the next prime number after 17?",
            "option_a": "18",
            "option_b": "19",
            "option_c": "21",
            "option_d": "23",
            "correct_answer": "B",
            "is_active": True,
        }
        res = self.client.post(url, data=data, follow=True)
        self.assertEqual(res.status_code, 200)

        created_q = AptitudeQuestion.objects.filter(
            test=self.test_obj,
            question="What is the next prime number after 17?",
        ).first()
        self.assertIsNotNone(created_q)
        self.assertEqual(created_q.category, "LOGICAL")
        self.assertEqual(created_q.correct_answer, "B")
        self.assertEqual(created_q.correct_option_text, "19")
        self.assertTrue(created_q.is_active)

    def test_invalid_questions_rejected(self):
        """Questions with missing options or invalid correct answer are rejected."""
        from hr.models import AptitudeQuestion

        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        url = reverse("hr:aptitude_questions", kwargs={"test_id": self.test_obj.pk})

        # Missing Option D and invalid correct answer 'Z'
        invalid_data = {
            "category": "QUANTITATIVE",
            "question": "Invalid question sample",
            "option_a": "10",
            "option_b": "20",
            "option_c": "30",
            "option_d": "",
            "correct_answer": "Z",
        }
        initial_count = AptitudeQuestion.objects.filter(test=self.test_obj).count()
        res = self.client.post(url, data=invalid_data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(AptitudeQuestion.objects.filter(test=self.test_obj).count(), initial_count)

    def test_hr_can_edit_question(self):
        """HR can update an existing question."""
        from hr.models import AptitudeQuestion

        q = AptitudeQuestion.objects.filter(test=self.test_obj).first()
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        edit_url = reverse("hr:aptitude_question_edit", kwargs={"question_id": q.pk})

        update_data = {
            "category": "VERBAL",
            "question": "Updated question prompt text?",
            "option_a": "First Option",
            "option_b": "Second Option",
            "option_c": "Third Option",
            "option_d": "Fourth Option",
            "correct_answer": "C",
            "is_active": True,
        }
        res = self.client.post(edit_url, data=update_data, follow=True)
        self.assertEqual(res.status_code, 200)

        q.refresh_from_db()
        self.assertEqual(q.question, "Updated question prompt text?")
        self.assertEqual(q.category, "VERBAL")
        self.assertEqual(q.correct_answer, "C")
        self.assertEqual(q.correct_option_text, "Third Option")

    def test_hr_can_toggle_question_active_status(self):
        """HR can toggle active/inactive state of a question."""
        from hr.models import AptitudeQuestion

        q = AptitudeQuestion.objects.filter(test=self.test_obj, is_active=True).first()
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        toggle_url = reverse("hr:aptitude_question_toggle_status", kwargs={"question_id": q.pk})

        self.client.post(toggle_url, follow=True)
        q.refresh_from_db()
        self.assertFalse(q.is_active)

        self.client.post(toggle_url, follow=True)
        q.refresh_from_db()
        self.assertTrue(q.is_active)

    def test_candidate_attempt_balances_all_three_categories(self):
        """Candidate test attempt includes questions from Quantitative, Logical, and Verbal categories."""
        from hr.models import AptitudeAttempt

        self.client.login(username=self.cand_user.email, password="CandPass123!")
        test_url = reverse("candidates:take_aptitude_test", kwargs={"application_id": self.app.pk})
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)

        attempt = AptitudeAttempt.objects.filter(application=self.app).first()
        self.assertIsNotNone(attempt)
        self.assertEqual(len(attempt.questions_data), 15)

        categories_in_test = {q["category"] for q in attempt.questions_data}
        self.assertIn("QUANTITATIVE", categories_in_test)
        self.assertIn("LOGICAL", categories_in_test)
        self.assertIn("VERBAL", categories_in_test)

    def test_candidate_question_and_option_randomization(self):
        """Two candidate attempts receive randomized questions and options with correct key mapping."""
        from hr.models import AptitudeAttempt, AptitudeQuestion

        # Candidate A starts test
        self.client.login(username=self.cand_user.email, password="CandPass123!")
        self.client.get(reverse("candidates:take_aptitude_test", kwargs={"application_id": self.app.pk}))
        attempt_a = AptitudeAttempt.objects.get(application=self.app)

        # Candidate B starts test
        self.client.logout()
        self.client.login(username=self.other_user.email, password="OtherPass123!")
        self.client.get(reverse("candidates:take_aptitude_test", kwargs={"application_id": self.other_app.pk}))
        attempt_b = AptitudeAttempt.objects.get(application=self.other_app)

        # Verify correct_key accurately maps to the underlying original correct answer
        for q_entry in attempt_a.questions_data:
            q_model = AptitudeQuestion.objects.get(pk=q_entry["question_id"])
            correct_opt = next(o for o in q_entry["options"] if o["key"] == q_entry["correct_key"])
            self.assertEqual(correct_opt["text"], q_model.correct_option_text)

    def test_attempt_stability_on_page_reload(self):
        """Refreshing test page does not reshuffle or change question set."""
        from hr.models import AptitudeAttempt

        self.client.login(username=self.cand_user.email, password="CandPass123!")
        test_url = reverse("candidates:take_aptitude_test", kwargs={"application_id": self.app.pk})

        # First request
        res1 = self.client.get(test_url)
        self.assertEqual(res1.status_code, 200)
        attempt1 = AptitudeAttempt.objects.get(application=self.app)
        q_order_1 = [q["question_id"] for q in attempt1.questions_data]

        # Second request (reload)
        res2 = self.client.get(test_url)
        self.assertEqual(res2.status_code, 200)
        attempt2 = AptitudeAttempt.objects.get(application=self.app)
        q_order_2 = [q["question_id"] for q in attempt2.questions_data]

        self.assertEqual(attempt1.pk, attempt2.pk)
        self.assertEqual(q_order_1, q_order_2)

    def test_candidate_answer_submission_and_scoring(self):
        """Submitted candidate answers are accurately graded against randomized option keys."""
        from hr.models import AptitudeAttempt, AptitudeResult

        self.client.login(username=self.cand_user.email, password="CandPass123!")
        test_url = reverse("candidates:take_aptitude_test", kwargs={"application_id": self.app.pk})
        self.client.get(test_url)

        attempt = AptitudeAttempt.objects.get(application=self.app)

        # Submit 10 correct answers out of 15
        post_data = {}
        for idx, q_entry in enumerate(attempt.questions_data):
            qid = str(q_entry["question_id"])
            if idx < 10:
                # Correct answer
                post_data[f"question_{qid}"] = q_entry["correct_key"]
            else:
                # Wrong answer
                wrong_key = "B" if q_entry["correct_key"] != "B" else "C"
                post_data[f"question_{qid}"] = wrong_key

        submit_url = reverse("candidates:submit_aptitude_test", kwargs={"application_id": self.app.pk})
        res = self.client.post(submit_url, data=post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        attempt.refresh_from_db()
        self.assertTrue(attempt.is_completed)

        result = AptitudeResult.objects.get(application=self.app)
        self.assertEqual(result.score, 10)
        self.assertEqual(result.total_marks, 15)
        self.assertEqual(result.percentage, 66.67)
        self.assertTrue(result.passed)

    def test_candidate_access_control(self):
        """Candidate cannot access or submit another candidate's assessment."""
        self.client.login(username=self.other_user.email, password="OtherPass123!")

        # Try to access Candidate A's test
        url = reverse("candidates:take_aptitude_test", kwargs={"application_id": self.app.pk})
        res = self.client.get(url, follow=True)
        self.assertRedirects(res, reverse("candidates:applications"))
        self.assertContains(res, "not authorized")

    def test_correct_answers_not_exposed_to_candidate_html(self):
        """Candidate test HTML does not leak correct answer keys."""
        self.client.login(username=self.cand_user.email, password="CandPass123!")
        test_url = reverse("candidates:take_aptitude_test", kwargs={"application_id": self.app.pk})
        response = self.client.get(test_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "correct_key")
        self.assertNotContains(response, "correct_answer")


class HRWeeklyPerformanceReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Human Resources", is_active=True)

        self.hr_user = User.objects.create_user(
            email="hr.manager@company.com",
            password="HRPassword123!",
            name="Jaimon Tomy",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            first_name="Jaimon",
            last_name="Tomy",
            employee_code="HR003",
            designation="HR Manager",
            department=self.dept,
            is_active=True,
        )

        self.other_hr_user = User.objects.create_user(
            email="other.hr@company.com",
            password="OtherHRPass123!",
            name="Bob Smith",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.other_hr = HRManager.objects.create(
            user=self.other_hr_user,
            first_name="Bob",
            last_name="Smith",
            employee_code="HR004",
            department=self.dept,
            is_active=True,
        )

        self.admin_user = User.objects.create_user(
            email="admin@company.com",
            password="AdminPassword123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

    def test_performance_matrix_calculation_and_tier_thresholds(self):
        """Test performance matrix mathematical calculation logic across all score tiers."""
        report = HRWeeklyReport.objects.create(
            hr_manager=self.hr_manager,
            week_start_date=date(2026, 9, 14),
            week_end_date=date(2026, 9, 20),
            work_summary="Handled recruitment activities and coordinated aptitude tests.",
            tasks_completed="Screened resumes, coordinated interviews.",
            status="SUBMITTED",
        )

        # 1. Test Good Tier (Example in spec: ratings sum to 31 -> 3.88/5 -> 77.5%)
        review = HRPerformanceReview.objects.create(
            report=report,
            reviewed_by=self.admin_user,
            task_completion=4,
            quality_of_work=4,
            recruitment_coordination=5,
            timeliness=3,
            documentation=4,
            communication=4,
            problem_solving=3,
            weekly_goal_achievement=4,
            overall_feedback="Good progress this week. Recruitment coordination was handled effectively.",
        )
        self.assertEqual(review.total_score, 31)
        self.assertEqual(float(review.average_score), 3.88)
        self.assertEqual(float(review.performance_percentage), 77.50)
        self.assertEqual(review.performance_status, "GOOD")

        # 2. Test Excellent Tier (>= 85%)
        review.task_completion = 5
        review.quality_of_work = 5
        review.recruitment_coordination = 5
        review.timeliness = 5
        review.documentation = 4
        review.communication = 5
        review.problem_solving = 5
        review.weekly_goal_achievement = 5
        review.save()
        self.assertEqual(review.total_score, 39)
        self.assertEqual(float(review.performance_percentage), 97.50)
        self.assertEqual(review.performance_status, "EXCELLENT")

        # 3. Test Needs Improvement Tier (50-69%)
        review.task_completion = 3
        review.quality_of_work = 3
        review.recruitment_coordination = 3
        review.timeliness = 2
        review.documentation = 3
        review.communication = 3
        review.problem_solving = 2
        review.weekly_goal_achievement = 3
        review.save()
        self.assertEqual(review.total_score, 22)
        self.assertEqual(float(review.performance_percentage), 55.00)
        self.assertEqual(review.performance_status, "NEEDS_IMPROVEMENT")

        # 4. Test Unsatisfactory Tier (< 50%)
        review.task_completion = 1
        review.quality_of_work = 1
        review.recruitment_coordination = 2
        review.timeliness = 1
        review.documentation = 1
        review.communication = 2
        review.problem_solving = 1
        review.weekly_goal_achievement = 1
        review.save()
        self.assertEqual(review.total_score, 10)
        self.assertEqual(float(review.performance_percentage), 25.00)
        self.assertEqual(review.performance_status, "UNSATISFACTORY")

    def test_hr_create_and_submit_weekly_report_flow(self):
        """HR creates and submits weekly report, verifying Admin receives real database notification."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        create_url = reverse("hr:weekly_report_create")
        post_data = {
            "week_start_date": "2026-09-14",
            "week_end_date": "2026-09-20",
            "work_summary": "Handled recruitment activities for Software Development and coordinated interview schedules.",
            "tasks_completed": "• Screened candidate resumes\n• Scheduled interviews\n• Coordinated aptitude tests",
            "achievements": "Completed screening for assigned vacancies",
            "challenges": "Delayed candidate responses",
            "pending_tasks": "Follow up with remaining candidates",
            "next_week_plan": "Schedule remaining interviews",
            "vacancies_worked": 3,
            "candidates_screened": 25,
            "candidates_shortlisted": 10,
            "aptitude_tests": 8,
            "interviews": 5,
            "candidates_selected": 2,
            "action": "SUBMIT",
        }

        response = self.client.post(create_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        report = HRWeeklyReport.objects.get(hr_manager=self.hr_manager, week_start_date=date(2026, 9, 14))
        self.assertEqual(report.status, "SUBMITTED")
        self.assertIsNotNone(report.submitted_at)

        # Check Admin Notification generated in DB
        admin_notif = AdminNotification.objects.filter(
            notification_type="HR_REPORT_SUBMITTED"
        ).first()
        self.assertIsNotNone(admin_notif)
        self.assertIn("Jaimon Tomy", admin_notif.message)
        self.assertIn(str(report.pk), admin_notif.link_url)

    def test_admin_review_and_matrix_scoring_flow(self):
        """Admin opens submitted report, enters matrix ratings/feedback, and triggers HR notification."""
        report = HRWeeklyReport.objects.create(
            hr_manager=self.hr_manager,
            week_start_date=date(2026, 9, 14),
            week_end_date=date(2026, 9, 20),
            work_summary="Handled recruitment operations.",
            tasks_completed="Screening & Interviews.",
            status="SUBMITTED",
        )

        self.client.login(username=self.admin_user.email, password="AdminPassword123!")

        # 1. Admin views report
        review_url = reverse("admin_module:hr_report_detail", kwargs={"report_id": report.pk})
        resp = self.client.get(review_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Jaimon Tomy")
        self.assertContains(resp, "Handled recruitment operations.")

        # Report transitions to UNDER_REVIEW
        report.refresh_from_db()
        self.assertEqual(report.status, "UNDER_REVIEW")

        # 2. Admin saves performance review matrix
        post_data = {
            "task_completion": 4,
            "task_completion_remarks": "Completed assigned tasks",
            "quality_of_work": 4,
            "quality_of_work_remarks": "Good quality",
            "recruitment_coordination": 5,
            "recruitment_coordination_remarks": "Very good coordination",
            "timeliness": 3,
            "timeliness_remarks": "Some delays",
            "documentation": 4,
            "documentation_remarks": "Records maintained",
            "communication": 4,
            "communication_remarks": "Good coordination",
            "problem_solving": 3,
            "problem_solving_remarks": "Needs improvement",
            "weekly_goal_achievement": 4,
            "weekly_goal_achievement_remarks": "Most goals achieved",
            "overall_feedback": "Good progress this week. Recruitment coordination was handled effectively.",
            "strengths": "Good candidate coordination and timely follow-up.",
            "areas_for_improvement": "Improve response time for pending interview coordination.",
            "recommendations": "Complete pending follow-ups within the next reporting period.",
            "next_week_expectations": "Focus on closing pending recruitment activities.",
            "status_decision": "REVIEWED",
        }

        save_resp = self.client.post(review_url, data=post_data, follow=True)
        self.assertEqual(save_resp.status_code, 200)

        report.refresh_from_db()
        self.assertEqual(report.status, "REVIEWED")
        self.assertIsNotNone(report.reviewed_at)

        review = report.performance_review
        self.assertEqual(review.total_score, 31)
        self.assertEqual(float(review.average_score), 3.88)
        self.assertEqual(float(review.performance_percentage), 77.50)
        self.assertEqual(review.performance_status, "GOOD")

        # 3. Verify HR Notification is created
        hr_notif = HRNotification.objects.filter(
            hr_manager=self.hr_manager,
            notification_type="PERFORMANCE_REVIEWED"
        ).first()
        self.assertIsNotNone(hr_notif)
        self.assertIn("77.5", hr_notif.message)

        # 4. HR logs in and views their reviewed report with performance matrix
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        hr_detail_url = reverse("hr:weekly_report_detail", kwargs={"pk": report.pk})
        hr_resp = self.client.get(hr_detail_url)
        self.assertEqual(hr_resp.status_code, 200)
        self.assertContains(hr_resp, "77.5%")
        self.assertContains(hr_resp, "3.88 / 5")
        self.assertContains(hr_resp, "Task Completion")
        self.assertContains(hr_resp, "Good progress this week")

    def test_hr_performance_analysis_and_history(self):
        """Verify performance tracking and multi-week history on HR and Admin dashboards."""
        # Create 3 reviewed weeks
        w1 = HRWeeklyReport.objects.create(
            hr_manager=self.hr_manager,
            week_start_date=date(2026, 8, 31),
            week_end_date=date(2026, 9, 6),
            work_summary="Week 1 summary",
            tasks_completed="Tasks 1",
            status="REVIEWED",
        )
        HRPerformanceReview.objects.create(
            report=w1,
            task_completion=4, quality_of_work=4, recruitment_coordination=4, timeliness=4,
            documentation=3, communication=4, problem_solving=3, weekly_goal_achievement=4,  # total=30 -> 75%
        )

        w2 = HRWeeklyReport.objects.create(
            hr_manager=self.hr_manager,
            week_start_date=date(2026, 9, 7),
            week_end_date=date(2026, 9, 13),
            work_summary="Week 2 summary",
            tasks_completed="Tasks 2",
            status="REVIEWED",
        )
        HRPerformanceReview.objects.create(
            report=w2,
            task_completion=4, quality_of_work=5, recruitment_coordination=5, timeliness=4,
            documentation=4, communication=4, problem_solving=3, weekly_goal_achievement=4,  # total=33 -> 82.5%
        )

        # HR views performance analysis
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        hr_perf_url = reverse("hr:performance_analysis")
        res = self.client.get(hr_perf_url)
        self.assertContains(res, "75.00%")
        self.assertContains(res, "82.50%")
        self.assertContains(res, "78.8%")  # average of 75.0 and 82.5

        # Admin views HR performance analysis dashboard
        self.client.login(username=self.admin_user.email, password="AdminPassword123!")
        admin_perf_url = reverse("admin_module:hr_performance_analysis")
        admin_res = self.client.get(admin_perf_url)
        self.assertEqual(admin_res.status_code, 200)
        self.assertContains(admin_res, "Jaimon Tomy")
        self.assertContains(admin_res, "78.8%")

    def test_security_and_permission_isolation(self):
        """HR cannot view/edit other HR reports; non-admin cannot access admin review pages."""
        rep = HRWeeklyReport.objects.create(
            hr_manager=self.hr_manager,
            week_start_date=date(2026, 9, 14),
            week_end_date=date(2026, 9, 20),
            work_summary="Private HR summary",
            tasks_completed="Tasks",
            status="DRAFT",
        )

        # Other HR attempts to view report
        self.client.login(username=self.other_hr_user.email, password="OtherHRPass123!")
        res = self.client.get(reverse("hr:weekly_report_detail", kwargs={"pk": rep.pk}))
        self.assertEqual(res.status_code, 404)

        # Other HR attempts to access admin review page
        admin_url = reverse("admin_module:hr_report_detail", kwargs={"report_id": rep.pk})
        admin_res = self.client.get(admin_url)
        self.assertNotEqual(admin_res.status_code, 200)  # Redirected or 403


class CandidateOnboardingToEmployeeWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Engineering", is_active=True)
        self.team = Team.objects.create(department=self.dept, team_name="Backend Core", is_active=True)

        # Admin user
        self.admin_user = User.objects.create_user(
            email="admin.system@hrms.com",
            password="AdminPassword123!",
            name="System Admin",
            role=User.RoleChoices.ADMIN,
            status=User.StatusChoices.ACTIVE,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        # HR Manager
        self.hr_user = User.objects.create_user(
            email="hr.recruiter@hrms.com",
            password="HRPassword123!",
            name="HR Recruiter",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            first_name="HR",
            last_name="Recruiter",
            employee_code="HRM-101",
            department=self.dept,
            is_active=True,
        )

        # Candidate user & application
        self.cand_user = User.objects.create_user(
            email="sarah.connor@test.com",
            password="CandidatePass123!",
            name="Sarah Connor",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user,
            first_name="Sarah",
            last_name="Connor",
            phone="+1-555-888-9999",
            date_of_birth=date(1995, 4, 12),
            address="456 Future Ave, Tech City",
        )
        self.vacancy = JobVacancy.objects.create(
            title="Senior Python Engineer",
            department=self.dept,
            status="OPEN",
        )
        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.vacancy,
            status="SELECTED",
        )

    def test_complete_onboarding_and_approval_flow(self):
        """HR submits onboarding proposal -> Admin approves -> Employee created with credentials & can log in."""
        # 1. HR views candidate application page showing Recruitment Complete
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        detail_url = reverse("hr:application_detail", kwargs={"pk": self.application.pk})
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Recruitment Complete — Candidate Selected")
        self.assertContains(res, "Start Employee Onboarding")

        # 2. HR submits Onboarding Proposal
        forward_url = reverse("hr:forward_to_admin", kwargs={"pk": self.application.pk})
        post_data = {
            "department": self.dept.pk,
            "designation": "Senior Python Developer",
            "team": self.team.pk,
            "team_lead": self.admin_user.pk,
            "joining_date": "2026-10-01",
            "employment_type": "FULL_TIME",
            "work_location": "Office HQ",
            "hr_justification": "Candidate passed all rounds with exceptional scores.",
        }
        res_submit = self.client.post(forward_url, post_data)
        self.assertEqual(res_submit.status_code, 302)

        # Verify DB state after HR proposal
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, "FORWARDED_TO_ADMIN")

        employee = Employee.objects.filter(user=self.cand_user).first()
        self.assertIsNotNone(employee)
        self.assertEqual(employee.employment_status, "INACTIVE")
        self.assertEqual(employee.designation, "Senior Python Developer")
        self.assertEqual(employee.department, self.dept)
        self.assertEqual(employee.team, self.team)

        approval = EmployeeApproval.objects.filter(employee=employee).first()
        self.assertIsNotNone(approval)
        self.assertEqual(approval.status, "PENDING")

        admin_notif = AdminNotification.objects.filter(notification_type="EMPLOYEE_APPROVAL").first()
        self.assertIsNotNone(admin_notif)
        self.assertIn("Sarah Connor", admin_notif.message)

        # Verify HR page now shows Pending Admin Approval and prevents duplicate proposals
        res_pending = self.client.get(detail_url)
        self.assertContains(res_pending, "Pending Admin Approval")

        res_dup = self.client.post(forward_url, post_data)
        self.assertEqual(res_dup.status_code, 302)
        # Should not create duplicate Employee record
        self.assertEqual(Employee.objects.filter(user=self.cand_user).count(), 1)

        # 3. Admin logs in, checks Pending Onboarding list and Review page
        self.client.login(username=self.admin_user.email, password="AdminPassword123!")
        pending_list_resp = self.client.get(reverse("admin_module:employees_pending"))
        self.assertEqual(pending_list_resp.status_code, 200)
        self.assertContains(pending_list_resp, "Sarah Connor")

        review_url = reverse("admin_module:recruitment_approval_review", kwargs={"employee_id": employee.pk})
        review_resp = self.client.get(review_url)
        self.assertEqual(review_resp.status_code, 200)
        self.assertContains(review_resp, "Sarah Connor")
        self.assertContains(review_resp, "Senior Python Developer")
        self.assertContains(review_resp, "Candidate passed all rounds with exceptional scores.")

        # 4. Admin approves onboarding and sets a temporary password
        approve_url = reverse("admin_module:recruitment_approval_approve", kwargs={"employee_id": employee.pk})
        approve_data = {
            "department": self.dept.pk,
            "designation": "Lead Python Developer",
            "team": self.team.pk,
            "temporary_password": "EmpSecretPass2026!",
            "comments": "Approved with promotion to Lead Developer.",
        }
        approve_resp = self.client.post(approve_url, approve_data)
        self.assertEqual(approve_resp.status_code, 302)

        # 5. Verify database updates upon approval
        employee.refresh_from_db()
        self.cand_user.refresh_from_db()
        approval.refresh_from_db()
        self.application.refresh_from_db()

        self.assertEqual(approval.status, "APPROVED")
        self.assertEqual(employee.employment_status, "ACTIVE")
        self.assertEqual(employee.designation, "Lead Python Developer")
        self.assertTrue(employee.employee_code.startswith("EMP"))
        self.assertEqual(self.cand_user.role, User.RoleChoices.EMPLOYEE)
        self.assertTrue(self.cand_user.check_password("EmpSecretPass2026!"))
        self.assertEqual(self.application.status, "HIRED")

        # Check candidate notification with login credentials
        cand_notif = CandidateNotification.objects.filter(
            candidate=self.candidate,
            notification_type="EMPLOYEE_CONVERTED",
        ).first()
        self.assertIsNotNone(cand_notif)
        self.assertIn("EmpSecretPass2026!", cand_notif.message)
        self.assertIn(employee.employee_code, cand_notif.message)

        # Check HR notification
        hr_notif = HRNotification.objects.filter(hr_manager=self.hr_manager).first()
        self.assertIsNotNone(hr_notif)
        self.assertIn("approved", hr_notif.message.lower())

        # 6. Newly converted employee logs in with temporary password and accesses dashboard
        self.client.logout()
        login_ok = self.client.login(username="sarah.connor@test.com", password="EmpSecretPass2026!")
        self.assertTrue(login_ok)

        redirect_resp = self.client.get(reverse("users:redirect"))
        self.assertEqual(redirect_resp.status_code, 302)
        self.assertIn(reverse("employees:dashboard"), redirect_resp.url)

        dash_resp = self.client.get(reverse("employees:dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, "Sarah Connor")

        # 7. HR views application detail and sees Onboarding Completed
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        res_completed = self.client.get(detail_url)
        self.assertEqual(res_completed.status_code, 200)
        self.assertContains(res_completed, "Employee Onboarding Completed")
        self.assertContains(res_completed, employee.employee_code)
        self.assertContains(res_completed, "View Employee Profile")

    def test_admin_rejection_flow(self):
        """Admin rejects onboarding proposal -> status becomes REJECTED and HR is notified."""
        # 1. HR submits Onboarding Proposal
        forward_url = reverse("hr:forward_to_admin", kwargs={"pk": self.application.pk})
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        self.client.post(forward_url, {
            "department": self.dept.pk,
            "designation": "Python Dev",
            "joining_date": "2026-10-01",
        })

        employee = Employee.objects.get(user=self.cand_user)
        approval = EmployeeApproval.objects.get(employee=employee)

        # 2. Admin rejects with reason
        self.client.login(username=self.admin_user.email, password="AdminPassword123!")
        reject_url = reverse("admin_module:recruitment_approval_reject", kwargs={"employee_id": employee.pk})
        reject_resp = self.client.post(reject_url, {
            "rejection_reason": "Position headcount cancelled by management.",
        })
        self.assertEqual(reject_resp.status_code, 302)

        # 3. Verify DB state after rejection
        approval.refresh_from_db()
        employee.refresh_from_db()
        self.cand_user.refresh_from_db()

        self.assertEqual(approval.status, "REJECTED")
        self.assertEqual(approval.rejection_reason, "Position headcount cancelled by management.")
        self.assertEqual(employee.employment_status, "INACTIVE")
        self.assertEqual(self.cand_user.role, User.RoleChoices.CANDIDATE)

        # 4. Check HR received notification with rejection reason
        hr_notif = HRNotification.objects.filter(hr_manager=self.hr_manager).first()
        self.assertIsNotNone(hr_notif)
        self.assertIn("rejected", hr_notif.message.lower())
        self.assertIn("Position headcount cancelled by management.", hr_notif.message)





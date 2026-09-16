from datetime import date, time
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from admin_module.models import Department
from candidates.models import Candidate, JobApplication, JobVacancy
from employees.models import Employee, EmployeeDocument
from hr.models import AptitudeResult, AptitudeTest, HRManager, Interview

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
            department=self.dept,
            employee_code="HRM-001",
            joining_date=date(2024, 1, 1),
            is_active=True,
        )

        # Linked employee & candidate
        self.candidate = Candidate.objects.create(
            user=self.hr_user,
            first_name="Alice",
            last_name="Walker",
            phone="+1-555-123-4567",
            date_of_birth=date(1990, 5, 20),
            address="123 Corporate Way, Cityville",
        )
        self.employee = Employee.objects.create(
            user=self.hr_user,
            candidate=self.candidate,
            employee_code="HRM-001",
            department=self.dept,
            designation="HR Manager",
            joining_date=date(2024, 1, 1),
            employment_status="ACTIVE",
        )
        self.doc = EmployeeDocument.objects.create(
            employee=self.employee,
            document_type="ID_PROOF",
            document=SimpleUploadedFile("id_proof.pdf", b"pdf content", content_type="application/pdf"),
        )

    def test_hr_dashboard_view(self):
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        response = self.client.get(reverse("hr:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Walker")

    def test_hr_profile_view_displays_all_sections(self):
        """HR Profile view displays Account, Personal, Professional, and Document information."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        response = self.client.get(reverse("hr:profile"))

        self.assertEqual(response.status_code, 200)

        # Account Info
        self.assertContains(response, "hr.manager@company.com")
        self.assertContains(response, "Active Account")
        self.assertContains(response, "HR Manager")

        # Personal Info
        self.assertContains(response, "Alice Walker")
        self.assertContains(response, "+1-555-123-4567")
        self.assertContains(response, "123 Corporate Way, Cityville")
        self.assertContains(response, "May 20, 1990")

        # Professional Info
        self.assertContains(response, "HRM-001")
        self.assertContains(response, "Human Resources")
        self.assertContains(response, "Active HR Lead")

        # Documents
        self.assertContains(response, "ID Proof")

        # Security check: Password hash must NEVER be present
        self.assertNotContains(response, self.hr_user.password)

    def test_hr_profile_fallback_for_missing_values(self):
        """HR profile handles missing optional data with proper fallback messages."""
        # Create minimal HR user without candidate or documents
        user2 = User.objects.create_user(
            email="minimal.hr@company.com",
            password="HRPassword123!",
            name="",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        HRManager.objects.create(
            user=user2,
            employee_code="HRM-999",
            is_active=True,
        )

        self.client.login(username=user2.email, password="HRPassword123!")
        response = self.client.get(reverse("hr:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "HRM-999")
        self.assertContains(response, "Unassigned")
        self.assertContains(response, "Not provided")
        self.assertContains(response, "Not uploaded")
        self.assertContains(response, "No documents uploaded yet.")

    def test_hr_profile_edit_view_get_prefills_data(self):
        """Edit profile form renders with prefilled database values."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        response = self.client.get(reverse("hr:profile_edit"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Walker")
        self.assertContains(response, "hr.manager@company.com")
        self.assertContains(response, "+1-555-123-4567")
        self.assertContains(response, "123 Corporate Way, Cityville")

    def test_hr_profile_edit_view_post_updates_database(self):
        """Submitting updated values saves to User, HRManager, Employee, and Candidate."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        post_data = {
            "full_name": "Alice M. Walker",
            "email": "alice.walker.updated@company.com",
            "phone": "+1-555-999-8888",
            "date_of_birth": "1991-06-15",
            "address": "456 Innovation Blvd, Tech Park",
            "department": self.engineering.pk,
        }
        response = self.client.post(reverse("hr:profile_edit"), data=post_data)
        self.assertRedirects(response, reverse("hr:profile"))

        # Verify DB updates
        self.hr_user.refresh_from_db()
        self.assertEqual(self.hr_user.name, "Alice M. Walker")
        self.assertEqual(self.hr_user.email, "alice.walker.updated@company.com")

        self.hr_manager.refresh_from_db()
        self.assertEqual(self.hr_manager.department, self.engineering)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.first_name, "Alice")
        self.assertEqual(self.candidate.last_name, "M. Walker")
        self.assertEqual(self.candidate.phone, "+1-555-999-8888")
        self.assertEqual(self.candidate.date_of_birth, date(1991, 6, 15))
        self.assertEqual(self.candidate.address, "456 Innovation Blvd, Tech Park")

        # Verify updated values appear on profile view
        profile_response = self.client.get(reverse("hr:profile"))
        self.assertContains(profile_response, "Alice M. Walker")
        self.assertContains(profile_response, "alice.walker.updated@company.com")
        self.assertContains(profile_response, "+1-555-999-8888")
        self.assertContains(profile_response, "Engineering")

    def test_hr_profile_document_upload_and_delete(self):
        """HR can upload a document and delete their own document."""
        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        # Upload document
        file_data = SimpleUploadedFile("cert.pdf", b"Dummy Certificate Data", content_type="application/pdf")
        upload_response = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "upload_document",
                "document_type": "EXPERIENCE_CERTIFICATE",
                "document": file_data,
            },
        )
        self.assertRedirects(upload_response, reverse("hr:profile"))

        new_doc = EmployeeDocument.objects.filter(employee=self.employee, document_type="EXPERIENCE_CERTIFICATE").first()
        self.assertIsNotNone(new_doc)

        # Profile shows newly uploaded document
        profile_response = self.client.get(reverse("hr:profile"))
        self.assertContains(profile_response, "Experience Certificate")

        # Delete document
        delete_response = self.client.post(
            reverse("hr:profile"),
            data={
                "action": "delete_document",
                "document_id": new_doc.pk,
            },
        )
        self.assertRedirects(delete_response, reverse("hr:profile"))
        self.assertFalse(EmployeeDocument.objects.filter(pk=new_doc.pk).exists())

    def test_unauthenticated_or_non_hr_cannot_access(self):
        """Unauthenticated or non-HR users cannot access HR profile or edit profile."""
        # Anonymous
        self.client.logout()
        res1 = self.client.get(reverse("hr:profile"))
        self.assertEqual(res1.status_code, 302)

        res2 = self.client.get(reverse("hr:profile_edit"))
        self.assertEqual(res2.status_code, 302)

        # Candidate user
        cand_user = User.objects.create_user(
            email="cand@test.com",
            password="CandPass123!",
            role=User.RoleChoices.CANDIDATE,
        )
        self.client.login(username="cand@test.com", password="CandPass123!")
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




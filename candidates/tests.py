"""Comprehensive test suite for Candidate Profile, Education, Skills, Documents, and Security."""
import io
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from datetime import date, timedelta
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import (
    Application,
    AptitudeTest,
    Candidate,
    CandidateDocument,
    CandidateEducation,
    CandidateSkill,
    Department,
    Interview,
    Job,
    Notification,
    Question,
    TestResult,
)
from .validators import validate_document_file, MAX_UPLOAD_SIZE_BYTES

User = get_user_model()


class CandidateProfileBackendTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create Primary Candidate (Candidate A)
        self.user_a = User.objects.create_user(
            username="alan_test",
            email="alan.test@example.com",
            password="securepassword123",
            first_name="Alan",
            last_name="Shaji",
        )
        self.candidate_a = Candidate.objects.create(
            user=self.user_a,
            full_name="Alan Shaji",
            phone="+91 98765 43210",
            city="Kochi",
            state="Kerala",
        )
        self.doc_a = CandidateDocument.objects.create(candidate=self.candidate_a)

        # Create Secondary Candidate (Candidate B for ownership/security testing)
        self.user_b = User.objects.create_user(
            username="bob_test",
            email="bob.test@example.com",
            password="securepassword456",
            first_name="Bob",
            last_name="Martin",
        )
        self.candidate_b = Candidate.objects.create(
            user=self.user_b,
            full_name="Bob Martin",
            phone="+91 91234 56789",
            city="Bangalore",
            state="Karnataka",
        )
        self.doc_b = CandidateDocument.objects.create(candidate=self.candidate_b)

    # ==========================================================================
    # 1. VIEW PROFILE
    # ==========================================================================
    def test_view_profile_requires_login(self):
        """Unauthenticated user accessing profile is redirected to login."""
        response = self.client.get(reverse("candidates:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_view_profile_authenticated(self):
        """Logged-in candidate can view their profile with dynamic context."""
        self.client.login(username="alan_test", password="securepassword123")
        response = self.client.get(reverse("candidates:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "candidates/candidate/profile.html")
        self.assertEqual(response.context["candidate"].candidate_id, self.candidate_a.candidate_id)
        self.assertIn("completion_pct", response.context)
        self.assertIn("completion_advice", response.context)
        self.assertContains(response, "Alan Shaji")

    # ==========================================================================
    # 2. EDIT & SAVE PROFILE (PERSONAL INFORMATION)
    # ==========================================================================
    def test_update_personal_information(self):
        """Candidate updates full name, phone, DOB, gender, address, city, state, pincode."""
        self.client.login(username="alan_test", password="securepassword123")
        update_data = {
            "full_name": "Alan Shaji Updated",
            "phone": "+91 99999 88888",
            "date_of_birth": "2002-05-14",
            "gender": "MALE",
            "email": "alan.updated@example.com",
            "address": "42 Palm Grove, Marine Drive",
            "city": "Ernakulam",
            "state": "Kerala",
            "pincode": "682011",
            "experience_level": "Fresher / 0-1 Years",
            "preferred_job_type": "Full Time",
            "preferred_locations": "Kochi, Bangalore",
            "notice_period": "Immediate Joiner (0 Days)",
        }
        response = self.client.post(reverse("candidates:edit_profile"), update_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("candidates:profile"))

        self.candidate_a.refresh_from_db()
        self.assertEqual(self.candidate_a.full_name, "Alan Shaji Updated")
        self.assertEqual(self.candidate_a.phone, "+91 99999 88888")
        self.assertEqual(str(self.candidate_a.date_of_birth), "2002-05-14")
        self.assertEqual(self.candidate_a.gender, "MALE")
        self.assertEqual(self.candidate_a.city, "Ernakulam")
        self.assertEqual(self.candidate_a.pincode, "682011")
        self.assertEqual(self.candidate_a.user.email, "alan.updated@example.com")

    # ==========================================================================
    # 3. EDUCATION UPDATE (10th, 12th, DEGREE)
    # ==========================================================================
    def test_update_education_qualifications(self):
        """Candidate updates 10th, 12th, and Degree records through edit profile."""
        self.client.login(username="alan_test", password="securepassword123")
        edu_data = {
            "full_name": "Alan Shaji",
            "phone": "+91 98765 43210",
            "date_of_birth": "2002-05-14",
            "gender": "MALE",
            "email": "alan.test@example.com",
            # Degree
            "degree_qualification": "Master of Computer Applications (MCA)",
            "degree_institution": "Cochin University of Science and Technology (CUSAT)",
            "degree_year": "2024 - 2026",
            "degree_percentage_or_cgpa": "8.8 CGPA",
            # 12th
            "twelfth_institution": "St. Joseph's Higher Secondary School",
            "twelfth_board": "State Board",
            "twelfth_year": "2021",
            "twelfth_percentage_or_cgpa": "92.4%",
            # 10th
            "tenth_institution": "Carmel English Medium School",
            "tenth_board": "State Board",
            "tenth_year": "2019",
            "tenth_percentage_or_cgpa": "94.0%",
        }
        response = self.client.post(reverse("candidates:edit_profile"), edu_data)
        self.assertEqual(response.status_code, 302)

        educations = list(self.candidate_a.educations.all())
        self.assertEqual(len(educations), 3)

        qual_types = [e.qualification_type for e in educations]
        self.assertTrue(any("MCA" in q or "Degree" in q for q in qual_types))
        self.assertTrue(any("12th" in q or "Higher Secondary" in q for q in qual_types))
        self.assertTrue(any("10th" in q or "Secondary" in q for q in qual_types))

    # ==========================================================================
    # 4. SKILLS UPDATE (ADD, EDIT, DELETE)
    # ==========================================================================
    def test_skill_add_and_delete(self):
        """Tests adding and deleting individual skills."""
        self.client.login(username="alan_test", password="securepassword123")

        # 1. Add skill
        response = self.client.post(reverse("candidates:skill_add"), {"skill_name": "Django"})
        self.assertEqual(response.status_code, 302)
        skill = CandidateSkill.objects.get(candidate=self.candidate_a, skill_name="Django")
        self.assertIsNotNone(skill)

        # 2. Edit skill
        response = self.client.post(reverse("candidates:skill_edit", args=[skill.skill_id]), {"skill_name": "Django REST Framework"})
        self.assertEqual(response.status_code, 302)
        skill.refresh_from_db()
        self.assertEqual(skill.skill_name, "Django REST Framework")

        # 3. Delete skill
        response = self.client.post(reverse("candidates:skill_delete", args=[skill.skill_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CandidateSkill.objects.filter(pk=skill.skill_id).exists())

    def test_bulk_skills_sync(self):
        """Tests comma-separated skill list sync in profile edit."""
        self.client.login(username="alan_test", password="securepassword123")
        data = {
            "full_name": "Alan Shaji",
            "phone": "+91 98765 43210",
            "date_of_birth": "2002-05-14",
            "gender": "MALE",
            "email": "alan.test@example.com",
            "skills_comma": "Python, Django, PostgreSQL, JavaScript",
        }
        response = self.client.post(reverse("candidates:edit_profile"), data)
        self.assertEqual(response.status_code, 302)

        skills = list(self.candidate_a.skills.values_list("skill_name", flat=True))
        self.assertEqual(len(skills), 4)
        self.assertIn("Python", skills)
        self.assertIn("PostgreSQL", skills)

    # ==========================================================================
    # 5. DOCUMENT UPLOADS & VALIDATIONS
    # ==========================================================================
    def test_valid_pdf_document_upload(self):
        """Candidate uploads a valid PDF resume."""
        self.client.login(username="alan_test", password="securepassword123")
        pdf_content = b"%PDF-1.4 Mock PDF file binary data content"
        pdf_file = SimpleUploadedFile("resume.pdf", pdf_content, content_type="application/pdf")

        response = self.client.post(reverse("candidates:document_upload"), {
            "document_type": "resume",
            "document_file": pdf_file,
        })
        self.assertEqual(response.status_code, 302)
        self.doc_a.refresh_from_db()
        self.assertTrue(bool(self.doc_a.resume))
        self.assertTrue(self.doc_a.resume.name.endswith(".pdf"))

    def test_valid_image_document_upload(self):
        """Candidate uploads a valid JPG image for ID proof."""
        self.client.login(username="alan_test", password="securepassword123")
        jpg_content = b"\xff\xd8\xff\xe0" + b"\x00" * 50
        jpg_file = SimpleUploadedFile("id_proof.jpg", jpg_content, content_type="image/jpeg")

        response = self.client.post(reverse("candidates:document_upload"), {
            "document_type": "id_proof",
            "document_file": jpg_file,
        })
        self.assertEqual(response.status_code, 302)
        self.doc_a.refresh_from_db()
        self.assertTrue(bool(self.doc_a.id_proof))

    def test_invalid_executable_upload_blocked(self):
        """Uploading an executable file (.exe or disguised) must be rejected."""
        self.client.login(username="alan_test", password="securepassword123")
        exe_file = SimpleUploadedFile("malware.exe", b"MZ" + b"\x00" * 30, content_type="application/x-msdownload")

        response = self.client.post(reverse("candidates:document_upload"), {
            "document_type": "resume",
            "document_file": exe_file,
        })
        self.doc_a.refresh_from_db()
        # File should not be uploaded
        self.assertFalse(bool(self.doc_a.resume))

        # Disguised executable (.exe renamed to .pdf)
        fake_pdf = SimpleUploadedFile("fake.pdf", b"MZ\x90\x00" + b"\x00" * 20, content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_document_file(fake_pdf)

    def test_oversized_file_blocked(self):
        """File exceeding 10MB must be rejected by validator."""
        oversized = SimpleUploadedFile("huge.pdf", b"%PDF" + b"0" * 100, content_type="application/pdf")
        oversized.size = MAX_UPLOAD_SIZE_BYTES + 1
        with self.assertRaises(ValidationError):
            validate_document_file(oversized)

    def test_replace_and_delete_document(self):
        """Test replacing an existing document and deleting it."""
        self.client.login(username="alan_test", password="securepassword123")
        
        # 1. Upload
        doc1 = SimpleUploadedFile("degree.pdf", b"%PDF-1.4 degree 1", content_type="application/pdf")
        self.client.post(reverse("candidates:document_upload"), {
            "document_type": "degree_certificate",
            "document_file": doc1,
        })
        self.doc_a.refresh_from_db()
        self.assertTrue(bool(self.doc_a.degree_certificate))

        # 2. Replace with doc2
        doc2 = SimpleUploadedFile("degree_v2.pdf", b"%PDF-1.4 degree 2", content_type="application/pdf")
        self.client.post(reverse("candidates:document_upload"), {
            "document_type": "degree_certificate",
            "document_file": doc2,
        })
        self.doc_a.refresh_from_db()
        self.assertIn("degree_v2", self.doc_a.degree_certificate.name)

        # 3. Delete
        self.client.post(reverse("candidates:delete_document", args=["degree_certificate"]))
        self.doc_a.refresh_from_db()
        self.assertFalse(bool(self.doc_a.degree_certificate))

    # ==========================================================================
    # 6. DYNAMIC PROFILE COMPLETION
    # ==========================================================================
    def test_dynamic_profile_completion_calculation(self):
        """Profile completion percentage increases dynamically as details are added."""
        # Initial minimal candidate score
        initial_score, _ = self.candidate_a.calculate_profile_completion()
        self.assertGreater(initial_score, 0)
        self.assertLess(initial_score, 50)

        # Add remaining personal info
        self.candidate_a.date_of_birth = "2002-05-14"
        self.candidate_a.gender = "MALE"
        self.candidate_a.address = "Marine Drive"
        self.candidate_a.pincode = "682011"
        self.candidate_a.save()

        score_personal, _ = self.candidate_a.calculate_profile_completion()
        self.assertGreater(score_personal, initial_score)

        # Add 3 skills
        CandidateSkill.objects.create(candidate=self.candidate_a, skill_name="Python")
        CandidateSkill.objects.create(candidate=self.candidate_a, skill_name="Django")
        CandidateSkill.objects.create(candidate=self.candidate_a, skill_name="PostgreSQL")

        score_skills, _ = self.candidate_a.calculate_profile_completion()
        self.assertGreater(score_skills, score_personal)

        # Add educations
        CandidateEducation.objects.create(
            candidate=self.candidate_a,
            qualification_type="MCA Degree",
            institution="CUSAT",
            year="2026",
            percentage_or_cgpa="8.8",
        )
        score_edu, _ = self.candidate_a.calculate_profile_completion()
        self.assertGreater(score_edu, score_skills)

        # Upload resume
        self.doc_a.resume = SimpleUploadedFile("res.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        self.doc_a.save()
        score_doc, _ = self.candidate_a.calculate_profile_completion()
        self.assertGreater(score_doc, score_edu)

        # Confirm update_profile_completion updates model field
        updated_pct = self.candidate_a.update_profile_completion()
        self.candidate_a.refresh_from_db()
        self.assertEqual(self.candidate_a.profile_completion_pct, updated_pct)

    # ==========================================================================
    # 7. CANDIDATE OWNERSHIP & SECURITY CHECKS
    # ==========================================================================
    def test_candidate_ownership_security(self):
        """Candidate B cannot modify or delete Candidate A's skills or educations."""
        # Candidate A creates a skill and education
        skill_a = CandidateSkill.objects.create(candidate=self.candidate_a, skill_name="SecretSkill")
        edu_a = CandidateEducation.objects.create(
            candidate=self.candidate_a,
            qualification_type="MCA",
            institution="CUSAT",
            year="2026",
            percentage_or_cgpa="90%",
        )

        # Candidate B logs in
        self.client.login(username="bob_test", password="securepassword456")

        # Candidate B tries to delete Candidate A's skill -> Expect 403 Forbidden
        response = self.client.post(reverse("candidates:skill_delete", args=[skill_a.skill_id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(CandidateSkill.objects.filter(pk=skill_a.skill_id).exists())

        # Candidate B tries to edit Candidate A's skill -> Expect 403 Forbidden
        response = self.client.post(reverse("candidates:skill_edit", args=[skill_a.skill_id]), {"skill_name": "Hacked"})
        self.assertEqual(response.status_code, 403)
        skill_a.refresh_from_db()
        self.assertEqual(skill_a.skill_name, "SecretSkill")

        # Candidate B tries to delete Candidate A's education -> Expect 403 Forbidden
        response = self.client.post(reverse("candidates:education_delete", args=[edu_a.education_id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(CandidateEducation.objects.filter(pk=edu_a.education_id).exists())

    def test_document_view_ownership(self):
        """Candidate can only view/download their own uploaded documents."""
        # Candidate A uploads resume
        self.doc_a.resume = SimpleUploadedFile("alan_resume.pdf", b"%PDF-1.4 Alan Resume Content", content_type="application/pdf")
        self.doc_a.save()

        # Candidate A logs in and accesses resume -> 200 OK
        self.client.login(username="alan_test", password="securepassword123")
        response = self.client.get(reverse("candidates:view_document", args=["resume"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # Candidate B logs in and attempts to access resume -> 404 (because Candidate B has not uploaded a resume)
        self.client.login(username="bob_test", password="securepassword456")
        response = self.client.get(reverse("candidates:view_document", args=["resume"]))
        self.assertEqual(response.status_code, 404)


# ==============================================================================
# JOB APPLICATION BACKEND TESTS
# ==============================================================================
class JobApplicationBackendTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Department
        self.department = Department.objects.create(
            name="IT & Engineering",
            code="IT",
            description="Software development and IT operations",
        )

        # Create Active Job Vacancy
        self.job = Job.objects.create(
            title="Python Developer",
            department=self.department,
            job_type=Job.JobType.FULL_TIME,
            experience_required="0-2 Years",
            location="Kochi, Kerala (Hybrid)",
            salary_display="₹6.0 - 8.5 LPA",
            description="Build scalable backend services with Django and PostgreSQL.",
            status=Job.Status.OPEN,
            deadline=date.today() + timedelta(days=30),
        )

        # Create Candidate A (Fully qualified with profile resume)
        self.user_a = User.objects.create_user(
            username="candidate_a",
            email="candidate_a@example.com",
            password="password123",
            first_name="Alice",
            last_name="Johnson",
        )
        self.candidate_a = Candidate.objects.create(
            user=self.user_a,
            full_name="Alice Johnson",
            phone="+91 98765 00001",
            city="Kochi",
            state="Kerala",
        )
        self.doc_a = CandidateDocument.objects.create(
            candidate=self.candidate_a,
            resume=SimpleUploadedFile("alice_resume.pdf", b"%PDF-1.4 Alice Resume", content_type="application/pdf"),
        )

        # Create Candidate B (For isolation and security testing)
        self.user_b = User.objects.create_user(
            username="candidate_b",
            email="candidate_b@example.com",
            password="password456",
            first_name="Bob",
            last_name="Smith",
        )
        self.candidate_b = Candidate.objects.create(
            user=self.user_b,
            full_name="Bob Smith",
            phone="+91 98765 00002",
            city="Bangalore",
            state="Karnataka",
        )
        self.doc_b = CandidateDocument.objects.create(
            candidate=self.candidate_b,
            resume=SimpleUploadedFile("bob_resume.pdf", b"%PDF-1.4 Bob Resume", content_type="application/pdf"),
        )

    # 1. Job List View (Public & Filterable)
    def test_job_list_view(self):
        """Job list is accessible and displays active vacancies."""
        response = self.client.get(reverse("candidates:job_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "candidates/jobs/job_list.html")
        self.assertContains(response, "Python Developer")
        self.assertEqual(response.context["total_jobs_count"], 1)

    # 2. Job Details View
    def test_job_details_view(self):
        """Job details page shows complete vacancy specs and apply button."""
        response = self.client.get(reverse("candidates:job_details", args=[self.job.job_id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "candidates/jobs/job_details.html")
        self.assertContains(response, "Python Developer")
        self.assertContains(response, "Kochi, Kerala (Hybrid)")
        self.assertFalse(response.context["has_applied"])

    # 3. Apply Requires Login
    def test_apply_requires_login(self):
        """Unauthenticated candidate attempting to apply is redirected to login."""
        response = self.client.get(reverse("candidates:job_apply", args=[self.job.job_id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    # 4. Successful Job Application Flow
    def test_apply_successful_flow(self):
        """
        Valid candidate applies:
        - Application created with status = APPLIED
        - Unique application_code generated (e.g. APP-2026-XXXX)
        - In-app notification created
        - Confirmation email sent
        - Success block rendered with ID, job title, and status
        """
        self.client.login(username="candidate_a", password="password123")
        mail.outbox.clear()

        apply_data = {
            "cover_note": "I have 2 years of solid Python and Django experience.",
        }
        response = self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), apply_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["submitted_success"])

        # Check Application created in database
        app = Application.objects.get(candidate=self.candidate_a, job=self.job)
        self.assertIsNotNone(app)
        self.assertEqual(app.status, Application.Status.APPLIED)
        self.assertTrue(app.application_code.startswith("APP-2026-"))
        self.assertEqual(app.cover_note, "I have 2 years of solid Python and Django experience.")
        self.assertTrue(bool(app.resume))

        # Check Notification created
        notif = Notification.objects.filter(candidate=self.candidate_a).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, Notification.NotificationType.APPLICATION)
        self.assertIn(f"Your application for {self.job.title} has been submitted successfully.", notif.message)

        # Check Confirmation Email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"Application Confirmation: {self.job.title}", mail.outbox[0].subject)
        self.assertIn(self.candidate_a.user.email, mail.outbox[0].to)
        self.assertIn(app.application_code, mail.outbox[0].body)

        # Check Success page contents
        self.assertContains(response, app.application_code)
        self.assertContains(response, "Python Developer")
        self.assertContains(response, "Application Submitted Successfully!")

    # 5. Duplicate Application Prevention (Backend & Database Constraint)
    def test_duplicate_application_prevention(self):
        """Prevent candidate from applying to the same job twice."""
        self.client.login(username="candidate_a", password="password123")

        # 1. First application succeeds
        self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), {"cover_note": "First try"})
        self.assertEqual(Application.objects.filter(candidate=self.candidate_a, job=self.job).count(), 1)

        # 2. Second application GET shows already applied message
        get_response = self.client.get(reverse("candidates:job_apply", args=[self.job.job_id]))
        self.assertContains(get_response, "Already Applied")

        # 3. Second application POST is rejected by view validation
        post_response = self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), {"cover_note": "Second try"})
        self.assertEqual(Application.objects.filter(candidate=self.candidate_a, job=self.job).count(), 1)

        # 4. Database unique constraint prevents duplicate directly
        with self.assertRaises(IntegrityError):
            Application.objects.create(
                candidate=self.candidate_a,
                job=self.job,
                status=Application.Status.APPLIED,
            )

    # 6. Apply to Closed Job Rejected
    def test_apply_closed_job_rejected(self):
        """Applying to a closed job vacancy is rejected."""
        self.job.status = Job.Status.CLOSED
        self.job.save()

        self.client.login(username="candidate_a", password="password123")
        response = self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), {"cover_note": "Please consider me"})
        # Should not create application
        self.assertFalse(Application.objects.filter(candidate=self.candidate_a, job=self.job).exists())

    # 7. Apply to Job with Expired Deadline Rejected
    def test_apply_expired_deadline_rejected(self):
        """Applying to a job with deadline in the past is rejected."""
        self.job.deadline = date.today() - timedelta(days=2)
        self.job.save()

        self.client.login(username="candidate_a", password="password123")
        response = self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), {"cover_note": "Late application"})
        self.assertFalse(Application.objects.filter(candidate=self.candidate_a, job=self.job).exists())

    # 8. Apply Without Resume Rejected
    def test_apply_missing_resume_rejected(self):
        """Candidate with no profile resume and no uploaded resume cannot apply."""
        # Remove Candidate A's resume
        self.doc_a.resume = None
        self.doc_a.save()

        self.client.login(username="candidate_a", password="password123")
        response = self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), {"cover_note": "No resume attached"})
        self.assertFalse(Application.objects.filter(candidate=self.candidate_a, job=self.job).exists())
        self.assertContains(response, "valid resume is required")

    # 9. Apply With Custom Uploaded Resume
    def test_apply_with_custom_uploaded_resume(self):
        """Candidate can attach a job-specific resume during application."""
        self.client.login(username="candidate_a", password="password123")
        custom_resume = SimpleUploadedFile("custom_python_cv.pdf", b"%PDF-1.4 Custom Python CV", content_type="application/pdf")

        response = self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), {
            "cover_note": "Specialized CV attached.",
            "custom_resume": custom_resume,
        })
        self.assertEqual(response.status_code, 200)
        app = Application.objects.get(candidate=self.candidate_a, job=self.job)
        self.assertIn("custom_python_cv", app.resume.name)

    # 10. Incomplete Profile Rejected
    def test_apply_incomplete_profile_rejected(self):
        """Candidate missing required phone or full name is rejected."""
        self.candidate_a.phone = ""
        self.candidate_a.save()

        self.client.login(username="candidate_a", password="password123")
        response = self.client.post(reverse("candidates:job_apply", args=[self.job.job_id]), {"cover_note": "My note"})
        self.assertFalse(Application.objects.filter(candidate=self.candidate_a, job=self.job).exists())

    # 11. Candidate Isolation on My Applications
    def test_my_applications_candidate_isolation(self):
        """Candidates can strictly ONLY see their own applications on My Applications."""
        # Candidate A applies for Job 1
        app_a = Application.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            status=Application.Status.APPLIED,
        )

        # Create Job 2 and Candidate B applies for Job 2
        job2 = Job.objects.create(
            title="UI/UX Designer",
            department=self.department,
            status=Job.Status.OPEN,
        )
        app_b = Application.objects.create(
            candidate=self.candidate_b,
            job=job2,
            status=Application.Status.SHORTLISTED,
        )

        # Candidate A logs in
        self.client.login(username="candidate_a", password="password123")
        response_a = self.client.get(reverse("candidates:my_applications"))
        self.assertEqual(response_a.status_code, 200)
        self.assertContains(response_a, app_a.application_code)
        self.assertNotContains(response_a, app_b.application_code)
        self.assertEqual(response_a.context["total_count"], 1)

        # Candidate B logs in
        self.client.login(username="candidate_b", password="password456")
        response_b = self.client.get(reverse("candidates:my_applications"))
        self.assertEqual(response_b.status_code, 200)
        self.assertContains(response_b, app_b.application_code)
        self.assertNotContains(response_b, app_a.application_code)
        self.assertEqual(response_b.context["total_count"], 1)

    # 12. Application Details Ownership Security (403 Forbidden)
    def test_application_details_ownership_security(self):
        """Candidate B cannot view Candidate A's application details (403 Forbidden)."""
        app_a = Application.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            status=Application.Status.INTERVIEW_SCHEDULED,
        )

        # Candidate A views -> 200 OK
        self.client.login(username="candidate_a", password="password123")
        response = self.client.get(reverse("candidates:application_details", args=[app_a.application_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, app_a.application_code)

        # Candidate B views -> 403 Forbidden
        self.client.login(username="candidate_b", password="password456")
        response_b = self.client.get(reverse("candidates:application_details", args=[app_a.application_id]))
        self.assertEqual(response_b.status_code, 403)

    # 13. Application Status Tamper Prevention (Read-Only)
    def test_application_status_tamper_prevention(self):
        """Candidate cannot modify application status via POST to application details."""
        app_a = Application.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            status=Application.Status.APPLIED,
        )

        self.client.login(username="candidate_a", password="password123")
        # Attempt to forge POST changing status to SELECTED
        response = self.client.post(
            reverse("candidates:application_details", args=[app_a.application_id]),
            {"status": "SELECTED"},
        )
        app_a.refresh_from_db()
        # Status must remain unchanged (APPLIED)
        self.assertEqual(app_a.status, Application.Status.APPLIED)

    # 14. Application Resume Download Ownership
    def test_application_resume_download_ownership(self):
        """Only the owning candidate can download their application resume."""
        app_a = Application.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            resume=SimpleUploadedFile("alice_app_cv.pdf", b"%PDF-1.4 App CV", content_type="application/pdf"),
            status=Application.Status.APPLIED,
        )

        # Candidate A downloads -> 200 OK
        self.client.login(username="candidate_a", password="password123")
        response = self.client.get(reverse("candidates:application_resume_download", args=[app_a.application_id]))
        self.assertEqual(response.status_code, 200)

        # Candidate B downloads -> 403 Forbidden
        self.client.login(username="candidate_b", password="password456")
        response_b = self.client.get(reverse("candidates:application_resume_download", args=[app_a.application_id]))
        self.assertEqual(response_b.status_code, 403)


# ==============================================================================
# HR RECRUITMENT STATUS INTEGRATION & NOTIFICATIONS TESTS
# ==============================================================================
class HRRecruitmentStatusIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.dept = Department.objects.create(name="IT & Engineering", code="ENG")
        self.job = Job.objects.create(
            title="Senior Python Engineer",
            department=self.dept,
            status=Job.Status.OPEN,
            experience_required="3-5 Years",
        )

        self.user = User.objects.create_user(
            username="candidate_hr_test",
            email="hr.test@example.com",
            password="testpassword123",
            first_name="Priya",
            last_name="Nair",
        )
        self.candidate = Candidate.objects.create(
            user=self.user,
            full_name="Priya Nair",
            phone="+91 98765 12345",
            city="Kochi",
        )
        self.doc = CandidateDocument.objects.create(
            candidate=self.candidate,
            resume=SimpleUploadedFile("priya_resume.pdf", b"%PDF-1.4 Resume", content_type="application/pdf"),
        )
        Notification.objects.filter(candidate=self.candidate).delete()

        # Candidate submits initial application (status: APPLIED)
        self.app = Application.objects.create(
            candidate=self.candidate,
            job=self.job,
            status=Application.Status.APPLIED,
        )

    # 1. Transition: APPLIED -> RESUME_REVIEW
    def test_hr_transition_applied_to_resume_review(self):
        """
        HR updates status from APPLIED to RESUME_REVIEW:
        - Signal creates notification titled 'Resume Under Review'
        - Candidate sees 'Resume Under Review' on My Applications
        - Candidate sees 'Resume Under Review' on Application Details
        """
        # HR changes status
        self.app.status = Application.Status.RESUME_REVIEW
        self.app.save()

        # Check signal generated notification
        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, "Resume Under Review")
        self.assertIn("under review", notif.message.lower())

        # Candidate views My Applications
        self.client.login(username="candidate_hr_test", password="testpassword123")
        response = self.client.get(reverse("candidates:my_applications"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resume Under Review")

        # Candidate views Application Details
        details_resp = self.client.get(reverse("candidates:application_details", args=[self.app.application_id]))
        self.assertEqual(details_resp.status_code, 200)
        self.assertContains(details_resp, "Resume Under Review")

    # 2. Transition: RESUME_REVIEW -> SHORTLISTED
    def test_hr_transition_resume_review_to_shortlisted(self):
        """
        HR updates status from RESUME_REVIEW to SHORTLISTED:
        - Signal creates notification titled 'Application Shortlisted'
        - Candidate sees 'Shortlisted' on My Applications
        - Dashboard shortlisted metric increments
        """
        self.app.status = Application.Status.RESUME_REVIEW
        self.app.save()

        # HR shortlists the candidate
        self.app.status = Application.Status.SHORTLISTED
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Application Shortlisted")
        self.assertIn("shortlisted", notif.message.lower())

        self.client.login(username="candidate_hr_test", password="testpassword123")
        response = self.client.get(reverse("candidates:my_applications"))
        self.assertContains(response, "Shortlisted")

        # Dashboard check
        dash_resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertEqual(dash_resp.context["shortlisted_count"], 1)

    # 3. Transition: SHORTLISTED -> APTITUDE_TEST
    def test_hr_transition_shortlisted_to_aptitude_test(self):
        """
        HR assigns Aptitude Test:
        - Signal creates notification titled 'Aptitude Test Assigned'
        - Application Details displays Aptitude Assessment banner
        """
        self.app.status = Application.Status.APTITUDE_TEST
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Aptitude Test Assigned")
        self.assertEqual(notif.notification_type, Notification.NotificationType.APTITUDE)

        self.client.login(username="candidate_hr_test", password="testpassword123")
        details_resp = self.client.get(reverse("candidates:application_details", args=[self.app.application_id]))
        self.assertContains(details_resp, "Aptitude Assessment Stage")

    # 4. Transition: APTITUDE_TEST -> INTERVIEW_SCHEDULED
    def test_hr_transition_aptitude_test_to_interview_scheduled(self):
        """
        HR schedules interview:
        - Signal creates notification titled 'Interview Scheduled'
        - Candidate sees 'Interview Scheduled' on My Applications and Details
        """
        self.app.status = Application.Status.INTERVIEW_SCHEDULED
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Interview Scheduled")
        self.assertEqual(notif.notification_type, Notification.NotificationType.INTERVIEW)

        self.client.login(username="candidate_hr_test", password="testpassword123")
        details_resp = self.client.get(reverse("candidates:application_details", args=[self.app.application_id]))
        self.assertContains(details_resp, "Interview Scheduled")

    # 5. Transition: INTERVIEW_SCHEDULED -> SELECTED
    def test_hr_transition_to_selected(self):
        """
        HR marks candidate as SELECTED:
        - Signal creates notification titled 'Application Selected'
        - Candidate views details: Candidate Selected card is shown
        """
        self.app.status = Application.Status.SELECTED
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Application Selected")
        self.assertIn("selected", notif.message.lower())

        self.client.login(username="candidate_hr_test", password="testpassword123")
        details_resp = self.client.get(reverse("candidates:application_details", args=[self.app.application_id]))
        self.assertContains(details_resp, "Candidate Selected")

    # 6. Transition: SHORTLISTED -> REJECTED
    def test_hr_transition_to_rejected(self):
        """
        HR marks candidate as REJECTED:
        - Signal creates notification titled 'Application Decision'
        - Candidate views details: Professional rejection card is shown
        """
        self.app.status = Application.Status.REJECTED
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Application Decision")
        self.assertIn("reviewed", notif.message.lower())

        self.client.login(username="candidate_hr_test", password="testpassword123")
        details_resp = self.client.get(reverse("candidates:application_details", args=[self.app.application_id]))
        self.assertContains(details_resp, "Application Decision")

    # 7. Dashboard Live Synchronization
    def test_dashboard_reflects_hr_status_changes(self):
        """Dashboard shows live application count, shortlisted count, and recent applications with HR status."""
        self.client.login(username="candidate_hr_test", password="testpassword123")

        # Change status to RESUME_REVIEW
        self.app.status = Application.Status.RESUME_REVIEW
        self.app.save()

        dash_resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertEqual(dash_resp.context["total_applications_count"], 1)
        self.assertContains(dash_resp, "Resume Under Review")

    # 8. Notifications List and Mark All Read
    def test_notifications_page_and_mark_all_read(self):
        """Candidate views notifications triggered by HR and marks all as read."""
        # Trigger 2 status changes
        self.app.status = Application.Status.RESUME_REVIEW
        self.app.save()
        self.app.status = Application.Status.SHORTLISTED
        self.app.save()

        self.client.login(username="candidate_hr_test", password="testpassword123")

        # View notifications page
        notif_resp = self.client.get(reverse("candidates:notifications"))
        self.assertEqual(notif_resp.status_code, 200)
        self.assertContains(notif_resp, "Resume Under Review")
        self.assertContains(notif_resp, "Application Shortlisted")
        self.assertEqual(notif_resp.context["unread_count"], 2)

        # Mark all as read
        post_read = self.client.post(reverse("candidates:notifications_mark_all_read"))
        self.assertEqual(post_read.status_code, 302)
        self.assertEqual(Notification.objects.filter(candidate=self.candidate, is_read=False).count(), 0)

    # 9. Security: Candidate Cannot Modify Status
    def test_candidate_cannot_modify_own_status(self):
        """Candidate POSTing to application details cannot tamper with status."""
        self.client.login(username="candidate_hr_test", password="testpassword123")

        response = self.client.post(
            reverse("candidates:application_details", args=[self.app.application_id]),
            {"status": "SELECTED"},
        )
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, Application.Status.APPLIED)


# ==============================================================================
# CANDIDATE NOTIFICATION AND EMAIL BACKEND TESTS
# ==============================================================================
class CandidateNotificationAndEmailBackendTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="notif_candidate",
            email="notif.candidate@example.com",
            password="testpassword123",
            first_name="Priya",
            last_name="Nair",
        )
        self.candidate = Candidate.objects.create(
            user=self.user,
            full_name="Priya Nair",
            phone="+91 98765 11111",
        )
        # Clear welcome notification from setup to start with clean unread count
        Notification.objects.filter(candidate=self.candidate).delete()

        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.job = Job.objects.create(
            title="Python Backend Developer",
            department=self.dept,
            location="Kochi, Kerala",
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.OPEN,
        )
        self.app = Application.objects.create(
            candidate=self.candidate,
            job=self.job,
            status=Application.Status.APPLIED,
        )

    # 1. Registration Notification & Unread Count
    def test_candidate_registration_creates_notification(self):
        """Registering a new account generates a welcome notification with unread count = 1."""
        response = self.client.post(
            reverse("candidates:register"),
            {
                "name": "New Candidate",
                "email": "new.candidate@example.com",
                "phone": "+91 99999 88888",
                "password": "SecurePassword@123",
                "confirm_password": "SecurePassword@123",
            },
        )
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(email="new.candidate@example.com")
        new_cand = Candidate.objects.get(user=new_user)
        notifs = Notification.objects.filter(candidate=new_cand)
        self.assertEqual(notifs.count(), 1)
        self.assertEqual(notifs.first().title, "Welcome to HRMS Portal")
        self.assertEqual(notifs.first().notification_type, Notification.NotificationType.REGISTRATION)
        self.assertFalse(notifs.first().is_read)

    # 2. Application Submitted Notification & Email
    def test_application_submitted_notification_and_email(self):
        """Applying for a job creates an in-app notification and dispatches a confirmation email."""
        mail.outbox = []
        new_job = Job.objects.create(
            title="Cloud Architect",
            department=self.dept,
            location="Bangalore",
            status=Job.Status.OPEN,
        )
        # Create resume for candidate
        doc, _ = CandidateDocument.objects.get_or_create(candidate=self.candidate)
        doc.resume = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 mock resume content", content_type="application/pdf")
        doc.save()

        self.client.login(username="notif_candidate", password="testpassword123")
        resp = self.client.post(reverse("candidates:job_apply", args=[new_job.pk]))
        self.assertEqual(resp.status_code, 200)

        # Check notification
        app_notif = Notification.objects.filter(
            candidate=self.candidate,
            notification_type=Notification.NotificationType.APPLICATION,
            title="Application Submitted",
        ).first()
        self.assertIsNotNone(app_notif)
        self.assertIn("Cloud Architect", app_notif.message)

        # Check confirmation email
        self.assertTrue(len(mail.outbox) >= 1)
        sent_email = mail.outbox[-1]
        self.assertIn("Cloud Architect", sent_email.subject)
        self.assertIn("notif.candidate@example.com", sent_email.to)

    # 3. Resume Under Review Notification
    def test_resume_under_review_notification(self):
        """HR changing status to RESUME_REVIEW creates 'Resume Under Review' notification."""
        self.app.status = Application.Status.RESUME_REVIEW
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Resume Under Review")
        self.assertIn("under review", notif.message.lower())

    # 4. Shortlisted Notification & Email
    def test_shortlisted_notification_and_email(self):
        """HR changing status to SHORTLISTED creates notification and sends email."""
        mail.outbox = []
        self.app.status = Application.Status.SHORTLISTED
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Application Shortlisted")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Shortlisted", mail.outbox[0].subject)
        self.assertIn("notif.candidate@example.com", mail.outbox[0].to)

    # 5. Aptitude Test Scheduled Notification & Email
    def test_aptitude_test_scheduled_notification_and_email(self):
        """HR assigning Aptitude Test creates notification and sends email."""
        mail.outbox = []
        self.app.status = Application.Status.APTITUDE_TEST
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Aptitude Test Assigned")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Aptitude", mail.outbox[0].subject)

    # 6. Interview Scheduled Notification & Email
    def test_interview_scheduled_notification_and_email(self):
        """Creating an Interview record directly or setting status creates notification and sends email."""
        mail.outbox = []
        interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            application=self.app,
            interview_round="Technical Round 1",
            date=date.today() + timedelta(days=3),
            time="11:00:00",
            mode=Interview.Mode.ONLINE,
            meeting_link="https://meet.google.com/abc-defg-hij",
            status=Interview.Status.SCHEDULED,
        )

        notif = Notification.objects.filter(candidate=self.candidate, notification_type=Notification.NotificationType.INTERVIEW).first()
        self.assertIsNotNone(notif)
        self.assertIn("Interview Scheduled", notif.title)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Interview Scheduled", mail.outbox[0].subject)
        self.assertIn("https://meet.google.com/abc-defg-hij", mail.outbox[0].body)

    # 7. Selected Notification & Email
    def test_selected_notification_and_email(self):
        """HR marking application as SELECTED creates notification and sends offer email."""
        mail.outbox = []
        self.app.status = Application.Status.SELECTED
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Application Selected")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Selection Offer", mail.outbox[0].subject)

    # 8. Rejected Notification & Email
    def test_rejected_notification_and_email(self):
        """HR marking application as REJECTED creates notification and sends decision email."""
        mail.outbox = []
        self.app.status = Application.Status.REJECTED
        self.app.save()

        notif = Notification.objects.filter(candidate=self.candidate).order_by("-created_at").first()
        self.assertEqual(notif.title, "Application Decision")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Status Update", mail.outbox[0].subject)

    # 9. Announcement Notification
    def test_announcement_notification_and_filtering(self):
        """Broadcast announcement creates notification displayed under announcements category."""
        from .signals import broadcast_announcement
        broadcast_announcement(
            title="System Maintenance Scheduled",
            message="The recruitment portal will be under scheduled maintenance tonight from 11 PM to 1 AM.",
            candidate=self.candidate,
        )
        notif = Notification.objects.filter(
            candidate=self.candidate,
            notification_type=Notification.NotificationType.GENERAL,
        ).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, "System Maintenance Scheduled")

        self.client.login(username="notif_candidate", password="testpassword123")
        resp = self.client.get(reverse("candidates:notifications") + "?category=announcements")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "System Maintenance Scheduled")

    # 10. Header Bell Unread Count Context Processor
    def test_header_bell_displays_real_unread_count(self):
        """Context processor returns accurate unread count and header displays badge."""
        Notification.objects.create(
            candidate=self.candidate,
            title="Update 1",
            message="Message 1",
            is_read=False,
        )
        Notification.objects.create(
            candidate=self.candidate,
            title="Update 2",
            message="Message 2",
            is_read=False,
        )
        self.client.login(username="notif_candidate", password="testpassword123")
        resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["unread_notifications_count"], 2)
        self.assertContains(resp, 'id="headerNotificationCount">2</span>')

    # 11. Mark Single Notification as Read
    def test_mark_single_notification_as_read(self):
        """Marking a single notification as read marks is_read=True and decrements unread count."""
        notif = Notification.objects.create(
            candidate=self.candidate,
            title="Action required",
            message="Check your profile details.",
            link="/profile/",
            is_read=False,
        )
        self.client.login(username="notif_candidate", password="testpassword123")

        # Mark read with stay=1
        resp = self.client.get(reverse("candidates:notification_mark_read", args=[notif.pk]) + "?stay=1")
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse("candidates:notifications"))

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    # 12. Mark All Notifications as Read
    def test_mark_all_notifications_as_read(self):
        """Mark all as read resets candidate's unread notifications to 0."""
        for i in range(3):
            Notification.objects.create(
                candidate=self.candidate,
                title=f"Notif {i}",
                message=f"Message {i}",
                is_read=False,
            )
        self.client.login(username="notif_candidate", password="testpassword123")
        resp = self.client.post(reverse("candidates:notifications_mark_all_read"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Notification.objects.filter(candidate=self.candidate, is_read=False).count(), 0)

    # 13. Candidate Isolation Security
    def test_notification_candidate_isolation_security(self):
        """Candidate B cannot mark read Candidate A's notification."""
        other_user = User.objects.create_user(
            username="other_candidate",
            email="other@example.com",
            password="testpassword123",
        )
        other_cand = Candidate.objects.create(user=other_user, full_name="Other Candidate")
        cand_a_notif = Notification.objects.create(
            candidate=self.candidate,
            title="Confidential",
            message="Private data",
            is_read=False,
        )

        self.client.login(username="other_candidate", password="testpassword123")
        resp = self.client.get(reverse("candidates:notification_mark_read", args=[cand_a_notif.pk]))
        self.assertEqual(resp.status_code, 403)
        cand_a_notif.refresh_from_db()
        self.assertFalse(cand_a_notif.is_read)

    # 14. Email Settings Security
    def test_email_configuration_security(self):
        """Settings configure email without hardcoded passwords and have default from email."""
        from django.conf import settings
        self.assertTrue(hasattr(settings, "EMAIL_BACKEND"))
        self.assertTrue(hasattr(settings, "DEFAULT_FROM_EMAIL"))
        # Verify no hardcoded password in settings module
        self.assertEqual(getattr(settings, "EMAIL_HOST_PASSWORD", ""), "")


class CandidateAptitudeTestBackendTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username="aptitude_user_a",
            email="aptitude_a@example.com",
            password="testpassword123",
            first_name="Alice",
            last_name="Test",
        )
        self.candidate_a = Candidate.objects.create(user=self.user_a, full_name="Alice Test")

        self.user_b = User.objects.create_user(
            username="aptitude_user_b",
            email="aptitude_b@example.com",
            password="testpassword123",
            first_name="Bob",
            last_name="Test",
        )
        self.candidate_b = Candidate.objects.create(user=self.user_b, full_name="Bob Test")

        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.job = Job.objects.create(
            title="Python Developer",
            description="Python developer role.",
            department=self.dept,
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.OPEN,
        )

        # Create Aptitude Test
        self.test = AptitudeTest.objects.create(
            title="Python Technical Assessment",
            job=self.job,
            description="Assessment covering core Python concepts.",
            duration_minutes=30,
            total_questions=4,
            passing_percentage=50,
            status=AptitudeTest.Status.ACTIVE,
            is_active=True,
        )
        # Assign candidate_a to test
        self.test.assigned_candidates.add(self.candidate_a)

        # Create 4 Questions with answers: A, B, C, D
        self.q1 = Question.objects.create(
            test=self.test,
            question_text="Which keyword defines a function?",
            option_a="def",
            option_b="func",
            option_c="function",
            option_d="define",
            correct_option=Question.CorrectOption.A,
        )
        self.q2 = Question.objects.create(
            test=self.test,
            question_text="Which type is immutable?",
            option_a="list",
            option_b="tuple",
            option_c="dict",
            option_d="set",
            correct_option=Question.CorrectOption.B,
        )
        self.q3 = Question.objects.create(
            test=self.test,
            question_text="Which module is used for regex?",
            option_a="regex",
            option_b="pyregex",
            option_c="re",
            option_d="strings",
            correct_option=Question.CorrectOption.C,
        )
        self.q4 = Question.objects.create(
            test=self.test,
            question_text="Which statement exits a loop prematurely?",
            option_a="exit",
            option_b="stop",
            option_c="quit",
            option_d="break",
            correct_option=Question.CorrectOption.D,
        )

    def test_property_aliases(self):
        """Verifies property aliases match prompt specification exactly."""
        self.assertEqual(self.test.duration, 30)
        self.assertEqual(self.test.passing_score, 50)
        self.assertEqual(self.q1.correct_answer, "A")

        result = TestResult.objects.create(
            candidate=self.candidate_a,
            test=self.test,
            total_questions=4,
            correct_answers=3,
            incorrect_answers=1,
            score_percentage=75.0,
            is_passed=True,
        )
        self.assertEqual(result.score, 3)
        self.assertEqual(result.percentage, 75.0)
        self.assertTrue(result.passed)
        self.assertIsNotNone(result.submitted_at)

    def test_aptitude_list_requires_login(self):
        """Unauthenticated candidate is redirected to login."""
        resp = self.client.get(reverse("candidates:aptitude_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_aptitude_list_view_shows_assigned_test(self):
        """Candidate A sees the assigned test in Available tab."""
        self.client.login(username="aptitude_user_a", password="testpassword123")
        resp = self.client.get(reverse("candidates:aptitude_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python Technical Assessment")
        self.assertEqual(resp.context["available_count"], 1)
        self.assertEqual(resp.context["completed_count"], 0)

    def test_open_test_environment_never_exposes_correct_answers(self):
        """Test view context and template payload MUST NOT include correct answers."""
        self.client.login(username="aptitude_user_a", password="testpassword123")
        resp = self.client.get(reverse("candidates:aptitude_test", args=[self.test.test_id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Which keyword defines a function?")

        # Check payload does not contain correct_option or correct_answer
        questions_json = resp.context["questions_json"]
        self.assertNotIn("correct_option", questions_json)
        self.assertNotIn("correct_answer", questions_json)
        self.assertNotIn('"correct"', questions_json)

    def test_open_test_unauthorized_candidate_blocked(self):
        """Candidate B (not assigned and not applied) cannot open test."""
        self.client.login(username="aptitude_user_b", password="testpassword123")
        resp = self.client.get(reverse("candidates:aptitude_test", args=[self.test.test_id]))
        self.assertEqual(resp.status_code, 403)

    def test_backend_calculates_pass_score(self):
        """Candidate answers 3 of 4 correctly (75% >= 50%) -> PASSED calculated on backend."""
        import json
        self.client.login(username="aptitude_user_a", password="testpassword123")
        answers = {
            str(self.q1.question_id): "A",  # Correct
            str(self.q2.question_id): "B",  # Correct
            str(self.q3.question_id): "C",  # Correct
            str(self.q4.question_id): "A",  # Wrong (correct is D)
        }
        resp = self.client.post(
            reverse("candidates:aptitude_submit", args=[self.test.test_id]),
            {"answers_json": json.dumps(answers)},
        )
        self.assertEqual(resp.status_code, 302)

        result = TestResult.objects.get(candidate=self.candidate_a, test=self.test)
        self.assertEqual(result.correct_answers, 3)
        self.assertEqual(result.incorrect_answers, 1)
        self.assertEqual(result.score_percentage, 75.0)
        self.assertTrue(result.is_passed)
        self.assertRedirects(resp, reverse("candidates:aptitude_result", args=[result.result_id]))

    def test_backend_calculates_fail_score(self):
        """Candidate answers 1 of 4 correctly (25% < 50%) -> FAILED."""
        import json
        self.client.login(username="aptitude_user_a", password="testpassword123")
        answers = {
            str(self.q1.question_id): "A",  # Correct
            str(self.q2.question_id): "C",  # Wrong
            str(self.q3.question_id): "A",  # Wrong
            str(self.q4.question_id): "A",  # Wrong
        }
        self.client.post(
            reverse("candidates:aptitude_submit", args=[self.test.test_id]),
            {"answers_json": json.dumps(answers)},
        )
        result = TestResult.objects.get(candidate=self.candidate_a, test=self.test)
        self.assertEqual(result.correct_answers, 1)
        self.assertEqual(result.score_percentage, 25.0)
        self.assertFalse(result.is_passed)

    def test_client_cannot_tamper_score(self):
        """Score sent from client is discarded; backend calculation is authoritative."""
        import json
        self.client.login(username="aptitude_user_a", password="testpassword123")
        # Attacker tries to send score=100 and passed=True with all wrong answers
        answers = {
            str(self.q1.question_id): "D",  # Wrong
            str(self.q2.question_id): "D",  # Wrong
            str(self.q3.question_id): "D",  # Wrong
            str(self.q4.question_id): "A",  # Wrong
        }
        self.client.post(
            reverse("candidates:aptitude_submit", args=[self.test.test_id]),
            {
                "answers_json": json.dumps(answers),
                "score": "100",
                "percentage": "100.0",
                "passed": "true",
            },
        )
        result = TestResult.objects.get(candidate=self.candidate_a, test=self.test)
        self.assertEqual(result.correct_answers, 0)
        self.assertEqual(result.score_percentage, 0.0)
        self.assertFalse(result.is_passed)

    def test_prevent_duplicate_test_submission(self):
        """Prevent candidate from submitting the same assessment twice."""
        import json
        self.client.login(username="aptitude_user_a", password="testpassword123")
        answers = {str(self.q1.question_id): "A"}

        # First submission
        resp1 = self.client.post(
            reverse("candidates:aptitude_submit", args=[self.test.test_id]),
            {"answers_json": json.dumps(answers)},
        )
        self.assertEqual(resp1.status_code, 302)
        self.assertEqual(TestResult.objects.filter(candidate=self.candidate_a, test=self.test).count(), 1)

        # Second attempt
        resp2 = self.client.post(
            reverse("candidates:aptitude_submit", args=[self.test.test_id]),
            {"answers_json": json.dumps(answers)},
        )
        self.assertEqual(resp2.status_code, 302)
        # Count remains 1
        self.assertEqual(TestResult.objects.filter(candidate=self.candidate_a, test=self.test).count(), 1)

    def test_test_submission_creates_notification(self):
        """Candidate receives an in-app notification after test submission."""
        import json
        self.client.login(username="aptitude_user_a", password="testpassword123")
        self.client.post(
            reverse("candidates:aptitude_submit", args=[self.test.test_id]),
            {"answers_json": json.dumps({str(self.q1.question_id): "A"})},
        )
        notif = Notification.objects.filter(
            candidate=self.candidate_a,
            notification_type=Notification.NotificationType.APTITUDE,
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Python Technical Assessment", notif.message)

    def test_test_result_candidate_isolation_security(self):
        """Candidate B cannot view Candidate A's result card (403 PermissionDenied)."""
        result_a = TestResult.objects.create(
            candidate=self.candidate_a,
            test=self.test,
            total_questions=4,
            correct_answers=4,
            score_percentage=100.0,
            is_passed=True,
        )
        # Candidate B attempts to view Candidate A's result
        self.client.login(username="aptitude_user_b", password="testpassword123")
        resp = self.client.get(reverse("candidates:aptitude_result", args=[result_a.result_id]))
        self.assertEqual(resp.status_code, 403)


class CandidateInterviewBackendTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username="interview_user_a",
            email="interview_a@example.com",
            password="testpassword123",
            first_name="Alice",
            last_name="Interview",
        )
        self.candidate_a = Candidate.objects.create(user=self.user_a, full_name="Alice Interview")

        self.user_b = User.objects.create_user(
            username="interview_user_b",
            email="interview_b@example.com",
            password="testpassword123",
            first_name="Bob",
            last_name="Interview",
        )
        self.candidate_b = Candidate.objects.create(user=self.user_b, full_name="Bob Interview")

        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.job = Job.objects.create(
            title="Senior Python Engineer",
            description="Python Engineering role.",
            department=self.dept,
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.OPEN,
        )

        today = date.today()
        # Upcoming scheduled interview
        self.upcoming_interview = Interview.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            interview_round="Technical Round 1",
            date=today + timedelta(days=3),
            time="11:00:00",
            mode=Interview.Mode.ONLINE,
            interviewer="Senior Tech Lead",
            meeting_link="https://meet.google.com/xyz-test-link",
            instructions="Prepare data structures and system design.",
            status=Interview.Status.SCHEDULED,
        )

        # Previous completed interview
        self.previous_interview = Interview.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            interview_round="HR Screening Round",
            date=today - timedelta(days=7),
            time="14:00:00",
            mode=Interview.Mode.ONLINE,
            interviewer="HR Manager",
            instructions="Culture fit screening.",
            status=Interview.Status.COMPLETED,
        )

    def test_interview_list_requires_authentication(self):
        """Unauthenticated candidate is redirected to login."""
        resp = self.client.get(reverse("candidates:interview_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_interview_list_displays_upcoming_and_previous(self):
        """Candidate A sees upcoming interview and previous interview."""
        self.client.login(username="interview_user_a", password="testpassword123")
        resp = self.client.get(reverse("candidates:interview_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "candidates/interviews/interview_list.html")
        self.assertEqual(resp.context["upcoming_count"], 1)
        self.assertEqual(resp.context["completed_count"], 1)
        self.assertContains(resp, "Technical Round 1")
        self.assertContains(resp, "HR Screening Round")
        self.assertContains(resp, "https://meet.google.com/xyz-test-link")

    def test_interview_details_view(self):
        """Candidate A views detailed interview round specifications."""
        self.client.login(username="interview_user_a", password="testpassword123")
        resp = self.client.get(reverse("candidates:interview_details", args=[self.upcoming_interview.interview_id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "candidates/interviews/interview_details.html")
        self.assertContains(resp, "Technical Round 1")
        self.assertContains(resp, "Prepare data structures and system design.")
        self.assertContains(resp, "Senior Tech Lead")
        self.assertContains(resp, "https://meet.google.com/xyz-test-link")

    def test_interview_candidate_isolation_security(self):
        """Candidate B cannot view Candidate A's interview (403 PermissionDenied)."""
        self.client.login(username="interview_user_b", password="testpassword123")
        resp = self.client.get(reverse("candidates:interview_details", args=[self.upcoming_interview.interview_id]))
        self.assertEqual(resp.status_code, 403)

    def test_hr_scheduling_triggers_notification_and_email(self):
        """When HR creates a scheduled interview, candidate gets in-app notif and email."""
        mail.outbox.clear()
        new_interview = Interview.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            interview_round="Director Round",
            date=date.today() + timedelta(days=5),
            time="16:00:00",
            mode=Interview.Mode.ONLINE,
            interviewer="Engineering Director",
            status=Interview.Status.SCHEDULED,
        )
        notif = Notification.objects.filter(
            candidate=self.candidate_a,
            notification_type=Notification.NotificationType.INTERVIEW,
            title="Interview Scheduled",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("Director Round", notif.message)
        self.assertIn(str(new_interview.interview_id), notif.link)

        # Verify email dispatched
        self.assertGreaterEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[-1]
        self.assertIn("Interview Scheduled", sent_email.subject)
        self.assertIn("Director Round", sent_email.body)

    def test_hr_rescheduling_triggers_notification(self):
        """When HR reschedules an interview, candidate receives a rescheduled notification."""
        self.upcoming_interview.status = Interview.Status.RESCHEDULED
        self.upcoming_interview.date = date.today() + timedelta(days=4)
        self.upcoming_interview.save()

        notif = Notification.objects.filter(
            candidate=self.candidate_a,
            notification_type=Notification.NotificationType.INTERVIEW,
            title="Interview Rescheduled",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("rescheduled", notif.message.lower())


class CandidateDashboardBackendTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="dash_user",
            email="dash@example.com",
            password="testpassword123",
            first_name="Diana",
            last_name="Prince",
        )
        self.candidate = Candidate.objects.create(
            user=self.user,
            full_name="Diana Prince",
            city="Themyscira",
        )
        # Add skill
        CandidateSkill.objects.create(candidate=self.candidate, skill_name="Python")

        self.dept = Department.objects.create(name="AI Lab", code="AI")
        self.job1 = Job.objects.create(
            title="Senior Python Architect",
            description="Python & Django backend architecture.",
            skills_required="Python, Django, PostgreSQL",
            department=self.dept,
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.OPEN,
        )
        self.job2 = Job.objects.create(
            title="Frontend React Engineer",
            description="React frontend vacancy.",
            skills_required="React, JavaScript",
            department=self.dept,
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.OPEN,
        )

        # Create Applications (1 APPLIED, 1 SHORTLISTED)
        self.app1 = Application.objects.create(
            candidate=self.candidate,
            job=self.job1,
            status=Application.Status.SHORTLISTED,
        )
        self.app2 = Application.objects.create(
            candidate=self.candidate,
            job=self.job2,
            status=Application.Status.APPLIED,
        )

        # Create Interview (1 Upcoming)
        today = date.today()
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job1,
            application=self.app1,
            interview_round="Technical Round 1",
            date=today + timedelta(days=2),
            time="11:00:00",
            mode=Interview.Mode.ONLINE,
            interviewer="Dr. Tech Lead",
            meeting_link="https://meet.google.com/dash-live-room",
            status=Interview.Status.SCHEDULED,
        )

        # Create Notifications (3 unread)
        for i in range(3):
            Notification.objects.create(
                candidate=self.candidate,
                title=f"Update {i}",
                message=f"Notice message {i}",
                is_read=False,
            )

        # Create Company Announcement
        Notification.objects.create(
            candidate=self.candidate,
            title="Q3 Annual Hiring Drive",
            message="Applications for engineering roles are now live.",
            notification_type=Notification.NotificationType.GENERAL,
        )

    def test_dashboard_requires_login(self):
        """Unauthenticated candidate is redirected to login."""
        resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_dashboard_dynamic_metrics_from_db(self):
        """All statistics in dashboard come directly from PostgreSQL queries."""
        self.client.login(username="dash_user", password="testpassword123")
        resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "candidates/candidate/dashboard.html")

        # Context metrics verification
        expected_unread = Notification.objects.filter(candidate=self.candidate, is_read=False).count()
        self.assertEqual(resp.context["candidate"].full_name, "Diana Prince")
        self.assertEqual(resp.context["total_applications_count"], 2)
        self.assertEqual(resp.context["shortlisted_count"], 1)
        self.assertEqual(resp.context["upcoming_interviews_count"], 1)
        self.assertEqual(resp.context["unread_notifications_count"], expected_unread)
        self.assertGreater(resp.context["completion_pct"], 0)

        # Verify rendered HTML contains exact DB values
        content = resp.content.decode()
        self.assertContains(resp, "Diana Prince")
        self.assertContains(resp, "Senior Python Architect")
        self.assertContains(resp, "Technical Round 1")
        self.assertContains(resp, "https://meet.google.com/dash-live-room")
        self.assertContains(resp, "Q3 Annual Hiring Drive")
        self.assertIn("dashboardTotalApps", content)
        self.assertIn("dashboardShortlisted", content)
        self.assertIn("dashboardInterviews", content)
        self.assertIn("dashboardUnreadNotifs", content)

    def test_dashboard_recommended_jobs_matches_skills(self):
        """Recommended jobs prioritize vacancies matching candidate's skills."""
        self.client.login(username="dash_user", password="testpassword123")
        resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(resp.status_code, 200)

        recommended = resp.context["recommended_jobs"]
        self.assertGreaterEqual(len(recommended), 1)
        # Senior Python Architect matches skill 'Python'
        self.assertTrue(any(j.title == "Senior Python Architect" for j in recommended))

    def test_dashboard_recent_applications_order(self):
        """Recent applications display latest submitted applications."""
        self.client.login(username="dash_user", password="testpassword123")
        resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(resp.status_code, 200)

        recent = resp.context["recent_applications"]
        self.assertEqual(len(recent), 2)
        # Must be ordered by applied_at desc
        self.assertGreaterEqual(recent[0].applied_at, recent[1].applied_at)


# ==============================================================================
# CANDIDATE SELECTION & EMPLOYEE MODULE INTEGRATION TESTS
# ==============================================================================
class CandidateSelectionEmployeeIntegrationTests(TestCase):
    """
    Tests the integration between Candidate selection (status = SELECTED)
    and the existing Employee module (employee_table).
    
    Validates:
    1. No duplicate Employee model or conflicting tables created.
    2. Selected candidates identified via candidate_id and user_id.
    3. Complete HR Onboarding dossier generated.
    4. Selection does NOT directly create employee records (lifecycle stage transition).
    5. HR Onboarding workflow successfully inserts into employee_table.
    6. Candidate portal reflects transition to employee lifecycle.
    """

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="selected_candidate",
            email="selected@example.com",
            password="testpassword123",
            first_name="Selena",
            last_name="Gomez",
        )
        self.staff_user = self.User.objects.create_user(
            username="hr_admin",
            email="hr@example.com",
            password="testpassword123",
            is_staff=True,
        )
        self.department = Department.objects.create(
            name="Cloud Engineering",
            code="CLOUD",
            description="Cloud and DevOps operations",
        )
        self.job = Job.objects.create(
            title="Senior DevOps Engineer",
            department=self.department,
            job_type=Job.JobType.FULL_TIME,
            experience_required="3-5 Years",
            location="Bangalore (Hybrid)",
            salary_display="₹18 - 24 LPA",
            description="Manage Kubernetes clusters and AWS infrastructure.",
            status=Job.Status.OPEN,
        )
        self.candidate = Candidate.objects.create(
            user=self.user,
            full_name="Selena Gomez",
            phone="+91 9876543210",
            gender=Candidate.Gender.FEMALE,
            address="404 DevOps Way",
            city="Bangalore",
            state="Karnataka",
            pincode="560001",
        )
        CandidateEducation.objects.create(
            candidate=self.candidate,
            qualification_type="B.Tech Computer Science",
            institution="National Institute of Technology",
            board_or_university="NIT",
            year="2018 - 2022",
            percentage_or_cgpa="8.9 CGPA",
        )
        CandidateSkill.objects.create(candidate=self.candidate, skill_name="Kubernetes")
        CandidateSkill.objects.create(candidate=self.candidate, skill_name="AWS")
        CandidateSkill.objects.create(candidate=self.candidate, skill_name="Terraform")

        self.docs = CandidateDocument.objects.create(
            candidate=self.candidate,
            resume=SimpleUploadedFile("selena_devops_resume.pdf", b"%PDF-1.4 devops resume content", content_type="application/pdf"),
            id_proof=SimpleUploadedFile("aadhaar_card.pdf", b"%PDF-1.4 id proof content", content_type="application/pdf"),
        )
        self.candidate.update_profile_completion()

        self.application = Application.objects.create(
            candidate=self.candidate,
            job=self.job,
            status=Application.Status.APPLIED,
        )

    def test_no_duplicate_employee_model_registered(self):
        """Verifies NO Employee model was defined in candidates app or Django apps."""
        from django.apps import apps
        candidates_models = [m.__name__ for m in apps.get_app_config("candidates").get_models()]
        self.assertNotIn("Employee", candidates_models)
        self.assertNotIn("EmployeeDocument", candidates_models)
        self.assertNotIn("EmployeeReport", candidates_models)
        self.assertNotIn("EmployeePerformance", candidates_models)
        self.assertNotIn("PerformanceWarning", candidates_models)

    def test_employee_table_schema_and_columns_exist(self):
        """Verifies PostgreSQL employee_table has the required 10 columns."""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'employee_table'
                ORDER BY ordinal_position;
            """)
            columns = [r[0] for r in cursor.fetchall()]

        required_columns = [
            "employee_id",
            "candidate_id",
            "user_id",
            "employee_code",
            "department_id",
            "designation",
            "joining_date",
            "employment_status",
            "created_by",
            "created_at",
        ]
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} missing in employee_table")

    def test_candidate_identification_by_candidate_id(self):
        """HR/Admin onboarding can identify candidate by candidate_id."""
        from candidates.onboarding import get_candidate_by_id_or_user
        found = get_candidate_by_id_or_user(candidate_id=self.candidate.candidate_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.pk, self.candidate.pk)
        self.assertEqual(found.full_name, "Selena Gomez")

    def test_candidate_identification_by_user_id(self):
        """HR/Admin onboarding can identify candidate by user_id."""
        from candidates.onboarding import get_candidate_by_id_or_user
        found = get_candidate_by_id_or_user(user_id=self.user.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.pk, self.candidate.pk)
        self.assertEqual(found.user.username, "selected_candidate")

    def test_onboarding_dossier_completeness(self):
        """Onboarding dossier includes personal info, educations, skills, and selected job."""
        from candidates.onboarding import get_candidate_onboarding_dossier
        # Transition to SELECTED
        self.application.status = Application.Status.SELECTED
        self.application.save()

        dossier = get_candidate_onboarding_dossier(candidate_id=self.candidate.candidate_id)
        self.assertIsNotNone(dossier)
        self.assertEqual(dossier["full_name"], "Selena Gomez")
        self.assertEqual(dossier["candidate_id"], self.candidate.candidate_id)
        self.assertEqual(dossier["user_id"], self.user.id)
        self.assertEqual(len(dossier["educations"]), 1)
        self.assertEqual(dossier["educations"][0]["qualification_type"], "B.Tech Computer Science")
        self.assertIn("Kubernetes", dossier["skills"])
        self.assertIn("resume", dossier["documents"])
        self.assertEqual(dossier["selected_application"]["job_title"], "Senior DevOps Engineer")
        self.assertEqual(dossier["selected_application"]["department_name"], "Cloud Engineering")
        self.assertFalse(dossier["is_onboarded"])
        self.assertIn("employee_code", dossier["suggested_employee"])
        self.assertEqual(dossier["suggested_employee"]["designation"], "Senior DevOps Engineer")

    def test_selection_does_not_directly_create_employee(self):
        """
        When HR selects candidate, application status is SELECTED, but
        Candidate module does NOT directly insert into employee_table.
        """
        from candidates.onboarding import is_candidate_onboarded, get_candidate_lifecycle_stage
        self.application.status = Application.Status.SELECTED
        self.application.save()

        # Check candidate properties
        self.candidate.refresh_from_db()
        self.assertTrue(self.candidate.is_selected)
        self.assertFalse(self.candidate.is_onboarded)
        self.assertFalse(is_candidate_onboarded(candidate_id=self.candidate.candidate_id))
        self.assertEqual(self.candidate.lifecycle_stage, "RECRUITMENT_SELECTED")

    def test_onboarding_signal_dispatched_on_selection(self):
        """Signal candidate_selected_for_onboarding is sent when status changes to SELECTED."""
        from candidates.onboarding import candidate_selected_for_onboarding
        signal_received = []

        def handler(sender, application, candidate, job, department, **kwargs):
            signal_received.append((application, candidate, job, department))

        candidate_selected_for_onboarding.connect(handler)
        try:
            self.application.status = Application.Status.SELECTED
            self.application.save()
            self.assertEqual(len(signal_received), 1)
            app, cand, job, dept = signal_received[0]
            self.assertEqual(cand.pk, self.candidate.pk)
            self.assertEqual(job.title, "Senior DevOps Engineer")
            self.assertEqual(dept.name, "Cloud Engineering")
        finally:
            candidate_selected_for_onboarding.disconnect(handler)

    def test_hr_onboarding_creates_employee_record(self):
        """
        HR/Admin onboarding workflow creates record in employee_table,
        concluding recruitment lifecycle and beginning employee lifecycle.
        """
        from candidates.onboarding import (
            create_employee_record,
            get_employee_record,
            is_candidate_onboarded,
            employee_onboarded,
        )

        self.application.status = Application.Status.SELECTED
        self.application.save()

        signal_called = []

        def on_onboard(sender, candidate, employee_record, **kwargs):
            signal_called.append((candidate, employee_record))

        employee_onboarded.connect(on_onboard)
        try:
            emp = create_employee_record(
                candidate_id=self.candidate.candidate_id,
                user_id=self.candidate.user_id,
                employee_code="EMP-2026-9001",
                designation="Senior DevOps Engineer",
                department_id=self.department.department_id,
                created_by=self.staff_user.id,
            )
            self.assertIsNotNone(emp)
            self.assertEqual(emp["employee_code"], "EMP-2026-9001")
            self.assertEqual(emp["candidate_id"], self.candidate.candidate_id)
            self.assertEqual(emp["user_id"], self.user.id)
            self.assertEqual(emp["designation"], "Senior DevOps Engineer")
            self.assertEqual(emp["employment_status"], "ACTIVE")

            # Check signal dispatched
            self.assertEqual(len(signal_called), 1)

            # Check candidate properties
            self.assertTrue(self.candidate.is_onboarded)
            self.assertEqual(self.candidate.lifecycle_stage, "EMPLOYEE_LIFECYCLE")
            retrieved_emp = self.candidate.employee_record
            self.assertEqual(retrieved_emp["employee_code"], "EMP-2026-9001")

            # Check lookup via user_id
            by_user = get_employee_record(user_id=self.user.id)
            self.assertEqual(by_user["employee_code"], "EMP-2026-9001")
        finally:
            employee_onboarded.disconnect(on_onboard)

    def test_duplicate_onboarding_call_returns_existing(self):
        """Calling create_employee_record multiple times returns existing without duplicate rows."""
        from candidates.onboarding import create_employee_record
        emp1 = create_employee_record(
            candidate_id=self.candidate.candidate_id,
            user_id=self.candidate.user_id,
            employee_code="EMP-2026-9002",
        )
        emp2 = create_employee_record(
            candidate_id=self.candidate.candidate_id,
            user_id=self.candidate.user_id,
            employee_code="EMP-2026-9003",
        )
        self.assertEqual(emp1["employee_id"], emp2["employee_id"])
        self.assertEqual(emp1["employee_code"], emp2["employee_code"])

    def test_onboarding_api_view_access(self):
        """Staff can fetch candidate onboarding JSON dossier via API."""
        # Non-staff receives 403 forbidden
        self.client.login(username="selected_candidate", password="testpassword123")
        resp = self.client.get(reverse("candidates:candidate_onboarding_api") + f"?candidate_id={self.candidate.candidate_id}")
        self.assertEqual(resp.status_code, 403)

        # Staff receives 200 JSON
        self.client.login(username="hr_admin", password="testpassword123")
        resp = self.client.get(reverse("candidates:candidate_onboarding_api") + f"?candidate_id={self.candidate.candidate_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["dossier"]["full_name"], "Selena Gomez")

        # By user_id
        resp_user = self.client.get(reverse("candidates:candidate_onboarding_api") + f"?user_id={self.user.id}")
        self.assertEqual(resp_user.status_code, 200)
        self.assertEqual(resp_user.json()["dossier"]["candidate_id"], self.candidate.candidate_id)

    def test_onboarding_dossier_html_view(self):
        """Staff can view candidate onboarding dossier HTML."""
        self.application.status = Application.Status.SELECTED
        self.application.save()
        self.client.login(username="hr_admin", password="testpassword123")
        resp = self.client.get(reverse("candidates:candidate_onboarding_dossier", kwargs={"candidate_id": self.candidate.candidate_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Candidate Onboarding Dossier")
        self.assertContains(resp, "Selena Gomez")
        self.assertContains(resp, "Senior DevOps Engineer")

    def test_complete_onboarding_post_action(self):
        """Staff POST creates employee record and redirects."""
        self.client.login(username="hr_admin", password="testpassword123")
        resp = self.client.post(reverse("candidates:complete_candidate_onboarding", kwargs={"candidate_id": self.candidate.candidate_id}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.candidate.is_onboarded)

    def test_candidate_portal_displays_onboarding_info(self):
        """Candidate portal displays onboarding status and employee record when selected."""
        from candidates.onboarding import create_employee_record
        self.application.status = Application.Status.SELECTED
        self.application.save()

        self.client.login(username="selected_candidate", password="testpassword123")

        # 1. Before employee creation
        resp = self.client.get(reverse("candidates:application_details", kwargs={"application_id": self.application.application_id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Candidate Selected — Offer Confirmed!")
        self.assertContains(resp, "Onboarding in Progress")

        # Dashboard shows selection milestone
        resp_dash = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(resp_dash.status_code, 200)
        self.assertContains(resp_dash, "Congratulations! You have been Selected.")

        # 2. After employee creation
        create_employee_record(
            candidate_id=self.candidate.candidate_id,
            user_id=self.candidate.user_id,
            employee_code="EMP-2026-7788",
            designation="Senior DevOps Engineer",
            department_id=self.department.department_id,
        )

        resp_after = self.client.get(reverse("candidates:application_details", kwargs={"application_id": self.application.application_id}))
        self.assertEqual(resp_after.status_code, 200)
        self.assertContains(resp_after, "Employee Lifecycle Active")
        self.assertContains(resp_after, "EMP-2026-7788")

        # Dashboard shows employee active
        resp_dash_after = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(resp_dash_after.status_code, 200)
        self.assertContains(resp_dash_after, "Welcome to the Team! You are officially onboarded.")
        self.assertContains(resp_dash_after, "EMP-2026-7788")


# ==============================================================================
# CANDIDATE SECURITY & AUTHORIZATION VERIFICATION TEST SUITE
# ==============================================================================
class CandidateSecurityAuthorizationTests(TestCase):
    """
    Complete security and authorization pass verifying:
    1. Candidate cannot access Admin dashboard (/admin/)
    2. Candidate cannot access HR dashboard (/hr/dashboard/)
    3. Candidate cannot access Employee dashboard (/employee/dashboard/)
    4. Candidate cannot create/edit/delete jobs
    5. Candidate cannot change application status
    6. Candidate cannot modify interview details
    7. Candidate cannot view another candidate's profile or HR dossier
    8. Candidate cannot view or download another candidate's documents/resumes
    9. Candidate cannot view another candidate's applications
    10. Candidate cannot view another candidate's aptitude test results
    11. Candidate cannot view another candidate's interviews
    12. Candidate cannot modify HR data (onboarding, employee creation)
    13. Candidate cannot edit/delete another candidate's skills or education
    14. Candidate cannot access another candidate's notifications
    15. Open Redirect attack prevention
    16. Password complexity validation enforcement
    17. File upload validation (rejecting executables, scripts, and forged headers)
    """

    def setUp(self):
        self.client = Client()

        # 1. Candidate User A (Primary test candidate)
        self.user_a = User.objects.create_user(
            username="candidate_alice",
            email="alice@example.com",
            password="AliceSecurePassword123!",
            first_name="Alice",
            last_name="Smith",
        )
        self.candidate_a = Candidate.objects.create(
            user=self.user_a,
            full_name="Alice Smith",
            phone="+91 9876543210",
            city="Kochi",
            state="Kerala",
        )
        self.doc_a = CandidateDocument.objects.create(
            candidate=self.candidate_a,
            resume=SimpleUploadedFile("alice_resume.pdf", b"%PDF-1.4 Alice Resume Content", content_type="application/pdf"),
        )
        self.skill_a = CandidateSkill.objects.create(candidate=self.candidate_a, skill_name="Python")
        self.edu_a = CandidateEducation.objects.create(
            candidate=self.candidate_a,
            qualification_type="MCA",
            institution="CUSAT",
            year="2024",
            percentage_or_cgpa="8.8 CGPA",
        )

        # 2. Candidate User B (Victim / Secondary candidate for IDOR testing)
        self.user_b = User.objects.create_user(
            username="candidate_bob",
            email="bob@example.com",
            password="BobSecurePassword123!",
            first_name="Bob",
            last_name="Jones",
        )
        self.candidate_b = Candidate.objects.create(
            user=self.user_b,
            full_name="Bob Jones",
            phone="+91 9123456780",
            city="Bangalore",
            state="Karnataka",
        )
        self.doc_b = CandidateDocument.objects.create(
            candidate=self.candidate_b,
            resume=SimpleUploadedFile("bob_resume.pdf", b"%PDF-1.4 Bob Secret Resume Content", content_type="application/pdf"),
        )
        self.skill_b = CandidateSkill.objects.create(candidate=self.candidate_b, skill_name="React")
        self.edu_b = CandidateEducation.objects.create(
            candidate=self.candidate_b,
            qualification_type="B.Tech",
            institution="NIT",
            year="2023",
            percentage_or_cgpa="8.5 CGPA",
        )

        # 3. Staff / HR User
        self.hr_user = User.objects.create_user(
            username="hr_recruiter",
            email="recruiter@example.com",
            password="HrSecurePassword123!",
            is_staff=True,
        )

        # 4. Department & Jobs
        self.department = Department.objects.create(
            name="Engineering Operations",
            code="ENG_OPS",
            description="Engineering Division",
        )
        self.job = Job.objects.create(
            title="Senior Backend Engineer",
            department=self.department,
            job_type=Job.JobType.FULL_TIME,
            experience_required="2-4 Years",
            location="Kochi (Hybrid)",
            description="Develop robust backend microservices in Python/Django.",
            status=Job.Status.OPEN,
        )

        # 5. Candidate B's Applications, Interviews, Test Results, Notifications
        self.app_b = Application.objects.create(
            candidate=self.candidate_b,
            job=self.job,
            status=Application.Status.SHORTLISTED,
            resume=SimpleUploadedFile("bob_app_resume.pdf", b"%PDF-1.4 Bob App Resume", content_type="application/pdf"),
        )
        self.interview_b = Interview.objects.create(
            candidate=self.candidate_b,
            job=self.job,
            application=self.app_b,
            interview_round="Round 1 - Technical Architecture",
            date=date.today() + timedelta(days=2),
            time="14:00:00",
            meeting_link="https://meet.google.com/bob-secret-interview",
        )
        self.test = AptitudeTest.objects.create(
            title="Backend Engineering Test",
            job=self.job,
            passing_percentage=60,
            duration_minutes=30,
            total_questions=10,
            status=AptitudeTest.Status.ACTIVE,
        )
        self.result_b = TestResult.objects.create(
            candidate=self.candidate_b,
            test=self.test,
            application=self.app_b,
            total_questions=10,
            correct_answers=9,
            score_percentage=90.00,
            is_passed=True,
        )
        self.notification_b = Notification.objects.create(
            candidate=self.candidate_b,
            title="Interview Invitation",
            message="Your technical interview is confirmed.",
            notification_type=Notification.NotificationType.INTERVIEW,
            link=f"/interviews/{self.interview_b.interview_id}/",
        )

    # --------------------------------------------------------------------------
    # 1. CANDIDATE CANNOT ACCESS ADMIN DASHBOARD
    # --------------------------------------------------------------------------
    def test_candidate_cannot_access_admin_dashboard(self):
        """Candidate attempting to access /admin/ is denied access by Django Admin."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get("/admin/", follow=False)
        # Django admin requires is_staff=True. Candidate user is redirected or 403
        self.assertIn(response.status_code, [302, 403])
        if response.status_code == 302:
            self.assertIn("/admin/login/", response.url)

    # --------------------------------------------------------------------------
    # 2. CANDIDATE CANNOT ACCESS HR DASHBOARD
    # --------------------------------------------------------------------------
    def test_candidate_cannot_access_hr_dashboard(self):
        """Candidate accessing /hr/dashboard/ strictly receives HTTP 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(reverse("candidates:hr_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_hr_user_can_access_hr_dashboard(self):
        """Staff/HR user can access /hr/dashboard/."""
        self.client.login(username="hr_recruiter", password="HrSecurePassword123!")
        response = self.client.get(reverse("candidates:hr_dashboard"))
        self.assertEqual(response.status_code, 200)

    # --------------------------------------------------------------------------
    # 3. CANDIDATE CANNOT ACCESS EMPLOYEE DASHBOARD
    # --------------------------------------------------------------------------
    def test_candidate_cannot_access_employee_dashboard(self):
        """Candidate accessing /employee/dashboard/ strictly receives HTTP 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(reverse("candidates:employee_dashboard"))
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 4. CANDIDATE CANNOT CREATE / EDIT / DELETE JOBS
    # --------------------------------------------------------------------------
    def test_candidate_cannot_create_jobs(self):
        """Candidate submitting POST to job endpoints receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(reverse("candidates:job_list"), {
            "title": "Malicious Job Vacancy",
            "department": self.department.pk,
            "description": "Unauthorized job",
        })
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_modify_jobs(self):
        """Candidate submitting POST/PUT/DELETE to job details receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(
            reverse("candidates:job_details", kwargs={"job_id": self.job.job_id}),
            {"title": "Hacked Job Title"},
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 5. CANDIDATE CANNOT CHANGE APPLICATION STATUS
    # --------------------------------------------------------------------------
    def test_candidate_cannot_change_application_status(self):
        """Candidate attempting to modify application status via POST receives 403 Forbidden."""
        # Create an application for Alice
        app_a = Application.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            status=Application.Status.APPLIED,
        )
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(
            reverse("candidates:application_details", kwargs={"application_id": app_a.application_id}),
            {"status": "SELECTED"},
        )
        self.assertEqual(response.status_code, 403)
        app_a.refresh_from_db()
        self.assertEqual(app_a.status, Application.Status.APPLIED)

    # --------------------------------------------------------------------------
    # 6. CANDIDATE CANNOT MODIFY INTERVIEW DETAILS
    # --------------------------------------------------------------------------
    def test_candidate_cannot_modify_interview_details(self):
        """Candidate attempting to POST changes to interview receives 403 Forbidden."""
        interview_a = Interview.objects.create(
            candidate=self.candidate_a,
            job=self.job,
            interview_round="Technical Round",
            date=date.today(),
            time="10:00:00",
        )
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(
            reverse("candidates:interview_details", kwargs={"interview_id": interview_a.interview_id}),
            {"time": "18:00:00", "interviewer": "Self-Assigned"},
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 7. CANDIDATE CANNOT VIEW ANOTHER CANDIDATE'S PROFILE / DOSSIER
    # --------------------------------------------------------------------------
    def test_candidate_cannot_view_another_candidate_onboarding_dossier(self):
        """Candidate Alice trying to view Bob's onboarding dossier receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(
            reverse("candidates:candidate_onboarding_dossier", kwargs={"candidate_id": self.candidate_b.candidate_id})
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 8. CANDIDATE CANNOT VIEW / DOWNLOAD ANOTHER CANDIDATE'S DOCUMENTS
    # --------------------------------------------------------------------------
    def test_candidate_cannot_download_another_candidate_application_resume(self):
        """Candidate Alice trying to download Bob's resume receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(
            reverse("candidates:application_resume_download", kwargs={"application_id": self.app_b.application_id})
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 9. CANDIDATE CANNOT VIEW ANOTHER CANDIDATE'S APPLICATIONS (IDOR)
    # --------------------------------------------------------------------------
    def test_candidate_cannot_view_another_candidate_application(self):
        """Candidate Alice accessing /applications/<bob_app_id>/ receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(
            reverse("candidates:application_details", kwargs={"application_id": self.app_b.application_id})
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 10. CANDIDATE CANNOT VIEW ANOTHER CANDIDATE'S APTITUDE RESULTS (IDOR)
    # --------------------------------------------------------------------------
    def test_candidate_cannot_view_another_candidate_aptitude_result(self):
        """Candidate Alice accessing /aptitude/results/<bob_result_id>/ receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(
            reverse("candidates:aptitude_result", kwargs={"result_id": self.result_b.result_id})
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 11. CANDIDATE CANNOT VIEW ANOTHER CANDIDATE'S INTERVIEWS (IDOR)
    # --------------------------------------------------------------------------
    def test_candidate_cannot_view_another_candidate_interview(self):
        """Candidate Alice accessing /interviews/<bob_interview_id>/ receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(
            reverse("candidates:interview_details", kwargs={"interview_id": self.interview_b.interview_id})
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 12. CANDIDATE CANNOT MODIFY HR DATA
    # --------------------------------------------------------------------------
    def test_candidate_cannot_complete_onboarding_action(self):
        """Candidate Alice attempting to invoke HR complete onboarding receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(
            reverse("candidates:complete_candidate_onboarding", kwargs={"candidate_id": self.candidate_b.candidate_id})
        )
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_access_hr_onboarding_api(self):
        """Candidate Alice attempting to query HR onboarding API receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(
            f"{reverse('candidates:candidate_onboarding_api')}?candidate_id={self.candidate_b.candidate_id}"
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 13. CANDIDATE CANNOT MUTATE ANOTHER CANDIDATE'S SKILLS OR EDUCATION
    # --------------------------------------------------------------------------
    def test_candidate_cannot_edit_another_candidate_skill(self):
        """Candidate Alice trying to edit Bob's skill receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(
            reverse("candidates:skill_edit", kwargs={"skill_id": self.skill_b.skill_id}),
            {"skill_name": "Hacked Skill"},
        )
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_delete_another_candidate_skill(self):
        """Candidate Alice trying to delete Bob's skill receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(
            reverse("candidates:skill_delete", kwargs={"skill_id": self.skill_b.skill_id})
        )
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_delete_another_candidate_education(self):
        """Candidate Alice trying to delete Bob's education receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.post(
            reverse("candidates:education_delete", kwargs={"education_id": self.edu_b.education_id})
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 14. CANDIDATE CANNOT ACCESS ANOTHER CANDIDATE'S NOTIFICATIONS
    # --------------------------------------------------------------------------
    def test_candidate_cannot_mark_another_candidate_notification_as_read(self):
        """Candidate Alice trying to mark Bob's notification as read receives 403 Forbidden."""
        self.client.login(username="candidate_alice", password="AliceSecurePassword123!")
        response = self.client.get(
            reverse("candidates:notification_mark_read", kwargs={"notification_id": self.notification_b.notification_id})
        )
        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------------------------------
    # 15. OPEN REDIRECT PREVENTION
    # --------------------------------------------------------------------------
    def test_login_open_redirect_is_prevented(self):
        """Login with next=https://evil.com safely falls back to candidates:profile."""
        response = self.client.post(reverse("candidates:login"), {
            "email": "alice@example.com",
            "password": "AliceSecurePassword123!",
            "next": "https://evil.com/phishing",
        })
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("evil.com", response.url)
        self.assertEqual(response.url, reverse("candidates:profile"))

    # --------------------------------------------------------------------------
    # 16. PASSWORD VALIDATION ENFORCEMENT
    # --------------------------------------------------------------------------
    def test_registration_rejects_weak_password(self):
        """Registration with simple/numeric password is rejected by Django validators."""
        response = self.client.post(reverse("candidates:register"), {
            "name": "New Candidate",
            "email": "new.candidate@example.com",
            "phone": "+91 9988776655",
            "password": "123",
            "confirm_password": "123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="new.candidate@example.com").exists())

    # --------------------------------------------------------------------------
    # 17. FILE UPLOAD VALIDATION SECURITY
    # --------------------------------------------------------------------------
    def test_file_upload_rejects_executable_files(self):
        """Upload validator strictly rejects .exe, .sh, .py, and PE/ELF headers."""
        malicious_exe = SimpleUploadedFile("malware.exe", b"MZ\x90\x00executable content", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_document_file(malicious_exe)

        malicious_script = SimpleUploadedFile("exploit.sh", b"#!/bin/bash\nrm -rf /", content_type="application/x-sh")
        with self.assertRaises(ValidationError):
            validate_document_file(malicious_script)

        disguised_pdf = SimpleUploadedFile("fake.pdf", b"MZ\x90\x00this is an exe disguised as pdf", content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_document_file(disguised_pdf)






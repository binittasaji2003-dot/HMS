import datetime
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from admin_module.models import Department
from candidates.models import (
    Candidate,
    CandidateEducation,
    JobApplication,
    JobVacancy,
    ResumeScreening,
    CandidateNotification,
    send_candidate_notification,
)
from candidates.screening_service import screen_job_application, run_resume_screening
from hr.models import HRManager

User = get_user_model()


class RecruitmentScreeningFlowTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Engineering", is_active=True)

        # 1. Create HR User
        self.hr_user = User.objects.create_user(
            email="hr_recruiter@example.com",
            name="HR Manager",
            password="HRPassword123!",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
            is_staff=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR001",
            is_active=True,
        )

        # 2. Create Candidates
        self.cand_user_a = User.objects.create_user(
            email="anju@gmail.com",
            name="Anju Biju",
            password="Password123!",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.cand_a = Candidate.objects.create(
            user=self.cand_user_a,
            first_name="Anju",
            last_name="Biju",
            phone="9876543210",
            date_of_birth="2000-01-01",
            address="Kochi, Kerala",
            tenth_board="CBSE",
            tenth_percentage="85%",
            tenth_passing_year=2016,
            twelfth_board="CBSE",
            twelfth_percentage="88%",
            twelfth_passing_year=2018,
            profile_photo=SimpleUploadedFile("photo.jpg", b"fake photo", content_type="image/jpeg"),
            resume=SimpleUploadedFile("resume.pdf", b"Python, Django, SQL, Git, B.Tech Computer Science 2022", content_type="application/pdf"),
            policy_agreement=True,
            profile_completed=True,
            skills="Python, Django, SQL, Git",
            total_experience_years=2,
            is_fresher=False,
        )
        CandidateEducation.objects.create(
            candidate=self.cand_a,
            education_level="Bachelor's",
            degree_program="B.Tech Computer Science",
            field_of_study="Computer Science",
            institution="Model Engineering College",
            education_status="Graduated",
            completion_year=2022,
        )

        self.cand_user_b = User.objects.create_user(
            email="candidate_b@example.com",
            name="Bob Martin",
            password="Password123!",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.cand_b = Candidate.objects.create(
            user=self.cand_user_b,
            first_name="Bob",
            last_name="Martin",
            phone="9876543211",
            date_of_birth="2001-02-02",
            address="Bangalore, Karnataka",
            tenth_board="State Board",
            tenth_percentage="70%",
            tenth_passing_year=2017,
            twelfth_board="State Board",
            twelfth_percentage="65%",
            twelfth_passing_year=2019,
            profile_photo=SimpleUploadedFile("photo_b.jpg", b"fake photo", content_type="image/jpeg"),
            resume=SimpleUploadedFile("resume_b.pdf", b"PHP, WordPress, HTML", content_type="application/pdf"),
            policy_agreement=True,
            profile_completed=True,
            skills="PHP, WordPress, HTML",
            total_experience_years=0,
            is_fresher=True,
        )
        CandidateEducation.objects.create(
            candidate=self.cand_b,
            education_level="Diploma",
            degree_program="Diploma in Electrical",
            field_of_study="Engineering",
            institution="Govt Poly",
            education_status="Graduated",
            completion_year=2021,
        )

        self.cand_user_c = User.objects.create_user(
            email="john_mathew@example.com",
            name="John Mathew",
            password="Password123!",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.cand_c = Candidate.objects.create(
            user=self.cand_user_c,
            first_name="John",
            last_name="Mathew",
            phone="9876543212",
            date_of_birth="1999-05-05",
            address="Trivandrum, Kerala",
            tenth_board="CBSE",
            tenth_percentage="90%",
            tenth_passing_year=2015,
            twelfth_board="CBSE",
            twelfth_percentage="92%",
            twelfth_passing_year=2017,
            profile_photo=SimpleUploadedFile("photo_c.jpg", b"fake photo", content_type="image/jpeg"),
            resume=SimpleUploadedFile("resume_c.pdf", b"Java, Spring Boot, Microservices, SQL", content_type="application/pdf"),
            policy_agreement=True,
            profile_completed=True,
            skills="Java, Spring Boot, Microservices, SQL",
            total_experience_years=3,
            is_fresher=False,
        )
        CandidateEducation.objects.create(
            candidate=self.cand_c,
            education_level="Bachelor's",
            degree_program="B.Tech IT",
            field_of_study="Information Technology",
            institution="CET Trivandrum",
            education_status="Graduated",
            completion_year=2021,
        )

        # 3. Create Job Vacancies
        today = timezone.localdate()
        future_date = today + datetime.timedelta(days=10)

        # Job 1: Python Developer
        self.job_python = JobVacancy.objects.create(
            title="Python Developer",
            department=self.dept,
            description="Developing web APIs using Django & Python.",
            skills_required="Python, Django, SQL",
            preferred_skills="Docker, Git",
            minimum_qualification="Bachelor's",
            required_field_of_study="Computer Science",
            graduation_year_min=2020,
            graduation_year_max=2024,
            experience_required_bool=True,
            minimum_experience=1.0,
            status="OPEN",
            closing_date=future_date,
            posted_by=self.hr_user,
        )

        # Job 2: Java Developer
        self.job_java = JobVacancy.objects.create(
            title="Java Developer",
            department=self.dept,
            description="Developing microservices with Java and Spring Boot.",
            skills_required="Java, Spring Boot, Microservices",
            preferred_skills="Kubernetes, AWS",
            minimum_qualification="Bachelor's",
            experience_required_bool=True,
            minimum_experience=2.0,
            status="OPEN",
            closing_date=future_date,
            posted_by=self.hr_user,
        )

        self.client = Client()

    def test_01_candidate_applies_before_deadline(self):
        """1. Candidate applies before deadline."""
        self.client.force_login(self.cand_user_a)
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": self.job_python.vacancy_id})
        resp = self.client.get(apply_url)
        self.assertEqual(resp.status_code, 200)

        dummy_resume = SimpleUploadedFile("anju_resume.pdf", b"Python, Django, SQL, Git, B.Tech Computer Science 2022", content_type="application/pdf")
        post_resp = self.client.post(
            apply_url,
            {
                "first_name": "Anju",
                "last_name": "Biju",
                "email": "anju@gmail.com",
                "phone": "9876543210",
                "date_of_birth": "2000-01-01",
                "current_state": "Kerala",
                "current_country": "India",
                "terms_agreement": True,
                "resume": dummy_resume,
                "information_source": "RESUME",
                "applied_skills": "Python, Django, SQL, Git",
            },
            follow=True,
        )
        self.assertEqual(post_resp.status_code, 200)
        app = JobApplication.objects.filter(candidate=self.cand_a, vacancy=self.job_python).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.status, "APPLIED")
        self.assertFalse(hasattr(app, "screening_result"))

        # Verify APPLICATION_SUBMITTED notification created
        notif = CandidateNotification.objects.filter(candidate=self.cand_a, application=app).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, "APPLICATION_SUBMITTED")
        self.assertEqual(notif.title, "Application Submitted Successfully")
        self.assertIn("Application review and shortlisting will take place after the job application period closes", notif.message)

    def test_02_candidate_cannot_apply_after_deadline_or_closed_job(self):
        """2 & 3. Job closes after deadline; candidate cannot apply to closed job."""
        past_date = timezone.localdate() - datetime.timedelta(days=2)
        expired_job = JobVacancy.objects.create(
            title="Expired Job Role",
            department=self.dept,
            description="Old closed job.",
            status="OPEN",
            closing_date=past_date,
            posted_by=self.hr_user,
        )
        # Check automatic job closure
        self.assertTrue(expired_job.check_and_update_status())
        self.assertEqual(expired_job.status, "CLOSED")
        self.assertEqual(expired_job.closed_reason, "DEADLINE_EXPIRED")

        self.client.force_login(self.cand_user_a)
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": expired_job.vacancy_id})
        resp = self.client.post(
            apply_url,
            {
                "first_name": "Anju",
                "last_name": "Biju",
                "terms_agreement": True,
            },
            follow=True,
        )
        self.assertFalse(JobApplication.objects.filter(candidate=self.cand_a, vacancy=expired_job).exists())

    def test_04_job_with_no_deadline_can_be_manually_closed(self):
        """4. Job with no deadline can be manually closed."""
        no_deadline_job = JobVacancy.objects.create(
            title="Open Ended Job",
            department=self.dept,
            description="Ongoing position.",
            status="OPEN",
            closing_date=None,
            posted_by=self.hr_user,
        )
        self.assertTrue(no_deadline_job.is_open)
        no_deadline_job.status = "CLOSED"
        no_deadline_job.closed_reason = "MANUALLY_CLOSED"
        no_deadline_job.save()
        self.assertFalse(no_deadline_job.is_open)

    def test_05_valid_applications_screened_and_matching_shortlisted(self):
        """7, 8, 9, 10, 11, 12, 13, 14: Job requirements match checks, Required vs Preferred skills."""
        # Candidate A applying to Python Dev: satisfies all mandatory requirements (Python, Django, SQL)
        # Missing preferred skill (Docker) must NOT cause rejection.
        app_a = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screening_a = screen_job_application(app_a)
        self.assertEqual(screening_a.status, "SHORTLISTED")
        self.assertTrue(screening_a.education_matched)
        self.assertTrue(screening_a.experience_matched)
        self.assertTrue(screening_a.graduation_year_matched)
        self.assertEqual(screening_a.required_skills_matched, 3)
        self.assertEqual(screening_a.required_skills_total, 3)
        app_a.refresh_from_db()
        self.assertEqual(app_a.status, "SHORTLISTED")

        # Candidate B applying to Python Dev: fails qualification & skills
        app_b = JobApplication.objects.create(
            candidate=self.cand_b,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screening_b = screen_job_application(app_b)
        self.assertEqual(screening_b.status, "NOT_SHORTLISTED")
        self.assertFalse(screening_b.education_matched)
        self.assertEqual(screening_b.required_skills_matched, 0)
        app_b.refresh_from_db()
        self.assertEqual(app_b.status, "REJECTED")  # rejected / not shortlisted

        # Candidate C applying to Java Dev: satisfies Java Dev requirements
        app_c = JobApplication.objects.create(
            candidate=self.cand_c,
            vacancy=self.job_java,
            status="APPLIED",
        )
        screening_c = screen_job_application(app_c)
        self.assertEqual(screening_c.status, "SHORTLISTED")
        app_c.refresh_from_db()
        self.assertEqual(app_c.status, "SHORTLISTED")

    def test_15_16_17_notifications_and_deduplication(self):
        """15, 16, 17: Shortlisted & Not-shortlisted notifications and duplicate prevention."""
        app_a = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        # Screen creates notification
        screening_a = screen_job_application(app_a, send_notification=True)
        self.assertEqual(screening_a.status, "SHORTLISTED")

        notifs_a = CandidateNotification.objects.filter(candidate=self.cand_a, application=app_a, notification_type="SHORTLISTED")
        self.assertEqual(notifs_a.count(), 1)
        notif_a = notifs_a.first()
        self.assertEqual(notif_a.title, "Congratulations! You have been shortlisted")
        self.assertIn("Next Step:\nAptitude Round", notif_a.message)
        self.assertFalse(notif_a.is_read)

        # Re-screen All / duplicate check: Must NOT create second notification
        screening_a2 = screen_job_application(app_a, send_notification=True)
        self.assertEqual(CandidateNotification.objects.filter(candidate=self.cand_a, application=app_a, notification_type="SHORTLISTED").count(), 1)

        # Candidate B Not Shortlisted Notification
        app_b = JobApplication.objects.create(
            candidate=self.cand_b,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screening_b = screen_job_application(app_b, send_notification=True)
        self.assertEqual(screening_b.status, "NOT_SHORTLISTED")

        notifs_b = CandidateNotification.objects.filter(candidate=self.cand_b, application=app_b, notification_type="NOT_SHORTLISTED")
        self.assertEqual(notifs_b.count(), 1)
        notif_b = notifs_b.first()
        self.assertEqual(notif_b.title, "Application Update")
        self.assertIn("has not been shortlisted", notif_b.message)

    def test_18_19_global_hr_shortlist_and_job_specific_shortlist(self):
        """18, 19, 20: Global HR Shortlist (/hr/applications/?status=SHORTLISTED) and Job-Specific Shortlist."""
        app_a = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screen_job_application(app_a)

        app_b = JobApplication.objects.create(
            candidate=self.cand_b,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screen_job_application(app_b)

        app_c = JobApplication.objects.create(
            candidate=self.cand_c,
            vacancy=self.job_java,
            status="APPLIED",
        )
        screen_job_application(app_c)

        self.client.force_login(self.hr_user)

        # Global Shortlist
        global_resp = self.client.get(reverse("hr:application_list") + "?status=SHORTLISTED")
        self.assertEqual(global_resp.status_code, 200)
        self.assertContains(global_resp, "Anju Biju")
        self.assertContains(global_resp, "Python Developer")
        self.assertContains(global_resp, "John Mathew")
        self.assertContains(global_resp, "Java Developer")
        self.assertNotContains(global_resp, "Bob Martin")

        # Job 1 Specific Shortlist
        job1_shortlist_resp = self.client.get(reverse("hr:job_shortlisted", kwargs={"vacancy_id": self.job_python.pk}))
        self.assertEqual(job1_shortlist_resp.status_code, 200)
        self.assertContains(job1_shortlist_resp, "Anju Biju")
        self.assertNotContains(job1_shortlist_resp, "John Mathew")
        self.assertNotContains(job1_shortlist_resp, "Bob Martin")

    def test_21_22_candidate_portal_isolation_and_next_stage(self):
        """21, 22: Candidate sees only own application, congratulations banner, and Next Step: Aptitude Round."""
        app_a = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screen_job_application(app_a)

        self.client.force_login(self.cand_user_a)
        cand_apps_resp = self.client.get(reverse("candidates:applications"))
        self.assertEqual(cand_apps_resp.status_code, 200)
        self.assertContains(cand_apps_resp, "🎉 Congratulations!")
        self.assertContains(cand_apps_resp, "Next Step: APTITUDE ROUND")
        self.assertNotContains(cand_apps_resp, "Bob Martin")
        self.assertNotContains(cand_apps_resp, "John Mathew")

    def test_23_24_25_hr_view_details_and_screening_result(self):
        """23, 24, 25: HR can view candidate application details and screening result breakdown."""
        app_a = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screen_job_application(app_a)

        self.client.force_login(self.hr_user)
        detail_resp = self.client.get(reverse("hr:application_detail", kwargs={"pk": app_a.pk}))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "Job-Specific Resume Screening Result")
        self.assertContains(detail_resp, "SHORTLISTED")
        self.assertContains(detail_resp, "Python")
        self.assertContains(detail_resp, "Django")
        self.assertContains(detail_resp, "SQL")
        self.assertContains(detail_resp, "APTITUDE ROUND")

    def test_28_threshold_decision_logic(self):
        """Verify score > 70 -> SHORTLISTED, score <= 70 -> NOT_SHORTLISTED."""
        app_a = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        scr_a = screen_job_application(app_a)
        self.assertGreater(scr_a.match_score, 70.0)
        self.assertEqual(scr_a.status, "SHORTLISTED")
        app_a.refresh_from_db()
        self.assertEqual(app_a.status, "SHORTLISTED")

        # Candidate B score <= 70 -> NOT_SHORTLISTED
        app_b = JobApplication.objects.create(
            candidate=self.cand_b,
            vacancy=self.job_python,
            status="APPLIED",
        )
        scr_b = screen_job_application(app_b)
        self.assertLessEqual(scr_b.match_score, 70.0)
        self.assertEqual(scr_b.status, "NOT_SHORTLISTED")
        app_b.refresh_from_db()
        self.assertEqual(app_b.status, "REJECTED")

    def test_29_automatic_screening_on_job_closure(self):
        """Verify automatic screening runs when job deadline passes or HR manually closes."""
        app = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        self.assertFalse(hasattr(app, "screening_result"))

        # HR manually closes job
        self.client.force_login(self.hr_user)
        close_url = reverse("hr:job_close", kwargs={"pk": self.job_python.pk})
        close_resp = self.client.post(close_url, follow=True)
        self.assertEqual(close_resp.status_code, 200)

        self.job_python.refresh_from_db()
        self.assertEqual(self.job_python.status, "CLOSED")
        self.assertEqual(self.job_python.closed_reason, "MANUALLY_CLOSED")

        # Application was automatically screened without HR clicking screening
        app.refresh_from_db()
        self.assertTrue(hasattr(app, "screening_result"))
        self.assertEqual(app.screening_result.status, "SHORTLISTED")
        self.assertEqual(app.status, "SHORTLISTED")

    def test_30_candidate_portal_modal_popup_and_dismiss(self):
        """Verify popup appears for unread decision notification and does not repeat after dismissal."""
        app_a = JobApplication.objects.create(
            candidate=self.cand_a,
            vacancy=self.job_python,
            status="APPLIED",
        )
        screen_job_application(app_a, send_notification=True)

        self.client.force_login(self.cand_user_a)
        dash_resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, "candidateDecisionModal")
        self.assertContains(dash_resp, "Congratulations!")
        self.assertContains(dash_resp, "APTITUDE ROUND")

        # Mark notification as read (simulating modal close or view)
        notif = CandidateNotification.objects.filter(candidate=self.cand_a, notification_type="SHORTLISTED").first()
        self.assertIsNotNone(notif)
        read_resp = self.client.get(reverse("candidates:mark_notification_read", kwargs={"notification_id": notif.pk}) + "?format=json")
        self.assertEqual(read_resp.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

        # Visiting dashboard again: popup is no longer rendered
        dash_resp2 = self.client.get(reverse("candidates:dashboard"))
        self.assertNotContains(dash_resp2, "candidateDecisionModal")

        # But notification remains available in notifications page
        notifs_resp = self.client.get(reverse("candidates:notifications"))
        self.assertEqual(notifs_resp.status_code, 200)
        self.assertContains(notifs_resp, "Congratulations! You have been shortlisted")

    def test_31_complete_five_applicant_scenario(self):
        """Section 23: Complete 5-applicant scenario with automatic closure screening."""
        job = JobVacancy.objects.create(
            title="Cloud Security Specialist",
            department=self.dept,
            description="Security and cloud operations.",
            skills_required="AWS, Security, Firewalls, Linux, SIEM",
            minimum_qualification="Bachelor's",
            experience_required_bool=True,
            minimum_experience=2.0,
            status="OPEN",
            closing_date=timezone.localdate() + datetime.timedelta(days=5),
            posted_by=self.hr_user,
        )

        # Applicant 1: Strong candidate (>70%, e.g. 85%) -> SHORTLISTED
        cand1_user = User.objects.create_user(email="cand1@example.com", name="Karthik Sundaram", password="Pass123!", role=User.RoleChoices.CANDIDATE, is_active=True)
        cand1 = Candidate.objects.create(user=cand1_user, first_name="Karthik", last_name="Sundaram", skills="AWS, Security, Firewalls, Linux, SIEM", total_experience_years=3, is_fresher=False, profile_completed=True, policy_agreement=True)
        CandidateEducation.objects.create(candidate=cand1, education_level="Bachelor's", degree_program="B.Tech CS", completion_year=2021)
        app1 = JobApplication.objects.create(candidate=cand1, vacancy=job, status="APPLIED", applied_skills="AWS, Security, Firewalls, Linux, SIEM")

        # Applicant 2: Good candidate (>70%, e.g. 75%) -> SHORTLISTED
        cand2_user = User.objects.create_user(email="cand2@example.com", name="Meera Nair", password="Pass123!", role=User.RoleChoices.CANDIDATE, is_active=True)
        cand2 = Candidate.objects.create(user=cand2_user, first_name="Meera", last_name="Nair", skills="AWS, Security, Linux, SIEM", total_experience_years=2, is_fresher=False, profile_completed=True, policy_agreement=True)
        CandidateEducation.objects.create(candidate=cand2, education_level="Bachelor's", degree_program="BCA", completion_year=2022)
        app2 = JobApplication.objects.create(candidate=cand2, vacancy=job, status="APPLIED", applied_skills="AWS, Security, Linux, SIEM")

        # Applicant 3: Marginal candidate (<=70%, e.g. 60%) -> NOT_SHORTLISTED
        cand3_user = User.objects.create_user(email="cand3@example.com", name="David George", password="Pass123!", role=User.RoleChoices.CANDIDATE, is_active=True)
        cand3 = Candidate.objects.create(user=cand3_user, first_name="David", last_name="George", skills="Linux, Firewalls", total_experience_years=2, is_fresher=False, profile_completed=True, policy_agreement=True)
        CandidateEducation.objects.create(candidate=cand3, education_level="Bachelor's", degree_program="B.Sc IT", completion_year=2020)
        app3 = JobApplication.objects.create(candidate=cand3, vacancy=job, status="APPLIED", applied_skills="Linux, Firewalls")

        # Applicant 4: Low match candidate (<=70%, e.g. 40%) -> NOT_SHORTLISTED
        cand4_user = User.objects.create_user(email="cand4@example.com", name="Rahul Verma", password="Pass123!", role=User.RoleChoices.CANDIDATE, is_active=True)
        cand4 = Candidate.objects.create(user=cand4_user, first_name="Rahul", last_name="Verma", skills="Photoshop, Graphic Design", total_experience_years=0, is_fresher=True, profile_completed=True, policy_agreement=True)
        CandidateEducation.objects.create(candidate=cand4, education_level="Diploma", degree_program="Diploma Arts", completion_year=2023)
        app4 = JobApplication.objects.create(candidate=cand4, vacancy=job, status="APPLIED", applied_skills="Photoshop, Graphic Design")

        # Applicant 5: Extraction failed candidate -> MANUAL_REVIEW
        cand5_user = User.objects.create_user(email="cand5@example.com", name="Unreadable Doc", password="Pass123!", role=User.RoleChoices.CANDIDATE, is_active=True)
        cand5 = Candidate.objects.create(
            user=cand5_user,
            first_name="Unreadable",
            last_name="Doc",
            skills="",
            total_experience_years=0,
            is_fresher=True,
            profile_completed=True,
            policy_agreement=True,
            resume=SimpleUploadedFile("corrupted.pdf", b"corrupted_binary_data", content_type="application/pdf"),
        )
        app5 = JobApplication.objects.create(candidate=cand5, vacancy=job, status="APPLIED", applied_resume=cand5.resume)

        # Run screening via batch service
        stats = run_resume_screening(job, force_rescreen=True)
        self.assertEqual(stats["total"], 5)
        self.assertEqual(stats["shortlisted"], 2)
        self.assertEqual(stats["not_shortlisted"], 2)
        self.assertEqual(stats["manual_review"], 1)

        # Verify Candidate Notifications
        self.assertTrue(CandidateNotification.objects.filter(candidate=cand1, notification_type="SHORTLISTED").exists())
        self.assertTrue(CandidateNotification.objects.filter(candidate=cand2, notification_type="SHORTLISTED").exists())
        self.assertTrue(CandidateNotification.objects.filter(candidate=cand3, notification_type="NOT_SHORTLISTED").exists())
        self.assertTrue(CandidateNotification.objects.filter(candidate=cand4, notification_type="NOT_SHORTLISTED").exists())
        self.assertFalse(CandidateNotification.objects.filter(candidate=cand5, notification_type__in=["SHORTLISTED", "NOT_SHORTLISTED"]).exists())

        # Verify HR Shortlisted views
        self.client.force_login(self.hr_user)
        shortlist_resp = self.client.get(reverse("hr:job_shortlisted", kwargs={"vacancy_id": job.pk}))
        self.assertEqual(shortlist_resp.status_code, 200)
        self.assertContains(shortlist_resp, "Karthik Sundaram")
        self.assertContains(shortlist_resp, "Meera Nair")
        self.assertNotContains(shortlist_resp, "David George")
        self.assertNotContains(shortlist_resp, "Rahul Verma")

    def test_32_full_notification_timing_lifecycle(self):
        """Verify strict notification timing: APPLIED on submission -> APPLICATION_SUBMITTED popup -> job closed -> SHORTLISTED popup."""
        # 1. Candidate applies before job closes
        self.client.force_login(self.cand_user_a)
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": self.job_python.vacancy_id})
        dummy_resume = SimpleUploadedFile("resume_timing.pdf", b"Python, Django, SQL, Git", content_type="application/pdf")
        self.client.post(
            apply_url,
            {
                "first_name": "Anju",
                "last_name": "Biju",
                "email": "anju@gmail.com",
                "phone": "9876543210",
                "terms_agreement": True,
                "resume": dummy_resume,
                "applied_skills": "Python, Django, SQL, Git",
            },
            follow=True,
        )
        app = JobApplication.objects.get(candidate=self.cand_a, vacancy=self.job_python)
        self.assertEqual(app.status, "APPLIED")
        self.assertFalse(hasattr(app, "screening_result"))

        # Candidate dashboard shows "Application Submitted" modal (NOT shortlisted)
        dash_resp = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, "Application Submitted")
        self.assertContains(dash_resp, "Your application has been received successfully")
        self.assertNotContains(dash_resp, "Congratulations! You have been shortlisted")
        self.assertNotContains(dash_resp, "APTITUDE ROUND")

        # Candidate applications list does not show score or congratulations
        apps_resp = self.client.get(reverse("candidates:applications"))
        self.assertEqual(apps_resp.status_code, 200)
        self.assertNotContains(apps_resp, "🎉 Congratulations!")
        self.assertNotContains(apps_resp, "Next Step: APTITUDE ROUND")

        # HR shortlisted list does NOT list this candidate while job is open & unscreened
        self.client.force_login(self.hr_user)
        hr_shortlist_resp = self.client.get(reverse("hr:job_shortlisted", kwargs={"vacancy_id": self.job_python.pk}))
        self.assertNotContains(hr_shortlist_resp, "Anju Biju")

        # 2. HR closes the job -> Triggers automatic screening
        close_url = reverse("hr:job_close", kwargs={"pk": self.job_python.pk})
        self.client.post(close_url, follow=True)

        app.refresh_from_db()
        self.assertEqual(app.status, "SHORTLISTED")
        self.assertTrue(hasattr(app, "screening_result"))

        # 3. Candidate now sees Shortlisted Congratulations popup
        self.client.force_login(self.cand_user_a)
        # Mark the submitted notification read so next unread popup is SHORTLISTED
        sub_notif = CandidateNotification.objects.filter(candidate=self.cand_a, notification_type="APPLICATION_SUBMITTED").first()
        sub_notif.is_read = True
        sub_notif.save()

        dash_resp_after = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(dash_resp_after.status_code, 200)
        self.assertContains(dash_resp_after, "Congratulations!")
        self.assertContains(dash_resp_after, "APTITUDE ROUND")

        # Candidate applications list now shows Congratulations
        apps_resp_after = self.client.get(reverse("candidates:applications"))
        self.assertContains(apps_resp_after, "🎉 Congratulations!")
        self.assertContains(apps_resp_after, "Next Step: APTITUDE ROUND")

        # HR shortlisted list now includes the candidate
        self.client.force_login(self.hr_user)
        hr_shortlist_after = self.client.get(reverse("hr:job_shortlisted", kwargs={"vacancy_id": self.job_python.pk}))
        self.assertContains(hr_shortlist_after, "Anju Biju")




from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from admin_module.models import Department
from candidates.models import Candidate, JobApplication, JobVacancy
from hr.models import HRManager, Interview

User = get_user_model()


class CandidateModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Engineering", is_active=True)

        # Admin user
        self.admin_user = User.objects.create_superuser(
            email="admin@company.com",
            password="AdminPass123!",
            name="Admin User",
            role=User.RoleChoices.ADMIN,
        )

        # HR user
        self.hr_user = User.objects.create_user(
            email="hr@company.com",
            password="HRPass123!",
            name="HR Manager",
            role=User.RoleChoices.HR,
            is_active=True,
        )
        self.hr_manager = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR001",
        )

        # Candidate user
        self.candidate_user = User.objects.create_user(
            email="candidate@example.com",
            password="CandPass123!",
            name="Jane Candidate",
            role=User.RoleChoices.CANDIDATE,
        )
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            first_name="Jane",
            last_name="Candidate",
            phone="1234567890",
            date_of_birth="1995-06-15",
            address="123 Silicon Road",
            profile_photo=SimpleUploadedFile("avatar.jpg", b"fake_avatar_content", content_type="image/jpeg"),
            resume=SimpleUploadedFile("resume.pdf", b"fake_resume_content", content_type="application/pdf"),
            tenth_board="CBSE",
            tenth_percentage="88%",
            tenth_passing_year=2011,
            twelfth_board="CBSE",
            twelfth_stream="Science",
            twelfth_percentage="85%",
            twelfth_passing_year=2013,
            is_fresher=True,
            skills="Python, Django, PostgreSQL",
            state="Karnataka",
            country="India",
            policy_agreement=True,
        )
        from candidates.models import CandidateEducation
        self.candidate_education = CandidateEducation.objects.create(
            candidate=self.candidate,
            education_level="Bachelor's",
            degree_program="B.Tech Computer Science",
            field_of_study="Computer Science",
            institution="NIT College",
            university_board="NIT Board",
            education_status="Graduated",
            completion_year=2017,
            percentage_or_cgpa="8.5 CGPA",
        )

        # Job Vacancy
        self.vacancy = JobVacancy.objects.create(
            title="Senior Backend Engineer",
            department=self.dept,
            description="Build scalable Django systems",
            responsibilities="Develop APIs",
            qualifications="Bachelor's in Computer Science or equivalent",
            skills_required="Django, Python",
            experience_required="0-2 years",
            location="Remote",
            posted_by=self.hr_user,
            status="OPEN",
        )

    def test_candidate_job_list_view(self):
        response = self.client.get(reverse("candidates:job_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Backend Engineer")

    def test_candidate_job_detail_view(self):
        response = self.client.get(
            reverse("candidates:job_detail", kwargs={"vacancy_id": self.vacancy.vacancy_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Senior Backend Engineer")

    def test_candidate_apply_and_view_applications(self):
        self.client.login(username=self.candidate_user.email, password="CandPass123!")

        # Apply view GET
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": self.vacancy.vacancy_id})
        response = self.client.get(apply_url)
        self.assertEqual(response.status_code, 200)

        # Apply view POST
        dummy_resume = SimpleUploadedFile("resume.pdf", b"fake resume content", content_type="application/pdf")
        post_response = self.client.post(
            apply_url,
            {
                "first_name": "Jane",
                "last_name": "Candidate",
                "email": "candidate@example.com",
                "phone": "1234567890",
                "date_of_birth": "1995-06-15",
                "terms_agreement": True,
                "resume": dummy_resume,
            },
            follow=True,
        )
        self.assertEqual(post_response.status_code, 200)

        # Check application created
        app = JobApplication.objects.filter(candidate=self.candidate, vacancy=self.vacancy).first()
        self.assertIsNotNone(app)
        self.assertIn(app.status, ["APPLIED", "SHORTLISTED", "NOT_SHORTLISTED"])

        # View applications list
        apps_response = self.client.get(reverse("candidates:applications"))
        self.assertEqual(apps_response.status_code, 200)
        self.assertContains(apps_response, "Senior Backend Engineer")

    def test_candidate_dashboard_and_profile_update(self):
        self.client.login(username=self.candidate_user.email, password="CandPass123!")

        # Dashboard
        dash_response = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, "Profile Completion")

        # Profile update
        prof_response = self.client.post(
            reverse("candidates:profile"),
            {
                "first_name": "Jane",
                "last_name": "Updated",
                "phone": "9876543210",
                "date_of_birth": "1995-06-15",
                "address": "123 Tech Street",
                "tenth_board": "CBSE",
                "tenth_percentage": "88%",
                "tenth_passing_year": 2011,
                "twelfth_board": "CBSE",
                "twelfth_stream": "Science",
                "twelfth_percentage": "85%",
                "twelfth_passing_year": 2013,
                "is_fresher": True,
                "policy_agreement": True,
            },
            follow=True,
        )
        self.assertEqual(prof_response.status_code, 200)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.last_name, "Updated")

    def test_end_to_end_recruitment_workflow(self):
        # 1. Candidate applies
        self.client.login(username=self.candidate_user.email, password="CandPass123!")
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": self.vacancy.vacancy_id})
        apply_resp = self.client.post(
            apply_url,
            {
                "first_name": "Jane",
                "last_name": "Candidate",
                "email": "candidate@example.com",
                "phone": "1234567890",
                "date_of_birth": "1995-06-15",
                "terms_agreement": True,
            },
            follow=True,
        )
        self.assertEqual(apply_resp.status_code, 200)

        app = JobApplication.objects.get(candidate=self.candidate, vacancy=self.vacancy)

        # Check notification dispatched upon application submission
        self.assertTrue(self.candidate.notifications.filter(notification_type="APPLICATION_SUBMITTED").exists())

        # 2. HR logs in and views applications
        self.client.logout()
        self.client.login(username=self.hr_user.email, password="HRPass123!")

        hr_apps_response = self.client.get(reverse("hr:application_list"))
        self.assertEqual(hr_apps_response.status_code, 200)
        self.assertContains(hr_apps_response, self.candidate.last_name)

        # HR updates application status to SHORTLISTED
        status_url = reverse("hr:application_status_update", kwargs={"pk": app.pk})
        self.client.post(status_url, {"status": "SHORTLISTED"}, follow=True)
        app.refresh_from_db()
        self.assertEqual(app.status, "SHORTLISTED")
        self.assertTrue(self.candidate.notifications.filter(title__icontains="shortlisted").exists())

        # HR schedules Aptitude Assessment
        self.client.post(
            status_url,
            {
                "status": "APTITUDE",
                "aptitude_date": "2026-10-10",
                "aptitude_time": "10:00",
                "aptitude_remarks": "Online quantitative & logical test",
            },
            follow=True,
        )
        app.refresh_from_db()
        self.assertEqual(app.status, "APTITUDE")
        self.assertEqual(str(app.aptitude_date), "2026-10-10")
        self.assertTrue(self.candidate.notifications.filter(notification_type="APTITUDE_SCHEDULED").exists())

        # HR schedules interview
        interview_url = reverse("hr:interview_create")
        self.client.post(
            interview_url,
            {
                "application_id": app.pk,
                "interview_date": "2026-10-15",
                "interview_time": "14:00",
                "remarks": "Technical round with Lead Engineer",
            },
            follow=True,
        )
        self.assertTrue(Interview.objects.filter(application=app).exists())
        self.assertTrue(self.candidate.notifications.filter(notification_type="INTERVIEW_SCHEDULED").exists())

        # HR updates application status to SELECTED
        self.client.post(status_url, {"status": "SELECTED"}, follow=True)
        app.refresh_from_db()
        self.assertEqual(app.status, "SELECTED")
        self.assertTrue(self.candidate.notifications.filter(title="Application Selected").exists())

        # 3. Candidate views notifications and marks them as read
        self.client.logout()
        self.client.login(username=self.candidate_user.email, password="CandPass123!")

        notif_resp = self.client.get(reverse("candidates:notifications"))
        self.assertEqual(notif_resp.status_code, 200)
        self.assertContains(notif_resp, "Application Selected")

        # Mark all read
        mark_all_resp = self.client.get(reverse("candidates:mark_all_notifications_read"), follow=True)
        self.assertEqual(mark_all_resp.status_code, 200)
        self.assertEqual(self.candidate.notifications.filter(is_read=False).count(), 0)

        # 4. Admin logs in and views recruitment status & selected candidates
        self.client.logout()
        self.client.login(username=self.admin_user.email, password="AdminPass123!")

        admin_status_resp = self.client.get(reverse("admin_module:recruitment_status"))
        self.assertEqual(admin_status_resp.status_code, 200)

        admin_selected_resp = self.client.get(reverse("admin_module:recruitment_selected"))
        self.assertEqual(admin_selected_resp.status_code, 200)
        self.assertContains(admin_selected_resp, self.candidate.last_name)

    def test_candidate_notification_isolation(self):
        other_user = User.objects.create_user(
            email="other_candidate@example.com",
            password="OtherPass123!",
            name="Other User",
            role=User.RoleChoices.CANDIDATE,
        )
        other_candidate = Candidate.objects.create(
            user=other_user,
            first_name="Other",
            last_name="User",
        )

        from candidates.models import CandidateNotification
        notif1 = CandidateNotification.objects.create(
            candidate=self.candidate,
            title="Private Notification for Jane",
            message="Confidential test details",
        )
        notif2 = CandidateNotification.objects.create(
            candidate=other_candidate,
            title="Private Notification for Other",
            message="Other confidential details",
        )

        self.client.login(username=self.candidate_user.email, password="CandPass123!")
        resp = self.client.get(reverse("candidates:notifications"))
        self.assertContains(resp, "Private Notification for Jane")
        self.assertNotContains(resp, "Private Notification for Other")

        # Candidate cannot mark other candidate's notification read
        other_read_resp = self.client.get(
            reverse("candidates:mark_notification_read", kwargs={"notification_id": notif2.pk})
        )
        self.assertEqual(other_read_resp.status_code, 404)

    def test_candidate_profile_completion_calculation_and_education_crud(self):
        # Create fresh candidate with minimal data
        fresh_user = User.objects.create_user(
            email="fresh_candidate@example.com",
            password="FreshPass123!",
            name="Fresh Candidate",
            role=User.RoleChoices.CANDIDATE,
        )
        fresh_cand = Candidate.objects.create(
            user=fresh_user,
            first_name="Fresh",
            last_name="Candidate",
            phone="9876543210",
        )

        self.client.login(username=fresh_user.email, password="FreshPass123!")

        # Initial profile with only name & phone has < 100% completion
        completion = fresh_cand.calculate_profile_completion()
        self.assertFalse(completion["is_complete"])
        self.assertIn("Date of Birth", completion["missing_fields"])
        self.assertIn("10th Education", [s["label"] for s in completion["sections"].values() if not s["complete"]])

        # 1. Update personal details
        fresh_cand.date_of_birth = "1998-05-15"
        fresh_cand.address = "456 Silicon Ave"
        fresh_cand.profile_photo = SimpleUploadedFile("avatar.jpg", b"fake image bytes", content_type="image/jpeg")
        fresh_cand.save()

        # 2. Add 10th details
        fresh_cand.tenth_board = "CBSE"
        fresh_cand.tenth_percentage = "88%"
        fresh_cand.tenth_passing_year = 2014
        fresh_cand.save()

        # 3. Add 12th details
        fresh_cand.twelfth_board = "CBSE"
        fresh_cand.twelfth_stream = "Science"
        fresh_cand.twelfth_percentage = "85%"
        fresh_cand.twelfth_passing_year = 2016
        fresh_cand.save()

        # 4. Add Bachelor's Degree via add_education view
        add_bachelors_resp = self.client.post(
            reverse("candidates:add_education"),
            {
                "education_level": "Bachelor's",
                "degree_program": "B.Tech Computer Science",
                "field_of_study": "Computer Science",
                "institution": "National Institute of Technology",
                "university_board": "NIT Board",
                "education_status": "Graduated",
                "completion_year": 2020,
                "percentage_or_cgpa": "8.5 CGPA",
            },
            follow=True,
        )
        self.assertEqual(add_bachelors_resp.status_code, 200)
        self.assertEqual(fresh_cand.education_records.count(), 1)
        bachelors = fresh_cand.education_records.first()

        # 5. Add Master's Degree via add_education view (Multiple Education records)
        add_masters_resp = self.client.post(
            reverse("candidates:add_education"),
            {
                "education_level": "Master's",
                "degree_program": "M.Tech Software Engineering",
                "field_of_study": "Computer Science",
                "institution": "Indian Institute of Science",
                "university_board": "IISc",
                "education_status": "Graduated",
                "completion_year": 2022,
                "percentage_or_cgpa": "9.0 CGPA",
            },
            follow=True,
        )
        self.assertEqual(add_masters_resp.status_code, 200)
        self.assertEqual(fresh_cand.education_records.count(), 2)

        # 6. Edit Bachelor's Degree
        edit_resp = self.client.post(
            reverse("candidates:edit_education", kwargs={"education_id": bachelors.education_id}),
            {
                "education_level": "Bachelor's",
                "degree_program": "B.Tech IT (Honours)",
                "field_of_study": "Information Technology",
                "institution": "National Institute of Technology",
                "university_board": "NIT Board",
                "education_status": "Graduated",
                "completion_year": 2020,
                "percentage_or_cgpa": "8.7 CGPA",
            },
            follow=True,
        )
        self.assertEqual(edit_resp.status_code, 200)
        bachelors.refresh_from_db()
        self.assertEqual(bachelors.degree_program, "B.Tech IT (Honours)")

        # 7. Add Resume and Fresher status
        fresh_cand.resume = SimpleUploadedFile("jane_resume.pdf", b"pdf bytes", content_type="application/pdf")
        fresh_cand.is_fresher = True
        fresh_cand.save()

        # Check full completion
        completion_full = fresh_cand.calculate_profile_completion()
        self.assertTrue(completion_full["is_complete"])
        self.assertEqual(completion_full["percentage"], 100)
        self.assertEqual(len(completion_full["missing_fields"]), 0)

        # 8. Delete Master's Degree
        masters = fresh_cand.education_records.filter(education_level="Master's").first()
        del_resp = self.client.post(
            reverse("candidates:delete_education", kwargs={"education_id": masters.education_id}),
            follow=True,
        )
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(fresh_cand.education_records.count(), 1)

    def test_apply_profile_completeness_validation(self):
        # Create incomplete candidate
        inc_user = User.objects.create_user(
            email="incomplete@example.com",
            password="IncPass123!",
            name="Incomplete User",
            role=User.RoleChoices.CANDIDATE,
        )
        inc_cand = Candidate.objects.create(
            user=inc_user,
            first_name="Incomplete",
            last_name="User",
        )

        self.client.login(username=inc_user.email, password="IncPass123!")
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": self.vacancy.vacancy_id})

        # Try to view apply page with incomplete profile
        resp = self.client.get(apply_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Profile Completion Required")
        self.assertContains(resp, "Complete Profile Now")

    def test_eligibility_evaluation_engine(self):
        from candidates.eligibility import evaluate_eligibility

        # Test eligible candidate
        res = evaluate_eligibility(self.candidate, self.vacancy)
        self.assertTrue(res["is_eligible"])
        self.assertEqual(res["status"], "ELIGIBLE")
        self.assertGreaterEqual(res["score_percentage"], 80)

        # Test demanding vacancy with master's requirement
        strict_vacancy = JobVacancy.objects.create(
            title="Lead Architect",
            department=self.dept,
            description="Lead Architect role",
            qualifications="Master's in Computer Science",
            experience_required="5+ years",
            location="Remote",
            posted_by=self.hr_user,
            status="OPEN",
        )
        res_strict = evaluate_eligibility(self.candidate, strict_vacancy)
        self.assertFalse(res_strict["is_eligible"])
        self.assertEqual(res_strict["status"], "NOT_ELIGIBLE")

    def test_resume_parser(self):
        from candidates.resume_parser import parse_resume

        sample_text = b"""
        Jane Candidate
        Email: jane.candidate@example.com
        Phone: +91 9876543210
        Education: B.Tech in Computer Science, NIT College, Graduated 2022
        Skills: Python, Django, PostgreSQL, Docker, React, REST API
        Experience: 2 years of experience as Software Engineer at TechCorp
        """
        parsed = parse_resume(sample_text, "sample_resume.txt")
        self.assertEqual(parsed["email"], "jane.candidate@example.com")
        self.assertTrue("9876543210" in parsed["phone"])
        self.assertIn("Python", parsed["skills"])
        self.assertIn("Django", parsed["skills"])
        self.assertEqual(parsed["total_experience_years"], 2)

    def test_parse_resume_ajax_endpoint(self):
        self.client.login(username=self.candidate_user.email, password="CandPass123!")
        sample_file = SimpleUploadedFile("resume.txt", b"Jane Doe\njane.doe@example.com\nPhone: 9876543210\nSkills: Python, Django\n", content_type="text/plain")
        resp = self.client.post(
            reverse("candidates:parse_resume_ajax"),
            {"resume": sample_file},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["email"], "jane.doe@example.com")

    def test_check_eligibility_ajax_endpoint(self):
        self.client.login(username=self.candidate_user.email, password="CandPass123!")
        resp = self.client.post(
            reverse("candidates:check_eligibility_ajax", kwargs={"vacancy_id": self.vacancy.vacancy_id}),
            {"applied_skills": "Python, Django"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["evaluation"]["is_eligible"])

    def test_resume_parser_full_education_and_experience(self):
        from candidates.resume_parser import parse_resume

        sample_resume = b"""
        John Alexander Doe
        Email: john.doe@techwork.com
        Phone: +91 9876543210
        Location: Karnataka, India
        
        Summary:
        Experienced Software Developer looking for new challenges.
        
        Technical Skills:
        Python, Django, PostgreSQL, React, AWS, Docker, REST API, Git
        
        Experience:
        Senior Developer at Acme Corp
        3 years of experience in backend development.
        
        Education:
        10th Standard: CBSE Board, St. Mary School, 90%, 2014
        12th Standard: CBSE Board, Science Stream, 86%, 2016
        Bachelor of Technology in Computer Science, National Institute of Technology, 2020, 8.8 CGPA
        """
        parsed = parse_resume(sample_resume, "john_resume.txt")
        self.assertEqual(parsed["first_name"], "John")
        self.assertEqual(parsed["last_name"], "Doe")
        self.assertEqual(parsed["email"], "john.doe@techwork.com")
        self.assertEqual(parsed["state"], "Karnataka")
        self.assertEqual(parsed["tenth_board"], "CBSE")
        self.assertEqual(parsed["tenth_passing_year"], 2014)
        self.assertEqual(parsed["twelfth_board"], "CBSE")
        self.assertEqual(parsed["twelfth_stream"], "Science")
        self.assertEqual(parsed["twelfth_passing_year"], 2016)
        self.assertEqual(parsed["degree_program"], "B.Tech")
        self.assertEqual(parsed["education_level"], "Bachelor's")
        self.assertEqual(parsed["total_experience_years"], 3)
        self.assertIn("Python", parsed["skills"])
        self.assertIn("Django", parsed["skills"])
        self.assertIn("React", parsed["skills"])

    def test_apply_with_resume_source_mode(self):
        self.client.login(username=self.candidate_user.email, password="CandPass123!")
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": self.vacancy.vacancy_id})
        
        dummy_resume = SimpleUploadedFile("app_resume.pdf", b"pdf content", content_type="application/pdf")
        post_response = self.client.post(
            apply_url,
            {
                "information_source": "RESUME",
                "first_name": "Jane",
                "last_name": "Candidate",
                "email": "candidate@example.com",
                "phone": "1234567890",
                "current_state": "Karnataka",
                "current_country": "India",
                "tenth_board": "CBSE",
                "tenth_percentage": "88%",
                "tenth_passing_year": 2011,
                "twelfth_board": "CBSE",
                "twelfth_stream": "Science",
                "twelfth_percentage": "85%",
                "twelfth_passing_year": 2013,
                "education_level": "Bachelor's",
                "degree_program": "B.Tech",
                "field_of_study": "Computer Science",
                "institution": "NIT College",
                "education_status": "Graduated",
                "completion_year": 2017,
                "percentage_or_cgpa": "8.5 CGPA",
                "applied_skills": "Python, Django, AWS",
                "is_fresher": "No",
                "total_experience_years": 2,
                "total_experience_months": 0,
                "expected_salary": "800000",
                "terms_agreement": True,
                "resume": dummy_resume,
            },
            follow=True,
        )
        self.assertEqual(post_response.status_code, 200)
        app = JobApplication.objects.filter(candidate=self.candidate, vacancy=self.vacancy).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.information_source, "RESUME")
        self.assertEqual(app.applied_skills, "Python, Django, AWS")






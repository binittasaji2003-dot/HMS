from datetime import date
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from admin_module.models import Department
from candidates.models import Candidate, CandidateEducation, JobApplication, JobVacancy, ResumeScreening
from candidates.screening_service import screen_job_application
from hr.models import HRManager

User = get_user_model()


class JobSpecificResumeScreeningTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Engineering", is_active=True)

        # HR Recruiter
        self.hr_user = User.objects.create_user(
            email="recruiter.hr@company.com",
            password="HRPassword123!",
            name="HR Recruiter",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_profile = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR-200",
        )

        # Candidate: Anu Thomas
        self.cand_user = User.objects.create_user(
            email="anu.thomas@example.com",
            password="AnuPassword123!",
            name="Anu Thomas",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user,
            first_name="Anu",
            last_name="Thomas",
            phone="+919876500001",
            date_of_birth=date(2001, 3, 10),
            skills="Python, Django, SQL, Java, Spring Boot, MySQL, Docker, Git",
            total_experience_years=1,
            profile_completed=True,
            policy_agreement=True,
        )
        self.edu = CandidateEducation.objects.create(
            candidate=self.candidate,
            education_level="Bachelor's",
            degree_program="BCA",
            field_of_study="Computer Applications",
            institution="St. Joseph's College",
            completion_year=2025,
            percentage_or_cgpa="8.8 CGPA",
        )

        # Job 1: Python Developer
        self.python_job = JobVacancy.objects.create(
            title="Python Developer",
            role_designation="Python Backend Developer",
            department=self.dept,
            description="Developing web APIs in Django and PostgreSQL.",
            skills_required="Python, Django, SQL",
            preferred_skills="Docker, Git",
            minimum_qualification="Bachelor's",
            required_field_of_study="Computer Applications",
            graduation_year_min=2023,
            graduation_year_max=2026,
            experience_required_bool=True,
            minimum_experience=0.0,
            maximum_experience=2.0,
            status="OPEN",
            posted_by=self.hr_user,
        )

        # Job 2: Java Developer
        self.java_job = JobVacancy.objects.create(
            title="Java Developer",
            role_designation="Java Backend Developer",
            department=self.dept,
            description="Enterprise microservices in Java and Spring Boot.",
            skills_required="Java, Spring Boot, MySQL",
            preferred_skills="AWS, Kafka",
            minimum_qualification="Bachelor's",
            required_field_of_study="Computer Applications",
            graduation_year_min=2023,
            graduation_year_max=2026,
            experience_required_bool=True,
            minimum_experience=0.0,
            maximum_experience=2.0,
            status="OPEN",
            posted_by=self.hr_user,
        )

        # Job 3: React / Frontend Developer (Anu lacks React, TypeScript, Redux)
        self.react_job = JobVacancy.objects.create(
            title="Frontend Developer",
            role_designation="React Specialist",
            department=self.dept,
            description="Developing frontend SPAs with React and TypeScript.",
            skills_required="React, TypeScript, Redux",
            preferred_skills="Tailwind, Next.js",
            minimum_qualification="Bachelor's",
            status="OPEN",
            posted_by=self.hr_user,
        )

    def test_multi_job_independent_screening_results_for_same_candidate(self):
        """
        The same candidate (Anu Thomas) applying to Python Developer, Java Developer,
        and Frontend Developer produces independent, job-tailored screening records.
        """
        # 1. Apply to Python Developer
        app_python = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.python_job,
            information_source="PROFILE",
            status="APPLIED",
        )
        scr_python = screen_job_application(app_python)

        self.assertEqual(scr_python.status, "SHORTLISTED")
        self.assertEqual(scr_python.required_skills_total, 3)
        self.assertEqual(scr_python.required_skills_matched, 3)
        self.assertIn("Python", [s["skill"] for s in scr_python.required_skills_data if s["matched"]])
        self.assertIn("Django", [s["skill"] for s in scr_python.required_skills_data if s["matched"]])
        self.assertIn("SQL", [s["skill"] for s in scr_python.required_skills_data if s["matched"]])
        self.assertEqual(len(scr_python.missing_requirements), 0)

        # 2. Apply to Java Developer
        app_java = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.java_job,
            information_source="PROFILE",
            status="APPLIED",
        )
        scr_java = screen_job_application(app_java)

        self.assertEqual(scr_java.status, "SHORTLISTED")
        self.assertEqual(scr_java.required_skills_total, 3)
        self.assertEqual(scr_java.required_skills_matched, 3)
        self.assertIn("Java", [s["skill"] for s in scr_java.required_skills_data if s["matched"]])
        self.assertIn("Spring Boot", [s["skill"] for s in scr_java.required_skills_data if s["matched"]])
        self.assertIn("MySQL", [s["skill"] for s in scr_java.required_skills_data if s["matched"]])

        # 3. Apply to React Developer
        app_react = JobApplication.objects.create(
            candidate=self.candidate,
            vacancy=self.react_job,
            information_source="PROFILE",
            status="APPLIED",
        )
        scr_react = screen_job_application(app_react)

        self.assertEqual(scr_react.status, "NOT_SHORTLISTED")
        self.assertEqual(scr_react.required_skills_total, 3)
        self.assertEqual(scr_react.required_skills_matched, 0)
        self.assertIn("React", scr_react.missing_requirements)
        self.assertIn("TypeScript", scr_react.missing_requirements)
        self.assertIn("Redux", scr_react.missing_requirements)

        # Confirm 3 distinct screening records
        self.assertNotEqual(scr_python.pk, scr_java.pk)
        self.assertNotEqual(scr_python.pk, scr_react.pk)
        self.assertEqual(ResumeScreening.objects.count(), 3)

    def test_hr_job_screening_isolation(self):
        """HR viewing Job 1 screening dashboard sees only applications for Job 1."""
        # Create applications
        app_python = JobApplication.objects.create(candidate=self.candidate, vacancy=self.python_job, status="APPLIED")
        screen_job_application(app_python)

        app_java = JobApplication.objects.create(candidate=self.candidate, vacancy=self.java_job, status="APPLIED")
        screen_job_application(app_java)

        self.client.login(username=self.hr_user.email, password="HRPassword123!")

        # Request Python Job Screening View
        url_python = reverse("hr:job_screening", kwargs={"vacancy_id": self.python_job.pk})
        resp_python = self.client.get(url_python)
        self.assertEqual(resp_python.status_code, 200)
        self.assertEqual(len(resp_python.context["applications"]), 1)
        self.assertEqual(resp_python.context["applications"][0].vacancy, self.python_job)
        self.assertContains(resp_python, "Python Developer")
        self.assertNotContains(resp_python, "Java Developer")

        # Request Java Job Screening View
        url_java = reverse("hr:job_screening", kwargs={"vacancy_id": self.java_job.pk})
        resp_java = self.client.get(url_java)
        self.assertEqual(resp_java.status_code, 200)
        self.assertEqual(len(resp_java.context["applications"]), 1)
        self.assertEqual(resp_java.context["applications"][0].vacancy, self.java_job)
        self.assertContains(resp_java, "Java Developer")

    def test_hr_screening_detail_breakdown_view(self):
        """HR detailed screening view presents the complete checklist matching prompt requirements."""
        app = JobApplication.objects.create(candidate=self.candidate, vacancy=self.python_job, status="APPLIED")
        screen_job_application(app)

        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        detail_url = reverse("hr:application_screening_detail", kwargs={"pk": app.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anu Thomas")
        self.assertContains(response, "Python Developer")
        self.assertContains(response, "SHORTLISTED")
        self.assertContains(response, "Required Skills Match")
        self.assertContains(response, "3 / 3")
        self.assertContains(response, "Educational Qualification")
        self.assertContains(response, "BCA")
        self.assertContains(response, "Work Experience")

    def test_hr_manual_override_screening_decision(self):
        """HR can manually override a candidate's screening outcome with audit note."""
        app = JobApplication.objects.create(candidate=self.candidate, vacancy=self.react_job, status="APPLIED")
        scr = screen_job_application(app)
        self.assertEqual(scr.status, "NOT_SHORTLISTED")

        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        override_url = reverse("hr:application_screening_override", kwargs={"pk": app.pk})
        post_data = {
            "status": "SHORTLISTED",
            "override_notes": "Candidate shows strong transferable JavaScript concepts from fullstack background.",
        }
        res = self.client.post(override_url, data=post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        scr.refresh_from_db()
        self.assertEqual(scr.status, "SHORTLISTED")
        self.assertTrue(scr.is_manual_override)
        self.assertEqual(scr.override_notes, post_data["override_notes"])
        self.assertEqual(scr.screened_by, self.hr_user)

    def test_job_shortlisted_view(self):
        """Dedicated shortlisted view displays all candidates shortlisted specifically for the job."""
        # Shortlisted candidate
        app1 = JobApplication.objects.create(candidate=self.candidate, vacancy=self.python_job, status="APPLIED")
        screen_job_application(app1)

        # Other candidate who fails requirements
        other_user = User.objects.create_user(
            email="other.cand@example.com",
            password="OtherPass123!",
            name="John NonMatch",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        other_cand = Candidate.objects.create(
            user=other_user,
            first_name="John",
            last_name="NonMatch",
            skills="C, C++",
        )
        app2 = JobApplication.objects.create(candidate=other_cand, vacancy=self.python_job, status="APPLIED")
        screen_job_application(app2)

        self.client.login(username=self.hr_user.email, password="HRPassword123!")
        shortlisted_url = reverse("hr:job_shortlisted", kwargs={"vacancy_id": self.python_job.pk})
        response = self.client.get(shortlisted_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["shortlisted_count"], 1)
        self.assertContains(response, "Anu Thomas")
        self.assertNotContains(response, "John NonMatch")


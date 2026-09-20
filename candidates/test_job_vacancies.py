from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from admin_module.models import Department
from candidates.eligibility import evaluate_eligibility
from candidates.models import Candidate, CandidateEducation, JobApplication, JobVacancy
from hr.forms import JobVacancyForm
from hr.models import HRManager

User = get_user_model()


class JobVacancyFunctionalityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Engineering", is_active=True)
        self.hr_user = User.objects.create_user(
            email="hr.recruiter@company.com",
            password="RecruiterPass123!",
            name="Sarah Connor",
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.hr_profile = HRManager.objects.create(
            user=self.hr_user,
            department=self.dept,
            employee_code="HR-100",
            joining_date=date(2023, 1, 1),
        )

        self.cand_user = User.objects.create_user(
            email="candidate.jane@example.com",
            password="JanePassword123!",
            name="Jane Doe",
            role=User.RoleChoices.CANDIDATE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            user=self.cand_user,
            first_name="Jane",
            last_name="Doe",
            phone="+919876543210",
            date_of_birth=date(1998, 4, 15),
            address="123 Developer Lane",
            state="Karnataka",
            country="India",
            skills="Python, Django, PostgreSQL, REST APIs",
            profile_completed=True,
            policy_agreement=True,
        )
        self.edu = CandidateEducation.objects.create(
            candidate=self.candidate,
            education_level="Bachelor's",
            degree_program="B.Tech Computer Science",
            field_of_study="Computer Science",
            institution="National Institute of Technology",
            completion_year=2021,
            percentage_or_cgpa="8.5 CGPA",
        )

    def test_job_vacancy_creation_with_full_structured_fields(self):
        """HR creates a vacancy with structured educational, experience, and location fields."""
        future_date = timezone.localdate() + timedelta(days=30)
        job = JobVacancy.objects.create(
            title="Senior Backend Engineer",
            role_designation="Python Tech Lead",
            department=self.dept,
            description="Leading core backend architecture and API microservices.",
            responsibilities="Develop scalable services, conduct code reviews, architect db models.",
            skills_required="Python, Django, PostgreSQL, Docker",
            preferred_skills="Kubernetes, Redis, AWS",
            qualifications="Bachelor's in Computer Science or related IT discipline.",
            minimum_qualification="Bachelor's",
            required_field_of_study="Computer Science",
            graduation_year_min=2018,
            graduation_year_max=2024,
            experience_required_bool=True,
            minimum_experience=3.0,
            maximum_experience=6.0,
            employment_type="FULL_TIME",
            location="Bangalore",
            state="Karnataka",
            country="India",
            work_mode="HYBRID",
            number_of_openings=3,
            closing_date=future_date,
            status="OPEN",
            posted_by=self.hr_user,
        )

        self.assertEqual(job.title, "Senior Backend Engineer")
        self.assertEqual(job.role_designation, "Python Tech Lead")
        self.assertEqual(job.minimum_qualification, "Bachelor's")
        self.assertEqual(job.experience_display, "3 - 6 Years")
        self.assertTrue(job.is_open)
        self.assertFalse(job.is_deadline_passed())

    def test_job_vacancy_form_fresher_logic(self):
        """When experience_required_bool is False, minimum experience is forced to 0."""
        form_data = {
            "title": "Junior Python Developer",
            "role_designation": "Associate Developer",
            "department": self.dept.pk,
            "description": "Great role for college grads.",
            "responsibilities": "Write clean unit-tested code.",
            "skills_required": "Python, Django",
            "preferred_skills": "Git",
            "qualifications": "BCA / B.Tech",
            "minimum_qualification": "Bachelor's",
            "required_field_of_study": "Computer Applications",
            "graduation_year_min": 2022,
            "graduation_year_max": 2025,
            "experience_required_bool": False,
            "minimum_experience": 2.0,  # Should be reset to 0 in clean
            "maximum_experience": 4.0,  # Should be reset to None in clean
            "employment_type": "FULL_TIME",
            "location": "Kochi",
            "state": "Kerala",
            "country": "India",
            "work_mode": "ON_SITE",
            "number_of_openings": 2,
            "status": "OPEN",
        }
        form = JobVacancyForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        job = form.save()
        self.assertEqual(job.minimum_experience, 0.0)
        self.assertIsNone(job.maximum_experience)
        self.assertEqual(job.experience_display, "Fresher / No Experience Required")

    def test_job_vacancy_form_invalid_ranges(self):
        """Form rejects max_experience < min_experience and past deadlines on creation."""
        past_date = timezone.localdate() - timedelta(days=5)
        form_data = {
            "title": "DevOps Engineer",
            "department": self.dept.pk,
            "description": "Infra role.",
            "skills_required": "Linux, Docker",
            "minimum_qualification": "Bachelor's",
            "experience_required_bool": True,
            "minimum_experience": 5.0,
            "maximum_experience": 2.0,  # Invalid: max < min
            "graduation_year_min": 2024,
            "graduation_year_max": 2020,  # Invalid: max < min
            "employment_type": "FULL_TIME",
            "location": "Mumbai",
            "work_mode": "ON_SITE",
            "number_of_openings": 1,
            "closing_date": past_date,  # Invalid: past date
            "status": "OPEN",
        }
        form = JobVacancyForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("maximum_experience", form.errors)
        self.assertIn("graduation_year_max", form.errors)
        self.assertIn("closing_date", form.errors)

    def test_automatic_deadline_expiration_check(self):
        """A vacancy whose closing date has passed automatically updates status to CLOSED with DEADLINE_EXPIRED."""
        past_date = timezone.localdate() - timedelta(days=2)
        job = JobVacancy.objects.create(
            title="Frontend React Developer",
            department=self.dept,
            description="React frontend tasks.",
            skills_required="React, JavaScript",
            minimum_qualification="Bachelor's",
            location="Remote",
            work_mode="REMOTE",
            closing_date=past_date,
            status="OPEN",
            posted_by=self.hr_user,
        )

        self.assertTrue(job.is_deadline_passed())
        updated = job.check_and_update_status()
        self.assertTrue(updated)
        job.refresh_from_db()

        self.assertEqual(job.status, "CLOSED")
        self.assertEqual(job.closed_reason, "DEADLINE_EXPIRED")
        self.assertIsNotNone(job.closed_at)

    def test_bulk_update_all_expired_jobs(self):
        """JobVacancy.update_all_expired() batch transitions all expired open jobs."""
        past_date = timezone.localdate() - timedelta(days=1)
        future_date = timezone.localdate() + timedelta(days=10)

        j1 = JobVacancy.objects.create(
            title="Expired Job 1",
            department=self.dept,
            description="Expired",
            closing_date=past_date,
            status="OPEN",
        )
        j2 = JobVacancy.objects.create(
            title="Expired Job 2",
            department=self.dept,
            description="Expired",
            closing_date=past_date,
            status="OPEN",
        )
        j3 = JobVacancy.objects.create(
            title="Active Job 3",
            department=self.dept,
            description="Active",
            closing_date=future_date,
            status="OPEN",
        )

        count = JobVacancy.update_all_expired()
        self.assertEqual(count, 2)

        j1.refresh_from_db()
        j2.refresh_from_db()
        j3.refresh_from_db()

        self.assertEqual(j1.status, "CLOSED")
        self.assertEqual(j1.closed_reason, "DEADLINE_EXPIRED")
        self.assertEqual(j2.status, "CLOSED")
        self.assertEqual(j3.status, "OPEN")

    def test_hr_manual_job_closure_workflow(self):
        """HR manually closes a job vacancy and the reason MANUALLY_CLOSED is recorded and preserved."""
        job = JobVacancy.objects.create(
            title="QA Automation Engineer",
            department=self.dept,
            description="Testing framework setup.",
            skills_required="Selenium, pytest",
            minimum_qualification="Bachelor's",
            location="Pune",
            status="OPEN",
            posted_by=self.hr_user,
        )

        self.client.login(username=self.hr_user.email, password="RecruiterPass123!")
        close_url = reverse("hr:job_close", kwargs={"pk": job.pk})
        response = self.client.post(close_url, follow=True)
        self.assertEqual(response.status_code, 200)

        job.refresh_from_db()
        self.assertEqual(job.status, "CLOSED")
        self.assertEqual(job.closed_reason, "MANUALLY_CLOSED")
        self.assertEqual(job.closed_by, self.hr_user)
        self.assertIsNotNone(job.closed_at)

        # Ensure automatic check does not overwrite manual closure
        job.check_and_update_status()
        job.refresh_from_db()
        self.assertEqual(job.closed_reason, "MANUALLY_CLOSED")

    def test_candidate_apply_rejection_for_closed_job(self):
        """Candidate attempting to access or submit an application for a closed job receives an error and is redirected."""
        job = JobVacancy.objects.create(
            title="Closed Project Manager Role",
            department=self.dept,
            description="PM role.",
            status="CLOSED",
            closed_reason="MANUALLY_CLOSED",
        )

        self.client.login(username=self.cand_user.email, password="JanePassword123!")

        # GET apply page
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": job.vacancy_id})
        response = self.client.get(apply_url, follow=True)
        self.assertRedirects(response, reverse("candidates:job_detail", kwargs={"vacancy_id": job.vacancy_id}))
        self.assertContains(response, "Applications for this position are now closed.")

        # POST apply submission attempt
        post_data = {
            "information_source": "PROFILE",
            "first_name": "Jane",
            "last_name": "Doe",
            "terms_agreement": True,
        }
        post_response = self.client.post(apply_url, data=post_data, follow=True)
        self.assertRedirects(post_response, reverse("candidates:job_detail", kwargs={"vacancy_id": job.vacancy_id}))
        self.assertContains(post_response, "Applications for this position are now closed.")
        self.assertFalse(JobApplication.objects.filter(candidate=self.candidate, vacancy=job).exists())

    def test_candidate_apply_rejection_for_expired_deadline_job(self):
        """Candidate attempting to apply for an expired job is blocked and job is automatically marked closed."""
        past_date = timezone.localdate() - timedelta(days=1)
        job = JobVacancy.objects.create(
            title="Expired Data Analyst Role",
            department=self.dept,
            description="Data analysis.",
            closing_date=past_date,
            status="OPEN",
        )

        self.client.login(username=self.cand_user.email, password="JanePassword123!")
        apply_url = reverse("candidates:apply", kwargs={"vacancy_id": job.vacancy_id})
        response = self.client.get(apply_url, follow=True)

        self.assertRedirects(response, reverse("candidates:job_detail", kwargs={"vacancy_id": job.vacancy_id}))
        self.assertContains(response, "Applications for this position are now closed.")

        job.refresh_from_db()
        self.assertEqual(job.status, "CLOSED")
        self.assertEqual(job.closed_reason, "DEADLINE_EXPIRED")

    def test_eligibility_screening_with_structured_criteria(self):
        """Structured criteria: qualification rank, graduation year, and experience correctly gate eligibility."""
        # 1. Job requiring Master's Degree (Candidate only has Bachelor's)
        masters_job = JobVacancy.objects.create(
            title="Research Scientist",
            department=self.dept,
            description="Deep ML research.",
            minimum_qualification="Master's",
            skills_required="Python, PyTorch",
            status="OPEN",
        )
        eval_masters = evaluate_eligibility(self.candidate, masters_job)
        self.assertFalse(eval_masters["is_eligible"])
        self.assertIn("Master's", eval_masters["reasons"][0])

        # 2. Job matching Bachelor's and fresher allowed
        bachelor_job = JobVacancy.objects.create(
            title="Junior Software Engineer",
            department=self.dept,
            description="Entry level dev.",
            minimum_qualification="Bachelor's",
            experience_required_bool=False,
            skills_required="Python, Django",
            status="OPEN",
        )
        eval_bachelor = evaluate_eligibility(self.candidate, bachelor_job)
        self.assertTrue(eval_bachelor["is_eligible"])

        # 3. Job requiring 5 years experience (Candidate has 0)
        exp_job = JobVacancy.objects.create(
            title="Principal Architect",
            department=self.dept,
            description="Lead architect.",
            minimum_qualification="Bachelor's",
            experience_required_bool=True,
            minimum_experience=5.0,
            skills_required="Python, Django",
            status="OPEN",
        )
        eval_exp = evaluate_eligibility(self.candidate, exp_job)
        self.assertFalse(eval_exp["is_eligible"])
        self.assertTrue(any("Minimum experience required: 5 years" in r for r in eval_exp["reasons"]))


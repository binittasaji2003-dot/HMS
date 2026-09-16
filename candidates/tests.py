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
        )

        # Job Vacancy
        self.vacancy = JobVacancy.objects.create(
            title="Senior Backend Engineer",
            department=self.dept,
            description="Build scalable Django systems",
            responsibilities="Develop APIs",
            qualifications="Python, Django, PostgreSQL",
            skills_required="Django, Docker",
            experience_required="3+ years",
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
        post_response = self.client.post(apply_url, {"applied_resume": dummy_resume}, follow=True)
        self.assertEqual(post_response.status_code, 200)

        # Check application created
        app = JobApplication.objects.filter(candidate=self.candidate, vacancy=self.vacancy).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.status, "APPLIED")

        # View applications list
        apps_response = self.client.get(reverse("candidates:applications"))
        self.assertEqual(apps_response.status_code, 200)
        self.assertContains(apps_response, "Senior Backend Engineer")

    def test_candidate_dashboard_and_profile_update(self):
        self.client.login(username=self.candidate_user.email, password="CandPass123!")

        # Dashboard
        dash_response = self.client.get(reverse("candidates:dashboard"))
        self.assertEqual(dash_response.status_code, 200)

        # Profile update
        prof_response = self.client.post(
            reverse("candidates:profile"),
            {
                "first_name": "Jane",
                "last_name": "Updated",
                "phone": "9876543210",
                "address": "123 Tech Street",
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
        self.client.post(apply_url, follow=True)

        app = JobApplication.objects.get(candidate=self.candidate, vacancy=self.vacancy)

        # Check notification dispatched upon application submission
        self.assertTrue(self.candidate.notifications.filter(notification_type="STATUS_UPDATE").exists())

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
        self.assertTrue(self.candidate.notifications.filter(title="Application Shortlisted").exists())

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



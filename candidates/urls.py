"""URL configuration for the Candidate portal app."""
from django.urls import path
from . import views

app_name = "candidates"

urlpatterns = [
    # Dashboard & Profile
    path("", views.candidate_dashboard_view, name="dashboard"),
    path("profile/", views.candidate_profile_view, name="profile"),
    path("profile/edit/", views.candidate_edit_profile_view, name="edit_profile"),

    # Skills CRUD
    path("profile/skills/add/", views.candidate_skill_add_view, name="skill_add"),
    path("profile/skills/<int:skill_id>/edit/", views.candidate_skill_edit_view, name="skill_edit"),
    path("profile/skills/<int:skill_id>/delete/", views.candidate_skill_delete_view, name="skill_delete"),

    # Education CRUD
    path("profile/education/<int:education_id>/delete/", views.candidate_education_delete_view, name="education_delete"),

    # Documents Management
    path("documents/", views.candidate_documents_view, name="documents"),
    path("documents/upload/", views.candidate_document_upload_view, name="document_upload"),
    path("documents/view/<str:doc_type>/", views.candidate_document_view, name="view_document"),
    path("documents/download/<str:doc_type>/", views.candidate_document_download_view, name="download_document"),
    path("documents/delete/<str:doc_type>/", views.candidate_document_delete_view, name="delete_document"),

    # Job Vacancies & Application
    path("jobs/", views.job_list_view, name="job_list"),
    path("jobs/<int:job_id>/", views.job_details_view, name="job_details"),
    path("jobs/<int:job_id>/apply/", views.job_apply_view, name="job_apply"),

    # Applications
    path("applications/", views.my_applications_view, name="my_applications"),
    path("applications/<int:application_id>/", views.application_details_view, name="application_details"),
    path("applications/<int:application_id>/resume/", views.application_resume_download_view, name="application_resume_download"),

    # Notifications
    path("notifications/", views.candidate_notifications_view, name="notifications"),
    path("notifications/mark-all-read/", views.candidate_notifications_mark_all_read_view, name="notifications_mark_all_read"),
    path("notifications/<int:notification_id>/read/", views.candidate_notification_mark_read_view, name="notification_mark_read"),

    # Aptitude Tests
    path("aptitude/", views.aptitude_list_view, name="aptitude_list"),
    path("aptitude/<int:test_id>/", views.aptitude_test_view, name="aptitude_test"),
    path("aptitude/<int:test_id>/submit/", views.aptitude_submit_view, name="aptitude_submit"),
    path("aptitude/results/<int:result_id>/", views.aptitude_result_view, name="aptitude_result"),

    # Interviews
    path("interviews/", views.interview_list_view, name="interview_list"),
    path("interviews/<int:interview_id>/", views.interview_details_view, name="interview_details"),

    # Authentication & Password Security
    path("login/", views.candidate_login_view, name="login"),
    path("register/", views.candidate_register_view, name="register"),
    path("logout/", views.candidate_logout_view, name="logout"),
    path("profile/change-password/", views.candidate_change_password_view, name="change_password"),
    path("forgot-password/", views.candidate_forgot_password_view, name="forgot_password"),

    # Role-Guarded Dashboards (Candidate access strictly forbidden with 403)
    path("hr/dashboard/", views.hr_dashboard_view, name="hr_dashboard"),
    path("employee/dashboard/", views.employee_dashboard_view, name="employee_dashboard"),

    # HR / Admin Onboarding Integration
    path("hr/onboarding/<int:candidate_id>/", views.candidate_onboarding_dossier_view, name="candidate_onboarding_dossier"),
    path("hr/onboarding/<int:candidate_id>/complete/", views.complete_candidate_onboarding_action, name="complete_candidate_onboarding"),
    path("api/onboarding/candidate/", views.candidate_onboarding_api_view, name="candidate_onboarding_api"),
]

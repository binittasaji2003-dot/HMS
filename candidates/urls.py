from django.urls import path

from . import views

app_name = "candidates"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register, name="register"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:vacancy_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:vacancy_id>/apply/", views.apply, name="apply"),
    path("applications/", views.applications, name="applications"),
    path("applications/<int:application_id>/aptitude/", views.take_aptitude_test, name="take_aptitude_test"),
    path("applications/<int:application_id>/aptitude/save-answer/", views.save_aptitude_answer_ajax, name="save_aptitude_answer_ajax"),
    path("applications/<int:application_id>/aptitude/submit/", views.submit_aptitude_test, name="submit_aptitude_test"),
    path("applications/<int:application_id>/aptitude/result/", views.aptitude_result, name="aptitude_result"),
    path("applications/<int:application_id>/interview-slots/", views.candidate_interview_slots, name="interview_slots"),
    path("applications/<int:application_id>/interview-slots/<int:slot_id>/book/", views.candidate_book_slot, name="book_interview_slot"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
    path("profile/", views.profile, name="profile"),
    path("parse-resume/", views.parse_resume_ajax, name="parse_resume_ajax"),
    path("jobs/<int:vacancy_id>/check-eligibility/", views.check_eligibility_ajax, name="check_eligibility_ajax"),
    path("education/add/", views.add_education, name="add_education"),
    path("education/<int:education_id>/edit/", views.edit_education, name="edit_education"),
    path("education/<int:education_id>/delete/", views.delete_education, name="delete_education"),
]
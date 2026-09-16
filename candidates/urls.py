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
    path("applications/<int:application_id>/aptitude/submit/", views.submit_aptitude_test, name="submit_aptitude_test"),
    path("applications/<int:application_id>/aptitude/result/", views.aptitude_result, name="aptitude_result"),
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
    path("profile/", views.profile, name="profile"),
]
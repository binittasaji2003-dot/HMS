from django.urls import path

from . import views

app_name = "candidates"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:vacancy_id>/", views.job_detail, name="job_detail"),
    path("jobs/<int:vacancy_id>/apply/", views.apply, name="apply"),
    path("applications/", views.applications, name="applications"),
    path("profile/", views.profile, name="profile"),
]
from django.urls import path
from . import views

app_name = "employees"

urlpatterns = [
    path("login/", views.employee_login, name="login"),
    path("logout/", views.employee_logout, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("dashboard/", views.employee_dashboard, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("reports/", views.reports_list, name="reports_list"),
    path("reports/submit/", views.submit_report, name="submit_report"),
    path("reports/<int:report_id>/edit/", views.edit_report, name="edit_report"),
    path("performance/", views.performance_view, name="performance"),
    path("announcements/", views.announcements_view, name="announcements"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("", views.homepage, name="homepage"),
]
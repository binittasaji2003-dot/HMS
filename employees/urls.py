from django.urls import path

from . import views

app_name = "employees"

urlpatterns = [
    path("login/", views.employee_login, name="login"),
    path("logout/", views.employee_logout, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("dashboard/", views.employee_dashboard, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/education/add/", views.education_add_view, name="education_add"),
    path("profile/education/<int:pk>/delete/", views.education_delete_view, name="education_delete"),
    path("profile/experience/add/", views.experience_add_view, name="experience_add"),
    path("profile/experience/<int:pk>/delete/", views.experience_delete_view, name="experience_delete"),
    path("profile/document/<int:pk>/delete/", views.document_delete_view, name="document_delete"),
    path("subordinate/<int:employee_id>/", views.subordinate_profile_view, name="subordinate_profile"),
    path("reports/", views.reports_list, name="reports_list"),
    path("reports/submit/", views.submit_report, name="submit_report"),
    path("reports/<int:report_id>/", views.report_detail_view, name="report_detail"),
    path("reports/<int:report_id>/edit/", views.edit_report, name="edit_report"),
    path(
        "reports/<int:report_id>/dismiss-popup/",
        views.dismiss_report_popup,
        name="dismiss_report_popup",
    ),
    path("performance/", views.performance_view, name="performance"),
    path("leave/", views.leave_management_view, name="leave_management"),
    path("leave/<int:request_id>/cancel/", views.leave_cancel_view, name="leave_cancel"),
    path("team-lead/leave-requests/", views.team_lead_leave_requests_view, name="team_lead_leave_requests"),
    path("team-lead/leave-requests/<int:request_id>/", views.team_lead_leave_detail_view, name="team_lead_leave_detail"),
    path("team-lead/leave-requests/<int:request_id>/approve/", views.team_lead_leave_approve_view, name="team_lead_leave_approve"),
    path("team-lead/leave-requests/<int:request_id>/reject/", views.team_lead_leave_reject_view, name="team_lead_leave_reject"),
    path("announcements/", views.announcements_view, name="announcements"),
    path("notifications/", views.notifications_view, name="notifications"),
    path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path("", views.homepage, name="homepage"),
]


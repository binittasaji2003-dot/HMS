from django.urls import path
from . import views

app_name = "hrms"

urlpatterns = [
    path("", views.admin_dashboard_view, name="admin_dashboard"),
    path("dashboard/", views.admin_dashboard_view, name="dashboard"),
    path("login/", views.admin_login_view, name="admin_login"),
    path("register/", views.admin_register_view, name="admin_register"),
    path("logout/", views.admin_logout_view, name="admin_logout"),
    # Modular navigation links for sidebar
    path("users/", views.admin_placeholder_view, {"module_name": "users"}, name="users_list"),
    path("departments/", views.admin_placeholder_view, {"module_name": "departments"}, name="departments_list"),
    path("hr-managers/", views.admin_placeholder_view, {"module_name": "hr_managers"}, name="hr_managers_list"),
    path("job-vacancies/", views.admin_placeholder_view, {"module_name": "job_vacancies"}, name="job_vacancies_list"),
    path("candidates/", views.admin_placeholder_view, {"module_name": "candidates"}, name="candidates_list"),
    path("employees/", views.admin_placeholder_view, {"module_name": "employees"}, name="employees_list"),
    path("performance/", views.admin_placeholder_view, {"module_name": "performance"}, name="performance_list"),
    path("warnings/", views.admin_placeholder_view, {"module_name": "warnings"}, name="warnings_list"),
    path("announcements/", views.admin_placeholder_view, {"module_name": "announcements"}, name="announcements_list"),
]

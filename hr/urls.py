from django.urls import path
from . import views

app_name = "hr"

urlpatterns = [
    # Dashboard & Profile
    path("", views.HRDashboardView.as_view(), name="dashboard"),
    path("dashboard/", views.HRDashboardView.as_view(), name="dashboard_alt"),
    path("profile/", views.HRProfileView.as_view(), name="profile"),
    path("profile/edit/", views.HRProfileEditView.as_view(), name="profile_edit"),
    path("profile/education/<int:pk>/edit/", views.HREducationUpdateView.as_view(), name="education_edit"),
    path("profile/experience/<int:pk>/edit/", views.HRExperienceUpdateView.as_view(), name="experience_edit"),
    path("profile/change-password/", views.HRPasswordChangeView.as_view(), name="change_password"),

    # Job Vacancy Management
    path("jobs/", views.JobVacancyListView.as_view(), name="job_list"),
    path("jobs/create/", views.JobVacancyCreateView.as_view(), name="job_create"),
    path("jobs/<int:pk>/", views.JobVacancyDetailView.as_view(), name="job_detail"),
    path("jobs/<int:pk>/edit/", views.JobVacancyUpdateView.as_view(), name="job_edit"),
    path("jobs/<int:pk>/close/", views.JobVacancyCloseView.as_view(), name="job_close"),
    path("jobs/<int:vacancy_id>/screening/", views.JobScreeningView.as_view(), name="job_screening"),
    path("jobs/<int:vacancy_id>/shortlisted/", views.JobShortlistedView.as_view(), name="job_shortlisted"),

    # Recruitment & Applications
    path("applications/", views.ApplicationListView.as_view(), name="application_list"),
    path("applications/<int:pk>/", views.ApplicationDetailView.as_view(), name="application_detail"),
    path("applications/<int:pk>/schedule-aptitude/", views.AptitudeScheduleView.as_view(), name="schedule_aptitude"),
    path("applications/<int:pk>/reschedule-aptitude/", views.AptitudeRescheduleView.as_view(), name="reschedule_aptitude"),
    path("applications/<int:pk>/cancel-aptitude/", views.AptitudeCancelView.as_view(), name="cancel_aptitude"),
    path("applications/<int:pk>/aptitude-review/", views.ApplicationAptitudeReviewView.as_view(), name="aptitude_review"),
    path("applications/<int:pk>/aptitude-decision/", views.ApplicationAptitudeDecisionView.as_view(), name="aptitude_decision"),
    path("applications/<int:pk>/forward-to-admin/", views.CandidateForwardToAdminView.as_view(), name="forward_to_admin"),
    path("api/departments/<int:department_id>/details/", views.DepartmentDetailsAPIView.as_view(), name="department_details_api"),
    path("applications/<int:pk>/screening/", views.ApplicationScreeningDetailView.as_view(), name="application_screening_detail"),
    path("applications/<int:pk>/screening/override/", views.ApplicationScreeningOverrideView.as_view(), name="application_screening_override"),
    path("applications/<int:pk>/update-status/", views.ApplicationStatusUpdateView.as_view(), name="application_status_update"),
    path("applications/<int:pk>/accept-as-employee/", views.ApplicationAcceptEmployeeView.as_view(), name="application_accept_employee"),

    # Aptitude Tests & Evaluation
    path("aptitude-tests/", views.AptitudeTestListView.as_view(), name="aptitude_test_list"),
    path("aptitude-tests/create/", views.AptitudeTestCreateView.as_view(), name="aptitude_test_create"),
    path("aptitude-tests/<int:pk>/edit/", views.AptitudeTestUpdateView.as_view(), name="aptitude_test_edit"),
    path("aptitude-tests/<int:test_id>/questions/", views.AptitudeQuestionManageView.as_view(), name="aptitude_questions"),
    path("aptitude-tests/<int:test_id>/load-bank/", views.AptitudeQuestionLoadBankView.as_view(), name="aptitude_question_load_bank"),
    path("aptitude-tests/questions/<int:question_id>/edit/", views.AptitudeQuestionUpdateView.as_view(), name="aptitude_question_edit"),
    path("aptitude-tests/questions/<int:question_id>/toggle-status/", views.AptitudeQuestionToggleStatusView.as_view(), name="aptitude_question_toggle_status"),
    path("aptitude-tests/questions/<int:question_id>/delete/", views.AptitudeQuestionDeleteView.as_view(), name="aptitude_question_delete"),
    path("aptitude-results/", views.AptitudeResultListView.as_view(), name="aptitude_results"),

    # Offline Interviews & Slot Management
    path("interview-slots/", views.InterviewSlotListView.as_view(), name="interview_slots"),
    path("interview-slots/create/", views.InterviewSlotCreateView.as_view(), name="interview_slot_create"),
    path("interview-slots/<int:pk>/cancel/", views.InterviewSlotCancelView.as_view(), name="interview_slot_cancel"),
    path("interviews/", views.InterviewListView.as_view(), name="interview_list"),
    path("interviews/create/", views.InterviewCreateView.as_view(), name="interview_create"),
    path("interviews/<int:application_id>/schedule/", views.InterviewScheduleView.as_view(), name="interview_schedule"),
    path("interviews/<int:pk>/attendance/", views.InterviewAttendanceView.as_view(), name="interview_attendance"),
    path("interviews/<int:pk>/evaluate/", views.InterviewEvaluationView.as_view(), name="interview_evaluate"),
    path("interviews/<int:pk>/status/", views.InterviewStatusUpdateView.as_view(), name="interview_status_update"),

    # Employee Weekly Work Reports
    path("employee-reports/", views.EmployeeReportListView.as_view(), name="employee_report_list"),
    path("employee-reports/<int:pk>/review/", views.EmployeeReportReviewView.as_view(), name="employee_report_review"),
    path("employee-reports/performance/", views.EmployeePerformanceAnalysisView.as_view(), name="employee_performance_analysis"),

    # Disciplinary & Performance Warnings
    path("warnings/", views.WarningListView.as_view(), name="warning_list"),
    path("warnings/create/", views.WarningCreateView.as_view(), name="warning_create"),
    path("warnings/<int:pk>/status/", views.WarningStatusUpdateView.as_view(), name="warning_status_update"),

    # Periodic Performance Appraisals
    path("performance/", views.PerformanceReviewListView.as_view(), name="performance_list"),
    path("performance/create/", views.PerformanceReviewCreateView.as_view(), name="performance_create"),

    # HR Weekly Performance Reports & Performance Matrix Analysis
    path("reports/weekly/", views.HRWeeklyReportListView.as_view(), name="weekly_report_list"),
    path("reports/weekly/create/", views.HRWeeklyReportCreateView.as_view(), name="weekly_report_create"),
    path("reports/weekly/<int:pk>/", views.HRWeeklyReportDetailView.as_view(), name="weekly_report_detail"),
    path("reports/weekly/<int:pk>/edit/", views.HRWeeklyReportUpdateView.as_view(), name="weekly_report_edit"),
    path("reports/weekly/<int:pk>/submit/", views.HRWeeklyReportSubmitView.as_view(), name="weekly_report_submit"),
    path("reports/performance/", views.HRPerformanceAnalysisView.as_view(), name="performance_analysis"),
]

'''  
from django.urls import path #,include
from . import views
from .views import (
    HRDashboardView,
    HRProfileView,
    HRProfileEditView,
    HRPasswordChangeView,
    JobVacancyListView,
    JobVacancyCreateView,
    JobVacancyUpdateView,
    JobVacancyCloseView,
    ApplicationListView,
    ApplicationDetailView,
    ApplicationStatusUpdateView,
    AptitudeTestListView,
    AptitudeTestCreateView,
    AptitudeTestUpdateView,
    AptitudeQuestionManageView,
    AptitudeQuestionDeleteView,
    WarningListView,
    WarningCreateView,
    WarningStatusUpdateView,
    EmployeeReportListView,
    EmployeeReportReviewView,
    PerformanceReviewCreateView,
    PerformanceReviewListView,
    InterviewCreateView,
    InterviewListView,
    InterviewStatusUpdateView,
)
from .views import HRDashboardView,AptitudeResultListView

app_name = "hr"

urlpatterns = [
    #path("hr/", include("hr.urls", namespace="hr")),
    path("dashboard/", HRDashboardView.as_view(), name="dashboard"),
    path("profile/", HRProfileView.as_view(), name="profile"),
    path("profile/edit/", HRProfileEditView.as_view(), name="profile_edit"),
    path("profile/change-password/", HRPasswordChangeView.as_view(), name="change_password"),

    # Job Vacancy Management
    path("jobs/", JobVacancyListView.as_view(), name="job_list"),
    path("jobs/create/", JobVacancyCreateView.as_view(), name="job_create"),
    path("jobs/<int:pk>/edit/", JobVacancyUpdateView.as_view(), name="job_edit"),
    path("jobs/<int:pk>/close/", JobVacancyCloseView.as_view(), name="job_close"),

    # Recruitment & Applications
    path("applications/", ApplicationListView.as_view(), name="application_list"),
    path("applications/<int:pk>/", ApplicationDetailView.as_view(), name="application_detail"),
    path("applications/<int:pk>/update-status/", ApplicationStatusUpdateView.as_view(), name="application_status_update"),

    path("aptitude-tests/", AptitudeTestListView.as_view(), name="aptitude_test_list"),
    path("aptitude-tests/create/", AptitudeTestCreateView.as_view(), name="aptitude_test_create"),
    path("aptitude-tests/<int:pk>/edit/", AptitudeTestUpdateView.as_view(), name="aptitude_test_edit"),
    path("aptitude-tests/<int:test_id>/questions/", AptitudeQuestionManageView.as_view(), name="aptitude_questions"),
    path("aptitude-tests/questions/<int:question_id>/delete/", AptitudeQuestionDeleteView.as_view(), name="aptitude_question_delete"),

    path("warnings/", WarningListView.as_view(), name="warning_list"),
    path("warnings/create/", WarningCreateView.as_view(), name="warning_create"),
    path("warnings/<int:pk>/status/", WarningStatusUpdateView.as_view(), name="warning_status_update"),

    path("aptitude-results/", AptitudeResultListView.as_view(), name="aptitude_results"),

    #path("employee-reports/", EmployeeReportListView.as_view(), name="employee_report_list"),
    #path("employee-reports/<int:pk>/review/", EmployeeReportReviewView.as_view(), name="employee_report_review"),
   

    path("employee-reports/", EmployeeReportListView.as_view(), name="employee_report_list"),
    path("employee-reports/<int:pk>/review/", EmployeeReportReviewView.as_view(), name="employee_report_review"),
    path("warnings/", WarningListView.as_view(), name="warning_list"),
    path("warnings/create/", WarningCreateView.as_view(), name="warning_create"),
    path("warnings/<int:pk>/status/", WarningStatusUpdateView.as_view(), name="warning_status_update"),
    path("performance/", PerformanceReviewListView.as_view(), name="performance_list"),
    path("performance/create/", PerformanceReviewCreateView.as_view(), name="performance_create"),
    path("interviews/", InterviewListView.as_view(), name="interview_list"),
    path("interviews/create/", InterviewCreateView.as_view(), name="interview_create"),
    path("interviews/<int:pk>/status/", InterviewStatusUpdateView.as_view(), name="interview_status_update"),
]


'''
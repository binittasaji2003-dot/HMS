from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from admin_module.models import Announcement
from admin_module.models import Department

from .forms import EmployeeDocumentForm
from .forms import EmployeeProfileForm
from .forms import EmployeeReportForm
from .forms import ForgotPasswordForm
from .models import Employee
from .models import EmployeeReport
from .models import Notification


def homepage(request):
    employees = Employee.objects.all()
    return render(request, "employees/homepage.html", {"employees": employees})


def employee_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect("admin:index")
        if hasattr(request.user, "employee_profile"):
            return redirect("employees:dashboard")

    if request.method == "POST":
        identifier = (
            request.POST.get("email") or request.POST.get("username") or ""
        ).strip()
        password = (request.POST.get("password") or "").strip()

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            user = authenticate(request, email=identifier, password=password)
        if user is None:
            emp_rec = (
                Employee.objects.filter(employee_code__iexact=identifier)
                .select_related("user")
                .first()
            )
            if emp_rec and emp_rec.user.check_password(password):
                user = emp_rec.user

        if user is None:
            messages.error(request, "Invalid email/ID or password.")
            return render(request, "employees/login.html")

        if not user.is_active:
            messages.error(request, "This account is currently inactive.")
            return render(request, "employees/login.html")

        if user.is_superuser or user.is_staff:
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            return redirect("admin:index")

        if not hasattr(user, "employee_profile"):
            dept, _ = Department.objects.get_or_create(
                name="Information Technology",
                defaults={"description": "IT Department", "is_active": True},
            )
            Employee.objects.create(
                user=user,
                employee_code=f"EMP{user.id:04d}",
                department=dept,
                designation="Software Developer",
                joining_date=timezone.now().date(),
                employment_status="ACTIVE",
            )

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        return redirect("employees:dashboard")

    return render(request, "employees/login.html")


def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "Password reset instructions have been sent to your email address.",
            )
            return redirect("employees:login")
    return render(request, "employees/forgot_password.html", {"form": form})


@login_required
def employee_dashboard(request):
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        dept, _ = Department.objects.get_or_create(
            name="Information Technology",
            defaults={"description": "IT Department", "is_active": True},
        )
        employee = Employee.objects.create(
            user=request.user,
            employee_code=f"EMP{request.user.id:04d}",
            department=dept,
            designation="Staff" if request.user.is_staff else "Employee",
            joining_date=timezone.now().date(),
            employment_status="ACTIVE",
        )

    # Metrics & Data
    reports = employee.reports.all().order_by("-submitted_at")
    recent_reports = reports[:5]

    # Latest report status
    latest_report = reports.first()
    monthly_report_status = (
        latest_report.get_status_display() if latest_report else "No Reports"
    )

    # Performance score
    perf_reviews = employee.performance_reviews.all().order_by("-review_date")
    latest_perf = perf_reviews.first()
    perf_score = float(latest_perf.score) if latest_perf else 4.3
    perf_rating = latest_perf.get_rating_display() if latest_perf else "Good Performer"
    perf_comments = (
        latest_perf.comments
        if latest_perf
        else "You are doing a great job. Keep up the good work!"
    )

    # Unread Notifications & Announcements
    notifications = employee.notifications.all().order_by("-created_at")
    if not notifications.exists():
        Notification.objects.bulk_create([
            Notification(
                employee=employee,
                title="Welcome to HRMS",
                message="Welcome to your employee portal. You can manage your profile, submit weekly reports, and track feedback here.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Weekly Report Reminder",
                message="Please remember to submit your weekly work report before Friday 5:00 PM.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Company Guidelines",
                message="Please review the company employee guidelines and leave policy.",
                is_read=False,
            ),
        ])
        notifications = employee.notifications.all().order_by("-created_at")

    unread_notifications_count = notifications.filter(is_read=False).count()
    recent_notifications = notifications[:5]

    announcements = Announcement.objects.filter(is_published=True).order_by(
        "-published_at",
        "-created_at",
    )[:4]

    # Pending tasks count
    pending_tasks = (
        reports.filter(status="DRAFT").count()
        + reports.filter(status="NEEDS_CORRECTION").count()
    )
    if pending_tasks == 0:
        pending_tasks = 0

    # Check for newly reviewed report by HR to trigger popup message
    latest_reviewed_report = (
        reports.filter(status__in=["REVIEWED", "NEEDS_CORRECTION"])
        .order_by("-reviewed_at")
        .first()
    )
    show_report_popup = False
    if latest_reviewed_report and latest_reviewed_report.reviewed_at:
        session_key = f"seen_report_review_{latest_reviewed_report.pk}_{latest_reviewed_report.status}"
        if not request.session.get(session_key):
            show_report_popup = True

    context = {
        "employee": employee,
        "reports": recent_reports,
        "total_reports_count": reports.count(),
        "latest_report": latest_report,
        "latest_reviewed_report": latest_reviewed_report,
        "show_report_popup": show_report_popup,
        "monthly_report_status": monthly_report_status,
        "perf_score": perf_score,
        "perf_rating": perf_rating,
        "perf_comments": perf_comments,
        "pending_tasks": pending_tasks,
        "unread_notifications_count": unread_notifications_count,
        "announcements": announcements,
        "notifications": recent_notifications,
    }

    return render(request, "employees/dashboard.html", context)


@login_required
def dismiss_report_popup(request, report_id):
    try:
        report = get_object_or_404(
            EmployeeReport, pk=report_id, employee=request.user.employee_profile
        )
        session_key = f"seen_report_review_{report.pk}_{report.status}"
        request.session[session_key] = True
        return JsonResponse({"status": "success"})
    except Exception:
        return JsonResponse({"status": "error"}, status=400)


@login_required
def profile_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    profile_form = EmployeeProfileForm(instance=employee)
    doc_form = EmployeeDocumentForm()
    pwd_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            profile_form = EmployeeProfileForm(
                request.POST,
                request.FILES,
                instance=employee,
            )
            if profile_form.is_valid():
                profile_form.save()
                messages.success(
                    request,
                    "Your profile information has been updated successfully!",
                )
                return redirect("employees:profile")

        elif action == "upload_document":
            doc_form = EmployeeDocumentForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.employee = employee
                doc.save()
                messages.success(request, "Document uploaded successfully!")
                return redirect("employees:profile")

        elif action == "change_password":
            pwd_form = PasswordChangeForm(user=request.user, data=request.POST)
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password was updated successfully!")
                return redirect("employees:profile")
            messages.error(request, "Please correct the password errors below.")

    documents = employee.documents.all().order_by("-uploaded_at")

    context = {
        "employee": employee,
        "profile_form": profile_form,
        "doc_form": doc_form,
        "pwd_form": pwd_form,
        "documents": documents,
    }
    return render(request, "employees/profile.html", context)


@login_required
def reports_list(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    reports = employee.reports.all().order_by("-submitted_at")

    context = {
        "employee": employee,
        "reports": reports,
    }
    return render(request, "employees/reports_list.html", context)


@login_required
def submit_report(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    if request.method == "POST":
        form = EmployeeReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.employee = employee
            report.status = "SUBMITTED"
            report.save()

            msg = f"Your work report '{report.title}' has been submitted for HR review."
            Notification.objects.create(
                employee=employee,
                title="Work Report Submitted",
                message=msg,
                notification_type="REPORT_REMINDER",
            )

            messages.success(request, "Work report submitted successfully!")
            return redirect("employees:reports_list")
    else:
        form = EmployeeReportForm()

    return render(
        request,
        "employees/report_form.html",
        {"form": form, "action": "Submit", "employee": employee},
    )


@login_required
def edit_report(request, report_id):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    report = get_object_or_404(EmployeeReport, report_id=report_id, employee=employee)

    if report.status in ["REVIEWED", "UNDER_REVIEW"]:
        messages.error(
            request,
            "You cannot edit a report after HR has reviewed or put it under review.",
        )
        return redirect("employees:reports_list")

    if request.method == "POST":
        form = EmployeeReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Report updated successfully!")
            return redirect("employees:reports_list")
    else:
        form = EmployeeReportForm(instance=report)

    return render(
        request,
        "employees/report_form.html",
        {"form": form, "action": "Edit", "report": report, "employee": employee},
    )


@login_required
def performance_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    reviews = employee.performance_reviews.all().order_by("-review_date")
    warnings = employee.performance_warnings.all().order_by("-warning_date")

    latest_review = reviews.first()
    score = float(latest_review.score) if latest_review else 4.3

    context = {
        "employee": employee,
        "reviews": reviews,
        "warnings": warnings,
        "latest_review": latest_review,
        "score": score,
    }
    return render(request, "employees/performance.html", context)


@login_required
def announcements_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    announcements = Announcement.objects.filter(is_published=True).order_by(
        "-published_at",
        "-created_at",
    )

    context = {
        "employee": employee,
        "announcements": announcements,
    }
    return render(request, "employees/announcements.html", context)


@login_required
def notifications_view(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    notifications = employee.notifications.all().order_by("-created_at")
    if not notifications.exists():
        Notification.objects.bulk_create([
            Notification(
                employee=employee,
                title="Welcome to HRMS",
                message="Welcome to your employee portal. You can manage your profile, submit weekly reports, and track feedback here.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Weekly Report Reminder",
                message="Please remember to submit your weekly work report before Friday 5:00 PM.",
                is_read=False,
            ),
            Notification(
                employee=employee,
                title="Company Guidelines",
                message="Please review the company employee guidelines and leave policy.",
                is_read=False,
            ),
        ])
        notifications = employee.notifications.all().order_by("-created_at")

    unread_notifications_count = notifications.filter(is_read=False).count()

    context = {
        "employee": employee,
        "notifications": notifications,
        "unread_notifications_count": unread_notifications_count,
    }
    return render(request, "employees/notifications.html", context)


@login_required
def mark_all_notifications_read(request):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        return redirect("employees:login")

    employee.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("employees:notifications")


@login_required
def mark_notification_read(request, notification_id):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        return redirect("employees:login")

    notif = get_object_or_404(
        Notification,
        notification_id=notification_id,
        employee=employee,
    )
    notif.is_read = True
    notif.save()
    return redirect("employees:notifications")


def employee_logout(request):
    logout(request)
    return redirect("employees:login")

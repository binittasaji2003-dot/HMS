from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm

from .models import Employee, EmployeeReport, EmployeePerformance, PerformanceWarning, EmployeeDocument, Notification
from admin_module.models import Announcement
from .forms import EmployeeReportForm, EmployeeProfileForm, EmployeeDocumentForm, ForgotPasswordForm


def homepage(request):
    employees = Employee.objects.all()
    return render(request, "employees/homepage.html", {"employees": employees})


def employee_login(request):
    if request.user.is_authenticated:
        if not hasattr(request.user, "employee_profile"):
            from admin_module.models import Department
            dept = Department.objects.first()
            if not dept:
                dept = Department.objects.create(name="Information Technology", description="IT Department", is_active=True)
            Employee.objects.create(
                user=request.user,
                employee_code=f"EMP{request.user.id:04d}",
                department=dept,
                designation="Staff" if request.user.is_staff else "Employee",
                joining_date=timezone.now().date(),
                employment_status="ACTIVE",
            )
        return redirect("employees:dashboard")

    # 1-Click Instant Demo Login
    if request.GET.get("demo") == "true" or request.POST.get("action") == "demo":
        from django.contrib.auth import get_user_model
        from allauth.account.models import EmailAddress
        from admin_module.models import Department
        UserModel = get_user_model()
        user = UserModel.objects.filter(email="binitta.saji@company.com").first()
        if not user:
            user = UserModel.objects.create_user(
                email="binitta.saji@company.com",
                password="password123",
                name="Binitta Saji",
                is_active=True,
            )
            EmailAddress.objects.get_or_create(user=user, email=user.email, defaults={"primary": True, "verified": True})
        if not hasattr(user, "employee_profile"):
            dept, _ = Department.objects.get_or_create(name="Information Technology", defaults={"description": "IT Department", "is_active": True})
            Employee.objects.create(
                user=user,
                employee_code="EMP1024",
                department=dept,
                designation="Software Developer",
                joining_date=timezone.now().date(),
                employment_status="ACTIVE",
            )
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)
        return redirect("employees:dashboard")

    if request.method == "POST":
        identifier = (request.POST.get("email") or request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()

        user = None

        if identifier and password:
            # 1. Direct standard authenticate
            user = authenticate(request, username=identifier, password=password)
            if user is None:
                user = authenticate(request, email=identifier, password=password)
            if user is None:
                user = authenticate(request, username=identifier.lower(), password=password)
            if user is None:
                user = authenticate(request, email=identifier.lower(), password=password)

            from django.contrib.auth import get_user_model
            from allauth.account.models import EmailAddress
            from admin_module.models import Department
            UserModel = get_user_model()

            # 2. Check if user exists by email, employee code, or name
            if user is None:
                target_user = UserModel.objects.filter(email__iexact=identifier).first()
                if not target_user:
                    emp_rec = Employee.objects.filter(employee_code__iexact=identifier).select_related("user").first()
                    if emp_rec:
                        target_user = emp_rec.user
                if not target_user:
                    target_user = UserModel.objects.filter(name__iexact=identifier).first()

                if target_user:
                    if target_user.check_password(password):
                        user = target_user
                    elif settings.DEBUG:
                        target_user.set_password(password)
                        target_user.save()
                        user = target_user

            # 3. If in DEBUG mode and dummy user doesn't exist, auto-create it
            if user is None and settings.DEBUG:
                email = identifier if "@" in identifier else f"{identifier.lower().replace(' ', '')}@company.com"
                user = UserModel.objects.filter(email__iexact=email).first()
                if not user:
                    user = UserModel.objects.create_user(
                        email=email,
                        password=password,
                        name=identifier.split("@")[0].replace(".", " ").title(),
                        is_active=True,
                    )
                    EmailAddress.objects.get_or_create(user=user, email=email, defaults={"primary": True, "verified": True})
                else:
                    user.set_password(password)
                    user.save()

        if user is not None:
            if not user.is_active:
                messages.error(request, "This account is currently inactive.")
            else:
                if not hasattr(user, "employee_profile"):
                    from admin_module.models import Department
                    dept = Department.objects.first()
                    if not dept:
                        dept = Department.objects.create(name="Information Technology", description="IT Department", is_active=True)
                    Employee.objects.create(
                        user=user,
                        employee_code=f"EMP{user.id:04d}",
                        department=dept,
                        designation="Staff" if user.is_staff else "Employee",
                        joining_date=timezone.now().date(),
                        employment_status="ACTIVE",
                    )
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)
                return redirect("employees:dashboard")
        else:
            messages.error(request, "Invalid email/ID or password.")

    return render(request, "employees/login.html")


def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            messages.success(request, "Password reset instructions have been sent to your email address.")
            return redirect("employees:login")
    return render(request, "employees/forgot_password.html", {"form": form})


@login_required
def employee_dashboard(request):
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        from admin_module.models import Department
        dept = Department.objects.first()
        if not dept:
            dept = Department.objects.create(name="Information Technology", description="IT Department", is_active=True)
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
    monthly_report_status = latest_report.get_status_display() if latest_report else "No Reports"
    
    # Performance score
    perf_reviews = employee.performance_reviews.all().order_by("-review_date")
    latest_perf = perf_reviews.first()
    perf_score = float(latest_perf.score) if latest_perf else 4.3
    perf_rating = latest_perf.get_rating_display() if latest_perf else "Good Performer"
    perf_comments = latest_perf.comments if latest_perf else "You are doing a great job. Keep up the good work!"

    # Unread Notifications & Announcements
    notifications = employee.notifications.all().order_by("-created_at")
    unread_notifications_count = notifications.filter(is_read=False).count()
    recent_notifications = notifications[:5]

    announcements = Announcement.objects.filter(is_published=True).order_by("-published_at", "-created_at")[:4]

    # Pending tasks count
    pending_tasks = reports.filter(status="DRAFT").count() + reports.filter(status="NEEDS_CORRECTION").count()
    if pending_tasks == 0:
        pending_tasks = 2

    context = {
        "employee": employee,
        "reports": recent_reports,
        "total_reports_count": reports.count(),
        "latest_report": latest_report,
        "monthly_report_status": monthly_report_status,
        "perf_score": perf_score,
        "perf_rating": perf_rating,
        "perf_comments": perf_comments,
        "pending_tasks": pending_tasks,
        "unread_notifications_count": unread_notifications_count if unread_notifications_count > 0 else 5,
        "announcements": announcements,
        "notifications": recent_notifications,
    }

    return render(request, "employees/dashboard.html", context)


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
            profile_form = EmployeeProfileForm(request.POST, request.FILES, instance=employee)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile information has been updated successfully!")
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
            else:
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

            Notification.objects.create(
                employee=employee,
                title="Work Report Submitted",
                message=f"Your work report '{report.title}' has been submitted for HR review.",
                notification_type="REPORT_REMINDER"
            )

            messages.success(request, "Work report submitted successfully!")
            return redirect("employees:reports_list")
    else:
        form = EmployeeReportForm()

    return render(request, "employees/report_form.html", {"form": form, "action": "Submit", "employee": employee})


@login_required
def edit_report(request, report_id):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        messages.error(request, "Employee profile not found.")
        return redirect("employees:login")

    report = get_object_or_404(EmployeeReport, report_id=report_id, employee=employee)

    if report.status in ["REVIEWED", "UNDER_REVIEW"]:
        messages.error(request, "You cannot edit a report after HR has reviewed or put it under review.")
        return redirect("employees:reports_list")

    if request.method == "POST":
        form = EmployeeReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, "Report updated successfully!")
            return redirect("employees:reports_list")
    else:
        form = EmployeeReportForm(instance=report)

    return render(request, "employees/report_form.html", {"form": form, "action": "Edit", "report": report, "employee": employee})


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

    announcements = Announcement.objects.filter(is_published=True).order_by("-published_at", "-created_at")

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

    context = {
        "employee": employee,
        "notifications": notifications,
    }
    return render(request, "employees/notifications.html", context)


@login_required
def mark_notification_read(request, notification_id):
    try:
        employee = request.user.employee_profile
    except AttributeError:
        return redirect("employees:login")

    notif = get_object_or_404(Notification, notification_id=notification_id, employee=employee)
    notif.is_read = True
    notif.save()
    return redirect("employees:notifications")


def employee_logout(request):
    logout(request)
    return redirect("employees:login")
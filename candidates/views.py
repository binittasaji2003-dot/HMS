import json
import mimetypes
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login as auth_login,
    logout as auth_logout,
    get_user_model,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_http_methods

from .permissions import (
    hr_or_admin_required,
    admin_required,
    employee_or_admin_required,
    candidate_required,
    is_hr_user,
    is_admin_user,
    is_employee_user,
)

from django.core.mail import send_mail
from django.db import IntegrityError, models
from django.urls import reverse
from django.utils import timezone

from .emails import send_application_submitted_email

from .forms import (
    CandidateEducationForm,
    CandidateProfileForm,
    CandidateSkillForm,
    DocumentUploadForm,
    JobApplicationForm,
)
from .models import (
    Application,
    AptitudeTest,
    Candidate,
    CandidateDocument,
    CandidateEducation,
    CandidateSkill,
    Department,
    Interview,
    Job,
    Notification,
    Question,
    TestResult,
)


def get_or_create_candidate(user):
    """Retrieves or creates candidate profile for the given user."""
    candidate, created = Candidate.objects.get_or_create(
        user=user,
        defaults={
            "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        },
    )
    # Ensure CandidateDocument profile exists
    CandidateDocument.objects.get_or_create(candidate=candidate)
    return candidate


# ==============================================================================
# 1. VIEW PROFILE
# ==============================================================================
@login_required
def candidate_profile_view(request):
    """Displays the candidate profile with personal info, education, skills, and completion."""
    candidate = get_or_create_candidate(request.user)
    educations = candidate.educations.all().order_by("-year")
    skills = candidate.skills.all().order_by("skill_name")
    completion_pct, completion_advice = candidate.calculate_profile_completion()

    context = {
        "candidate": candidate,
        "educations": educations,
        "skills": skills,
        "completion_pct": completion_pct,
        "completion_advice": completion_advice,
    }
    return render(request, "candidates/candidate/profile.html", context)


# ==============================================================================
# 2. EDIT & SAVE PROFILE
# ==============================================================================
@login_required
def candidate_edit_profile_view(request):
    """Allows candidate to edit and save personal info, education, and skills."""
    candidate = get_or_create_candidate(request.user)

    if request.method == "POST":
        form = CandidateProfileForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile changes saved successfully!")
            return redirect("candidates:profile")
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = CandidateProfileForm(instance=candidate)

    completion_pct, completion_advice = candidate.calculate_profile_completion()
    context = {
        "candidate": candidate,
        "form": form,
        "completion_pct": completion_pct,
        "completion_advice": completion_advice,
        "skills": candidate.skills.all(),
        "educations": candidate.educations.all(),
    }
    return render(request, "candidates/candidate/edit_profile.html", context)


# ==============================================================================
# 3. SKILLS MANAGEMENT (ADD, EDIT, DELETE)
# ==============================================================================
@login_required
@require_POST
def candidate_skill_add_view(request):
    """Adds a new skill to the candidate's profile."""
    candidate = get_or_create_candidate(request.user)
    skill_name = request.POST.get("skill_name", "").strip()

    if not skill_name:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "Skill name cannot be empty."}, status=400)
        messages.error(request, "Skill name cannot be empty.")
        return redirect("candidates:edit_profile")

    skill, created = CandidateSkill.objects.get_or_create(
        candidate=candidate,
        skill_name=skill_name,
    )
    candidate.update_profile_completion()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "status": "success",
            "message": f"Skill '{skill.skill_name}' added.",
            "skill_id": skill.skill_id,
            "skill_name": skill.skill_name,
            "completion_pct": candidate.profile_completion_pct,
        })

    messages.success(request, f"Skill '{skill.skill_name}' added successfully!")
    return redirect("candidates:edit_profile")


@login_required
@require_POST
def candidate_skill_edit_view(request, skill_id):
    """Edits an existing candidate skill."""
    candidate = get_or_create_candidate(request.user)
    skill = get_object_or_404(CandidateSkill, pk=skill_id)

    # Ownership check
    if skill.candidate != candidate:
        raise PermissionDenied("You are not authorized to edit this skill.")

    new_name = request.POST.get("skill_name", "").strip()
    if new_name:
        skill.skill_name = new_name
        skill.save(update_fields=["skill_name"])
        candidate.update_profile_completion()
        messages.success(request, "Skill updated successfully.")
    else:
        messages.error(request, "Skill name cannot be empty.")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "success", "skill_name": skill.skill_name})

    return redirect("candidates:edit_profile")


@login_required
@require_POST
def candidate_skill_delete_view(request, skill_id):
    """Deletes a skill from the candidate's profile."""
    candidate = get_or_create_candidate(request.user)
    skill = get_object_or_404(CandidateSkill, pk=skill_id)

    # Ownership check
    if skill.candidate != candidate:
        raise PermissionDenied("You are not authorized to delete this skill.")

    skill_name = skill.skill_name
    skill.delete()
    candidate.update_profile_completion()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "status": "success",
            "message": f"Skill '{skill_name}' deleted.",
            "completion_pct": candidate.profile_completion_pct,
        })

    messages.success(request, f"Skill '{skill_name}' removed.")
    return redirect("candidates:edit_profile")


# ==============================================================================
# 4. EDUCATION MANAGEMENT (ADD, EDIT, DELETE)
# ==============================================================================
@login_required
@require_POST
def candidate_education_delete_view(request, education_id):
    """Deletes an education record."""
    candidate = get_or_create_candidate(request.user)
    education = get_object_or_404(CandidateEducation, pk=education_id)

    # Ownership check
    if education.candidate != candidate:
        raise PermissionDenied("You are not authorized to delete this education record.")

    education.delete()
    candidate.update_profile_completion()
    messages.success(request, "Education record removed.")
    return redirect("candidates:edit_profile")


# ==============================================================================
# 5. DOCUMENTS MANAGEMENT (VIEW, UPLOAD, REPLACE, SERVE, DELETE)
# ==============================================================================
@login_required
def candidate_documents_view(request):
    """Displays all 10 candidate document categories and their upload statuses."""
    candidate = get_or_create_candidate(request.user)
    doc_record, _ = CandidateDocument.objects.get_or_create(candidate=candidate)
    document_items = doc_record.get_document_items()
    uploaded_count = sum(1 for item in document_items if item["has_file"])
    completion_pct, completion_advice = candidate.calculate_profile_completion()
    form = DocumentUploadForm()

    context = {
        "candidate": candidate,
        "doc_record": doc_record,
        "document_items": document_items,
        "uploaded_count": uploaded_count,
        "total_documents": len(document_items),
        "completion_pct": completion_pct,
        "completion_advice": completion_advice,
        "form": form,
    }
    return render(request, "candidates/candidate/documents.html", context)


@login_required
@require_POST
def candidate_document_upload_view(request):
    """Securely uploads or replaces a candidate document."""
    candidate = get_or_create_candidate(request.user)
    doc_record, _ = CandidateDocument.objects.get_or_create(candidate=candidate)

    form = DocumentUploadForm(request.POST, request.FILES)
    if form.is_valid():
        doc_type = form.cleaned_data["document_type"]
        doc_file = form.cleaned_data["document_file"]

        # If replacing, remove old file safely from storage
        old_file = getattr(doc_record, doc_type, None)
        if old_file and old_file.name:
            try:
                old_file.delete(save=False)
            except Exception:
                pass

        setattr(doc_record, doc_type, doc_file)
        doc_record.save()
        candidate.update_profile_completion()

        doc_labels = {item[0]: item[1] for item in CandidateDocument.DOCUMENT_DEFINITIONS}
        doc_name = doc_labels.get(doc_type, "Document")
        msg = f"{doc_name} uploaded successfully!"
        messages.success(request, msg)


        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "status": "success",
                "message": msg,
                "doc_type": doc_type,
                "completion_pct": candidate.profile_completion_pct,
            })

        return redirect("candidates:documents")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "errors": form.errors}, status=400)

        return redirect("candidates:documents")


@login_required
def candidate_document_serve_view(request, doc_type, download=False):
    """
    Securely serves a candidate document.
    Enforces strict ownership: Candidates can ONLY view/download their own documents.
    """
    candidate = get_or_create_candidate(request.user)
    doc_record = getattr(candidate, "documents", None)
    if not doc_record:
        raise Http404("Document record not found.")

    valid_fields = {item[0] for item in CandidateDocument.DOCUMENT_DEFINITIONS}
    if doc_type not in valid_fields:
        raise Http404("Invalid document category.")

    file_field = getattr(doc_record, doc_type, None)
    if not file_field or not file_field.name:
        raise Http404(f"No file has been uploaded for {doc_type}.")

    try:
        file_handle = file_field.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404("File not found on storage server.")

    content_type, _ = mimetypes.guess_type(file_field.name)
    if not content_type:
        content_type = "application/octet-stream"

    filename = os.path.basename(file_field.name)
    response = FileResponse(file_handle, content_type=content_type)

    if download:
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
    else:
        response["Content-Disposition"] = f'inline; filename="{filename}"'

    # Security headers
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def candidate_document_view(request, doc_type):
    """View candidate document inline in browser."""
    return candidate_document_serve_view(request, doc_type, download=False)


@login_required
def candidate_document_download_view(request, doc_type):
    """Download candidate document as attachment."""
    return candidate_document_serve_view(request, doc_type, download=True)


@login_required
@require_POST
def candidate_document_delete_view(request, doc_type):
    """Deletes an uploaded candidate document."""
    candidate = get_or_create_candidate(request.user)
    doc_record = getattr(candidate, "documents", None)

    valid_fields = {item[0] for item in CandidateDocument.DOCUMENT_DEFINITIONS}
    if doc_record and doc_type in valid_fields:
        file_field = getattr(doc_record, doc_type, None)
        if file_field and file_field.name:
            try:
                file_field.delete(save=False)
            except Exception:
                pass
            setattr(doc_record, doc_type, None)
            doc_record.save()
            candidate.update_profile_completion()
            messages.success(request, "Document deleted successfully.")

    return redirect("candidates:documents")


# ==============================================================================
# 6. CANDIDATE DASHBOARD
# ==============================================================================
@login_required
def candidate_dashboard_view(request):
    """
    Candidate portal main dashboard.
    Dynamically powered by PostgreSQL using optimized ORM queries (select_related).
    Displays candidate metrics, recent applications, upcoming interviews, recommended jobs,
    and company announcements.
    """
    candidate = get_or_create_candidate(request.user)
    completion_pct, completion_advice = candidate.calculate_profile_completion()
    today = timezone.now().date()

    # 1. Applications queries
    applications_qs = (
        Application.objects.filter(candidate=candidate)
        .select_related("job", "job__department")
        .order_by("-applied_at")
    )
    total_applications_count = applications_qs.count()
    shortlisted_count = applications_qs.filter(status=Application.Status.SHORTLISTED).count()
    recent_applications = list(applications_qs[:5])
    applied_job_ids = set(applications_qs.values_list("job_id", flat=True))

    # 2. Upcoming interviews query
    upcoming_interviews_qs = (
        Interview.objects.filter(
            candidate=candidate,
            status__in=[Interview.Status.SCHEDULED, Interview.Status.RESCHEDULED],
            date__gte=today,
        )
        .select_related("job", "application")
        .order_by("date", "time")
    )
    upcoming_interviews_count = upcoming_interviews_qs.count()
    upcoming_interviews = list(upcoming_interviews_qs[:2])
    next_interview = upcoming_interviews[0] if upcoming_interviews else None

    # 3. Unread notifications query
    unread_notifications_count = Notification.objects.filter(
        candidate=candidate, is_read=False
    ).count()

    # 4. Company Announcements query
    announcements = list(
        Notification.objects.filter(
            models.Q(candidate=candidate) | models.Q(candidate__isnull=True),
            notification_type__in=[
                Notification.NotificationType.GENERAL,
                Notification.NotificationType.REGISTRATION,
            ],
        ).order_by("-created_at")[:3]
    )

    # 5. Recommended Jobs matching candidate skills
    candidate_skills = list(candidate.skills.values_list("skill_name", flat=True))
    open_jobs_qs = Job.objects.filter(status=Job.Status.OPEN).select_related("department")

    recommended_jobs = []
    if candidate_skills:
        skill_q = models.Q()
        for s in candidate_skills:
            skill_q |= models.Q(skills_required__icontains=s) | models.Q(title__icontains=s)
        matching_jobs = list(open_jobs_qs.filter(skill_q).distinct()[:4])
        recommended_jobs.extend(matching_jobs)

    # If fewer than 4, fill with latest open jobs
    if len(recommended_jobs) < 4:
        existing_ids = {j.pk for j in recommended_jobs}
        more_jobs = list(
            open_jobs_qs.exclude(pk__in=existing_ids).order_by("-posted_at")[: (4 - len(existing_ids))]
        )
        recommended_jobs.extend(more_jobs)

    context = {
        "candidate": candidate,
        "completion_pct": completion_pct,
        "completion_advice": completion_advice,
        "total_applications_count": total_applications_count,
        "shortlisted_count": shortlisted_count,
        "upcoming_interviews_count": upcoming_interviews_count,
        "upcoming_interviews": upcoming_interviews,
        "next_interview": next_interview,
        "unread_notifications_count": unread_notifications_count,
        "recent_applications": recent_applications,
        "applied_job_ids": applied_job_ids,
        "recommended_jobs": recommended_jobs,
        "candidate_skills": candidate_skills,
        "announcements": announcements,
    }
    return render(request, "candidates/candidate/dashboard.html", context)


# ==============================================================================
# 7. AUTHENTICATION (LOGIN, LOGOUT)
# ==============================================================================
def candidate_login_view(request):
    """Login view supporting authentication by email or username."""
    if request.user.is_authenticated:
        return redirect("candidates:profile")

    if request.method == "POST":
        email_or_username = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        User = get_user_model()
        user_obj = None

        # Check if login with email
        try:
            user_obj = User.objects.get(email__iexact=email_or_username)
            username_to_auth = user_obj.username
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            username_to_auth = email_or_username

        user = authenticate(request, username=username_to_auth, password=password)
        if user is not None:
            auth_login(request, user)
            next_url = request.GET.get("next") or request.POST.get("next") or ""
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            # Secure redirect validation to prevent Open Redirect attacks
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("candidates:profile")
        else:
            messages.error(request, "Invalid email/username or password. Please try again.")

    return render(request, "candidates/authentication/login.html")


def candidate_logout_view(request):
    """Logs out the candidate and redirects to login."""
    auth_logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("candidates:login")


def candidate_register_view(request):
    """
    Candidate registration view. Creates User, Candidate, and triggers
    welcome notification via signals. Enforces secure password complexity.
    """
    if request.user.is_authenticated:
        return redirect("candidates:profile")

    if request.method == "POST":
        full_name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        User = get_user_model()

        # Validations
        if not full_name:
            messages.error(request, "Full Name is required.")
            return render(request, "candidates/authentication/register.html")

        if not email or "@" not in email:
            messages.error(request, "A valid Email Address is required.")
            return render(request, "candidates/authentication/register.html")

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email address already exists. Please login.")
            return render(request, "candidates/authentication/register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return render(request, "candidates/authentication/register.html")

        # Enforce standard Django password validators
        try:
            validate_password(password)
        except DjangoValidationError as val_err:
            for msg in val_err.messages:
                messages.error(request, msg)
            return render(request, "candidates/authentication/register.html")

        # Generate unique username
        base_username = email.split("@")[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        candidate = Candidate.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
        )
        CandidateDocument.objects.get_or_create(candidate=candidate)

        # Authenticate and login
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)

        messages.success(request, f"Welcome to HRMS Portal, {full_name}! Your account has been registered.")
        return redirect("candidates:profile")

    return render(request, "candidates/authentication/register.html")


@login_required
@candidate_required
def candidate_change_password_view(request):
    """
    Secure password change view for Candidate users.
    Enforces current password verification, new password validation, and CSRF protection.
    """
    candidate = get_or_create_candidate(request.user)

    if request.method == "POST":
        old_password = request.POST.get("old_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not request.user.check_password(old_password):
            messages.error(request, "Current password is incorrect.")
        elif not new_password:
            messages.error(request, "New password cannot be blank.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            try:
                validate_password(new_password, user=request.user)
                request.user.set_password(new_password)
                request.user.save(update_fields=["password"])
                update_session_auth_hash(request, request.user)
                messages.success(request, "Your password has been changed successfully!")
                return redirect("candidates:change_password")
            except DjangoValidationError as err:
                for msg in err.messages:
                    messages.error(request, msg)

    return render(request, "candidates/candidate/change_password.html", {"candidate": candidate})


def candidate_forgot_password_view(request):
    """
    Secure forgot password view.
    Accepts email address and provides safe confirmation message.
    """
    if request.user.is_authenticated:
        return redirect("candidates:profile")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        if not email:
            messages.error(request, "Please enter your email address.")
        else:
            messages.success(
                request,
                f"If an account exists for {email}, password reset instructions have been sent to your email."
            )
            return redirect("candidates:login")

    return render(request, "candidates/authentication/forgot_password.html")


# ==============================================================================
# 8. JOB VACANCIES (LIST & DETAILS)
# ==============================================================================
def job_list_view(request):
    """
    Displays open job vacancies with keyword, department, experience, and job type filters.
    Read-only view. Candidates cannot create, edit, or delete jobs.
    """
    if request.method not in ["GET", "HEAD", "OPTIONS"]:
        raise PermissionDenied("Candidates are not authorized to create, modify, or delete job vacancies.")

    jobs = Job.objects.filter(status=Job.Status.OPEN).select_related("department").order_by("-posted_at")

    # Keyword search
    query = request.GET.get("q", "").strip()
    if query:
        jobs = jobs.filter(
            models.Q(title__icontains=query)
            | models.Q(description__icontains=query)
            | models.Q(skills_required__icontains=query)
            | models.Q(department__name__icontains=query)
        )

    # Department filter
    dept_param = request.GET.get("dept", "").strip()
    if dept_param:
        jobs = jobs.filter(
            models.Q(department__name__icontains=dept_param)
            | models.Q(department__code__iexact=dept_param)
        )

    # Experience filter
    exp_param = request.GET.get("exp", "").strip()
    if exp_param:
        jobs = jobs.filter(experience_required__icontains=exp_param)

    # Job type filter
    type_param = request.GET.get("type", "").strip()
    if type_param:
        jobs = jobs.filter(job_type__iexact=type_param.replace("-", "_"))

    # Sorting
    sort_param = request.GET.get("sort", "").strip().lower()
    if sort_param == "salary":
        jobs = jobs.order_by("-salary_max", "-salary_min")
    elif sort_param == "experience":
        jobs = jobs.order_by("experience_required")
    else:
        jobs = jobs.order_by("-posted_at")

    # Check applied jobs if candidate is authenticated
    applied_job_ids = set()
    if request.user.is_authenticated:
        try:
            candidate = Candidate.objects.get(user=request.user)
            applied_job_ids = set(
                Application.objects.filter(candidate=candidate).values_list("job_id", flat=True)
            )
        except Candidate.DoesNotExist:
            pass

    departments = Department.objects.all()

    context = {
        "jobs": jobs,
        "total_jobs_count": jobs.count(),
        "departments": departments,
        "applied_job_ids": applied_job_ids,
        "query": query,
        "selected_dept": dept_param,
        "selected_exp": exp_param,
        "selected_type": type_param,
        "selected_sort": sort_param,
    }
    return render(request, "candidates/jobs/job_list.html", context)


def job_details_view(request, job_id):
    """
    Displays full details of a specific job vacancy.
    Shows current application status if candidate has already applied.
    Read-only view. Candidates cannot create, edit, or delete jobs.
    """
    if request.method not in ["GET", "HEAD", "OPTIONS"]:
        raise PermissionDenied("Candidates are not authorized to create, modify, or delete job vacancies.")

    job = get_object_or_404(Job.objects.select_related("department"), pk=job_id)
    similar_jobs = Job.objects.filter(status=Job.Status.OPEN, department=job.department).exclude(pk=job.job_id)[:3]

    has_applied = False
    candidate_app = None
    if request.user.is_authenticated:
        try:
            candidate = Candidate.objects.get(user=request.user)
            candidate_app = Application.objects.filter(candidate=candidate, job=job).first()
            has_applied = candidate_app is not None
        except Candidate.DoesNotExist:
            pass

    context = {
        "job": job,
        "similar_jobs": similar_jobs,
        "has_applied": has_applied,
        "candidate_app": candidate_app,
    }
    return render(request, "candidates/jobs/job_details.html", context)


# ==============================================================================
# 9. JOB APPLICATION (VALIDATION, SUBMISSION, NOTIFICATION, EMAIL)
# ==============================================================================
@login_required
def job_apply_view(request, job_id):
    """
    Handles job application submission with the 7 strict validations:
    1. Candidate is logged in (@login_required)
    2. Job exists (get_object_or_404)
    3. Job is active (status == OPEN)
    4. Application deadline has not passed
    5. Candidate profile has required information (full_name, phone)
    6. Candidate has a resume (profile resume or uploaded)
    7. Candidate has not already applied (prevents duplicate applications)
    """
    candidate = get_or_create_candidate(request.user)
    job = get_object_or_404(Job.objects.select_related("department"), pk=job_id)

    # Check profile resume availability
    doc_record = getattr(candidate, "documents", None)
    has_profile_resume = bool(doc_record and doc_record.resume and doc_record.resume.name)
    existing_app = Application.objects.filter(candidate=candidate, job=job).first()

    # Pre-validation error checks
    validation_error = None
    if existing_app:
        validation_error = (
            f"You have already applied for this position ({job.title}) on "
            f"{existing_app.applied_at.strftime('%d %B %Y')} with reference {existing_app.application_code}."
        )
    elif job.status != Job.Status.OPEN:
        validation_error = f"This job vacancy ({job.title}) is currently closed for applications."
    elif job.deadline and job.deadline < timezone.now().date():
        validation_error = f"The application deadline ({job.deadline.strftime('%d %B %Y')}) for this job has passed."
    elif not candidate.full_name or not candidate.phone:
        validation_error = "Please complete your full name and phone number in your profile before applying."

    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        # Re-validate constraints on POST
        if validation_error:
            if is_ajax:
                return JsonResponse({"status": "error", "message": validation_error}, status=400)
            messages.error(request, validation_error)
            return redirect("candidates:job_details", job_id=job.job_id)

        form = JobApplicationForm(request.POST, request.FILES)
        custom_resume = request.FILES.get("custom_resume")

        # Validate resume requirement
        if not has_profile_resume and not custom_resume:
            msg = "A valid resume is required to apply. Please upload your resume in your profile or attach one below."
            if is_ajax:
                return JsonResponse({"status": "error", "message": msg}, status=400)
            messages.error(request, msg)
            return render(request, "candidates/jobs/apply.html", {
                "job": job,
                "candidate": candidate,
                "form": form,
                "has_profile_resume": has_profile_resume,
                "profile_resume": doc_record.resume if has_profile_resume else None,
                "validation_error": msg,
            })

        if form.is_valid():
            cover_note = form.cleaned_data.get("cover_note", "")

            try:
                # Create Application with initial status APPLIED
                application = Application(
                    candidate=candidate,
                    job=job,
                    cover_note=cover_note,
                    status=Application.Status.APPLIED,
                )

                if custom_resume:
                    application.resume = custom_resume
                elif has_profile_resume:
                    application.resume = doc_record.resume

                application.save()

            except IntegrityError:
                # Database unique constraint protection
                msg = "You have already submitted an application for this vacancy."
                if is_ajax:
                    return JsonResponse({"status": "error", "message": msg}, status=400)
                messages.error(request, msg)
                return redirect("candidates:my_applications")

            # 1. Create In-App Notification
            notification_message = f"Your application for {job.title} has been submitted successfully."
            Notification.objects.create(
                candidate=candidate,
                title="Application Submitted",
                message=notification_message,
                notification_type=Notification.NotificationType.APPLICATION,
                link=reverse("candidates:application_details", kwargs={"application_id": application.application_id}),
            )

            # 2. Send Confirmation Email
            send_application_submitted_email(application)

            if is_ajax:
                return JsonResponse({
                    "status": "success",
                    "application_id": application.application_id,
                    "application_code": application.application_code,
                    "job_title": job.title,
                    "applied_date": application.applied_at.strftime("%d %B %Y"),
                    "current_status": application.get_status_display(),
                    "redirect_url": reverse("candidates:application_details", kwargs={"application_id": application.application_id}),
                })

            # Render the success view on the apply page
            context = {
                "job": job,
                "candidate": candidate,
                "submitted_application": application,
                "submitted_success": True,
            }
            return render(request, "candidates/jobs/apply.html", context)

        else:
            if is_ajax:
                return JsonResponse({"status": "error", "errors": form.errors}, status=400)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    else:
        form = JobApplicationForm()

    context = {
        "job": job,
        "candidate": candidate,
        "form": form,
        "has_profile_resume": has_profile_resume,
        "profile_resume": doc_record.resume if has_profile_resume else None,
        "existing_app": existing_app,
        "validation_error": validation_error,
        "submitted_success": False,
    }
    return render(request, "candidates/jobs/apply.html", context)


# ==============================================================================
# 10. MY APPLICATIONS
# ==============================================================================
@login_required
def my_applications_view(request):
    """
    Displays list of all job applications submitted by the logged-in candidate.
    Candidate isolation: Candidates can strictly ONLY see their own applications.
    Computes summary metric cards: Total, Under Review, Shortlisted, Selected.
    """
    candidate = get_or_create_candidate(request.user)
    applications = (
        Application.objects.filter(candidate=candidate)
        .select_related("job", "job__department")
        .order_by("-applied_at")
    )

    # Metric calculations
    total_count = applications.count()
    under_review_count = applications.filter(status=Application.Status.RESUME_REVIEW).count()
    shortlisted_count = applications.filter(status=Application.Status.SHORTLISTED).count()
    selected_count = applications.filter(status=Application.Status.SELECTED).count()

    # Status filter tab
    status_filter = request.GET.get("status", "").strip().upper()
    active_tab = status_filter or "ALL"
    if status_filter and status_filter in Application.Status.values:
        filtered_applications = applications.filter(status=status_filter)
    else:
        filtered_applications = applications

    # Tab counts
    status_counts = {
        "ALL": total_count,
        "APPLIED": applications.filter(status=Application.Status.APPLIED).count(),
        "RESUME_REVIEW": under_review_count,
        "SHORTLISTED": shortlisted_count,
        "APTITUDE_TEST": applications.filter(status=Application.Status.APTITUDE_TEST).count(),
        "INTERVIEW_SCHEDULED": applications.filter(status=Application.Status.INTERVIEW_SCHEDULED).count(),
        "SELECTED": selected_count,
        "REJECTED": applications.filter(status=Application.Status.REJECTED).count(),
    }

    context = {
        "candidate": candidate,
        "applications": filtered_applications,
        "total_count": total_count,
        "under_review_count": under_review_count,
        "shortlisted_count": shortlisted_count,
        "selected_count": selected_count,
        "active_tab": active_tab,
        "status_counts": status_counts,
    }
    return render(request, "candidates/applications/my_applications.html", context)


# ==============================================================================
# 11. APPLICATION DETAILS
# ==============================================================================
@login_required
def application_details_view(request, application_id):
    """
    Displays full details of a specific job application.
    Security: Strictly candidate-isolated (403 Forbidden if accessing another candidate's application).
    Read-only protection: Candidates cannot modify application status.
    Displays: Job info, application status, applied date, resume used, interviews, test results.
    """
    candidate = get_or_create_candidate(request.user)
    application = get_object_or_404(
        Application.objects.select_related("job", "job__department", "candidate"),
        pk=application_id,
    )

    # Ownership enforcement: Candidate can ONLY access their own application
    if application.candidate != candidate:
        raise PermissionDenied("You are not authorized to view this application.")

    # Read-only enforcement: Prevent candidates from changing recruitment decision / status
    if request.method == "POST":
        raise PermissionDenied("Candidates cannot modify application status. Status is managed exclusively by the HR recruitment team.")

    # Associated interviews
    interviews = application.interviews.all().order_by("-date", "-time")

    # Associated aptitude test results
    test_results = application.test_results.all().order_by("-completed_at")

    # Stepper logic
    # Workflow stages: APPLIED -> RESUME_REVIEW -> SHORTLISTED -> APTITUDE_TEST -> INTERVIEW_SCHEDULED -> FINAL_DECISION
    status_order = [
        Application.Status.APPLIED,
        Application.Status.RESUME_REVIEW,
        Application.Status.SHORTLISTED,
        Application.Status.APTITUDE_TEST,
        Application.Status.INTERVIEW_SCHEDULED,
        Application.Status.SELECTED,
    ]

    current_idx = 0
    if application.status in status_order:
        current_idx = status_order.index(application.status)
    elif application.status == Application.Status.REJECTED:
        current_idx = len(status_order) - 1

    stepper_steps = [
        {"title": "Applied", "date": application.applied_at.strftime("%d %b %Y"), "status": "completed" if current_idx > 0 else "current" if current_idx == 0 else "upcoming"},
        {"title": "Resume Under Review", "date": "In Review" if current_idx == 1 else "Completed" if current_idx > 1 else "Pending", "status": "completed" if current_idx > 1 else "current" if current_idx == 1 else "upcoming"},
        {"title": "Shortlisted", "date": "Shortlisted" if current_idx >= 2 else "Pending", "status": "completed" if current_idx > 2 else "current" if current_idx == 2 else "upcoming"},
        {"title": "Aptitude Test", "date": "Passed" if current_idx > 3 else "Active" if current_idx == 3 else "Pending", "status": "completed" if current_idx > 3 else "current" if current_idx == 3 else "upcoming"},
        {"title": "Interview Scheduled", "date": "Scheduled" if current_idx == 4 else "Completed" if current_idx > 4 else "Pending", "status": "completed" if current_idx > 4 else "current" if current_idx == 4 else "upcoming"},
        {"title": "Final Decision", "date": application.get_status_display() if current_idx >= 5 else "Pending", "status": "current" if current_idx >= 5 else "upcoming"},
    ]

    # Resume filename extraction
    resume_filename = ""
    if application.resume and application.resume.name:
        resume_filename = os.path.basename(application.resume.name)

    context = {
        "candidate": candidate,
        "application": application,
        "interviews": interviews,
        "test_results": test_results,
        "stepper_steps": stepper_steps,
        "resume_filename": resume_filename,
    }
    return render(request, "candidates/applications/application_details.html", context)


@login_required
def application_resume_download_view(request, application_id):
    """
    Securely serves the resume attached to an application.
    Enforces ownership: Only the candidate who owns the application can download it.
    """
    candidate = get_or_create_candidate(request.user)
    application = get_object_or_404(Application, pk=application_id)

    if application.candidate != candidate:
        raise PermissionDenied("You are not authorized to download this file.")

    if not application.resume or not application.resume.name:
        raise Http404("No resume attached to this application.")

    try:
        file_handle = application.resume.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404("File not found on storage server.")

    content_type, _ = mimetypes.guess_type(application.resume.name)
    if not content_type:
        content_type = "application/pdf"

    filename = os.path.basename(application.resume.name)
    response = FileResponse(file_handle, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


# ==============================================================================
# 12. NOTIFICATIONS (LIST & ACTIONS)
# ==============================================================================
@login_required
def candidate_notifications_view(request):
    """
    Displays all notifications for the logged-in candidate with category filters.
    Includes notifications triggered when HR changes application status.
    """
    candidate = get_or_create_candidate(request.user)
    notifications = Notification.objects.filter(candidate=candidate).order_by("-created_at")

    category = request.GET.get("category", "all").strip().lower()
    if category == "apps":
        filtered_notifications = notifications.filter(notification_type=Notification.NotificationType.APPLICATION)
    elif category == "interviews":
        filtered_notifications = notifications.filter(notification_type=Notification.NotificationType.INTERVIEW)
    elif category == "aptitude":
        filtered_notifications = notifications.filter(notification_type=Notification.NotificationType.APTITUDE)
    elif category == "announcements":
        filtered_notifications = notifications.filter(
            notification_type__in=[Notification.NotificationType.GENERAL, Notification.NotificationType.REGISTRATION]
        )
    else:
        filtered_notifications = notifications

    total_count = notifications.count()
    unread_count = notifications.filter(is_read=False).count()
    apps_count = notifications.filter(notification_type=Notification.NotificationType.APPLICATION).count()
    interviews_count = notifications.filter(notification_type=Notification.NotificationType.INTERVIEW).count()
    aptitude_count = notifications.filter(notification_type=Notification.NotificationType.APTITUDE).count()
    announcements_count = notifications.filter(
        notification_type__in=[Notification.NotificationType.GENERAL, Notification.NotificationType.REGISTRATION]
    ).count()

    context = {
        "candidate": candidate,
        "notifications": filtered_notifications,
        "category": category,
        "total_count": total_count,
        "unread_count": unread_count,
        "apps_count": apps_count,
        "interviews_count": interviews_count,
        "aptitude_count": aptitude_count,
        "announcements_count": announcements_count,
    }
    return render(request, "candidates/notifications/notifications.html", context)


@login_required
@require_POST
def candidate_notifications_mark_all_read_view(request):
    """Marks all unread notifications as read for the logged-in candidate."""
    candidate = get_or_create_candidate(request.user)
    Notification.objects.filter(candidate=candidate, is_read=False).update(is_read=True)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "success", "message": "All notifications marked as read.", "unread_count": 0})

    messages.success(request, "All notifications marked as read.")
    return redirect("candidates:notifications")


@login_required
def candidate_notification_mark_read_view(request, notification_id):
    """Marks a single notification as read and redirects to its destination link or stays on page."""
    candidate = get_or_create_candidate(request.user)
    notif = get_object_or_404(Notification, pk=notification_id)

    # Ownership check: Candidate cannot access another candidate's notification
    if notif.candidate != candidate:
        raise PermissionDenied("You are not authorized to access this notification.")

    if not notif.is_read:
        notif.is_read = True
        notif.save(update_fields=["is_read"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        unread_count = candidate.notifications.filter(is_read=False).count()
        return JsonResponse({"status": "success", "notification_id": notification_id, "unread_count": unread_count})

    if request.GET.get("stay") == "1":
        return redirect("candidates:notifications")

    if notif.link:
        if url_has_allowed_host_and_scheme(notif.link, allowed_hosts={request.get_host()}):
            return redirect(notif.link)
        if notif.link.startswith("/"):
            return redirect(notif.link)

    return redirect("candidates:notifications")


# ==============================================================================
# 7. APTITUDE TEST VIEWS
# ==============================================================================
@login_required
def aptitude_list_view(request):
    """
    Displays assessments categorized into Available, Upcoming, and Completed for the logged-in candidate.
    """
    candidate = get_or_create_candidate(request.user)

    # 1. Tests completed by candidate
    completed_results = (
        TestResult.objects.filter(candidate=candidate)
        .select_related("test", "test__job", "application")
        .order_by("-completed_at")
    )
    completed_test_ids = set(completed_results.values_list("test_id", flat=True))

    # Base query for tests accessible to this candidate
    base_accessible_tests = AptitudeTest.objects.filter(is_active=True).filter(
        models.Q(assigned_candidates=candidate)
        | models.Q(job__applications__candidate=candidate)
        | models.Q(job__isnull=True)
    ).distinct()

    # 2. Available tests: active and not yet taken
    available_tests = (
        base_accessible_tests.filter(status=AptitudeTest.Status.ACTIVE)
        .exclude(test_id__in=completed_test_ids)
        .select_related("job")
        .prefetch_related("questions")
        .order_by("-created_at")
    )

    # 3. Upcoming tests: upcoming status and not yet taken
    upcoming_tests = (
        base_accessible_tests.filter(status=AptitudeTest.Status.UPCOMING)
        .exclude(test_id__in=completed_test_ids)
        .select_related("job")
        .prefetch_related("questions")
        .order_by("created_at")
    )

    current_tab = request.GET.get("tab", "available").strip().lower()
    if current_tab not in ["available", "upcoming", "completed"]:
        current_tab = "available"

    context = {
        "candidate": candidate,
        "available_tests": available_tests,
        "upcoming_tests": upcoming_tests,
        "completed_results": completed_results,
        "available_count": available_tests.count(),
        "upcoming_count": upcoming_tests.count(),
        "completed_count": completed_results.count(),
        "current_tab": current_tab,
    }
    return render(request, "candidates/aptitude/aptitude_list.html", context)


@login_required
def aptitude_test_view(request, test_id):
    """
    Renders the assessment environment for the candidate.
    Strictly verifies candidate authorization, active status, and prevents duplicate attempts.
    Never exposes correct answers to the client template or JSON.
    """
    candidate = get_or_create_candidate(request.user)
    test = get_object_or_404(AptitudeTest.objects.select_related("job"), pk=test_id, is_active=True)

    # Duplicate attempt check
    existing_result = TestResult.objects.filter(candidate=candidate, test=test).first()
    if existing_result:
        messages.info(request, f"You have already completed '{test.title}'. Here is your result.")
        return redirect("candidates:aptitude_result", result_id=existing_result.result_id)

    # Active status check
    if test.status != AptitudeTest.Status.ACTIVE:
        messages.warning(request, f"This assessment is not currently active (Status: {test.get_status_display()}).")
        return redirect("candidates:aptitude_list")

    # Authorization check: directly assigned, or candidate applied to job, or company-wide
    has_access = (
        test.assigned_candidates.filter(pk=candidate.pk).exists()
        or test.job is None
        or Application.objects.filter(candidate=candidate, job=test.job).exists()
    )
    if not has_access:
        raise PermissionDenied("You are not assigned or authorized to take this assessment.")

    questions = list(test.questions.all().order_by("question_id"))
    if not questions:
        messages.warning(request, "No questions have been configured for this assessment yet. Please contact recruitment.")
        return redirect("candidates:aptitude_list")

    # Security: Build client payload WITHOUT correct answers
    sanitized_questions = []
    for q in questions:
        sanitized_questions.append({
            "id": q.question_id,
            "question": q.question_text,
            "options": [q.option_a, q.option_b, q.option_c, q.option_d],
        })

    context = {
        "candidate": candidate,
        "test": test,
        "sanitized_questions": sanitized_questions,
        "questions_json": json.dumps(sanitized_questions),
        "total_questions": len(questions),
        "duration_minutes": test.duration_minutes,
        "passing_percentage": test.passing_percentage,
    }
    return render(request, "candidates/aptitude/test.html", context)


@login_required
@require_POST
def aptitude_submit_view(request, test_id):
    """
    Handles secure test submission.
    Calculates score exclusively on the Django backend against database records.
    Prevents duplicate submissions and stores TestResult.
    """
    candidate = get_or_create_candidate(request.user)
    test = get_object_or_404(AptitudeTest.objects.select_related("job"), pk=test_id)

    # 1. Duplicate submission check
    existing_result = TestResult.objects.filter(candidate=candidate, test=test).first()
    if existing_result:
        messages.info(request, "You have already submitted this assessment.")
        return redirect("candidates:aptitude_result", result_id=existing_result.result_id)

    # 2. Authorization check
    has_access = (
        test.assigned_candidates.filter(pk=candidate.pk).exists()
        or test.job is None
        or Application.objects.filter(candidate=candidate, job=test.job).exists()
    )
    if not has_access:
        raise PermissionDenied("You are not authorized to take this assessment.")

    # 3. Parse submitted answers
    answers_map = {}
    raw_json = request.POST.get("answers_json")
    if raw_json:
        try:
            parsed = json.loads(raw_json)
            idx_map = {0: "A", 1: "B", 2: "C", 3: "D"}
            for q_id, opt in parsed.items():
                if isinstance(opt, int) and opt in idx_map:
                    answers_map[int(q_id)] = idx_map[opt]
                elif isinstance(opt, str) and opt.upper() in ["A", "B", "C", "D"]:
                    answers_map[int(q_id)] = opt.upper()
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback to standard form inputs (e.g. question_1=A or question_1=0)
    for key, val in request.POST.items():
        if key.startswith("question_"):
            try:
                q_id = int(key.replace("question_", ""))
                val_str = str(val).strip().upper()
                if val_str in ["A", "B", "C", "D"]:
                    answers_map[q_id] = val_str
                elif val_str.isdigit() and int(val_str) in [0, 1, 2, 3]:
                    answers_map[q_id] = {0: "A", 1: "B", 2: "C", 3: "D"}[int(val_str)]
            except ValueError:
                continue

    # 4. BACKEND SCORE CALCULATION
    questions = test.questions.all()
    total_questions = questions.count()
    correct_count = 0

    for question in questions:
        chosen_option = answers_map.get(question.question_id)
        if chosen_option and chosen_option == question.correct_option:
            correct_count += 1

    incorrect_count = total_questions - correct_count
    score_percentage = round((correct_count / total_questions * 100), 2) if total_questions > 0 else 0.00
    is_passed = score_percentage >= test.passing_percentage

    # Associate with candidate application if linked to job
    application = None
    if test.job:
        application = Application.objects.filter(candidate=candidate, job=test.job).first()

    try:
        test_result = TestResult.objects.create(
            candidate=candidate,
            test=test,
            application=application,
            total_questions=total_questions,
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            score_percentage=score_percentage,
            is_passed=is_passed,
        )
    except IntegrityError:
        # Caught duplicate constraint
        existing = TestResult.objects.filter(candidate=candidate, test=test).first()
        if existing:
            return redirect("candidates:aptitude_result", result_id=existing.result_id)
        raise

    # 5. Create Candidate In-App Notification
    Notification.objects.create(
        candidate=candidate,
        title="Aptitude Test Completed",
        message=f"You completed '{test.title}' with a score of {score_percentage}% ({'PASSED' if is_passed else 'FAILED'}).",
        notification_type=Notification.NotificationType.APTITUDE,
        link=reverse("candidates:aptitude_result", kwargs={"result_id": test_result.result_id}),
    )

    # 6. Response
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "status": "success",
            "redirect_url": reverse("candidates:aptitude_result", kwargs={"result_id": test_result.result_id}),
        })

    status_msg = "PASSED" if is_passed else "FAILED"
    messages.success(request, f"Assessment submitted successfully! You scored {score_percentage}% ({status_msg}).")
    return redirect("candidates:aptitude_result", result_id=test_result.result_id)


@login_required
def aptitude_result_view(request, result_id):
    """
    Renders the verified score card and breakdown for the candidate's test result.
    Enforces strict ownership authorization.
    """
    candidate = get_or_create_candidate(request.user)
    result = get_object_or_404(
        TestResult.objects.select_related("test", "test__job", "candidate", "application"),
        pk=result_id,
    )

    # Strict ownership check
    if result.candidate != candidate:
        raise PermissionDenied("You do not have permission to view this assessment result.")

    context = {
        "candidate": candidate,
        "result": result,
        "test": result.test,
        "job": result.test.job,
        "application": result.application,
    }
    return render(request, "candidates/aptitude/result.html", context)


# ==============================================================================
# 8. INTERVIEW VIEWS
# ==============================================================================
@login_required
def interview_list_view(request):
    """
    Displays the candidate's interview rounds partitioned into upcoming and previous.
    Strictly read-only; candidates can view schedule, panel, and meeting links.
    """
    candidate = get_or_create_candidate(request.user)
    today = timezone.now().date()

    # Query candidate interviews
    interviews = (
        Interview.objects.filter(candidate=candidate)
        .select_related("job", "application")
        .order_by("date", "time")
    )

    # Upcoming: Scheduled or Rescheduled for today or future date
    upcoming_interviews = interviews.filter(
        status__in=[Interview.Status.SCHEDULED, Interview.Status.RESCHEDULED],
        date__gte=today,
    )

    # Previous: Completed, Cancelled, or past date
    previous_interviews = interviews.exclude(
        pk__in=upcoming_interviews.values_list("pk", flat=True)
    ).order_by("-date", "-time")

    featured_upcoming = upcoming_interviews.first()
    upcoming_count = upcoming_interviews.count()
    completed_count = interviews.filter(status=Interview.Status.COMPLETED).count()
    rescheduled_count = interviews.filter(status=Interview.Status.RESCHEDULED).count()

    context = {
        "candidate": candidate,
        "upcoming_interviews": upcoming_interviews,
        "previous_interviews": previous_interviews,
        "featured_upcoming": featured_upcoming,
        "upcoming_count": upcoming_count,
        "completed_count": completed_count,
        "rescheduled_count": rescheduled_count,
    }
    return render(request, "candidates/interviews/interview_list.html", context)


@login_required
def interview_details_view(request, interview_id):
    """
    Displays comprehensive interview round details for candidate preparation.
    Enforces strict candidate ownership (403 on unauthorized access).
    Read-only: candidate cannot edit any schedule, interviewer, or link details.
    """
    if request.method not in ["GET", "HEAD", "OPTIONS"]:
        raise PermissionDenied("Candidates cannot modify interview schedules or details. Contact HR for rescheduling.")

    candidate = get_or_create_candidate(request.user)
    interview = get_object_or_404(
        Interview.objects.select_related("job", "job__department", "application", "candidate"),
        pk=interview_id,
    )

    # Strict ownership check
    if interview.candidate != candidate:
        raise PermissionDenied("You do not have permission to view this interview.")

    documents = getattr(candidate, "documents", None)

    context = {
        "candidate": candidate,
        "interview": interview,
        "job": interview.job,
        "application": interview.application,
        "documents": documents,
    }
    return render(request, "candidates/interviews/interview_details.html", context)


# ==============================================================================
# 11. HR ONBOARDING INTEGRATION VIEWS & DASHBOARDS
# ==============================================================================
@login_required
@hr_or_admin_required
def hr_dashboard_view(request):
    """
    HR Dashboard view.
    Strictly forbidden for Candidates (raises PermissionDenied / HTTP 403 Forbidden).
    """
    from .onboarding import get_candidates_awaiting_onboarding
    candidates_awaiting = get_candidates_awaiting_onboarding()
    context = {
        "candidates_awaiting": candidates_awaiting,
        "total_awaiting": len(candidates_awaiting),
    }
    return render(request, "candidates/hr/dashboard.html", context)


@login_required
@employee_or_admin_required
def employee_dashboard_view(request):
    """
    Employee Dashboard view.
    Strictly forbidden for Candidates (raises PermissionDenied / HTTP 403 Forbidden).
    """
    from .onboarding import get_employee_record
    emp_record = get_employee_record(user_id=request.user.id)
    return render(request, "candidates/employee/dashboard.html", {"employee_record": emp_record, "is_employee_view": True})


@login_required
@hr_or_admin_required
def candidate_onboarding_dossier_view(request, candidate_id):
    """
    Renders comprehensive onboarding dossier for a selected candidate.
    Staff/HR only view. Candidates strictly receive 403 Forbidden.
    """
    from .onboarding import get_candidate_onboarding_dossier
    dossier = get_candidate_onboarding_dossier(candidate_id=candidate_id)
    if not dossier:
        raise Http404("Candidate not found")
    return render(request, "candidates/hr/candidate_onboarding_dossier.html", {"dossier": dossier})


@login_required
@hr_or_admin_required
def candidate_onboarding_api_view(request):
    """
    JSON API endpoint for HR/Admin onboarding module integration.
    Identifiable through candidate_id or user_id query parameter.
    Candidates strictly receive 403 Forbidden.
    """
    from .onboarding import get_candidate_onboarding_dossier
    candidate_id = request.GET.get("candidate_id")
    user_id = request.GET.get("user_id")

    if not candidate_id and not user_id:
        return JsonResponse(
            {"error": "Either candidate_id or user_id query parameter is required."},
            status=400,
        )

    cid = int(candidate_id) if candidate_id and candidate_id.isdigit() else None
    uid = int(user_id) if user_id and user_id.isdigit() else None

    dossier = get_candidate_onboarding_dossier(candidate_id=cid, user_id=uid)
    if not dossier:
        return JsonResponse({"error": "Candidate not found."}, status=404)

    return JsonResponse({"status": "success", "dossier": dossier})


@login_required
@hr_or_admin_required
@require_POST
def complete_candidate_onboarding_action(request, candidate_id):
    """
    Staff action to record employee in employee_table upon completing HR onboarding.
    Candidates strictly receive 403 Forbidden.
    """
    from .onboarding import create_employee_record, get_candidate_by_id_or_user
    candidate = get_candidate_by_id_or_user(candidate_id=candidate_id)
    if not candidate:
        raise Http404("Candidate not found")

    emp_rec = create_employee_record(
        candidate_id=candidate.candidate_id,
        user_id=candidate.user_id,
        created_by=request.user.id,
    )
    messages.success(request, f"Employee record {emp_rec['employee_code']} created successfully in employee_table.")
    return redirect("candidates:candidate_onboarding_dossier", candidate_id=candidate_id)




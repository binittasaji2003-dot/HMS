from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CandidateProfileForm, CandidateRegistrationForm, JobApplicationForm, JobApplicationSubmitForm
from .models import Candidate, JobApplication, JobVacancy


def _candidate_for(user):
    first_name, _, last_name = (getattr(user, "name", "") or "").partition(" ")
    candidate, _ = Candidate.objects.get_or_create(
        user=user,
        defaults={
            "first_name": first_name or "Candidate",
            "last_name": last_name or first_name or "User",
        },
    )
    return candidate


def register(request):
    """Candidate self-registration view."""
    if request.user.is_authenticated:
        return redirect("candidates:dashboard")

    if request.method == "POST":
        form = CandidateRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Registration successful! Please sign in with your email and password to access the job portal.",
            )
            next_url = request.GET.get("next")
            if next_url:
                return redirect(f"/accounts/login/?next={next_url}")
            return redirect("account_login")
    else:
        form = CandidateRegistrationForm()

    return render(request, "candidates/register.html", {"form": form})


@login_required
def dashboard(request):
    candidate = _candidate_for(request.user)
    applications = candidate.applications.select_related("vacancy", "vacancy__department").order_by("-applied_at")
    all_open_jobs = JobVacancy.objects.filter(status="OPEN").select_related("department").order_by("-posted_date")
    return render(
        request,
        "candidates/dashboard.html",
        {
            "candidate": candidate,
            "applications": applications[:5],
            "application_count": applications.count(),
            "open_jobs": all_open_jobs.count(),
            "available_jobs": all_open_jobs[:6],
        },
    )


def job_list(request):
    jobs = JobVacancy.objects.filter(status="OPEN").select_related("department").order_by("-posted_date")
    query = request.GET.get("q", "").strip()
    dept_filter = request.GET.get("department", "").strip()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(skills_required__icontains=query)
            | Q(department__name__icontains=query)
            | Q(location__icontains=query)
        )
    if dept_filter:
        jobs = jobs.filter(department_id=dept_filter)

    from admin_module.models import Department
    departments = Department.objects.filter(is_active=True)
    return render(request, "candidates/job_list.html", {"jobs": jobs, "query": query, "departments": departments, "selected_dept": dept_filter})


def job_detail(request, vacancy_id):
    job = get_object_or_404(JobVacancy.objects.select_related("department"), vacancy_id=vacancy_id)
    applied = False
    is_expired = False
    if job.closing_date and job.closing_date < timezone.now().date():
        is_expired = True

    if request.user.is_authenticated:
        applied = JobApplication.objects.filter(candidate__user=request.user, vacancy=job).exists()
    return render(
        request,
        "candidates/job_detail.html",
        {"job": job, "applied": applied, "is_expired": is_expired},
    )


@login_required
def apply(request, vacancy_id):
    candidate = _candidate_for(request.user)
    job = get_object_or_404(JobVacancy, vacancy_id=vacancy_id)

    # 1. Vacancy status check
    if job.status != "OPEN":
        messages.error(request, "This job vacancy is closed and is no longer accepting applications.")
        return redirect("candidates:job_detail", vacancy_id=vacancy_id)

    # 2. Closing date check
    if job.closing_date and job.closing_date < timezone.now().date():
        messages.error(request, "The application deadline for this job vacancy has expired.")
        return redirect("candidates:job_detail", vacancy_id=vacancy_id)

    # 3. Duplicate application check
    existing_application = JobApplication.objects.filter(candidate=candidate, vacancy=job).first()
    if existing_application:
        messages.info(request, "You have already applied for this job vacancy.")
        return redirect("candidates:applications")

    if request.method == "POST":
        if "first_name" in request.POST:
            form = JobApplicationSubmitForm(request.POST, request.FILES, candidate=candidate)
            if form.is_valid():
                fn = form.cleaned_data["first_name"].strip()
                ln = form.cleaned_data["last_name"].strip()
                dob = form.cleaned_data.get("date_of_birth")
                ph = form.cleaned_data.get("phone", "").strip()
                uploaded_resume = form.cleaned_data.get("resume")
                terms = form.cleaned_data.get("terms_agreement", False)

                candidate.first_name = fn
                candidate.last_name = ln
                if dob:
                    candidate.date_of_birth = dob
                if ph:
                    candidate.phone = ph
                if terms:
                    candidate.policy_agreement = terms
                if uploaded_resume:
                    candidate.resume = uploaded_resume
                candidate.save()

                if request.user.name != f"{fn} {ln}".strip():
                    request.user.name = f"{fn} {ln}".strip()
                    request.user.save(update_fields=["name"])

                application = JobApplication(
                    candidate=candidate,
                    vacancy=job,
                    applied_resume=uploaded_resume or candidate.resume,
                    status="APPLIED",
                )
                application.save()

                from .models import send_candidate_notification
                from django.urls import reverse
                send_candidate_notification(
                    candidate=candidate,
                    application=application,
                    title="Application Submitted",
                    message=f"Your application for '{job.title}' has been successfully submitted.",
                    notification_type="STATUS_UPDATE",
                    link_url=reverse("candidates:applications"),
                )

                messages.success(request, f"Your application for '{job.title}' has been submitted successfully!")
                return redirect("candidates:applications")
        else:
            # Direct or test submission
            uploaded_resume = request.FILES.get("applied_resume")
            application = JobApplication.objects.create(
                candidate=candidate,
                vacancy=job,
                applied_resume=uploaded_resume or candidate.resume,
                status="APPLIED",
            )
            from .models import send_candidate_notification
            from django.urls import reverse
            send_candidate_notification(
                candidate=candidate,
                application=application,
                title="Application Submitted",
                message=f"Your application for '{job.title}' has been successfully submitted.",
                notification_type="STATUS_UPDATE",
                link_url=reverse("candidates:applications"),
            )
            messages.success(request, f"Your application for '{job.title}' has been submitted successfully!")
            return redirect("candidates:applications")
    else:
        form = JobApplicationSubmitForm(candidate=candidate)

    return render(request, "candidates/apply.html", {"job": job, "form": form, "candidate": candidate})


@login_required
def applications(request):
    candidate = _candidate_for(request.user)
    applications_list = (
        candidate.applications.select_related(
            "vacancy", "vacancy__department", "aptitude_test"
        )
        .prefetch_related(
            "aptitude_results__test",
            "interviews__interviewer__user",
        )
        .order_by("-applied_at")
    )
    return render(request, "candidates/applications.html", {"applications": applications_list})


@login_required
def profile(request):
    candidate = _candidate_for(request.user)
    if request.method == "POST":
        form = CandidateProfileForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            cand = form.save(commit=False)
            # Check profile completion
            if cand.first_name and cand.last_name and cand.phone and (cand.resume or cand.profile_photo):
                cand.profile_completed = True
            cand.save()

            # Keep user.name synchronized
            if request.user.name != f"{cand.first_name} {cand.last_name}".strip():
                request.user.name = f"{cand.first_name} {cand.last_name}".strip()
                request.user.save(update_fields=["name"])

            messages.success(request, "Your candidate profile has been updated successfully.")
            return redirect("candidates:profile")
    else:
        form = CandidateProfileForm(instance=candidate)

    return render(request, "candidates/profile.html", {"candidate": candidate, "form": form})


@login_required
def take_aptitude_test(request, application_id):
    """Candidate aptitude test view with 3-category balanced questions, timer, and option shuffling."""
    import datetime
    import random
    from hr.models import AptitudeAttempt, AptitudeQuestion, AptitudeResult, AptitudeTest
    from hr.question_bank import seed_default_questions

    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate", "vacancy"),
        application_id=application_id,
    )

    # Security check: verify candidate owns this application
    if application.candidate != candidate:
        messages.error(request, "You are not authorized to access this aptitude assessment.")
        return redirect("candidates:applications")

    # Find active test
    test = AptitudeTest.objects.filter(status="ACTIVE").order_by("-created_at").first()
    if not test:
        messages.warning(
            request,
            "No active aptitude assessment is currently scheduled for this position. Please check back later.",
        )
        return redirect("candidates:applications")

    # Check existing attempt
    attempt = AptitudeAttempt.objects.filter(
        application=application,
        test=test,
    ).first()

    now = timezone.now()

    if attempt:
        if attempt.is_completed:
            messages.info(request, "You have already completed this aptitude assessment.")
            return redirect("candidates:aptitude_result", application_id=application.pk)

        # Check if attempt time expired
        if now >= attempt.expires_at:
            # Auto-submit and grade expired attempt
            score = 0
            for q in attempt.questions_data:
                qid = str(q.get("question_id"))
                if attempt.answers_data.get(qid) == q.get("correct_key"):
                    score += 1

            total_marks = len(attempt.questions_data)
            percentage = round((score / total_marks * 100), 2) if total_marks > 0 else 0.0
            passed = percentage >= test.pass_percentage

            attempt.is_completed = True
            attempt.completed_at = now
            attempt.save()

            AptitudeResult.objects.update_or_create(
                test=test,
                application=application,
                defaults={
                    "score": score,
                    "total_marks": total_marks,
                    "percentage": percentage,
                    "passed": passed,
                },
            )
            messages.warning(request, "Assessment time has expired. Your answers have been submitted automatically.")
            return redirect("candidates:aptitude_result", application_id=application.pk)

    else:
        # Generate new stable attempt with balanced 3-category questions
        active_qs = AptitudeQuestion.objects.filter(
            Q(test=test) | Q(test__isnull=True),
            is_active=True,
        )
        if not active_qs.exists():
            seed_default_questions(test=test)
            active_qs = AptitudeQuestion.objects.filter(
                Q(test=test) | Q(test__isnull=True),
                is_active=True,
            )

        quant_pool = list(active_qs.filter(category="QUANTITATIVE"))
        logical_pool = list(active_qs.filter(category="LOGICAL"))
        verbal_pool = list(active_qs.filter(category="VERBAL"))

        target_total = test.total_questions or 15
        base_per_category = max(1, target_total // 3)

        chosen_quant = random.sample(quant_pool, min(len(quant_pool), base_per_category))
        chosen_logical = random.sample(logical_pool, min(len(logical_pool), base_per_category))
        chosen_verbal = random.sample(verbal_pool, min(len(verbal_pool), base_per_category))

        combined_qs = chosen_quant + chosen_logical + chosen_verbal
        remaining_needed = target_total - len(combined_qs)
        if remaining_needed > 0:
            used_ids = {q.pk for q in combined_qs}
            remaining_pool = [q for q in active_qs if q.pk not in used_ids]
            if remaining_pool:
                extra = random.sample(remaining_pool, min(len(remaining_pool), remaining_needed))
                combined_qs.extend(extra)

        # Task 5: Shuffle questions
        random.shuffle(combined_qs)

        # Task 6: Shuffle answer options for each question
        questions_data = []
        for q in combined_qs:
            original_correct_text = q.correct_option_text
            option_texts = [q.option_a, q.option_b, q.option_c, q.option_d]
            random.shuffle(option_texts)

            shuffled_options = []
            correct_key = "A"
            for idx, key in enumerate(["A", "B", "C", "D"]):
                text = option_texts[idx]
                shuffled_options.append({"key": key, "text": text})
                if text == original_correct_text:
                    correct_key = key

            questions_data.append({
                "question_id": q.pk,
                "category": q.category,
                "category_display": q.get_category_display(),
                "question": q.question,
                "options": shuffled_options,
                "correct_key": correct_key,  # Kept secure on server
            })

        duration = test.duration_minutes or 30
        expires_at = now + datetime.timedelta(minutes=duration)

        attempt = AptitudeAttempt.objects.create(
            test=test,
            application=application,
            expires_at=expires_at,
            questions_data=questions_data,
        )

    remaining_seconds = max(0, int((attempt.expires_at - timezone.now()).total_seconds()))

    # Sanitize questions to NOT expose correct_key to HTML
    display_questions = []
    for q in attempt.questions_data:
        display_questions.append({
            "question_id": q["question_id"],
            "category": q.get("category", ""),
            "category_display": q.get("category_display", ""),
            "question": q["question"],
            "options": q["options"],
        })

    return render(
        request,
        "candidates/aptitude_test.html",
        {
            "application": application,
            "test": test,
            "attempt": attempt,
            "questions": display_questions,
            "time_remaining_seconds": remaining_seconds,
            "total_questions": len(display_questions),
        },
    )


@login_required
def submit_aptitude_test(request, application_id):
    """Handle candidate aptitude test submission and calculate scores securely."""
    from hr.models import AptitudeAttempt, AptitudeResult

    if request.method != "POST":
        return redirect("candidates:take_aptitude_test", application_id=application_id)

    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate", "vacancy"),
        application_id=application_id,
    )

    if application.candidate != candidate:
        messages.error(request, "Unauthorized submission.")
        return redirect("candidates:applications")

    attempt = AptitudeAttempt.objects.filter(
        application=application,
        is_completed=False,
    ).first()

    if not attempt:
        return redirect("candidates:aptitude_result", application_id=application.pk)

    now = timezone.now()
    score = 0
    candidate_answers = {}

    for q in attempt.questions_data:
        qid = str(q.get("question_id"))
        selected = request.POST.get(f"question_{qid}", "").strip().upper()
        if selected in ["A", "B", "C", "D"]:
            candidate_answers[qid] = selected
            if selected == q.get("correct_key"):
                score += 1

    total_marks = len(attempt.questions_data)
    percentage = round((score / total_marks * 100), 2) if total_marks > 0 else 0.0
    passed = percentage >= (attempt.test.pass_percentage or 50)

    attempt.answers_data = candidate_answers
    attempt.is_completed = True
    attempt.completed_at = now
    attempt.save()

    AptitudeResult.objects.update_or_create(
        test=attempt.test,
        application=application,
        defaults={
            "score": score,
            "total_marks": total_marks,
            "percentage": percentage,
            "passed": passed,
        },
    )

    from .models import send_candidate_notification
    from django.urls import reverse
    send_candidate_notification(
        candidate=candidate,
        application=application,
        title="Aptitude Assessment Completed",
        message=f"You completed the aptitude assessment for '{application.vacancy.title}'. Score: {score}/{total_marks} ({percentage}%). Status: {'Passed' if passed else 'Completed'}.",
        notification_type="APTITUDE_RESULT",
        link_url=reverse("candidates:aptitude_result", kwargs={"application_id": application.pk}),
    )

    # If candidate passes and application status is APTITUDE, record progression
    if passed and application.status == "APTITUDE":
        messages.success(
            request,
            f"Congratulations! You scored {score}/{total_marks} ({percentage}%) and passed the aptitude assessment.",
        )
    else:
        messages.info(
            request,
            f"Assessment completed. Your score: {score}/{total_marks} ({percentage}%).",
        )

    return redirect("candidates:aptitude_result", application_id=application.pk)


@login_required
def aptitude_result(request, application_id):
    """View completed aptitude test results for candidate."""
    from hr.models import AptitudeAttempt, AptitudeResult

    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate", "vacancy"),
        application_id=application_id,
    )

    if application.candidate != candidate:
        messages.error(request, "Unauthorized access.")
        return redirect("candidates:applications")

    result = AptitudeResult.objects.filter(application=application).order_by("-completed_at").first()
    attempt = AptitudeAttempt.objects.filter(application=application, is_completed=True).order_by("-completed_at").first()

    if not result and not attempt:
        messages.warning(request, "No completed aptitude assessment record found for this application.")
        return redirect("candidates:applications")

    return render(
        request,
        "candidates/aptitude_result.html",
        {
            "application": application,
            "result": result,
            "attempt": attempt,
        },
    )


@login_required
def notifications(request):
    """Notification center for the authenticated candidate."""
    from .models import CandidateNotification

    candidate = _candidate_for(request.user)
    notif_qs = candidate.notifications.select_related("application", "application__vacancy").order_by("-created_at")

    filter_type = request.GET.get("filter", "all")
    if filter_type == "unread":
        notif_qs = notif_qs.filter(is_read=False)

    return render(
        request,
        "candidates/notifications.html",
        {
            "candidate": candidate,
            "notifications": notif_qs,
            "filter_type": filter_type,
            "unread_count": candidate.notifications.filter(is_read=False).count(),
        },
    )


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single candidate notification as read."""
    from .models import CandidateNotification

    candidate = _candidate_for(request.user)
    notif = get_object_or_404(CandidateNotification, pk=notification_id, candidate=candidate)
    notif.is_read = True
    notif.save(update_fields=["is_read"])

    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        return redirect(next_url)
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect("candidates:notifications")


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for current candidate."""
    candidate = _candidate_for(request.user)
    candidate.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("candidates:notifications")

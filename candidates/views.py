from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .forms import (
    CandidateEducationForm,
    CandidateProfileForm,
    CandidateRegistrationForm,
    JobApplicationForm,
    JobApplicationSubmitForm,
)
from .models import Candidate, CandidateEducation, JobApplication, JobVacancy, send_candidate_notification


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
    completion_data = candidate.calculate_profile_completion()
    applications = candidate.applications.select_related("vacancy", "vacancy__department").order_by("-applied_at")
    all_open_jobs = JobVacancy.objects.filter(status="OPEN").select_related("department").order_by("-posted_date")
    shortlisted_count = candidate.applications.filter(status="SHORTLISTED").count()
    interviews_count = candidate.applications.filter(status="INTERVIEW").count()

    return render(
        request,
        "candidates/dashboard.html",
        {
            "candidate": candidate,
            "completion_data": completion_data,
            "profile_percentage": completion_data["percentage"],
            "is_profile_complete": completion_data["is_complete"],
            "missing_fields": completion_data["missing_fields"],
            "applications": applications[:5],
            "application_count": applications.count(),
            "open_jobs": all_open_jobs.count(),
            "shortlisted_count": shortlisted_count,
            "interviews_count": interviews_count,
            "available_jobs": all_open_jobs[:6],
        },
    )


def job_list(request):
    JobVacancy.update_all_expired()
    jobs = JobVacancy.objects.filter(status="OPEN").select_related("department").order_by("-posted_date")
    query = request.GET.get("q", "").strip()
    dept_filter = request.GET.get("department", "").strip()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(role_designation__icontains=query)
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
    job.check_and_update_status()

    applied = False
    is_closed = (job.status != "OPEN")
    is_expired = job.is_deadline_passed()

    if request.user.is_authenticated:
        applied = JobApplication.objects.filter(candidate__user=request.user, vacancy=job).exists()
    return render(
        request,
        "candidates/job_detail.html",
        {"job": job, "applied": applied, "is_expired": is_expired, "is_closed": is_closed},
    )


from django.http import JsonResponse
from .eligibility import evaluate_eligibility
from .resume_parser import parse_resume


@login_required
def parse_resume_ajax(request):
    """AJAX endpoint to parse uploaded resume and extract candidate data."""
    import logging
    logger = logging.getLogger(__name__)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST method required"}, status=405)
    
    resume_file = request.FILES.get("resume")
    if not resume_file:
        return JsonResponse({"success": False, "error": "No resume file provided"}, status=400)
    
    try:
        logger.info(f"Parsing resume: {resume_file.name}, size: {resume_file.size} bytes")
        parsed_data = parse_resume(resume_file, resume_file.name)
        logger.info(f"Resume extraction complete. Found name: {parsed_data.get('first_name')} {parsed_data.get('last_name')}, skills count: {len(parsed_data.get('skills', '').split(',')) if parsed_data.get('skills') else 0}")
        return JsonResponse({"success": True, "data": parsed_data})
    except Exception as e:
        logger.exception(f"Error parsing resume {resume_file.name}: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def check_eligibility_ajax(request, vacancy_id):
    """AJAX endpoint to evaluate eligibility against a job vacancy."""
    candidate = _candidate_for(request.user)
    job = get_object_or_404(JobVacancy, vacancy_id=vacancy_id)
    job.check_and_update_status()
    
    app_data = {}
    if request.method == "POST":
        import json
        if request.content_type == "application/json":
            try:
                app_data = json.loads(request.body.decode("utf-8"))
            except Exception:
                app_data = {}
        else:
            app_data = request.POST.dict()

    evaluation = evaluate_eligibility(candidate, job, app_data)
    return JsonResponse({"success": True, "evaluation": evaluation})


@login_required
def apply(request, vacancy_id):
    candidate = _candidate_for(request.user)
    job = get_object_or_404(JobVacancy, vacancy_id=vacancy_id)
    job.check_and_update_status()

    # 1. Vacancy status and deadline checks
    if job.status != "OPEN":
        messages.error(request, "Applications for this position are now closed.")
        return redirect("candidates:job_detail", vacancy_id=vacancy_id)

    # 2. Duplicate application check
    existing_application = JobApplication.objects.filter(candidate=candidate, vacancy=job).first()
    if existing_application:
        messages.info(request, "You have already applied for this job vacancy.")
        return redirect("candidates:applications")


    # 4. Profile completeness check
    completion_data = candidate.calculate_profile_completion()
    if not completion_data["is_complete"]:
        messages.warning(
            request,
            f"Please complete your profile before applying. Your profile is {completion_data['percentage']}% complete.",
        )
        return render(
            request,
            "candidates/apply.html",
            {
                "job": job,
                "candidate": candidate,
                "profile_incomplete": True,
                "completion_data": completion_data,
                "missing_fields": completion_data["missing_fields"],
                "completion_percentage": completion_data["percentage"],
            },
        )

    # Initial eligibility evaluation
    eligibility_eval = evaluate_eligibility(candidate, job)

    if request.method == "POST":
        job.check_and_update_status()
        if job.status != "OPEN":
            messages.error(request, "Applications for this position are now closed.")
            return redirect("candidates:job_detail", vacancy_id=vacancy_id)

        if "first_name" in request.POST or "information_source" in request.POST:
            form = JobApplicationSubmitForm(request.POST, request.FILES, candidate=candidate)
            if form.is_valid():
                cd = form.cleaned_data
                
                # Check backend eligibility gate
                eval_post = evaluate_eligibility(candidate, job, cd)
                if not eval_post["is_eligible"]:
                    messages.error(
                        request,
                        f"Cannot submit application: {eval_post['summary']}",
                    )
                    return render(
                        request,
                        "candidates/apply.html",
                        {
                            "job": job,
                            "form": form,
                            "candidate": candidate,
                            "profile_incomplete": False,
                            "completion_data": completion_data,
                            "eligibility_eval": eval_post,
                        },
                    )

                info_source = cd.get("information_source", "PROFILE")
                uploaded_resume = cd.get("resume")
                update_profile = cd.get("update_profile_with_resume", False)

                fn = cd.get("first_name", "").strip()
                mn = cd.get("middle_name", "").strip()
                ln = cd.get("last_name", "").strip()
                dob = cd.get("date_of_birth")
                ph = cd.get("phone", "").strip()
                addr = cd.get("address", "").strip()
                st = cd.get("current_state", "").strip()
                cntry = cd.get("current_country", "India").strip()
                sk = cd.get("applied_skills", "").strip()
                terms = cd.get("terms_agreement", False)

                # If requested, update profile
                if update_profile:
                    if fn:
                        candidate.first_name = fn
                    if mn is not None:
                        candidate.middle_name = mn
                    if ln:
                        candidate.last_name = ln
                    if dob:
                        candidate.date_of_birth = dob
                    if ph:
                        candidate.phone = ph
                    if addr:
                        candidate.address = addr
                    if st:
                        candidate.state = st
                    if cntry:
                        candidate.country = cntry
                    if sk:
                        candidate.skills = sk
                    if uploaded_resume:
                        candidate.resume = uploaded_resume
                    if terms:
                        candidate.policy_agreement = terms
                    candidate.save()

                    if request.user.name != f"{fn} {ln}".strip():
                        request.user.name = f"{fn} {ln}".strip()
                        request.user.save(update_fields=["name"])

                # Create JobApplication
                application = JobApplication(
                    candidate=candidate,
                    vacancy=job,
                    applied_resume=uploaded_resume or candidate.resume,
                    status="APPLIED",
                    information_source=info_source,
                    eligibility_status=eval_post["status"],
                    eligibility_details=eval_post,
                    is_currently_employed=form.get_bool("is_currently_employed", False),
                    is_past_employee=form.get_bool("is_past_employee", False),
                    past_employee_id=cd.get("past_employee_id", ""),
                    past_designation=cd.get("past_designation", ""),
                    past_employment_period=cd.get("past_employment_period", ""),
                    current_state=st or candidate.state,
                    current_country=cntry or candidate.country or "India",
                    willing_to_relocate=form.get_bool("willing_to_relocate", True),
                    legally_authorized=form.get_bool("legally_authorized", True),
                    requires_visa_sponsorship=form.get_bool("requires_visa_sponsorship", False),
                    visa_status=cd.get("visa_status", ""),
                    current_salary=cd.get("current_salary", ""),
                    expected_salary=cd.get("expected_salary", ""),
                    available_joining_days=cd.get("available_joining_days"),
                    why_interested=cd.get("why_interested", ""),
                    applied_skills=sk or candidate.skills,
                )
                application.save()

                from .models import send_candidate_notification
                from django.urls import reverse

                send_candidate_notification(
                    candidate=candidate,
                    application=application,
                    title="Application Submitted Successfully",
                    message=(
                        f"Thank you for applying for the {job.title} position.\n\n"
                        f"Your application has been received successfully.\n\n"
                        f"Application review and shortlisting will take place after the job application period closes.\n\n"
                        f"You will be notified regarding the next steps."
                    ),
                    notification_type="APPLICATION_SUBMITTED",
                    link_url=reverse("candidates:applications"),
                )

                messages.success(
                    request,
                    f"Your application for '{job.title}' has been submitted successfully!",
                )
                return redirect("candidates:applications")
            else:
                messages.error(request, "Please review the form errors below and complete all required questions.")
        else:
            # Fallback direct apply
            uploaded_resume = request.FILES.get("applied_resume")
            eval_direct = evaluate_eligibility(candidate, job)
            application = JobApplication.objects.create(
                candidate=candidate,
                vacancy=job,
                applied_resume=uploaded_resume or candidate.resume,
                status="APPLIED",
                information_source="PROFILE",
                eligibility_status=eval_direct["status"],
                eligibility_details=eval_direct,
            )

            from .models import send_candidate_notification
            from django.urls import reverse

            send_candidate_notification(
                candidate=candidate,
                application=application,
                title="Application Submitted Successfully",
                message=(
                    f"Thank you for applying for the {job.title} position.\n\n"
                    f"Your application has been received successfully.\n\n"
                    f"Application review and shortlisting will take place after the job application period closes.\n\n"
                    f"You will be notified regarding the next steps."
                ),
                notification_type="APPLICATION_SUBMITTED",
                link_url=reverse("candidates:applications"),
            )

            messages.success(request, f"Your application for '{job.title}' has been submitted successfully!")
            return redirect("candidates:applications")
    else:
        form = JobApplicationSubmitForm(candidate=candidate)

    return render(
        request,
        "candidates/apply.html",
        {
            "job": job,
            "form": form,
            "candidate": candidate,
            "education_records": candidate.education_records.all(),
            "profile_incomplete": False,
            "completion_data": completion_data,
            "eligibility_eval": eligibility_eval,
        },
    )


@login_required
def applications(request):
    candidate = _candidate_for(request.user)
    applications_list = (
        candidate.applications.select_related(
            "vacancy", "vacancy__department", "aptitude_test", "screening_result"
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
    education_records = candidate.education_records.all()
    education_form = CandidateEducationForm()

    if request.method == "POST":
        form = CandidateProfileForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            cand = form.save()
            completion_data = cand.calculate_profile_completion()

            # Keep user.name synchronized
            if request.user.name != f"{cand.first_name} {cand.last_name}".strip():
                request.user.name = f"{cand.first_name} {cand.last_name}".strip()
                request.user.save(update_fields=["name"])

            messages.success(
                request,
                f"Your candidate profile has been updated successfully! Profile readiness is now {completion_data['percentage']}%.",
            )
            return redirect("candidates:profile")
    else:
        form = CandidateProfileForm(instance=candidate)

    completion_data = candidate.calculate_profile_completion()
    return render(
        request,
        "candidates/profile.html",
        {
            "candidate": candidate,
            "form": form,
            "education_records": education_records,
            "education_form": education_form,
            "completion_data": completion_data,
            "profile_percentage": completion_data["percentage"],
            "is_profile_complete": completion_data["is_complete"],
            "missing_fields": completion_data["missing_fields"],
        },
    )


@login_required
def add_education(request):
    candidate = _candidate_for(request.user)
    if request.method == "POST":
        form = CandidateEducationForm(request.POST, request.FILES)
        if form.is_valid():
            edu = form.save(commit=False)
            edu.candidate = candidate
            edu.save()
            candidate.calculate_profile_completion()
            messages.success(
                request,
                f"Education record '{edu.education_level} - {edu.degree_program}' added successfully.",
            )
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {err}")
    return redirect("candidates:profile")


@login_required
def edit_education(request, education_id):
    candidate = _candidate_for(request.user)
    education = get_object_or_404(CandidateEducation, education_id=education_id, candidate=candidate)
    if request.method == "POST":
        form = CandidateEducationForm(request.POST, request.FILES, instance=education)
        if form.is_valid():
            form.save()
            candidate.calculate_profile_completion()
            messages.success(request, "Education record updated successfully.")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {err}")
        return redirect("candidates:profile")
    else:
        form = CandidateEducationForm(instance=education)
        return render(request, "candidates/edit_education.html", {"form": form, "education": education})


@login_required
def delete_education(request, education_id):
    candidate = _candidate_for(request.user)
    education = get_object_or_404(CandidateEducation, education_id=education_id, candidate=candidate)
    if request.method == "POST":
        degree = f"{education.education_level} - {education.degree_program}"
        education.delete()
        candidate.calculate_profile_completion()
        messages.success(request, f"Education record '{degree}' removed successfully.")
    return redirect("candidates:profile")


@login_required
def take_aptitude_test(request, application_id):
    """Candidate aptitude test view with backend window validation, balanced 3-category questions, timer, and option shuffling."""
    import datetime
    import random
    from hr.models import AptitudeAttempt, AptitudeQuestion, AptitudeResult, AptitudeTest
    from hr.question_bank import seed_default_questions

    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate", "vacancy", "aptitude_test"),
        application_id=application_id,
    )

    # Security check: verify candidate owns this application
    if application.candidate != candidate:
        messages.error(request, "You are not authorized to access this aptitude assessment.")
        return redirect("candidates:applications")

    # If application has already moved past aptitude stage or completed
    if application.status in ["APTITUDE_REVIEW", "INTERVIEW", "SELECTED", "REJECTED"]:
        completed_attempt = AptitudeAttempt.objects.filter(application=application, is_completed=True).first()
        if completed_attempt:
            return redirect("candidates:aptitude_result", application_id=application.pk)
        messages.info(request, f"This application is currently at the {application.get_status_display()} stage.")
        return redirect("candidates:applications")

    now = timezone.now()
    start_dt = application.get_aptitude_start_datetime()
    end_dt = application.get_aptitude_end_datetime()

    # Backend Window Validation: Block Early Access
    if start_dt and now < start_dt:
        messages.warning(
            request,
            f"The aptitude assessment is scheduled for {start_dt.strftime('%B %d, %Y at %I:%M %p')}. The test window is not open yet.",
        )
        return redirect("candidates:applications")

    # Find active test
    test = application.aptitude_test or AptitudeTest.objects.filter(status="ACTIVE").order_by("-created_at").first()
    if not test:
        messages.warning(
            request,
            "No active aptitude assessment is currently available for this position. Please contact HR.",
        )
        return redirect("candidates:applications")

    # Check existing attempt
    attempt = AptitudeAttempt.objects.filter(
        application=application,
        test=test,
    ).first()

    # Backend Window Validation: Block Late Access / Expired window
    if end_dt and now >= end_dt:
        if attempt and not attempt.is_completed:
            # Auto-submit active incomplete attempt
            score = 0
            correct_count = 0
            incorrect_count = 0
            unanswered_count = 0
            cand_answers = attempt.answers_data or {}
            for q in attempt.questions_data:
                qid = str(q.get("question_id"))
                ans = cand_answers.get(qid)
                ck = q.get("correct_key")
                if not ans:
                    unanswered_count += 1
                elif ans == ck:
                    correct_count += 1
                    score += 1
                else:
                    incorrect_count += 1

            total_marks = len(attempt.questions_data)
            percentage = round((score / total_marks * 100), 2) if total_marks > 0 else 0.0
            passing_score = application.aptitude_passing_score if application.aptitude_passing_score is not None else (test.pass_percentage or 50)
            passed = percentage >= passing_score

            attempt.submission_type = "AUTO_SUBMITTED"
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
                    "correct_answers_count": correct_count,
                    "incorrect_answers_count": incorrect_count,
                    "unanswered_count": unanswered_count,
                    "submission_type": "AUTO_SUBMITTED",
                },
            )

            application.status = "APTITUDE_REVIEW"
            application.save(update_fields=["status"])

            send_candidate_notification(
                candidate=candidate,
                application=application,
                title="Aptitude Assessment Submitted",
                message=f"Your aptitude assessment for '{application.vacancy.title}' has been submitted automatically as the time window expired. It is now under review by HR.",
                notification_type="APTITUDE_RESULT",
                link_url=reverse("candidates:aptitude_result", kwargs={"application_id": application.pk}),
            )

            messages.warning(request, "The test window has closed. Your assessment answers have been submitted automatically.")
            return redirect("candidates:aptitude_result", application_id=application.pk)
        elif attempt and attempt.is_completed:
            return redirect("candidates:aptitude_result", application_id=application.pk)
        else:
            messages.error(request, "The test window for this aptitude assessment has closed. You can no longer start this test.")
            return redirect("candidates:applications")

    if attempt:
        if attempt.is_completed:
            return redirect("candidates:aptitude_result", application_id=application.pk)

        # Check if individual attempt timer expired
        if now >= attempt.expires_at:
            # Auto-submit and grade expired attempt
            score = 0
            correct_count = 0
            incorrect_count = 0
            unanswered_count = 0
            cand_answers = attempt.answers_data or {}
            for q in attempt.questions_data:
                qid = str(q.get("question_id"))
                ans = cand_answers.get(qid)
                ck = q.get("correct_key")
                if not ans:
                    unanswered_count += 1
                elif ans == ck:
                    correct_count += 1
                    score += 1
                else:
                    incorrect_count += 1

            total_marks = len(attempt.questions_data)
            percentage = round((score / total_marks * 100), 2) if total_marks > 0 else 0.0
            passing_score = application.aptitude_passing_score if application.aptitude_passing_score is not None else (test.pass_percentage or 50)
            passed = percentage >= passing_score

            attempt.submission_type = "AUTO_SUBMITTED"
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
                    "correct_answers_count": correct_count,
                    "incorrect_answers_count": incorrect_count,
                    "unanswered_count": unanswered_count,
                    "submission_type": "AUTO_SUBMITTED",
                },
            )

            application.status = "APTITUDE_REVIEW"
            application.save(update_fields=["status"])

            send_candidate_notification(
                candidate=candidate,
                application=application,
                title="Aptitude Assessment Submitted",
                message=f"Your aptitude assessment for '{application.vacancy.title}' has been submitted automatically. Your submission is now under review by HR.",
                notification_type="APTITUDE_RESULT",
                link_url=reverse("candidates:aptitude_result", kwargs={"application_id": application.pk}),
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

        # Shuffle questions
        random.shuffle(combined_qs)

        # Shuffle answer options for each question
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

        duration = application.aptitude_duration_minutes or test.duration_minutes or 30
        expires_at = now + datetime.timedelta(minutes=duration)
        if end_dt and expires_at > end_dt:
            expires_at = end_dt

        # Update application status to APTITUDE (In Progress) if not already
        if application.status != "APTITUDE":
            application.status = "APTITUDE"
            application.save(update_fields=["status"])

        attempt = AptitudeAttempt.objects.create(
            test=test,
            application=application,
            expires_at=expires_at,
            questions_data=questions_data,
            answers_data={},
        )

    remaining_seconds = max(0, int((attempt.expires_at - timezone.now()).total_seconds()))
    if end_dt:
        window_remaining = max(0, int((end_dt - timezone.now()).total_seconds()))
        remaining_seconds = min(remaining_seconds, window_remaining)

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
            "saved_answers": attempt.answers_data or {},
            "time_remaining_seconds": remaining_seconds,
            "total_questions": len(display_questions),
        },
    )


@login_required
def save_aptitude_answer_ajax(request, application_id):
    """Save an answer selection incrementally via AJAX."""
    import json
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST method required"}, status=405)

    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate"),
        application_id=application_id,
    )

    if application.candidate != candidate:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    from hr.models import AptitudeAttempt
    attempt = AptitudeAttempt.objects.filter(
        application=application,
        is_completed=False,
    ).first()

    if not attempt:
        return JsonResponse({"success": False, "error": "No active test attempt found."}, status=400)

    now = timezone.now()
    if now >= attempt.expires_at:
        return JsonResponse({"success": False, "error": "Test attempt time has expired."}, status=400)

    # Parse question_id and selected option
    question_id = request.POST.get("question_id")
    selected_option = request.POST.get("selected_option", "").strip().upper()

    if not question_id and request.body:
        try:
            data = json.loads(request.body)
            question_id = data.get("question_id")
            selected_option = (data.get("selected_option") or "").strip().upper()
        except Exception:
            pass

    if not question_id or selected_option not in ["A", "B", "C", "D"]:
        return JsonResponse({"success": False, "error": "Invalid question ID or option."}, status=400)

    answers = dict(attempt.answers_data or {})
    answers[str(question_id)] = selected_option
    attempt.answers_data = answers
    attempt.save(update_fields=["answers_data"])

    return JsonResponse({
        "success": True,
        "question_id": str(question_id),
        "selected_option": selected_option,
        "total_saved": len(answers),
    })


@login_required
def submit_aptitude_test(request, application_id):
    """Handle candidate aptitude test submission and calculate scores securely for HR review only."""
    from hr.models import AptitudeAttempt, AptitudeResult

    if request.method != "POST":
        return redirect("candidates:take_aptitude_test", application_id=application_id)

    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("candidate", "vacancy", "aptitude_test"),
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
    is_auto = request.POST.get("auto_submit") == "true" or (now >= attempt.expires_at)
    sub_type = "AUTO_SUBMITTED" if is_auto else "CANDIDATE_SUBMITTED"

    candidate_answers = dict(attempt.answers_data or {})
    for q in attempt.questions_data:
        qid = str(q.get("question_id"))
        selected = request.POST.get(f"question_{qid}", "").strip().upper()
        if selected in ["A", "B", "C", "D"]:
            candidate_answers[qid] = selected

    score = 0
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0

    for q in attempt.questions_data:
        qid = str(q.get("question_id"))
        cand_ans = candidate_answers.get(qid)
        correct_key = q.get("correct_key")
        if not cand_ans:
            unanswered_count += 1
        elif cand_ans == correct_key:
            correct_count += 1
            score += 1
        else:
            incorrect_count += 1

    total_marks = len(attempt.questions_data)
    percentage = round((score / total_marks * 100), 2) if total_marks > 0 else 0.0
    passing_threshold = application.aptitude_passing_score if application.aptitude_passing_score is not None else ((attempt.test.pass_percentage if attempt.test else None) or 50)
    passed = percentage >= passing_threshold

    attempt.answers_data = candidate_answers
    attempt.submission_type = sub_type
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
            "correct_answers_count": correct_count,
            "incorrect_answers_count": incorrect_count,
            "unanswered_count": unanswered_count,
            "submission_type": sub_type,
        },
    )

    # Transition application status to APTITUDE_REVIEW
    application.status = "APTITUDE_REVIEW"
    application.save(update_fields=["status"])

    # Dispatch notification to candidate WITHOUT any score, percentage, or pass/fail
    send_candidate_notification(
        candidate=candidate,
        application=application,
        title="Aptitude Assessment Submitted",
        message=f"Your aptitude assessment for '{application.vacancy.title}' has been successfully submitted and is currently under review by our recruitment team.",
        notification_type="APTITUDE_RESULT",
        link_url=reverse("candidates:aptitude_result", kwargs={"application_id": application.pk}),
    )

    if is_auto:
        messages.warning(
            request,
            "Your test time has ended. Your assessment has been automatically submitted and is now under review by HR.",
        )
    else:
        messages.success(
            request,
            "Your aptitude assessment has been submitted successfully! Your submission is now under review by the HR recruitment team.",
        )

    return redirect("candidates:aptitude_result", application_id=application.pk)


@login_required
def aptitude_result(request, application_id):
    """View completed aptitude test submission status for candidate (Score protected: HR-Only)."""
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

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("format") == "json":
        return JsonResponse({"success": True, "notification_id": notification_id, "is_read": True})

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


@login_required
def candidate_interview_slots(request, application_id):
    """Displays available physical offline interview slots for candidate to select."""
    from hr.models import InterviewSlot
    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("vacancy", "candidate"),
        pk=application_id,
        candidate=candidate,
    )

    if application.status not in ["INTERVIEW_SCHEDULING", "INTERVIEW_SCHEDULED", "INTERVIEW", "INTERVIEW_REVIEW", "SELECTED"]:
        messages.warning(request, "Interview slot selection is only available for eligible candidates.")
        return redirect("candidates:applications")

    available_slots = InterviewSlot.objects.filter(
        Q(vacancy=application.vacancy) | Q(vacancy__isnull=True),
        status="AVAILABLE",
        interview_date__gte=timezone.localdate(),
    ).select_related("location", "interviewer__user").order_by("interview_date", "start_time")

    booked_interview = application.interviews.select_related("location", "interviewer__user", "slot").order_by("-interview_date").first()

    context = {
        "application": application,
        "candidate": candidate,
        "job": application.vacancy,
        "slots": available_slots,
        "booked_interview": booked_interview,
    }
    return render(request, "candidates/interview_booking.html", context)


@login_required
def candidate_book_slot(request, application_id, slot_id):
    """Handles candidate interview slot selection and atomic confirmation."""
    from hr.models import InterviewSlot, Interview
    candidate = _candidate_for(request.user)
    application = get_object_or_404(
        JobApplication.objects.select_related("vacancy", "candidate"),
        pk=application_id,
        candidate=candidate,
    )

    if request.method != "POST":
        return redirect("candidates:interview_slots", application_id=application.pk)

    if application.status not in ["INTERVIEW_SCHEDULING", "INTERVIEW_SCHEDULED"]:
        messages.error(request, "This application is not in the interview slot selection stage.")
        return redirect("candidates:applications")

    with transaction.atomic():
        slot = InterviewSlot.objects.select_for_update().filter(
            pk=slot_id,
            status="AVAILABLE",
            interview_date__gte=timezone.localdate(),
        ).select_related("location", "interviewer").first()

        if not slot:
            messages.error(request, "This interview slot is no longer available. Please select another slot.")
            return redirect("candidates:interview_slots", application_id=application.pk)

        # Release any previously booked slot for this application
        prev_slot = InterviewSlot.objects.filter(booked_application=application, status="BOOKED").first()
        if prev_slot and prev_slot != slot:
            prev_slot.status = "AVAILABLE"
            prev_slot.booked_by = None
            prev_slot.booked_application = None
            prev_slot.save(update_fields=["status", "booked_by", "booked_application"])

        # Book the chosen slot
        slot.status = "BOOKED"
        slot.booked_by = candidate
        slot.booked_application = application
        slot.save(update_fields=["status", "booked_by", "booked_application"])

        # Create or update Interview record
        interview, _ = Interview.objects.update_or_create(
            application=application,
            defaults={
                "slot": slot,
                "location": slot.location,
                "interviewer": slot.interviewer,
                "interview_type": slot.interview_type,
                "interview_date": slot.interview_date,
                "interview_time": slot.start_time,
                "instructions": slot.instructions,
                "status": "SCHEDULED",
                "attendance": "NOT_MARKED",
            }
        )

        application.status = "INTERVIEW_SCHEDULED"
        application.save(update_fields=["status", "updated_at"])

        formatted_date = slot.interview_date.strftime("%d %B %Y")
        formatted_time = slot.start_time.strftime("%I:%M %p")
        venue_name = slot.location.location_name
        address_text = slot.location.address

        notif_msg = (
            f"Your interview for {application.vacancy.title} has been successfully scheduled.\n\n"
            f"Date: {formatted_date}\n"
            f"Time: {formatted_time}\n"
            f"Venue: {venue_name}\n"
            f"Address: {address_text}\n\n"
            f"Please report to the interview venue at least 10 minutes before the scheduled time."
        )

        send_candidate_notification(
            candidate=candidate,
            application=application,
            title="Interview Scheduled",
            message=notif_msg,
            notification_type="INTERVIEW_SCHEDULED",
            link_url=reverse_lazy("candidates:applications"),
        )

    messages.success(
        request,
        f"🎯 Interview scheduled successfully for {formatted_date} at {formatted_time} at {venue_name}!",
    )
    return redirect("candidates:applications")


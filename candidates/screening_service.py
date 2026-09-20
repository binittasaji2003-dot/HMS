import re
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.urls import reverse
from .models import ResumeScreening, JobApplication, JobVacancy, send_candidate_notification
from .resume_parser import parse_resume



def parse_skills_string(skills_str: str) -> List[str]:
    """Parse comma/newline/semicolon-separated skills string into a clean list preserving original casing for display."""
    if not skills_str:
        return []
    raw_skills = re.split(r"[,;\n\r]+", skills_str)
    cleaned = []
    seen = set()
    for s in raw_skills:
        item = s.strip()
        if item and len(item) > 1 and item.lower() not in seen:
            seen.add(item.lower())
            cleaned.append(item)
    return cleaned


def skill_in_extracted(target_skill: str, extracted_skills: List[str], full_resume_text: str = "") -> bool:
    """Robust matching of a target skill against extracted skills and resume text."""
    target_lower = target_skill.lower().strip()
    if not target_lower:
        return False
    
    # 1. Exact or substring match in extracted skills list
    for es in extracted_skills:
        es_lower = es.lower().strip()
        if target_lower == es_lower:
            return True
        if target_lower in es_lower or es_lower in target_lower:
            # Avoid single letter false positives
            if len(target_lower) >= 3 or target_lower in ["c", "r", "go", "js", "ts", "c#", "c++", "sql", "git"]:
                return True

    # 2. Check in full resume text using word boundary or search pattern
    if full_resume_text:
        text_lower = full_resume_text.lower()
        if target_lower in ["c", "r", "go"]:
            pattern = rf"\b{re.escape(target_lower)}\b"
            if re.search(pattern, text_lower):
                return True
        elif target_lower in ["c++", "c#", ".net"]:
            if target_lower in text_lower:
                return True
        else:
            pattern = rf"\b{re.escape(target_lower)}\b"
            if re.search(pattern, text_lower) or target_lower in text_lower:
                return True

    return False


def screen_job_application(
    application: JobApplication,
    screened_by=None,
    send_notification: bool = True,
) -> ResumeScreening:
    """
    Evaluates and generates a job-specific ResumeScreening record for a specific JobApplication.
    The evaluation strictly compares candidate qualifications, experience, and uploaded resume against
    the requirements of the specific JobVacancy applied to.
    
    If resume extraction fails, the screening is marked for MANUAL_REVIEW and no automatic notification is sent.
    """
    candidate = application.candidate
    vacancy = application.vacancy

    # 0. Check if application was submitted after deadline (late application check)
    is_late_application = False
    if vacancy.closing_date and application.applied_at:
        app_date = application.applied_at.date() if hasattr(application.applied_at, "date") else application.applied_at
        if app_date > vacancy.closing_date:
            is_late_application = True

    # 1. Gather all candidate skills from resume, profile, and application form
    extracted_skills_set = set()
    full_resume_text = ""
    resume_extraction_failed = False

    # Parse resume document if available
    resume_file = application.applied_resume or candidate.resume
    if resume_file:
        try:
            resume_file.seek(0)
            parsed_data = parse_resume(resume_file, getattr(resume_file, "name", ""))
            resume_file.seek(0)
            skills_found = parsed_data.get("skills_list", [])
            if not skills_found and parsed_data.get("skills"):
                skills_found = parse_skills_string(parsed_data.get("skills"))
            if skills_found:
                for sk in skills_found:
                    extracted_skills_set.add(sk)
            full_resume_text = parsed_data.get("raw_text", "")

            # Check if extraction failed (no extractable text/skills, or unreadable document)
            if parsed_data.get("extraction_failed") or (
                not skills_found and not parsed_data.get("skills") and not parsed_data.get("email") and not parsed_data.get("phone") and len(full_resume_text.strip()) < 30
            ):
                resume_extraction_failed = True
        except Exception:
            resume_extraction_failed = True
    else:
        # No resume document available
        pass

    # Profile skills
    if candidate.skills:
        for sk in parse_skills_string(candidate.skills):
            extracted_skills_set.add(sk)

    # Application specific skills
    if getattr(application, "applied_skills", None):
        for sk in parse_skills_string(application.applied_skills):
            extracted_skills_set.add(sk)

    extracted_skills_list = sorted(list(extracted_skills_set), key=lambda s: s.lower())

    # 2. Required Skills Match (Mandatory)
    required_skills_list = parse_skills_string(vacancy.skills_required or "")
    required_skills_data = []
    missing_requirements = []
    req_matched_count = 0

    for req_skill in required_skills_list:
        matched = skill_in_extracted(req_skill, extracted_skills_list, full_resume_text)
        if matched:
            req_matched_count += 1
        else:
            missing_requirements.append(req_skill)
        required_skills_data.append({
            "skill": req_skill,
            "matched": matched,
        })

    required_skills_passed = (req_matched_count == len(required_skills_list)) if required_skills_list else True

    # 3. Preferred Skills Match (Optional / Bonus)
    preferred_skills_list = parse_skills_string(vacancy.preferred_skills or "")
    preferred_skills_data = []
    pref_matched_count = 0

    for pref_skill in preferred_skills_list:
        matched = skill_in_extracted(pref_skill, extracted_skills_list, full_resume_text)
        if matched:
            pref_matched_count += 1
        preferred_skills_data.append({
            "skill": pref_skill,
            "matched": matched,
        })

    # 4. Educational Qualification Match
    edu_level_rank = {
        "Doctorate / PhD": 5,
        "M.Phil": 4.5,
        "Master's": 4,
        "Bachelor's": 3,
        "Diploma": 2,
        "Other": 1,
    }

    candidate_edus = list(candidate.education_records.all()) if hasattr(candidate, "education_records") else []
    highest_rank = 0
    candidate_highest_edu_str = "None Recorded"
    candidate_field_str = ""
    candidate_grad_year = None

    for edu in candidate_edus:
        rank = edu_level_rank.get(edu.education_level, 1)
        if rank > highest_rank:
            highest_rank = rank
            candidate_highest_edu_str = f"{edu.degree_program or edu.education_level}"
            candidate_field_str = edu.field_of_study or edu.degree_program
            candidate_grad_year = edu.completion_year

    # Check required qualification
    req_qual_level = vacancy.minimum_qualification or "Bachelor's"
    req_rank = edu_level_rank.get(req_qual_level, 3)

    # Check if vacancy.qualifications text specifies a higher degree
    vac_qual_desc = (vacancy.qualifications or "").lower()
    if "phd" in vac_qual_desc or "doctorate" in vac_qual_desc:
        req_rank = max(req_rank, 5)
    elif any(m in vac_qual_desc for m in ["master", "m.tech", "mca", "mba", "msc", "m.sc"]):
        req_rank = max(req_rank, 4)
    elif any(b in vac_qual_desc for b in ["bachelor", "graduate", "b.tech", "bca", "b.sc", "degree"]):
        req_rank = max(req_rank, 3)

    education_matched = True
    education_remarks = "Qualification matches vacancy requirements."

    if highest_rank < req_rank:
        # Check text fallback keywords in highest edu text
        qual_matched = False
        if req_rank >= 5 and any(k in candidate_highest_edu_str.lower() for k in ["phd", "ph.d", "doctorate"]):
            qual_matched = True
        elif req_rank >= 4 and any(k in candidate_highest_edu_str.lower() for k in ["master", "mca", "mba", "m.tech", "msc", "m.sc"]):
            qual_matched = True
        elif req_rank == 3 and any(k in candidate_highest_edu_str.lower() for k in ["bachelor", "bca", "bba", "b.tech", "bsc", "b.sc", "b.com", "be", "b.e"]):
            qual_matched = True
        elif req_rank == 2 and "diploma" in candidate_highest_edu_str.lower():
            qual_matched = True

        if not qual_matched:
            education_matched = False
            education_remarks = f"Required: {req_qual_level}. Candidate has: {candidate_highest_edu_str}."
            missing_requirements.append(f"Qualification ({req_qual_level})")

    # 5. Field of Study Match
    req_field = vacancy.required_field_of_study
    field_matched = True
    if req_field and req_field != "Other":
        field_matched = False
        for edu in candidate_edus:
            if edu.field_of_study == req_field or req_field.lower() in (edu.degree_program or "").lower():
                field_matched = True
                break
        if not field_matched:
            missing_requirements.append(f"Field of Study ({req_field})")

    # 6. Graduation Year Match
    grad_min = vacancy.graduation_year_min
    grad_max = vacancy.graduation_year_max
    grad_matched = True
    grad_remarks = "Graduation year meets criteria."
    req_grad_range = ""

    if grad_min and grad_max:
        req_grad_range = f"{grad_min} – {grad_max}"
    elif grad_min:
        req_grad_range = f"{grad_min} or later"
    elif grad_max:
        req_grad_range = f"Up to {grad_max}"

    if (grad_min or grad_max) and candidate_grad_year:
        if grad_min and candidate_grad_year < grad_min:
            grad_matched = False
            grad_remarks = f"Graduation year ({candidate_grad_year}) is earlier than minimum ({grad_min})."
            missing_requirements.append(f"Graduation Year ({req_grad_range})")
        elif grad_max and candidate_grad_year > grad_max:
            grad_matched = False
            grad_remarks = f"Graduation year ({candidate_grad_year}) is later than maximum ({grad_max})."
            missing_requirements.append(f"Graduation Year ({req_grad_range})")

    # 7. Work Experience Match
    exp_required_bool = vacancy.experience_required_bool
    min_exp_years = vacancy.minimum_experience or 0.0

    # Fallback to textual experience parsing if needed
    if not exp_required_bool and min_exp_years == 0 and vacancy.experience_required:
        from .eligibility import parse_min_experience_years
        text_min = parse_min_experience_years(vacancy.experience_required)
        if text_min > 0:
            min_exp_years = text_min
            exp_required_bool = True

    cand_years = float(candidate.total_experience_years or 0)
    cand_months = float(candidate.total_experience_months or 0)
    total_cand_exp = cand_years + (cand_months / 12.0)

    candidate_exp_disp = "Fresher" if total_cand_exp == 0 else f"{total_cand_exp:.1f} years"
    experience_matched = True
    experience_remarks = "Experience meets vacancy criteria."
    req_exp_display = vacancy.experience_display

    if exp_required_bool and min_exp_years > 0:
        if total_cand_exp < min_exp_years:
            if (min_exp_years - total_cand_exp) > 0.5:
                experience_matched = False
                experience_remarks = f"Minimum {min_exp_years:g} years required. Candidate has {candidate_exp_disp}."
                missing_requirements.append(f"Experience ({min_exp_years:g}+ Years)")
            else:
                experience_remarks = f"Experience is slightly under {min_exp_years:g} years ({total_cand_exp:.1f} yrs), eligible for review."

    # 8. Calculate overall match score percentage based on job-specific criteria
    score_weights = []
    # Required skills weight (50%)
    if required_skills_list:
        score_weights.append((req_matched_count / len(required_skills_list)) * 50.0)
    else:
        score_weights.append(50.0)

    # Education weight (20%)
    score_weights.append(20.0 if education_matched else 5.0)

    # Experience weight (20%)
    score_weights.append(20.0 if experience_matched else 5.0)

    # Preferred skills weight (10%)
    if preferred_skills_list:
        score_weights.append((pref_matched_count / len(preferred_skills_list)) * 10.0)
    else:
        score_weights.append(10.0)

    total_score = round(sum(score_weights), 1)

    from django.conf import settings
    SHORTLIST_THRESHOLD = float(getattr(settings, "SHORTLIST_THRESHOLD", 70.0))

    # 9. Final Screening Decision based on Match Score & Threshold
    if is_late_application:
        status = "NOT_SHORTLISTED"
        decision_reason = f"Application was submitted after the deadline ({vacancy.closing_date}) for {vacancy.title} had expired."
    elif resume_extraction_failed:
        status = "MANUAL_REVIEW"
        decision_reason = "Resume file extraction failed or document format unreadable. Manual review required by HR."
    else:
        if total_score > SHORTLIST_THRESHOLD:
            status = "SHORTLISTED"
            decision_reason = f"Candidate achieved a match score of {total_score:g}% (above {SHORTLIST_THRESHOLD:g}% threshold) based on job requirements for {vacancy.title}."
        else:
            status = "NOT_SHORTLISTED"
            decision_reason = f"Candidate achieved a match score of {total_score:g}% (does not meet the {SHORTLIST_THRESHOLD:g}% threshold) for {vacancy.title}."

    # 10. Create or update ResumeScreening record
    screening, _ = ResumeScreening.objects.update_or_create(
        application=application,
        defaults={
            "status": status,
            "match_score": total_score,
            "required_skills_total": len(required_skills_list),
            "required_skills_matched": req_matched_count,
            "required_skills_data": required_skills_data,
            "preferred_skills_total": len(preferred_skills_list),
            "preferred_skills_matched": pref_matched_count,
            "preferred_skills_data": preferred_skills_data,
            "extracted_skills": extracted_skills_list,
            "education_matched": education_matched,
            "required_education": req_qual_level,
            "candidate_education": candidate_highest_edu_str,
            "education_remarks": education_remarks,
            "field_of_study_matched": field_matched,
            "required_field_of_study": req_field or "Any / Relevant",
            "candidate_field_of_study": candidate_field_str or "Not Specified",
            "graduation_year_matched": grad_matched,
            "required_graduation_range": req_grad_range or "Any",
            "candidate_graduation_year": str(candidate_grad_year) if candidate_grad_year else "Not Specified",
            "graduation_remarks": grad_remarks,
            "experience_matched": experience_matched,
            "required_experience": req_exp_display,
            "candidate_experience": candidate_exp_disp,
            "experience_remarks": experience_remarks,
            "decision_reason": decision_reason,
            "missing_requirements": missing_requirements,
            "screened_by": screened_by,
        },
    )

    # 11. Update JobApplication status to reflect screening outcome
    if status == "SHORTLISTED" and application.status in ["APPLIED", "RESUME_REVIEW"]:
        application.status = "SHORTLISTED"
        application.save(update_fields=["status", "updated_at"])
    elif status == "NOT_SHORTLISTED" and application.status in ["APPLIED", "RESUME_REVIEW"]:
        application.status = "REJECTED"
        application.save(update_fields=["status", "updated_at"])

    # 12. Automatic Candidate Notifications (deduplicated)
    if send_notification:
        try:
            applications_url = reverse("candidates:applications")
        except Exception:
            applications_url = "/candidates/applications/"

        if status == "SHORTLISTED":
            shortlist_title = "Congratulations! You have been shortlisted"
            shortlist_msg = (
                f"Congratulations! Your resume has been shortlisted for the {vacancy.title} position.\n\n"
                f"Your resume screening score is {total_score:g}%.\n\n"
                f"You have successfully moved to the next step of the recruitment process.\n\n"
                f"Next Step:\nAptitude Round\n\n"
                f"Please check your Candidate Portal for further details."
            )
            send_candidate_notification(
                candidate=candidate,
                application=application,
                title=shortlist_title,
                message=shortlist_msg,
                notification_type="SHORTLISTED",
                link_url=applications_url,
            )
        elif status == "NOT_SHORTLISTED":
            not_shortlist_title = "Application Update"
            not_shortlist_msg = (
                f"Thank you for applying for the {vacancy.title} position.\n\n"
                f"Your application has been reviewed against the requirements for this position.\n\n"
                f"At this time, your application has not been shortlisted for the next stage of the recruitment process.\n\n"
                f"We appreciate your interest and encourage you to apply for other suitable opportunities."
            )
            send_candidate_notification(
                candidate=candidate,
                application=application,
                title=not_shortlist_title,
                message=not_shortlist_msg,
                notification_type="NOT_SHORTLISTED",
                link_url=applications_url,
            )
        # For MANUAL_REVIEW / EXTRACTION_FAILED, do NOT send automated notifications.

    return screening


def run_resume_screening(
    job: JobVacancy,
    force_rescreen: bool = False,
    screened_by=None,
    send_notification: bool = True,
) -> Dict[str, Any]:
    """
    Batch screening service for all applications of a specific JobVacancy.
    Idempotent: Running multiple times does not duplicate screening records or notifications.
    """
    # 1. Update status if deadline has expired
    job.check_and_update_status()

    # 2. Retrieve applications for this specific job vacancy
    applications_qs = job.applications.select_related("candidate__user", "screening_result").order_by("applied_at")

    stats = {
        "total": 0,
        "shortlisted": 0,
        "not_shortlisted": 0,
        "manual_review": 0,
        "skipped": 0,
    }

    for app in applications_qs:
        has_screening = hasattr(app, "screening_result")
        if not force_rescreen and has_screening and app.screening_result.status:
            # Already screened
            stats["total"] += 1
            scr_status = app.screening_result.status
            if scr_status == "SHORTLISTED":
                stats["shortlisted"] += 1
            elif scr_status == "NOT_SHORTLISTED":
                stats["not_shortlisted"] += 1
            else:
                stats["manual_review"] += 1
            continue

        screening = screen_job_application(
            application=app,
            screened_by=screened_by,
            send_notification=send_notification,
        )
        stats["total"] += 1
        if screening.status == "SHORTLISTED":
            stats["shortlisted"] += 1
        elif screening.status == "NOT_SHORTLISTED":
            stats["not_shortlisted"] += 1
        else:
            stats["manual_review"] += 1

    return stats

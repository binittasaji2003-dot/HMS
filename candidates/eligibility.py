import re
from typing import Dict, Any, List


def parse_min_experience_years(exp_str: str) -> float:
    """Extract minimum required experience years from text string."""
    if not exp_str:
        return 0.0
    exp_lower = exp_str.lower().strip()
    if "fresher" in exp_lower or "0" in exp_lower and ("-" not in exp_lower or exp_lower.startswith("0")):
        return 0.0
    
    # Check for patterns like "3-5 years", "2 - 4 yrs", "3+ years", "5 years"
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*\d+", exp_lower)
    if match:
        return float(match.group(1))
    
    match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)", exp_lower)
    if match:
        return float(match.group(1))
    
    digits = re.findall(r"\d+(?:\.\d+)?", exp_lower)
    if digits:
        return float(digits[0])
    
    return 0.0


def parse_skills_list(skills_str: str) -> List[str]:
    """Parse comma/newline/semicolon-separated skills string into a normalized list."""
    if not skills_str:
        return []
    parts = re.split(r"[,;\n\r]+", skills_str)
    skills = []
    for p in parts:
        cleaned = p.strip().lower()
        if cleaned and len(cleaned) > 1:
            skills.append(cleaned)
    return skills


def evaluate_eligibility(candidate, vacancy, application_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Evaluates candidate eligibility against structured job vacancy requirements.
    Returns:
    {
        "is_eligible": bool,
        "status": "ELIGIBLE" | "NOT_ELIGIBLE",
        "score_percentage": int,
        "reasons": List[str],
        "checklist": List[Dict],
        "summary": str
    }
    """
    if application_data is None:
        application_data = {}

    checklist = []
    failed_reasons = []
    all_mandatory_passed = True

    # 1. Profile Completion Check
    completion_pct = getattr(candidate, "calculate_completion_percentage", lambda: 100)()
    profile_ready = completion_pct >= 50 or getattr(candidate, "profile_completed", False)
    if not profile_ready:
        all_mandatory_passed = False
        failed_reasons.append("Candidate profile is incomplete (minimum 50% required).")
    checklist.append({
        "category": "Profile",
        "label": "Profile Completion",
        "required": "Minimum 50% completed profile",
        "actual": f"{completion_pct}% completed",
        "passed": profile_ready,
        "is_mandatory": True,
        "remarks": "Profile complete." if profile_ready else "Candidate profile is incomplete (minimum 50% required)."
    })

    # 2. Educational Qualification Check
    candidate_edus = list(candidate.education_records.all()) if hasattr(candidate, "education_records") else []
    
    edu_level_rank = {
        "Doctorate / PhD": 5,
        "M.Phil": 4.5,
        "Master's": 4,
        "Bachelor's": 3,
        "Diploma": 2,
        "Other": 1
    }
    
    actual_highest_degree = "None recorded"
    actual_field = ""
    actual_completion_year = None
    highest_rank = 0

    for edu in candidate_edus:
        rank = edu_level_rank.get(edu.education_level, 1)
        if rank > highest_rank:
            highest_rank = rank
            actual_highest_degree = f"{edu.education_level} ({edu.degree_program or edu.field_of_study})"
            actual_field = edu.field_of_study or edu.degree_program
            actual_completion_year = edu.completion_year

    if application_data.get("degree_program") and actual_highest_degree == "None recorded":
        actual_highest_degree = application_data.get("degree_program")

    # Determine required qualification level
    req_qual_level = getattr(vacancy, "minimum_qualification", None)
    req_rank = edu_level_rank.get(req_qual_level, 0) if req_qual_level else 0
    vac_qual_desc = getattr(vacancy, "qualifications", "") or ""

    if vac_qual_desc:
        vac_qual_lower = vac_qual_desc.lower()
        if "phd" in vac_qual_lower or "doctorate" in vac_qual_lower:
            req_rank = max(req_rank, 5)
        elif "master" in vac_qual_lower or "m.tech" in vac_qual_lower or "mca" in vac_qual_lower or "mba" in vac_qual_lower or "msc" in vac_qual_lower or "m.sc" in vac_qual_lower:
            req_rank = max(req_rank, 4)
        elif "bachelor" in vac_qual_lower or "graduate" in vac_qual_lower or "b.tech" in vac_qual_lower or "bca" in vac_qual_lower or "b.sc" in vac_qual_lower or "degree" in vac_qual_lower:
            req_rank = max(req_rank, 3)

    edu_passed = True
    edu_remarks = "Qualification matches vacancy criteria."

    if req_rank > 0:
        if highest_rank < req_rank:
            # Check text fallback in actual_highest_degree
            qual_matched = False
            if req_rank >= 5 and any(k in actual_highest_degree.lower() for k in ["phd", "ph.d", "doctorate"]):
                qual_matched = True
            elif req_rank >= 4 and any(k in actual_highest_degree.lower() for k in ["master", "mca", "mba", "m.tech", "msc", "m.sc"]):
                qual_matched = True
            elif req_rank == 3 and any(k in actual_highest_degree.lower() for k in ["bachelor", "bca", "bba", "b.tech", "bsc", "b.sc", "b.com", "be", "b.e"]):
                qual_matched = True
            elif req_rank == 2 and "diploma" in actual_highest_degree.lower():
                qual_matched = True

            if not qual_matched:
                edu_passed = False
                qual_display = req_qual_level if req_qual_level and edu_level_rank.get(req_qual_level, 0) == req_rank else (vac_qual_desc or "Higher Degree")
                edu_remarks = f"Required qualification: {qual_display}. Candidate qualification: {actual_highest_degree}."

    if not edu_passed:
        all_mandatory_passed = False
        failed_reasons.append(edu_remarks)

    checklist.append({
        "category": "Education",
        "label": "Educational Qualification",
        "required": req_qual_level or vac_qual_desc or "Any Graduate / Relevant Degree",
        "actual": actual_highest_degree,
        "passed": edu_passed,
        "is_mandatory": True,
        "remarks": edu_remarks
    })

    # 3. Field of Study Check (if specified)
    req_field = getattr(vacancy, "required_field_of_study", None)
    if req_field and req_field != "Other":
        field_passed = False
        for edu in candidate_edus:
            if edu.field_of_study == req_field or req_field.lower() in (edu.degree_program or "").lower():
                field_passed = True
                break
        if not field_passed and not candidate_edus:
            field_passed = False
        
        field_remarks = f"Field of Study matches {req_field}." if field_passed else f"Preferred Field: {req_field}. Candidate Field: {actual_field or 'Not Specified'}."
        checklist.append({
            "category": "Education",
            "label": "Field of Study",
            "required": req_field,
            "actual": actual_field or "General",
            "passed": field_passed,
            "is_mandatory": False,  # Field of study is evaluated as preferred
            "remarks": field_remarks
        })

    # 4. Graduation Year Eligibility Check (if specified)
    grad_min = getattr(vacancy, "graduation_year_min", None)
    grad_max = getattr(vacancy, "graduation_year_max", None)
    if grad_min or grad_max:
        year_passed = True
        year_remarks = "Graduation year meets requirements."
        if actual_completion_year:
            if grad_min and actual_completion_year < grad_min:
                year_passed = False
                year_remarks = f"Graduation year ({actual_completion_year}) is earlier than required minimum ({grad_min})."
            elif grad_max and actual_completion_year > grad_max:
                year_passed = False
                year_remarks = f"Graduation year ({actual_completion_year}) is later than required maximum ({grad_max})."
        
        if not year_passed:
            all_mandatory_passed = False
            failed_reasons.append(year_remarks)

        req_year_str = f"{grad_min or 'Any'} - {grad_max or 'Present'}"
        checklist.append({
            "category": "Education",
            "label": "Graduation Year",
            "required": req_year_str,
            "actual": str(actual_completion_year) if actual_completion_year else "Not specified",
            "passed": year_passed,
            "is_mandatory": True,
            "remarks": year_remarks
        })

    # 5. Work Experience Check
    exp_required_bool = getattr(vacancy, "experience_required_bool", False)
    min_exp_years = getattr(vacancy, "minimum_experience", 0.0) or 0.0
    vac_exp_str = getattr(vacancy, "experience_required", "") or ""
    text_min_exp = parse_min_experience_years(vac_exp_str)

    if text_min_exp > 0 and min_exp_years == 0:
        min_exp_years = text_min_exp
        exp_required_bool = True

    # Check if application_data supplied fresher choice
    is_fresher_input = application_data.get("is_fresher")
    if is_fresher_input in [True, "Yes", "yes", "true", "True"]:
        total_candidate_years = 0.0
    else:
        candidate_years = float(candidate.total_experience_years or 0)
        candidate_months = float(candidate.total_experience_months or 0)
        total_candidate_years = candidate_years + (candidate_months / 12.0)

        if application_data.get("total_experience_years") is not None:
            try:
                app_years = float(application_data.get("total_experience_years"))
                app_months = float(application_data.get("total_experience_months") or 0)
                calc_years = app_years + (app_months / 12.0)
                if calc_years > 0:
                    total_candidate_years = calc_years
            except ValueError:
                pass

    exp_passed = True
    exp_remarks = "Experience meets vacancy requirement."
    if exp_required_bool and min_exp_years > 0:
        if total_candidate_years < min_exp_years:
            if (min_exp_years - total_candidate_years) > 0.5:
                exp_passed = False
                candidate_exp_disp = "Fresher" if total_candidate_years == 0 else f"{total_candidate_years:.1f} years"
                exp_remarks = f"Minimum experience required: {min_exp_years:g} years. Candidate experience: {candidate_exp_disp}."
            else:
                exp_remarks = f"Experience is slightly under {min_exp_years:g} years ({total_candidate_years:.1f} yrs), eligible for review."
    elif not exp_required_bool and min_exp_years == 0:
        exp_remarks = "Freshers & all experience levels are welcome."

    if not exp_passed:
        all_mandatory_passed = False
        failed_reasons.append(exp_remarks)

    checklist.append({
        "category": "Experience",
        "label": "Work Experience",
        "required": getattr(vacancy, "experience_display", "Fresher / Any Experience"),
        "actual": f"{total_candidate_years:.1f} years" if total_candidate_years > 0 else "Fresher",
        "passed": exp_passed,
        "is_mandatory": True,
        "remarks": exp_remarks
    })

    # 6. Core & Preferred Skills Match Check
    vac_skills = parse_skills_list(getattr(vacancy, "skills_required", "") or "")
    pref_skills = parse_skills_list(getattr(vacancy, "preferred_skills", "") or "")
    candidate_skills_str = f"{candidate.skills or ''} {application_data.get('applied_skills', '')} {application_data.get('skills', '')}"
    candidate_skills = parse_skills_list(candidate_skills_str)

    matched_skills = []
    for vs in vac_skills:
        if any(vs in cs or cs in vs for cs in candidate_skills):
            matched_skills.append(vs)

    skills_passed = True
    if vac_skills:
        match_ratio = len(matched_skills) / len(vac_skills)
        if match_ratio < 0.2 and len(vac_skills) >= 3:
            skills_passed = True  # Skills are preferred, do not block application
            skills_remarks = f"Matched {len(matched_skills)} of {len(vac_skills)} core skills."
        else:
            skills_remarks = f"Matched {len(matched_skills)}/{len(vac_skills)} core skills: {', '.join(matched_skills) if matched_skills else 'General fit'}."
    else:
        skills_remarks = "General role competencies."

    checklist.append({
        "category": "Skills",
        "label": "Core Skills Match",
        "required": getattr(vacancy, "skills_required", "General") or "General",
        "actual": f"{len(matched_skills)} matched" if matched_skills else "General",
        "passed": skills_passed,
        "is_mandatory": False,
        "remarks": skills_remarks
    })

    # Optional preferred skills match
    if pref_skills:
        matched_pref = [ps for ps in pref_skills if any(ps in cs or cs in ps for cs in candidate_skills)]
        checklist.append({
            "category": "Skills",
            "label": "Preferred Skills Bonus",
            "required": getattr(vacancy, "preferred_skills", ""),
            "actual": f"{len(matched_pref)}/{len(pref_skills)} preferred skills matched",
            "passed": len(matched_pref) > 0,
            "is_mandatory": False,
            "remarks": f"Matched {len(matched_pref)} bonus skills: {', '.join(matched_pref) if matched_pref else 'None'}."
        })

    is_eligible = all_mandatory_passed
    status = "ELIGIBLE" if is_eligible else "NOT_ELIGIBLE"

    if is_eligible:
        summary = "You are eligible to apply for this position."
    else:
        summary = "You are not eligible to apply for this position."

    total_checks = len(checklist)
    passed_checks = sum(1 for item in checklist if item["passed"])
    score_pct = int((passed_checks / total_checks) * 100) if total_checks else 100

    return {
        "is_eligible": is_eligible,
        "status": status,
        "score_percentage": score_pct,
        "reasons": failed_reasons,
        "checklist": checklist,
        "summary": summary
    }

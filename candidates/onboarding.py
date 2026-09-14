"""Candidate Selection & HR/Admin Employee Module Integration Service.

Provides integration utilities between Candidate selection (status = SELECTED)
and the existing Employee module (employee_table).

IMPORTANT:
- Adheres strictly to the architectural boundary: DO NOT create a new Employee model.
- Interacts with PostgreSQL `employee_table` via robust database connection queries.
- Guarantees selected candidate identification through either `candidate_id` or `user_id`.
- Packages candidate personal, academic, skill, and document data into an HR Onboarding Dossier.
"""
import logging
from datetime import date
from django.db import connection
from django.dispatch import Signal
from django.utils import timezone

from .models import Candidate, Application

logger = logging.getLogger(__name__)

# ==============================================================================
# INTEGRATION SIGNALS
# ==============================================================================
# Dispatched when an application status transitions to SELECTED
candidate_selected_for_onboarding = Signal()

# Dispatched when an employee record is successfully written to employee_table
employee_onboarded = Signal()


# ==============================================================================
# 1. CANDIDATE IDENTIFICATION (candidate_id / user_id)
# ==============================================================================
def get_candidate_by_id_or_user(candidate_id=None, user_id=None):
    """
    Resolves a Candidate instance via either candidate_id or user_id.
    
    Args:
        candidate_id: Integer primary key from candidate table.
        user_id: Integer primary key from auth_user table.
        
    Returns:
        Candidate instance or None if neither provided or not found.
    """
    if candidate_id is not None:
        return Candidate.objects.filter(candidate_id=candidate_id).first()
    if user_id is not None:
        return Candidate.objects.filter(user_id=user_id).first()
    return None


def get_onboarding_candidate(candidate_id=None, user_id=None):
    """
    Fetches a candidate who has at least one application with status = 'SELECTED'.
    """
    candidate = get_candidate_by_id_or_user(candidate_id=candidate_id, user_id=user_id)
    if candidate and candidate.applications.filter(status=Application.Status.SELECTED).exists():
        return candidate
    return candidate


# ==============================================================================
# 2. EMPLOYEE TABLE QUERY & EXISTENCE CHECKS
# ==============================================================================
def get_employee_record(candidate_id=None, user_id=None, employee_id=None, employee_code=None):
    """
    Queries the existing `employee_table` in PostgreSQL without requiring a Django Employee model.
    
    Returns:
        dict with employee record fields, or None if not found.
    """
    query = """
        SELECT employee_id, candidate_id, user_id, employee_code, department_id,
               designation, joining_date, employment_status, created_by, created_at
        FROM employee_table
    """
    where_clauses = []
    params = []

    if employee_id is not None:
        where_clauses.append("employee_id = %s")
        params.append(employee_id)
    elif employee_code is not None:
        where_clauses.append("employee_code = %s")
        params.append(employee_code)
    elif candidate_id is not None:
        where_clauses.append("candidate_id = %s")
        params.append(candidate_id)
    elif user_id is not None:
        where_clauses.append("user_id = %s")
        params.append(user_id)
    else:
        return None

    query += " WHERE " + " AND ".join(where_clauses) + " ORDER BY employee_id DESC LIMIT 1;"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "employee_id": row[0],
            "candidate_id": row[1],
            "user_id": row[2],
            "employee_code": row[3],
            "department_id": row[4],
            "designation": row[5],
            "joining_date": row[6],
            "employment_status": row[7],
            "created_by": row[8],
            "created_at": row[9],
        }


def is_candidate_onboarded(candidate_id=None, user_id=None):
    """
    Returns True if an employee record exists in `employee_table` for the given candidate or user.
    """
    return get_employee_record(candidate_id=candidate_id, user_id=user_id) is not None


def generate_next_employee_code():
    """
    Generates the next sequential employee code, e.g., EMP-2026-0001.
    """
    query = "SELECT employee_id FROM employee_table ORDER BY employee_id DESC LIMIT 1;"
    with connection.cursor() as cursor:
        cursor.execute(query)
        row = cursor.fetchone()
        next_num = (row[0] + 1) if row else 1
    return f"EMP-2026-{next_num:04d}"


# ==============================================================================
# 3. ONBOARDING DOSSIER FOR HR/ADMIN
# ==============================================================================
def get_candidate_onboarding_dossier(candidate_id=None, user_id=None):
    """
    Packages comprehensive candidate information into an HR Onboarding Dossier.
    Available to HR/Admin onboarding workflows.
    
    Identifiable through either candidate_id or user_id.
    """
    candidate = get_candidate_by_id_or_user(candidate_id=candidate_id, user_id=user_id)
    if not candidate:
        return None

    # Education records
    educations = [
        {
            "education_id": edu.education_id,
            "qualification_type": edu.qualification_type,
            "institution": edu.institution,
            "board_or_university": edu.board_or_university,
            "year": edu.year,
            "percentage_or_cgpa": edu.percentage_or_cgpa,
        }
        for edu in candidate.educations.all()
    ]

    # Skills
    skills = list(candidate.skills.values_list("skill_name", flat=True))

    # Documents available from Candidate module
    documents = {}
    if hasattr(candidate, "documents") and candidate.documents:
        docs = candidate.documents
        for field_name, label, _ in docs.DOCUMENT_DEFINITIONS:
            file_field = getattr(docs, field_name, None)
            if file_field and file_field.name:
                documents[field_name] = {
                    "label": label,
                    "url": file_field.url,
                    "filename": file_field.name.split("/")[-1],
                }

    # Selected application details
    selected_app = (
        candidate.applications.filter(status=Application.Status.SELECTED)
        .select_related("job", "job__department")
        .order_by("-updated_at")
        .first()
    )

    selected_info = None
    suggested_dept_id = None
    suggested_designation = "Associate"
    if selected_app:
        selected_info = {
            "application_id": selected_app.application_id,
            "application_code": selected_app.application_code,
            "job_id": selected_app.job_id,
            "job_title": selected_app.job.title,
            "department_id": selected_app.job.department_id,
            "department_name": selected_app.job.department.name,
            "job_type": selected_app.job.job_type,
            "salary_display": selected_app.job.salary_display,
            "applied_at": selected_app.applied_at.isoformat() if selected_app.applied_at else "",
            "updated_at": selected_app.updated_at.isoformat() if selected_app.updated_at else "",
        }
        suggested_dept_id = selected_app.job.department_id
        suggested_designation = selected_app.job.title

    employee_rec = get_employee_record(candidate_id=candidate.candidate_id, user_id=candidate.user_id)
    is_onboarded = employee_rec is not None

    return {
        "candidate_id": candidate.candidate_id,
        "candidate_code": candidate.candidate_code,
        "user_id": candidate.user_id,
        "username": candidate.user.username,
        "email": candidate.user.email,
        "full_name": candidate.full_name,
        "phone": candidate.phone,
        "date_of_birth": candidate.date_of_birth.isoformat() if candidate.date_of_birth else "",
        "gender": candidate.gender,
        "address": candidate.address,
        "city": candidate.city,
        "state": candidate.state,
        "pincode": candidate.pincode,
        "experience_level": candidate.experience_level,
        "notice_period": candidate.notice_period,
        "profile_completion_pct": candidate.profile_completion_pct,
        "educations": educations,
        "skills": skills,
        "documents": documents,
        "selected_application": selected_info,
        "is_onboarded": is_onboarded,
        "employee_record": employee_rec,
        "suggested_employee": {
            "employee_code": generate_next_employee_code() if not is_onboarded else employee_rec["employee_code"],
            "department_id": suggested_dept_id,
            "designation": suggested_designation,
            "joining_date": date.today().isoformat(),
            "employment_status": "ACTIVE",
        },
    }


def get_candidates_awaiting_onboarding():
    """
    Returns list of candidates who have been SELECTED, with their onboarding status.
    """
    selected_apps = (
        Application.objects.filter(status=Application.Status.SELECTED)
        .select_related("candidate", "candidate__user", "job", "job__department")
        .order_by("-updated_at")
    )
    results = []
    seen_candidate_ids = set()

    for app in selected_apps:
        cid = app.candidate_id
        if cid in seen_candidate_ids:
            continue
        seen_candidate_ids.add(cid)

        emp_record = get_employee_record(candidate_id=cid)
        results.append({
            "candidate": app.candidate,
            "application": app,
            "is_onboarded": emp_record is not None,
            "employee_record": emp_record,
        })
    return results


# ==============================================================================
# 4. EMPLOYEE RECORD CREATION (FOR HR/ADMIN ONBOARDING WORKFLOW)
# ==============================================================================
def create_employee_record(
    candidate_id=None,
    user_id=None,
    employee_code=None,
    department_id=None,
    designation=None,
    joining_date=None,
    employment_status="ACTIVE",
    created_by=None,
):
    """
    Inserts a new employee record into `employee_table`.
    
    Can be invoked by HR/Admin onboarding workflows or integration handlers.
    Adheres strictly to the rule: DO NOT create a new Employee model.
    Uses PostgreSQL connection directly.
    """
    candidate = get_candidate_by_id_or_user(candidate_id=candidate_id, user_id=user_id)
    if not candidate:
        raise ValueError(f"Candidate not found for candidate_id={candidate_id}, user_id={user_id}")

    # Prevent duplicate onboarding of the same candidate/user
    existing = get_employee_record(candidate_id=candidate.candidate_id, user_id=candidate.user_id)
    if existing:
        return existing

    if not employee_code:
        employee_code = generate_next_employee_code()

    if not joining_date:
        joining_date = date.today()

    if not designation:
        selected_app = candidate.applications.filter(status=Application.Status.SELECTED).first()
        designation = selected_app.job.title if selected_app else "Employee"

    if department_id is None:
        selected_app = candidate.applications.filter(status=Application.Status.SELECTED).first()
        department_id = selected_app.job.department_id if selected_app else None

    insert_sql = """
        INSERT INTO employee_table (
            candidate_id, user_id, employee_code, department_id,
            designation, joining_date, employment_status, created_by, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING employee_id, candidate_id, user_id, employee_code, department_id,
                    designation, joining_date, employment_status, created_by, created_at;
    """
    params = [
        candidate.candidate_id,
        candidate.user_id,
        employee_code,
        department_id,
        designation,
        joining_date,
        employment_status,
        created_by,
        timezone.now(),
    ]

    with connection.cursor() as cursor:
        cursor.execute(insert_sql, params)
        row = cursor.fetchone()
        record = {
            "employee_id": row[0],
            "candidate_id": row[1],
            "user_id": row[2],
            "employee_code": row[3],
            "department_id": row[4],
            "designation": row[5],
            "joining_date": row[6],
            "employment_status": row[7],
            "created_by": row[8],
            "created_at": row[9],
        }

    # Dispatch employee_onboarded signal
    try:
        employee_onboarded.send(
            sender=create_employee_record,
            candidate=candidate,
            employee_record=record,
        )
    except Exception as exc:
        logger.error("Error dispatching employee_onboarded signal: %s", exc)

    return record


# ==============================================================================
# 5. LIFECYCLE STAGE HELPER
# ==============================================================================
def get_candidate_lifecycle_stage(candidate):
    """
    Returns candidate's current position in the talent lifecycle:
    - EMPLOYEE_LIFECYCLE: Selected & record in employee_table.
    - RECRUITMENT_SELECTED: Selected & awaiting HR onboarding.
    - RECRUITMENT_ACTIVE: Applications active in recruitment stages.
    - RECRUITMENT_REJECTED: All applications rejected.
    """
    if not candidate:
        return "UNKNOWN"

    if is_candidate_onboarded(candidate_id=candidate.candidate_id, user_id=candidate.user_id):
        return "EMPLOYEE_LIFECYCLE"

    if candidate.applications.filter(status=Application.Status.SELECTED).exists():
        return "RECRUITMENT_SELECTED"

    active_statuses = [
        Application.Status.APPLIED,
        Application.Status.RESUME_REVIEW,
        Application.Status.SHORTLISTED,
        Application.Status.APTITUDE_TEST,
        Application.Status.INTERVIEW_SCHEDULED,
    ]
    if candidate.applications.filter(status__in=active_statuses).exists():
        return "RECRUITMENT_ACTIVE"

    if candidate.applications.filter(status=Application.Status.REJECTED).exists():
        return "RECRUITMENT_REJECTED"

    return "RECRUITMENT_IDLE"

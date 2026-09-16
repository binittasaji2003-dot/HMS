# Smart HR Management System (HRMS) — Complete Project Documentation

Welcome to the comprehensive, simple English documentation for the **Smart HR Management System (HRMS)**. This guide provides a full walkthrough of the architecture, features, user roles, database models, workflows, testing, and setup instructions.

---

## 1. Complete Project Overview

The **Smart HR Management System (HRMS)** is an integrated enterprise web application designed to digitize, streamline, and automate human resources operations, talent recruitment, employee performance evaluation, weekly work tracking, and organizational governance.

Built on the industrial-grade **Cookiecutter Django** foundation, the system bridges 4 distinct organizational roles into one unified platform:
- **Admin**: Executive governance, organizational department control, employee approval, notices, system audit, and performance escalations.
- **HR Managers**: Job vacancy postings, talent recruitment pipeline, aptitude tests, interview scheduling, employee work report reviews, and performance warnings.
- **Employees**: Self-service portal for attendance, leave management, weekly work report submissions, document uploads, tasks, and company notices.
- **Candidates**: Public career portal, online job applications, aptitude examinations, and application status tracking.

---

## 2. System Architecture & Tech Stack

```
                                  +-----------------------+
                                  |    Web Client / UI    |
                                  | Bootstrap 5 + Tailwind|
                                  +-----------+-----------+
                                              | HTTP / HTTPS
                                              v
+-----------------------------------------------------------------------------------------+
|                                    Docker Services                                      |
|                                                                                         |
|  +-----------------------------------------------------------------------------------+  |
|  |                             Django 6.0 Web Container                              |  |
|  |                                                                                   |  |
|  |  +-----------------+  +-----------------+  +-----------------+  +--------------+  |  |
|  |  |  admin_module   |  |   hr (Talent)   |  | employees (Self)|  |  candidates  |  |  |
|  |  +-----------------+  +-----------------+  +-----------------+  +--------------+  |  |
|  |  +-----------------------------------------------------------------------------+  |  |
|  |  |                users (Role-Based Custom Authentication Model)               |  |  |
|  |  +-----------------------------------------------------------------------------+  |  |
|  +------------------------------------------+----------------------------------------+  |
|                                             | ORM                                       |
|                                             v                                           |
|  +-----------------------------------------------------------------------------------+  |
|  |                            PostgreSQL 16 Database                                 |  |
|  +-----------------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------------+
```

### Core Technologies
- **Backend Framework**: Django 6.0 (Cookiecutter Django template standard).
- **Programming Language**: Python 3.14 / 3.13.
- **Database**: PostgreSQL 16 (Relational Database with Foreign Key constraints and cascades).
- **Authentication**: `django-allauth` + Custom Role-Based Authentication (`User` model with `email` as `USERNAME_FIELD`).
- **Containerization**: Docker Compose (`django` web service + `postgres` database service).
- **Frontend & Styling**: Bootstrap 5.3, Tailwind CSS, Bootstrap Icons, Responsive Mobile-First Grid.
- **Client Scripting**: Vanilla JavaScript (Async/Await Fetch API, dynamic calendar rendering, interactive modals).
- **Testing**: `pytest`, `pytest-django`, `Faker`.

---

## 3. Role-Based Access Control & User Roles

Access control is enforced both at the URL dispatcher level and inside Class-Based View permission mixins:

| User Role | Dashboard URL | Primary Responsibilities |
|---|---|---|
| **Admin** (`role="Admin"`) | `/admin-portal/dashboard/` | Full organizational oversight, departments, employee approvals, company announcements, review HR warnings, terminate/retain staff. |
| **HR Manager** (`role="HR"`) | `/hr/dashboard/` | Post vacancies, manage applications, create aptitude tests/questions, schedule interviews, review weekly employee reports, issue warnings. |
| **Employee** (`role="Employee"`) | `/employees/dashboard/` | View attendance, apply for leaves, submit weekly work reports, upload certificates, check notices and ratings. |
| **Candidate** (`role="Candidate"`) | `/candidates/` | Browse job openings, apply with resumes, take online aptitude tests, check interview calls and selection offers. |

### Role Selection Portal (`/accounts/role-select/` or `/login-select/`)
Clicking **Sign In** anywhere across the application opens the modern **Role Chooser**. Users can select their role (Admin, HR, Employee, or Candidate) to navigate directly to their dedicated sign-in interface. The login form dynamically adapts its badges, descriptions, and registration links based on the chosen role. Users can switch roles at any time using the **Switch Role** button.

---

## 4. Public Portal & Landing Page Experience

The public landing page (`/`) is styled in a **White + Royal Blue** modern aesthetic:
- **Entrance Animation**: Smooth CSS `fadeInUp` and subtle floating cards.
- **Live Enterprise Metrics**: Dynamic counters displaying active employees, total departments, and live job openings.
- **Dynamic Vacancies Section**: Fetches active `JobVacancy` records directly from the database with department tags, location, job type, and closing dates.
- **Direct Action Links**: One-click "View Details" and "Apply Now" buttons with automatic routing.
- **Company Announcements & Features**: Highlights organization culture and quick navigation links.

---

## 5. Candidate Portal & Recruitment Lifecycle

The recruitment lifecycle is automated end-to-end:

```
[ Job Vacancy Posted ] 
         │
         ▼
[ Candidate Registers / Logs In ] 
         │
         ▼
[ Submits Application with Resume ] 
         │
         ▼
[ HR Shortlists / Rejects Application ] 
         │
         ▼
[ Online Aptitude Test & Auto-Grading ] 
         │
         ▼
[ Interview Scheduled with Date & Mode ] 
         │
         ▼
[ Candidate Selected -> Admin Approves -> Activated as Employee ]
```

1. **White + Blue Theme & Layout**: All candidate portal pages are styled in a modern, professional **White + Royal Blue** palette (`base_candidate.html`) with smooth navigation, clear status indicators, and clean responsive Bootstrap form cards.
2. **Browsing Vacancies Upon Login**: Once logged in, candidates can immediately view live active vacancies on their Dashboard (`/candidates/`) or browse/search with department filters on `/candidates/jobs/`.
3. **Comprehensive Application Form (`/candidates/apply/<id>/`)**:
   - **First Name & Last Name** (Required, prefilled from profile).
   - **Email Address** (Required, prefilled from account).
   - **Phone Number** (Optional/prefilled).
   - **Date of Birth** (Optional/prefilled).
   - **Highest Education / Qualification** (e.g. B.Tech / MCA / B.Sc).
   - **Work Experience** (Optional — freshers are not blocked and can submit without prior experience).
   - **Resume / CV Upload** (PDF/DOC/DOCX — with automatic fallback to saved profile resume if already uploaded).
   - **Terms & Data Privacy Agreement** (Required declaration checkbox).
4. **Recruitment Pipeline Tracking**: Candidates track their applications on `/candidates/applications/` through a 4-stage visual pipeline: Applied &rarr; Under Review &rarr; Aptitude Assessment &rarr; Selection.
5. **Selection & Onboarding**: Selected candidates are routed to the Admin Approval queue. Once approved, an `Employee` account is created and activated.

---

## 6. HR Portal & Talent Acquisition Management

HR managers access the recruitment suite at `/hr/dashboard/`:
- **Vacancies Management**: Create, edit, and close job postings.
- **Applicant Tracking System (ATS)**: Review submitted resumes, filter by status (`PENDING`, `SHORTLISTED`, `REJECTED`, `SELECTED`), and update applicant progress.
- **Aptitude Test Generator**: Build timed online tests, add/remove multiple-choice questions, set passing percentages, and view live results.
- **Interview Scheduling**: Assign interview dates, formats (Google Meet/Teams/Office), and record interviewer feedback.
- **Weekly Report Review**: Evaluate weekly reports submitted by employees, score quality, and provide constructive feedback.
- **Performance Warnings**: Issue formal warnings for conduct, attendance, or productivity, with direct escalation to Admin.

---

## 7. Employee Portal & Self-Service Operations

Employees access their dashboard at `/employees/dashboard/`:
- **Overview & Profile**: View employment status, designation, department, and joining date.
- **Weekly Work Reports**: Submit weekly tasks completed, challenges faced, and plans for the next week.
- **Leave Management**: Apply for casual, medical, or earned leaves and track approval status.
- **Attendance Records**: Check monthly attendance summaries.
- **Document Locker**: Securely upload and store 10th certificates, 12th certificates, ID proofs, and experience letters.
- **Notifications & Warnings**: Receive instant notifications when HR reviews a report or issues feedback.

---

## 8. Admin Portal & Enterprise Governance Suite

The executive suite at `/admin-portal/dashboard/` provides high-level control:
- **Department Management**: Add, modify, and manage organizational departments.
- **Employee Directory**: Full access to all staff members with status controls (`ACTIVE`, `INACTIVE`, `ON_LEAVE`, `TERMINATED`).
- **Recruitment Approvals**: Review candidates selected by HR and authorize official employee account creation.
- **Broadcast Announcements**: Publish company-wide bulletins, holiday notices, and policy memos.
- **HR Warning Escalation & Disciplinary Decisions**: Review warnings escalated by HR, choose to retain with corrective action plans, or execute formal termination.
- **Executive System Reports**: View weekly HR output, departmental headcounts, and company performance trends.

---

## 9. Weekly Work Reports Workflow

```
[ Employee submits Report ] ──> [ Status: SUBMITTED ]
                                        │
                                        ▼
                               [ HR Reviews Report ]
                                        │
                                        ├── [ Status: REVIEWED + HR Feedback ]
                                        │
                                        └── (If Critical Issues) ──> [ Escalated to Admin ]
```

1. **Submission**: Employees submit their weekly activities via `/employees/reports/submit/`.
2. **HR Inspection**: HR managers review pending submissions at `/hr/employee-reports/`, assign a rating, and attach guidance.
3. **Notification**: The employee receives an immediate notification of the review status.
4. **Archiving**: Historical reports are stored for annual performance reviews.

---

## 10. Performance Management & Warning System

1. **Reviews**: HR conducts periodic evaluations with structured criteria (competence, communication, punctuality, teamwork).
2. **Warning Generation**: If an employee underperforms or breaches policy, HR creates a warning record (`PerformanceWarning`).
3. **Escalation**: Serious offenses or repeated infractions are escalated to the Admin (`SENT_TO_ADMIN`).
4. **Executive Decision**: The Admin reviews the case, hears the employee's representation, and marks the final resolution (`RESOLVED`, `CONTINUED`, or `TERMINATED`).

---

## 11. Kerala & India Public Holidays & Company Calendar Module

The system includes a dedicated `Holiday` model and a reusable calendar component (`templates/components/calendar.html`):

### Seeded Kerala & National Public Holidays
- **Republic Day** (January 26)
- **Maha Shivaratri** (February)
- **Eid-ul-Fitr / Ramadan** (March/April)
- **Good Friday** (April)
- **Vishu & Dr. Ambedkar Jayanti** (April 14)
- **May Day / Labour Day** (May 1)
- **Bakrid / Eid al-Adha** (May/June)
- **Muharram** (June/July)
- **Independence Day** (August 15)
- **Sree Narayana Guru Jayanti** (August)
- **Thiruvonam (Onam Festival)** (September)
- **Third Onam / Sri Krishna Jayanti** (September)
- **Sree Narayana Guru Samadhi** (September 21)
- **Gandhi Jayanti** (October 2)
- **Mahanavami & Vijayadashami (Dussehra / Pooja)** (October)
- **Deepavali (Diwali)** (October/November)
- **Christmas Day** (December 25)

### Component Features
- **Interactive Month Navigation**: Previous/Next month buttons with dynamic date generation.
- **Visual Badges**: Red tags for Kerala/India Public Holidays; Blue tags for Employee Birthdays.
- **Detail Modal**: Click any date to view all events scheduled for that day.
- **API Endpoint**: Accessible at `/api/calendar/events/` returning standard JSON event objects.

---

## 12. Celebratory Birthday Notification System

- **Automated Birthday Detection**: Reads candidate and employee dates of birth and detects matching dates.
- **Festive Confetti Popup**: Renders a celebratory modal (`components/birthday_popup.html`) with cake animations and warm personalized wishes.
- **Session Throttling**: Displays once per session or day using `sessionStorage` and `/api/birthday/dismiss/` to avoid disrupting daily workflows.

---

## 13. Database Schema, Relations & Model Architecture

### `users` App
- **`User`**: Custom user model (`email` as login, `name`, `role`, `status`). Constraints enforce a single active Admin role.

### `admin_module` App
- **`Department`**: `name`, `description`, `is_active`, `created_by`, `created_at`.
- **`Announcement`**: `title`, `content`, `announcement_type`, `target_audience`, `is_published`, `published_at`.
- **`EmployeeApproval`**: `employee` (1-to-1 with Employee), `status`, `approved_by`, `comments`, `approved_at`.
- **`Holiday`**: `name`, `date`, `holiday_type` (`PUBLIC`/`RESTRICTED`/`COMPANY`), `description`, `is_active`.

### `candidates` App
- **`JobVacancy`**: `title`, `department`, `job_type`, `openings_count`, `experience_years`, `location`, `status`, `closing_date`.
- **`Candidate`**: `user`, `full_name`, `phone`, `date_of_birth`, `highest_qualification`, `resume`, `skills`.
- **`JobApplication`**: `candidate`, `vacancy`, `status` (`PENDING`, `SHORTLISTED`, `REJECTED`, `SELECTED`), `applied_at`.
- **`AptitudeExam`**: `candidate`, `vacancy`, `score`, `passed`, `completed_at`.
- **`InterviewSchedule`**: `candidate`, `vacancy`, `scheduled_at`, `mode`, `meeting_link`, `status`.

### `hr` App
- **`HRManager`**: `user`, `employee_code`, `department`, `phone`, `joining_date`.
- **`AptitudeTest`**: `title`, `duration_minutes`, `passing_score`, `is_active`.
- **`AptitudeQuestion`**: `test`, `question_text`, `option_a`, `option_b`, `option_c`, `option_d`, `correct_option`.
- **`Interview`**: `candidate`, `job`, `interview_date`, `round`, `status`, `feedback`.

### `employees` App
- **`Employee`**: `user`, `candidate`, `employee_code`, `department`, `designation`, `joining_date`, `employment_status`.
- **`EmployeeDocument`**: `employee`, `document_type`, `document`.
- **`EmployeeReport`**: `employee`, `week_start_date`, `week_end_date`, `summary`, `challenges`, `status`, `hr_feedback`.
- **`EmployeePerformance`**: `employee`, `review_date`, `rating`, `strengths`, `areas_of_improvement`.
- **`PerformanceWarning`**: `employee`, `warning_title`, `description`, `severity`, `status`, `hr_notes`, `admin_decision`.

---

## 14. URL Routing & API Reference Catalog

### Public Routes
- `/` — Homepage (White + Blue Theme, live metrics, vacancies)
- `/about/` — About platform overview
- `/accounts/login/` — Universal Role-Based Login
- `/accounts/logout/` — Secure Session Logout

### Calendar & Notification APIs
- `GET /api/calendar/events/` — JSON feed of Kerala/India holidays and employee birthdays
- `POST /api/birthday/dismiss/` — Dismiss session birthday celebration popup

### Admin Module Routes (`/admin-portal/`)
- `/admin-portal/dashboard/` — Admin Executive Dashboard
- `/admin-portal/departments/` — Department List
- `/admin-portal/departments/add/` — Add New Department
- `/admin-portal/employees/` — Full Employee Management
- `/admin-portal/recruitment/jobs/` — Job Vacancy Monitor
- `/admin-portal/recruitment/approvals/` — Candidate Approvals Queue
- `/admin-portal/announcements/` — Broadcast Announcements Manager
- `/admin-portal/reports/` — Executive System Reports
- `/admin-portal/responsibilities/warnings/` — Warning Review & Escalations

### HR Module Routes (`/hr/`)
- `/hr/dashboard/` — HR Management Dashboard
- `/hr/profile/` — HR Manager Profile Details
- `/hr/profile/edit/` — Edit HR Profile & Department
- `/hr/jobs/` — Job Openings List
- `/hr/jobs/create/` — Post New Vacancy
- `/hr/applications/` — ATS Application Pipeline
- `/hr/aptitude-tests/` — Aptitude Tests Management
- `/hr/aptitude-results/` — Test Evaluation Scores
- `/hr/interviews/` — Interview Schedules
- `/hr/employee-reports/` — Weekly Employee Reports Review
- `/hr/warnings/` — Disciplinary Warnings Management
- `/hr/performance/` — Periodic Appraisals & Ratings

### Employee Module Routes (`/employees/`)
- `/employees/dashboard/` — Employee Personal Dashboard
- `/employees/profile/` — Employee Profile Details
- `/employees/reports/` — Work Reports List
- `/employees/reports/submit/` — Submit Weekly Work Report
- `/employees/leave/` — Leave Application & Balance
- `/employees/attendance/` — Monthly Attendance Log
- `/employees/documents/` — Document Repository
- `/employees/notifications/` — Notifications Center

### Candidate Module Routes (`/candidates/`)
- `/candidates/` — Candidate Portal Home
- `/candidates/register/` — Candidate Registration
- `/candidates/jobs/` — Open Vacancies List
- `/candidates/jobs/<id>/` — Vacancy Details
- `/candidates/apply/<id>/` — Apply for Position
- `/candidates/profile/` — Candidate Profile & Resume Upload

---

## 15. Docker Containerization & Environment Configuration

The application runs inside a multi-container Docker environment orchestrated via `docker-compose.local.yml`:

```yaml
services:
  django:
    build:
      context: .
      dockerfile: ./compose/local/django/Dockerfile
    image: hr_management_system_local_django
    container_name: hr_management_system_local_django
    ports:
      - "8000:8000"
    volumes:
      - .:/app:z
    env_file:
      - ./.envs/.local/.django
      - ./.envs/.local/.postgres
    depends_on:
      - postgres

  postgres:
    build:
      context: .
      dockerfile: ./compose/production/postgres/Dockerfile
    image: hr_management_system_production_postgres
    container_name: hr_management_system_local_postgres
    volumes:
      - hr_management_system_local_postgres_data:/var/lib/postgresql/data
    env_file:
      - ./.envs/.local/.postgres
```

---

## 16. Automated Testing Strategy & Test Execution Guide

All unit, integration, and URL availability tests are executed with `pytest`:

```bash
docker compose -f docker-compose.local.yml exec django pytest
```

### Coverage Highlights:
- **`tests/test_all_pages.py`**: Asserts HTTP 200 on all 40+ endpoints across Public, Admin, HR, Employee, and Candidate portals.
- **`admin_module/tests.py`**: Access control, department management, employee status modification, announcements, and recruitment approvals.
- **`candidates/tests.py`**: Registration, profile updates, application submission, duplicate prevention, and aptitude exams.
- **`employees/tests.py`**: Authentication, report submission, leave tracking, and dashboard rendering.
- **`hr_management_system/users/tests/`**: Custom user managers, authentication redirects, and form validations.

**Current Test Status**: `72 passed, 0 failed [100% Success]`.

---

## 17. Step-by-Step Installation, Setup & Startup Guide

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- Git.

### 1. Clone the Repository
```bash
git clone <repository_url>
cd hr_management_system
```

### 2. Build and Start Docker Containers
```bash
docker compose -f docker-compose.local.yml up -d --build
```

### 3. Run Database Migrations
```bash
docker compose -f docker-compose.local.yml exec django python manage.py migrate
```

### 4. Seed Holiday Data
```bash
docker compose -f docker-compose.local.yml exec django python seed_holidays.py
```

### 5. Create Superuser / Admin Account
```bash
docker compose -f docker-compose.local.yml exec django python manage.py createsuperuser
```

### 6. Access the Application
Open your web browser and navigate to:
- **Web Application**: `http://localhost:8000/`
- **Django Admin**: `http://localhost:8000/admin/`

---

## 18. Seed Data, Demo Credentials & Test Scenarios

| Portal | Email | Password | Role | Description |
|---|---|---|---|---|
| **Admin** | `admin@hrms.local` | `AdminPass123!` | Admin | System Administrator & Executive Governance |
| **HR Manager** | `hr@hrms.local` | `HRPass123!` | HR | Senior HR Recruiter & Talent Manager |
| **Employee** | `employee@hrms.local` | `EmpPass123!` | Employee | Software Engineer (Engineering Dept) |
| **Candidate** | `candidate@hrms.local` | `CandPass123!` | Candidate | Active Job Applicant |

---

## 19. Troubleshooting Guide & Common Pitfalls

1. **Port 8000 Conflict**:
   If port 8000 is occupied, stop other local servers or map to another port in `docker-compose.local.yml` (e.g., `8080:8000`).

2. **Custom User Model Mapping**:
   The `User` model uses `email` as its unique identifier and stores the full name in the `name` field. `first_name`, `last_name`, and `username` properties are resolved dynamically in `hr_management_system/users/apps.py` without requiring database schema alterations.

3. **Running Migrations**:
   Always execute `python manage.py makemigrations` and `python manage.py migrate` inside the `django` container using `docker compose exec`.

4. **Static Files in Production**:
   Run `docker compose -f docker-compose.local.yml exec django python manage.py collectstatic --no-input` before deploying.

---

## 20. Future Roadmap & Enhancement Recommendations

1. **Real-time Notifications via WebSockets**: Integrate `django-channels` and Redis for instant in-app alerts on report reviews and interview invitations.
2. **Automated AI Resume Parsing**: Add OCR / NLP to parse uploaded PDF resumes and automatically autofill candidate work history and skills.
3. **Integrated Payroll & Tax Module**: Extend the employee portal to generate monthly PDF payslips, calculate tax deductions, and record reimbursement claims.
4. **Biometric Attendance Integration**: Connect physical RFID/biometric hardware directly to the attendance API for automated clock-in/out recording.
5. **Mobile Application**: Expose a secure Django REST Framework / GraphQL API to power iOS and Android mobile apps for employees and managers.

---
*Documentation compiled and verified for Smart HR Management System (HRMS) v1.0.0 Enterprise Release.*


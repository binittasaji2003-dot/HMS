"""Django management command to seed comprehensive, realistic test/demo data for an IT Company Smart HRMS."""
"""Django management command to seed comprehensive, realistic test/demo data for an IT Company Smart HRMS.

Only creates new test credentials for Employee and Candidate accounts.
Uses existing HR Managers and Admin user in the database without creating new credentials for them.
"""

from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

try:
    from allauth.account.models import EmailAddress
except ImportError:
    EmailAddress = None

from admin_module.models import Announcement, Department, EmployeeApproval, Holiday
from candidates.models import (
    Candidate,
    CandidateNotification,
    JobApplication,
    JobVacancy,
)
from employees.models import (
    Employee,
    EmployeePerformance,
    EmployeeReport,
    Notification,
    PerformanceWarning,
)
from hr.models import (
    AptitudeAttempt,
    AptitudeQuestion,
    AptitudeResult,
    AptitudeTest,
    HRManager,
    Interview,
)
from hr.question_bank import seed_default_questions

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with comprehensive realistic test/demo data for an IT Company Smart HRMS."
    help = "Seed the database with comprehensive realistic test/demo data for Employees and Candidates in an IT Company Smart HRMS."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Starting IT Company Demo Data Seeding ==="))

        stats = {
            "users": 0,
            "hr_managers": 0,
            "employees": 0,
            "candidates": 0,
            "vacancies": 0,
            "applications": 0,
            "reports": 0,
            "reviews": 0,
            "warnings": 0,
        }

        # -------------------------------------------------------------------------
        # Helper: Create or update a user securely
        # Helper: Create or update test users (Employees & Candidates ONLY)
        # -------------------------------------------------------------------------
        def create_or_update_user(email, password, name, role, is_active=True, is_staff=False, is_superuser=False):
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                user = User(
                    email=email,
                    name=name,
                    role=role,
                    status=User.StatusChoices.ACTIVE if is_active else User.StatusChoices.INACTIVE,
                    is_active=is_active,
                    is_staff=is_staff,
                    is_superuser=is_superuser,
                )
                user.set_password(password)
                user.save()
                stats["users"] += 1
                self.stdout.write(f"  [+] Created User: {name} <{email}> (Role: {role})")
            else:
                user.name = name
                user.role = role
                user.is_active = is_active
                user.is_staff = is_staff or user.is_staff
                user.is_superuser = is_superuser or user.is_superuser
                user.status = User.StatusChoices.ACTIVE if is_active else User.StatusChoices.INACTIVE
                user.set_password(password)
                user.save()
                self.stdout.write(f"  [*] Updated User: {name} <{email}> (Password: {password})")

            if EmailAddress:
                EmailAddress.objects.get_or_create(
                    user=user,
                    email=email,
                    defaults={"primary": True, "verified": True},
                )
            return user

        # -------------------------------------------------------------------------
        # 1. DEPARTMENTS (IT Company Core Structure)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n1. Seeding IT Departments..."))
        self.stdout.write(self.style.HTTP_INFO("\n1. Seeding / Verifying IT Departments..."))
        it_departments = [
            ("Software Engineering", "Core full-stack, frontend, backend, and mobile software engineering."),
            ("Cloud & DevOps", "AWS/GCP cloud infrastructure, CI/CD pipelines, Docker, Kubernetes, and Site Reliability."),
            ("Quality Assurance", "Manual & automated test engineering, performance verification, and security testing."),
            ("Data & Artificial Intelligence", "Big data engineering, machine learning models, BI, and data analytics."),
            ("Product & UI/UX Design", "Product management, user experience research, design systems, and prototyping."),
            ("Human Resources", "Talent acquisition, employee relations, onboarding, and people operations."),
            ("Finance & Accounts", "Payroll processing, financial audits, operational budgets, and billing."),
            ("Operations & IT Support", "Internal IT helpdesk, workstation provisioning, and network security."),
        ]

        dept_objs = {}
        for d_name, d_desc in it_departments:
            dept, _ = Department.objects.get_or_create(
                name=d_name,
                defaults={"description": d_desc, "is_active": True},
            )
            dept_objs[d_name] = dept
            self.stdout.write(f"  [+] Department: {dept.name}")

        # -------------------------------------------------------------------------
        # 2. ADMIN USER
        # -------------------------------------------------------------------------
        # 2. ADMIN USER
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n2. Checking Admin User..."))
        admin_user = (
            User.objects.filter(role=User.RoleChoices.ADMIN).first()
            or User.objects.filter(is_superuser=True).first()
        )
        if not admin_user:
            admin_user = create_or_update_user(
                email="binittasaji2003@gmail.com",
                password="admin@1234",
                name="System Administrator",
                role=User.RoleChoices.ADMIN,
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(f"  [+] Admin User: {admin_user.name} <{admin_user.email}> (Password: admin@1234)")
        else:
            admin_user.set_password("admin@1234")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.role = User.RoleChoices.ADMIN
            admin_user.status = User.StatusChoices.ACTIVE
            admin_user.save()
            if EmailAddress:
                ea, _ = EmailAddress.objects.get_or_create(
                    user=admin_user,
                    email=admin_user.email,
                    defaults={"primary": True, "verified": True},
                )
                ea.verified = True
                ea.primary = True
                ea.save()
            self.stdout.write(f"  [*] Admin User: {admin_user.name} <{admin_user.email}> (Password: admin@1234)")

        # -------------------------------------------------------------------------
        # 3. HR MANAGERS
        # 3. RESOLVE EXISTING HR MANAGERS (DO NOT CREATE NEW HR CREDENTIALS)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n3. Seeding HR Managers..."))
        hr_data = [
            ("Priya Sharma", "priya.hr@gmail.com", "priya@1234", "HR0001", "Senior Talent Acquisition Lead"),
            ("Vikram Malhotra", "vikram.hr@gmail.com", "vikram@1234", "HR0002", "HR Operations & People Partner"),
        ]
        self.stdout.write(self.style.HTTP_INFO("\n3. Referencing Existing HR Managers..."))
        existing_hr_managers = list(
            HRManager.objects.filter(user__role=User.RoleChoices.HR).select_related("user")
        )
        if not existing_hr_managers:
            existing_hr_managers = list(HRManager.objects.all().select_related("user"))

        hr_objs = []
        for name, email, pwd, code, designation in hr_data:
            user = create_or_update_user(
                email=email,
                password=pwd,
                name=name,
                role=User.RoleChoices.HR,
                is_active=True,
                is_staff=False,
            )
            hr_manager, created = HRManager.objects.get_or_create(
                user=user,
                defaults={
                    "department": dept_objs["Human Resources"],
                    "employee_code": code,
                    "joining_date": date(2023, 6, 1),
                    "is_active": True,
                },
            )
            if not created:
                hr_manager.employee_code = code
                hr_manager.department = dept_objs["Human Resources"]
                hr_manager.is_active = True
                hr_manager.save()
            hr_objs.append(hr_manager)
            stats["hr_managers"] += 1

            # Ensure linked Employee profile exists for HR managers
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    "employee_code": code,
                    "department": dept_objs["Human Resources"],
                    "designation": designation,
                    "joining_date": date(2023, 6, 1),
                    "employment_status": "ACTIVE",
                    "created_by": admin_user,
                },
            )
            self.stdout.write(f"  [+] HR Manager: {name} ({code}) <{email}>")

        primary_hr = hr_objs[0] if hr_objs else None
        secondary_hr = hr_objs[1] if len(hr_objs) > 1 else primary_hr

        # -------------------------------------------------------------------------
        # 4. EMPLOYEES (Covering ACTIVE, ON_LEAVE, INACTIVE, TERMINATED)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n4. Seeding Employees across IT Departments & Statuses..."))
        employee_seed_list = [
            {
                "name": "Pooja Hegde",
                "email": "pooja@gmail.com",
                "password": "pooja@1234",
                "code": "EMP0001",
                "dept": "Software Engineering",
                "designation": "Senior Full Stack Developer (Python/React)",
                "status": "ACTIVE",
                "joining_date": date(2024, 3, 1),
            },
            {
                "name": "Anjali Nair",
                "email": "anjali@gmail.com",
                "password": "anjali@1234",
                "code": "EMP0002",
                "dept": "Cloud & DevOps",
                "designation": "Cloud & DevOps Engineer (AWS/K8s)",
                "status": "ACTIVE",
                "joining_date": date(2024, 6, 15),
            },
            {
                "name": "Rahul Verma",
                "email": "rahul@gmail.com",
                "password": "rahul@1234",
                "code": "EMP0003",
                "dept": "Quality Assurance",
                "designation": "QA Automation Engineer (PyTest/Selenium)",
                "status": "ON_LEAVE",
                "joining_date": date(2024, 8, 10),
            },
            {
                "name": "Neha Sharma",
                "email": "neha@gmail.com",
                "password": "neha@1234",
                "code": "EMP0004",
                "dept": "Data & Artificial Intelligence",
                "designation": "Data & Analytics Specialist (PowerBI/SQL)",
                "status": "INACTIVE",
                "joining_date": date(2023, 11, 20),
            },
            {
                "name": "Arjun Reddy",
                "email": "arjun@gmail.com",
                "password": "arjun@1234",
                "code": "EMP0005",
                "dept": "Software Engineering",
                "designation": "Junior Backend Developer",
                "status": "TERMINATED",
                "joining_date": date(2024, 1, 10),
            },
            {
                "name": "Sneha Patel",
                "email": "sneha@gmail.com",
                "password": "sneha@1234",
                "code": "EMP0006",
                "dept": "Product & UI/UX Design",
                "designation": "UI/UX Product Designer (Figma/Design Systems)",
                "status": "ACTIVE",
                "joining_date": date(2024, 9, 1),
            },
            {
                "name": "Rohan Mehta",
                "email": "rohan@gmail.com",
                "password": "rohan@1234",
                "code": "EMP0007",
                "dept": "Cloud & DevOps",
                "designation": "Senior Site Reliability Engineer (SRE)",
                "status": "ACTIVE",
                "joining_date": date(2023, 5, 12),
            },
        ]

        emp_objs = {}
        for e in employee_seed_list:
            u = create_or_update_user(
                email=e["email"],
                password=e["password"],
                name=e["name"],
                role=User.RoleChoices.EMPLOYEE,
                is_active=(e["status"] != "TERMINATED"),
            )
            emp, created = Employee.objects.get_or_create(
                user=u,
                defaults={
                    "employee_code": e["code"],
                    "department": dept_objs[e["dept"]],
                    "designation": e["designation"],
                    "joining_date": e["joining_date"],
                    "employment_status": e["status"],
                    "created_by": admin_user,
                },
            )
            if not created:
                emp.employee_code = e["code"]
                emp.department = dept_objs[e["dept"]]
                emp.designation = e["designation"]
                emp.joining_date = e["joining_date"]
                emp.employment_status = e["status"]
                emp.save()
            emp_objs[e["code"]] = emp
            stats["employees"] += 1
            self.stdout.write(f"  [+] Employee: {e['code']} - {e['name']} ({e['designation']}) [{e['status']}]")

        # -------------------------------------------------------------------------
        # 5. CANDIDATES & CANDIDATE PROFILES
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n5. Seeding Candidates..."))
        candidates_seed_list = [
            ("Aditya", "Kumar", "aditya@gmail.com", "aditya@1234", "9876543211", "Bengaluru, India"),
            ("Meera", "Krishnan", "meera@gmail.com", "meera@1234", "9876543212", "Chennai, India"),
            ("Karthik", "Sundaram", "karthik@gmail.com", "karthik@1234", "9876543213", "Hyderabad, India"),
            ("Divya", "Iyer", "divya@gmail.com", "divya@1234", "9876543214", "Pune, India"),
            ("Siddharth", "Rao", "siddharth@gmail.com", "siddharth@1234", "9876543215", "Mumbai, India"),
            ("Kavita", "Joshi", "kavita@gmail.com", "kavita@1234", "9876543216", "New Delhi, India"),
            ("Varun", "Nair", "varun@gmail.com", "varun@1234", "9876543217", "Kochi, India"),
        ]

        cand_objs = {}
        for fn, ln, email, pwd, phone, addr in candidates_seed_list:
            u = create_or_update_user(
                email=email,
                password=pwd,
                name=f"{fn} {ln}",
                role=User.RoleChoices.CANDIDATE,
                is_active=True,
            )
            cand, created = Candidate.objects.get_or_create(
                user=u,
                defaults={
                    "first_name": fn,
                    "last_name": ln,
                    "phone": phone,
                    "address": addr,
                    "date_of_birth": date(1998, 5, 20),
                    "policy_agreement": True,
                    "profile_completed": True,
                },
            )
            if not created:
                cand.first_name = fn
                cand.last_name = ln
                cand.phone = phone
                cand.address = addr
                cand.profile_completed = True
                cand.policy_agreement = True
                cand.save()
            cand_objs[email] = cand
            stats["candidates"] += 1
            self.stdout.write(f"  [+] Candidate: {fn} {ln} <{email}>")

        # -------------------------------------------------------------------------
        # 6. JOB VACANCIES (Covering OPEN and CLOSED statuses)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n6. Seeding IT Job Vacancies..."))
        vacancies_seed = [
            (
                "Senior Python/Django Backend Architect",
                "Software Engineering",
                "Architect and develop highly scalable distributed cloud backend microservices using Django and PostgreSQL.",
                "Build APIs, mentor junior engineers, optimize database queries.",
                "B.Tech / MCA in Computer Science.",
                "Python, Django, PostgreSQL, Celery, Redis, Docker",
                "4-7 Years",
                "Bengaluru (Hybrid)",
                "OPEN",
            ),
            (
                "React & TypeScript Frontend Specialist",
                "Software Engineering",
                "Design responsive, accessible, high-performance web applications using React 18, TypeScript, and Tailwind CSS.",
                "Develop clean UI components and collaborate with backend teams.",
                "Bachelor's degree in engineering/computer applications.",
                "React, TypeScript, Redux Toolkit, CSS3, HTML5",
                "3-5 Years",
                "Remote / Hybrid",
                "OPEN",
            ),
            (
                "AWS Cloud Infrastructure & Kubernetes Engineer",
                "Cloud & DevOps",
                "Manage production multi-region AWS cloud environments, Terraform IaC, Kubernetes clusters, and observability.",
                "Automate deployments, implement security policies, and manage CI/CD.",
                "AWS Solutions Architect / CKA certified preferred.",
                "AWS, Kubernetes, Terraform, Docker, GitHub Actions, Prometheus",
                "3-6 Years",
                "Hyderabad (Onsite)",
                "OPEN",
            ),
            (
                "Data Scientist & Machine Learning Engineer",
                "Data & Artificial Intelligence",
                "Develop predictive statistical models, NLP algorithms, and automated data pipelines.",
                "Train, validate, and deploy production ML models.",
                "Master's or B.Tech in Data Science / Computer Science.",
                "Python, PyTorch, Scikit-Learn, Pandas, SQL, MLflow",
                "2-5 Years",
                "Bengaluru (Hybrid)",
                "OPEN",
            ),
            (
                "Lead QA Automation Engineer (Playwright/Python)",
                "Quality Assurance",
                "Lead end-to-end automated testing strategies across microservices, REST APIs, and UI platforms.",
                "Build CI/CD automated test suites and performance testing scripts.",
                "Degree in Computer Science / IT.",
                "Python, Playwright, Selenium, PyTest, Postman, JMeter",
                "4-6 Years",
                "Pune (Hybrid)",
                "OPEN",
            ),
            (
                "Principal UI/UX Designer & Design Systems Lead",
                "Product & UI/UX Design",
                "Drive end-to-end design strategy, design systems, interactive Figma prototypes, and user research.",
                "Deliver high fidelity design systems and user journey flows.",
                "Degree in Design / Human-Computer Interaction.",
                "Figma, Prototyping, Wireframing, UX Research, Design Systems",
                "5+ Years",
                "Bengaluru (Onsite)",
                "OPEN",
            ),
            (
                "Cybersecurity & Network Infrastructure Engineer",
                "Operations & IT Support",
                "Monitor threat landscape, firewall configuration, SIEM log analysis, and enterprise network security.",
                "Perform vulnerability assessments and ensure regulatory compliance.",
                "CEH / CISSP / CCNA certification.",
                "Network Security, Firewalls, Linux, SIEM, Penetration Testing",
                "3-5 Years",
                "Mumbai (Onsite)",
                "OPEN",
            ),
            (
                "Legacy PHP & MySQL Maintenance Developer",
                "Software Engineering",
                "Maintain legacy internal portals and coordinate migration to modern Django architecture.",
                "Bug fixing and legacy patch support.",
                "Bachelor's in IT / CS.",
                "PHP 7, MySQL, Apache",
                "2+ Years",
                "Remote",
                "CLOSED",
            ),
            (
                "Junior Desktop Support Technician",
                "Operations & IT Support",
                "Provide Level 1 IT hardware troubleshooting and software license support.",
                "Setup workstations and resolve user tickets.",
                "Diploma in IT / Hardware Networking.",
                "Windows 11, macOS, Active Directory, LAN",
                "1-2 Years",
                "Bengaluru (Onsite)",
                "CLOSED",
            ),
        ]

        posted_by_user = primary_hr.user if primary_hr else (admin_user or None)

        vac_objs = {}
        for title, dept_name, desc, resp, qual, skills, exp, loc, status in vacancies_seed:
            vac, created = JobVacancy.objects.get_or_create(
                title=title,
                defaults={
                    "department": dept_objs[dept_name],
                    "description": desc,
                    "responsibilities": resp,
                    "qualifications": qual,
                    "skills_required": skills,
                    "experience_required": exp,
                    "location": loc,
                    "status": status,
                    "posted_by": hr_objs[0].user,
                    "posted_by": posted_by_user,
                    "closing_date": date.today() + timedelta(days=30) if status == "OPEN" else date.today() - timedelta(days=10),
                },
            )
            if not created:
                vac.department = dept_objs[dept_name]
                vac.description = desc
                vac.status = status
                vac.save()
            vac_objs[title] = vac
            stats["vacancies"] += 1
            self.stdout.write(f"  [+] Job Vacancy: {title} ({status})")

        # -------------------------------------------------------------------------
        # 7. APTITUDE TESTS & QUESTION BANKS
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n7. Seeding Aptitude Tests & Questions..."))
        test_seed_list = [
            ("Standard IT & Quantitative Aptitude Test", "Comprehensive 3-category assessment covering Quantitative, Logical Reasoning, and Verbal Ability.", 30, 15, 50),
            ("Senior Data Science & Logic Assessment", "Advanced logic and analytical reasoning test for analytical roles.", 45, 20, 60),
            ("DevOps & Cloud Systems Aptitude Assessment", "Technical logic, network aptitude, and problem-solving evaluation.", 30, 15, 50),
        ]

        test_objs = []
        for t_title, t_desc, t_dur, t_qs, t_pass in test_seed_list:
            t_obj, _ = AptitudeTest.objects.get_or_create(
                title=t_title,
                defaults={
                    "description": t_desc,
                    "duration_minutes": t_dur,
                    "total_questions": t_qs,
                    "pass_percentage": t_pass,
                    "created_by": primary_hr,
                    "status": "ACTIVE",
                },
            )
            seed_default_questions(test=t_obj)
            test_objs.append(t_obj)
            self.stdout.write(f"  [+] Aptitude Test: {t_title} ({t_obj.questions.count()} questions)")

        primary_test = test_objs[0]

        # -------------------------------------------------------------------------
        # 8. JOB APPLICATIONS (COVERING EVERY STATUS IN STATUS_CHOICES)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n8. Seeding Job Applications (Full Recruitment Pipeline)..."))
        pipeline_seed = [
            # 1. APPLIED
            (
                "aditya@gmail.com",
                "Senior Python/Django Backend Architect",
                "APPLIED",
                None, None, None,
            ),
            # 2. RESUME_REVIEW
            (
                "meera@gmail.com",
                "React & TypeScript Frontend Specialist",
                "RESUME_REVIEW",
                None, None, None,
            ),
            # 3. SHORTLISTED
            (
                "karthik@gmail.com",
                "AWS Cloud Infrastructure & Kubernetes Engineer",
                "SHORTLISTED",
                None, None, None,
            ),
            # 4. APTITUDE
            (
                "divya@gmail.com",
                "Data Scientist & Machine Learning Engineer",
                "APTITUDE",
                date.today() + timedelta(days=2),
                "10:00:00",
                "Please ensure video camera is active and quiet environment is maintained.",
            ),
            # 5. INTERVIEW
            (
                "siddharth@gmail.com",
                "Lead QA Automation Engineer (Playwright/Python)",
                "INTERVIEW",
                date.today() - timedelta(days=3),
                "11:00:00",
                "Aptitude test completed with high score.",
            ),
            # 6. SELECTED
            (
                "kavita@gmail.com",
                "Principal UI/UX Designer & Design Systems Lead",
                "SELECTED",
                date.today() - timedelta(days=7),
                "14:00:00",
                "Passed both technical and portfolio interview rounds with distinction.",
            ),
            # 7. REJECTED
            (
                "varun@gmail.com",
                "Cybersecurity & Network Infrastructure Engineer",
                "REJECTED",
                date.today() - timedelta(days=10),
                "15:00:00",
                "Profile does not meet required experience in SIEM tooling.",
            ),
            ("aditya@gmail.com", "Senior Python/Django Backend Architect", "APPLIED", None, None, None),
            ("meera@gmail.com", "React & TypeScript Frontend Specialist", "RESUME_REVIEW", None, None, None),
            ("karthik@gmail.com", "AWS Cloud Infrastructure & Kubernetes Engineer", "SHORTLISTED", None, None, None),
            ("divya@gmail.com", "Data Scientist & Machine Learning Engineer", "APTITUDE", date.today() + timedelta(days=2), "10:00:00", "Please ensure video camera is active and quiet environment is maintained."),
            ("siddharth@gmail.com", "Lead QA Automation Engineer (Playwright/Python)", "INTERVIEW", date.today() - timedelta(days=3), "11:00:00", "Aptitude test completed with high score."),
            ("kavita@gmail.com", "Principal UI/UX Designer & Design Systems Lead", "SELECTED", date.today() - timedelta(days=7), "14:00:00", "Passed both technical and portfolio interview rounds with distinction."),
            ("varun@gmail.com", "Cybersecurity & Network Infrastructure Engineer", "REJECTED", date.today() - timedelta(days=10), "15:00:00", "Profile does not meet required experience in SIEM tooling."),
        ]

        app_objs = {}
        for email, vac_title, status, apt_date, apt_time, remarks in pipeline_seed:
            cand = cand_objs[email]
            vac = vac_objs[vac_title]

            app, created = JobApplication.objects.get_or_create(
                candidate=cand,
                vacancy=vac,
                defaults={
                    "status": status,
                    "aptitude_date": apt_date,
                    "aptitude_time": apt_time,
                    "aptitude_test": primary_test if apt_date else None,
                    "aptitude_remarks": remarks or "",
                },
            )
            if not created:
                app.status = status
                app.aptitude_date = apt_date
                app.aptitude_time = apt_time
                app.aptitude_test = primary_test if apt_date else None
                app.aptitude_remarks = remarks or ""
                app.save()

            app_objs[email] = app
            stats["applications"] += 1
            self.stdout.write(f"  [+] Application: {cand} -> {vac.title} [{status}]")

            # Notification to candidate
            CandidateNotification.objects.get_or_create(
                candidate=cand,
                application=app,
                title=f"Application Status: {app.get_status_display()}",
                defaults={
                    "message": f"Your application for '{vac.title}' is currently marked as {app.get_status_display()}.",
                    "notification_type": "STATUS_UPDATE",
                    "link_url": "/candidate/applications/",
                    "is_read": False,
                },
            )

        # -------------------------------------------------------------------------
        # 9. APTITUDE RESULTS & ATTEMPTS
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n9. Seeding Aptitude Attempts & Scorecards..."))
        # Seed test results for Divya, Siddharth, Kavita
        aptitude_results_seed = [
            ("divya@gmail.com", 13, 15, 86.67, True),
            ("siddharth@gmail.com", 14, 15, 93.33, True),
            ("kavita@gmail.com", 15, 15, 100.00, True),
        ]
        for email, score, total, pct, passed in aptitude_results_seed:
            app = app_objs[email]
            AptitudeResult.objects.update_or_create(
                test=primary_test,
                application=app,
                defaults={
                    "score": score,
                    "total_marks": total,
                    "percentage": pct,
                    "passed": passed,
                },
            )
            AptitudeAttempt.objects.get_or_create(
                test=primary_test,
                application=app,
                defaults={
                    "expires_at": timezone.now() + timedelta(minutes=30),
                    "is_completed": True,
                    "completed_at": timezone.now() - timedelta(days=1),
                    "questions_data": [],
                    "answers_data": {},
                },
            )
            self.stdout.write(f"  [+] Aptitude Scorecard: {app.candidate} -> {score}/{total} ({pct}%)")

        # -------------------------------------------------------------------------
        # 10. INTERVIEW SESSIONS (SCHEDULED, COMPLETED, CANCELLED)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n10. Seeding Interview Sessions..."))
        interview_seed = [
            (
                "siddharth@gmail.com",
                primary_hr,
                date.today() + timedelta(days=1),
                "14:00:00",
                "SCHEDULED",
                "Technical architecture & automation framework interview. Google Meet: https://meet.google.com/qa-lead-round",
            ),
            (
                "kavita@gmail.com",
                secondary_hr,
                date.today() - timedelta(days=4),
                "11:00:00",
                "COMPLETED",
                "Exceptional portfolio demonstration and design systems expertise. Highly recommended for offer.",
            ),
            (
                "varun@gmail.com",
                primary_hr,
                date.today() - timedelta(days=8),
                "16:00:00",
                "CANCELLED",
                "Session cancelled due to candidate profile misalignment.",
            ),
        ]

        for email, hr, i_date, i_time, i_status, remarks in interview_seed:
            app = app_objs[email]
            Interview.objects.get_or_create(
                application=app,
                interview_date=i_date,
                interview_time=i_time,
                defaults={
                    "interviewer": hr,
                    "status": i_status,
                    "remarks": remarks,
                },
            )
            self.stdout.write(f"  [+] Interview: {app.candidate} [{i_status}] on {i_date} at {i_time}")

        # Connect Selected Candidate Kavita Joshi to an EmployeeApproval record
        kavita_cand = cand_objs["kavita@gmail.com"]
        kavita_emp = Employee.objects.filter(user__email="kavita@gmail.com").first()
        if not kavita_emp:
            kavita_emp = Employee.objects.create(
                user=kavita_cand.user,
                candidate=kavita_cand,
                employee_code="EMP0008",
                department=dept_objs["Product & UI/UX Design"],
                designation="Principal UI/UX Designer",
                joining_date=date.today() + timedelta(days=14),
                employment_status="ACTIVE",
                created_by=admin_user,
            )
            stats["employees"] += 1

        EmployeeApproval.objects.get_or_create(
            employee=kavita_emp,
            defaults={
                "status": "APPROVED",
                "approved_by": admin_user,
                "approved_at": timezone.now(),
                "comments": "Approved selected candidate onboarding for Principal UI/UX Designer.",
            },
        )

        # -------------------------------------------------------------------------
        # 11. EMPLOYEE WEEKLY REPORTS (DRAFT, SUBMITTED, UNDER_REVIEW, REVIEWED, NEEDS_CORRECTION)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n11. Seeding Employee Weekly Reports across All Statuses..."))
        today = date.today()
        reports_seed = [
            # Pooja Hegde (Software Engineering) - REVIEWED, SUBMITTED, DRAFT
            (
                "EMP0001",
                "Weekly Sprint Report - Week 36",
                today - timedelta(days=21),
                today - timedelta(days=15),
                "Implemented JWT auth refresh and database query optimizations for high-throughput candidate endpoints.",
                "Completed 12 Jira tickets, merged 4 pull requests with 98% test coverage.",
                "Achieved sub-50ms API response time across all candidate portal endpoints.",
                "Minor database lock contention during concurrent test migrations.",
                "REVIEWED",
                primary_hr,
                "Great work on performance optimizations! High quality code and documentation.",
                today - timedelta(days=14),
            ),
            (
                "EMP0001",
                "Weekly Sprint Report - Week 37",
                today - timedelta(days=14),
                today - timedelta(days=8),
                "Integrated randomized aptitude assessment timers and scorecard generation module.",
                "Built complete 3-category question selector with stable candidate attempts.",
                "Zero open bugs reported in QA verification phase.",
                "None.",
                "REVIEWED",
                primary_hr,
                "Approved. Excellent milestone delivery.",
                today - timedelta(days=7),
            ),
            (
                "EMP0001",
                "Weekly Sprint Report - Week 38",
                today - timedelta(days=7),
                today - timedelta(days=1),
                "Built candidate notification center and responsive recruitment pipeline stepper cards.",
                "Implemented context processors, dropdown preview, and read badge updates.",
                "Feature completed ahead of deadline.",
                "Coordination with mobile responsiveness testers.",
                "SUBMITTED",
                None,
                "",
                None,
            ),
            (
                "EMP0001",
                "Weekly Sprint Report - Current Week (In Progress)",
                today,
                today + timedelta(days=4),
                "Drafting test seed data and preparing final demo walkthrough documentation.",
                "Creating seed management command and credentials document.",
                "",
                "",
                "DRAFT",
                None,
                "",
                None,
            ),
            # Anjali Nair (Cloud & DevOps) - UNDER_REVIEW
            (
                "EMP0002",
                "Weekly Cloud Infrastructure Report",
                today - timedelta(days=7),
                today - timedelta(days=1),
                "Upgraded Kubernetes cluster nodes, renewed TLS certificates, and tuned Terraform state locks.",
                "Provisioned multi-AZ Redis cache and configured Automated DB Snapshot backups.",
                "100% uptime maintained across all production microservices.",
                "Temporary bandwidth throttle during off-peak data sync.",
                "UNDER_REVIEW",
                secondary_hr,
                "",
                None,
            ),
            # Rahul Verma (Quality Assurance) - NEEDS_CORRECTION
            (
                "EMP0003",
                "QA Automation Test Execution Report",
                today - timedelta(days=14),
                today - timedelta(days=8),
                "Executed automated regression suite for HR management and employee profile modules.",
                "Created 24 new Playwright end-to-end test scenarios.",
                "Automated 85% of manual test cases for candidate registration.",
                "Encountered flakiness on legacy report export endpoint.",
                "NEEDS_CORRECTION",
                primary_hr,
                "Please attach the detailed test execution log and failover analysis before final sign-off.",
                today - timedelta(days=7),
            ),
            # Sneha Patel (Product & UI/UX Design) - SUBMITTED
            (
                "EMP0006",
                "Design Systems & Component Library Report",
                today - timedelta(days=7),
                today - timedelta(days=1),
                "Delivered high-fidelity UI wireframes and responsive layouts for HR candidate details page.",
                "Updated color palette and badge tokens in the design library.",
                "Presented prototype to stakeholder committee with positive feedback.",
                "Aligning color contrast ratios for WCAG AA compliance.",
                "SUBMITTED",
                None,
                "",
                None,
            ),
        ]

        for code, title, s_date, e_date, summary, tasks, achieve, challenges, r_status, hr_reviewer, hr_comm, rev_date in reports_seed:
            emp = emp_objs.get(code)
            if not emp:
                continue
            rep, created = EmployeeReport.objects.get_or_create(
                employee=emp,
                title=title,
                week_start_date=s_date,
                defaults={
                    "week_end_date": e_date,
                    "work_summary": summary,
                    "tasks_completed": tasks,
                    "achievements": achieve,
                    "challenges": challenges,
                    "status": r_status,
                    "reviewed_by": hr_reviewer,
                    "hr_comments": hr_comm,
                    "reviewed_at": timezone.now() if rev_date else None,
                },
            )
            if not created:
                rep.status = r_status
                rep.reviewed_by = hr_reviewer
                rep.hr_comments = hr_comm
                rep.reviewed_at = timezone.now() if rev_date else None
                rep.save()
            stats["reports"] += 1
            self.stdout.write(f"  [+] Employee Report: {emp.employee_code} - '{title}' [{r_status}]")

        # -------------------------------------------------------------------------
        # 12. EMPLOYEE PERFORMANCE APPRAISALS (EXCELLENT, GOOD, AVERAGE, NEEDS_IMPROVEMENT)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n12. Seeding Performance Appraisals across All Rating Tiers..."))
        reviews_seed = [
            (
                "EMP0001",
                "Q4 2025 Annual Review",
                4.9,
                "EXCELLENT",
                "Pooja consistently exceeds delivery expectations, drives technical excellence, and mentors junior software developers.",
                hr_objs[0],
            ),
            (
                "EMP0002",
                "Q4 2025 Annual Review",
                4.2,
                "GOOD",
                "Anjali demonstrates strong ownership of cloud infrastructure and consistently maintains zero-downtime deployments.",
                hr_objs[1],
            ),
            (
                "EMP0003",
                "Q4 2025 Annual Review",
                3.3,
                "AVERAGE",
                "Rahul fulfills baseline QA expectations. Needs to focus on framework scalability and proactive test automation.",
                hr_objs[0],
            ),
            (
                "EMP0005",
                "Q4 2025 Review",
                1.8,
                "NEEDS_IMPROVEMENT",
                "Arjun has repeatedly missed sprint deadlines and exhibited critical non-compliance with software development standards.",
                hr_objs[0],
            ),
            (
                "EMP0006",
                "Q4 2025 Review",
                4.7,
                "EXCELLENT",
                "Sneha produced world-class UI/UX design deliverables, greatly improving candidate and employee portal usability.",
                hr_objs[1],
            ),
            (
                "EMP0007",
                "Q4 2025 Review",
                4.4,
                "GOOD",
                "Rohan provides stellar on-call support and has successfully driven automation across server maintenance.",
                hr_objs[1],
            ),
        ]

        for code, period, score, rating, comments, hr_rev in reviews_seed:
            emp = emp_objs.get(code)
            if not emp:
                continue
            rev, _ = EmployeePerformance.objects.get_or_create(
                employee=emp,
                review_period=period,
                defaults={
                    "score": score,
                    "rating": rating,
                    "comments": comments,
                    "reviewed_by": hr_rev,
                },
            )
            stats["reviews"] += 1
            self.stdout.write(f"  [+] Performance Appraisal: {emp.employee_code} -> [{rating}] (Score: {score})")

        # -------------------------------------------------------------------------
        # 13. PERFORMANCE WARNINGS (OPEN, SENT_TO_ADMIN, RESOLVED with DECISIONS)
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n13. Seeding Disciplinary & Performance Warnings..."))
        warnings_seed = [
            # 1. OPEN (No admin decision yet)
            (
                "EMP0003",
                "Punctuality and attendance adherence for daily morning technical standups.",
                "HR recommends mandatory schedule counseling and shift timeliness tracking.",
                "OPEN",
                None,
                "",
                None,
            ),
            # 2. SENT_TO_ADMIN (Awaiting Admin Decision)
            (
                "EMP0004",
                "Unexcused prolonged absence from project deliverables and sprint milestones.",
                "HR recommends placing employee on a 30-day structured Performance Improvement Plan (PIP).",
                "SENT_TO_ADMIN",
                None,
                "",
                None,
            ),
            # 3. RESOLVED - CONTINUE
            (
                "EMP0006",
                "Minor non-compliance with standardized file naming and asset archiving guidelines.",
                "HR recommended informal reminder and retraining on asset management.",
                "RESOLVED",
                "CONTINUE",
                "Issue addressed after 1-on-1 feedback session. Full compliance restored.",
                admin_user,
            ),
            # 4. RESOLVED - ANOTHER_WARNING
            (
                "EMP0001",
                "Delay in rotating production API keys during quarterly compliance check.",
                "HR recommends second advisory notice regarding security compliance.",
                "RESOLVED",
                "ANOTHER_WARNING",
                "Second advisory issued. Security credentials rotated immediately.",
                admin_user,
            ),
            # 5. RESOLVED - TERMINATION
            (
                "EMP0005",
                "Severe violation of IT security protocols: unauthorized export of codebase repository and sustained non-performance.",
                "HR recommends immediate employment termination in accordance with company policy.",
                "RESOLVED",
                "TERMINATION",
                "Termination confirmed and executed by Administration. Access revoked.",
                admin_user,
            ),
            ("EMP0003", "Punctuality and attendance adherence for daily morning technical standups.", "HR recommends mandatory schedule counseling and shift timeliness tracking.", "OPEN", None, "", None),
            ("EMP0004", "Unexcused prolonged absence from project deliverables and sprint milestones.", "HR recommends placing employee on a 30-day structured Performance Improvement Plan (PIP).", "SENT_TO_ADMIN", None, "", None),
            ("EMP0006", "Minor non-compliance with standardized file naming and asset archiving guidelines.", "HR recommended informal reminder and retraining on asset management.", "RESOLVED", "CONTINUE", "Issue addressed after 1-on-1 feedback session. Full compliance restored.", admin_user),
            ("EMP0001", "Delay in rotating production API keys during quarterly compliance check.", "HR recommends second advisory notice regarding security compliance.", "RESOLVED", "ANOTHER_WARNING", "Second advisory issued. Security credentials rotated immediately.", admin_user),
            ("EMP0005", "Severe violation of IT security protocols: unauthorized export of codebase repository and sustained non-performance.", "HR recommends immediate employment termination in accordance with company policy.", "RESOLVED", "TERMINATION", "Termination confirmed and executed by Administration. Access revoked.", admin_user),
        ]

        for code, reason, hr_rec, w_status, admin_dec, admin_comm, dec_user in warnings_seed:
            emp = emp_objs.get(code)
            if not emp:
                continue
            warn, _ = PerformanceWarning.objects.get_or_create(
                employee=emp,
                reason=reason,
                defaults={
                    "issued_by": primary_hr,
                    "hr_recommendation": hr_rec,
                    "status": w_status,
                    "admin_decision": admin_dec,
                    "admin_comments": admin_comm,
                    "decided_by": dec_user,
                    "decision_date": timezone.now() if admin_dec else None,
                },
            )
            stats["warnings"] += 1
            self.stdout.write(f"  [+] Warning: {emp.employee_code} [{w_status}] Decision: {admin_dec or 'None'}")

        # -------------------------------------------------------------------------
        # 14. ANNOUNCEMENTS & HOLIDAYS
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.HTTP_INFO("\n14. Seeding Company Announcements & Holidays..."))
        announcements_seed = [
            (
                "Annual Company Tech Symposium 2026",
                "All employees are invited to the Annual Technology & Innovation Symposium. Keynote speeches from industry AI leaders.",
                "GENERAL",
                "All",
            ),
            (
                "Annual Performance Appraisal Cycle Launch",
                "The Q1 Performance appraisal cycle is now active. Please ensure all pending weekly reports are submitted on time.",
                "HR",
                "All",
            ),
            (
                "Scheduled Cloud Infrastructure Maintenance",
                "Internal staging environments and CI/CD runners will undergo scheduled maintenance this Sunday between 02:00 AM and 04:00 AM IST.",
                "NOTICE",
                "Engineering",
            ),
            (
                "Upcoming Public Holiday Notice",
                "Office will remain closed in observance of the upcoming National Holiday. Emergency on-call schedules remain active for SREs.",
                "HOLIDAY",
                "All",
            ),
            ("Annual Company Tech Symposium 2026", "All employees are invited to the Annual Technology & Innovation Symposium. Keynote speeches from industry AI leaders.", "GENERAL", "All"),
            ("Annual Performance Appraisal Cycle Launch", "The Q1 Performance appraisal cycle is now active. Please ensure all pending weekly reports are submitted on time.", "HR", "All"),
            ("Scheduled Cloud Infrastructure Maintenance", "Internal staging environments and CI/CD runners will undergo scheduled maintenance this Sunday between 02:00 AM and 04:00 AM IST.", "NOTICE", "Engineering"),
            ("Upcoming Public Holiday Notice", "Office will remain closed in observance of the upcoming National Holiday. Emergency on-call schedules remain active for SREs.", "HOLIDAY", "All"),
        ]

        for a_title, a_content, a_type, a_target in announcements_seed:
            Announcement.objects.get_or_create(
                title=a_title,
                defaults={
                    "content": a_content,
                    "announcement_type": a_type,
                    "target_audience": a_target,
                    "is_active": True,
                    "is_published": True,
                    "published_at": timezone.now(),
                    "created_by": admin_user,
                },
            )

        holidays_seed = [
            ("Republic Day", date(2026, 1, 26), "PUBLIC", "National Holiday"),
            ("Holi Celebration", date(2026, 3, 25), "PUBLIC", "Festival of Colors"),
            ("May Day / Labor Day", date(2026, 5, 1), "PUBLIC", "International Labor Day"),
            ("Independence Day", date(2026, 8, 15), "PUBLIC", "National Independence Day"),
            ("Gandhi Jayanti", date(2026, 10, 2), "PUBLIC", "Mahatma Gandhi Birthday"),
            ("Diwali (Deepavali)", date(2026, 11, 8), "PUBLIC", "Festival of Lights"),
            ("Christmas Day", date(2026, 12, 25), "PUBLIC", "Christmas Celebration"),
            ("Company Foundation Day", date(2026, 9, 15), "COMPANY", "Annual Company Anniversary"),
        ]

        for h_name, h_date, h_type, h_desc in holidays_seed:
            Holiday.objects.get_or_create(
                name=h_name,
                date=h_date,
                defaults={
                    "holiday_type": h_type,
                    "description": h_desc,
                    "is_active": True,
                },
            )

        # -------------------------------------------------------------------------
        # Summary Output
        # -------------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n======================================================="))
        self.stdout.write(self.style.SUCCESS(" IT COMPANY DEMO DATA SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("======================================================="))
        self.stdout.write(f"  - Users created/updated:       {stats['users']}")
        self.stdout.write(f"  - HR Managers seeded:          {stats['hr_managers']}")
        self.stdout.write(f"  - Test Users created/updated:  {stats['users']}")
        self.stdout.write(f"  - Employees seeded:            {stats['employees']}")
        self.stdout.write(f"  - Candidates seeded:           {stats['candidates']}")
        self.stdout.write(f"  - Job Vacancies seeded:        {stats['vacancies']}")
        self.stdout.write(f"  - Job Applications seeded:     {stats['applications']}")
        self.stdout.write(f"  - Employee Reports seeded:     {stats['reports']}")
        self.stdout.write(f"  - Performance Reviews seeded:  {stats['reviews']}")
        self.stdout.write(f"  - Performance Warnings seeded: {stats['warnings']}")
        self.stdout.write(self.style.SUCCESS("=======================================================\n"))

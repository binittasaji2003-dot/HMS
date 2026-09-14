import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from admin_module.models import Department, Announcement
from employees.models import Employee, EmployeeReport, EmployeePerformance, PerformanceWarning, Notification
from allauth.account.models import EmailAddress

User = get_user_model()


def seed_data():
    print("1. Running database migrations...")
    call_command("makemigrations", "employees", interactive=False)
    call_command("migrate", interactive=False)

    print("2. Creating default Department...")
    dept, _ = Department.objects.get_or_create(
        name="Information Technology",
        defaults={"description": "IT & Software Development Department", "is_active": True}
    )

    print("3. Creating Test Employee User...")
    email = "binitta.saji@company.com"
    password = "password123"

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = User.objects.create_user(
            email=email,
            password=password,
            name="Binitta Saji",
            is_active=True
        )
        print(f"   --> Created User: {email} / Password: {password}")
    else:
        user.set_password(password)
        user.name = "Binitta Saji"
        user.is_active = True
        user.save()
        print(f"   --> Reset User credentials: {email} / Password: {password}")

    # Create/verify allauth EmailAddress record
    EmailAddress.objects.get_or_create(
        user=user,
        email=email,
        defaults={"primary": True, "verified": True}
    )

    print("4. Creating Employee Profile...")
    employee, created = Employee.objects.get_or_create(
        user=user,
        defaults={
            "employee_code": "EMP1024",
            "department": dept,
            "designation": "Software Developer",
            "joining_date": date(2025, 1, 15),
            "employment_status": "ACTIVE"
        }
    )
    if not created:
        employee.employee_code = "EMP1024"
        employee.department = dept
        employee.designation = "Software Developer"
        employee.save()
    print(f"   --> Employee Record: {employee.employee_code} ({employee.designation})")

    print("5. Seeding Sample Reports...")
    today = date.today()
    sample_reports = [
        ("Weekly Report - Week 4", today - timedelta(days=5), today, "Submitted full feature integration.", "Completed UI overhaul and login views.", "SUBMITTED"),
        ("Weekly Report - Week 3", today - timedelta(days=12), today - timedelta(days=6), "Worked on candidate module API.", "Fixed validation issues.", "REVIEWED"),
        ("Weekly Report - Week 2", today - timedelta(days=19), today - timedelta(days=13), "Backend API architecture.", "Database migrations setup.", "REVIEWED"),
        ("Weekly Report - Week 1", today - timedelta(days=26), today - timedelta(days=20), "Initial project onboarding.", "Environment configuration.", "REVIEWED"),
    ]
    for title, s_date, e_date, summary, tasks, status in sample_reports:
        EmployeeReport.objects.get_or_create(
            employee=employee,
            title=title,
            defaults={
                "week_start_date": s_date,
                "week_end_date": e_date,
                "work_summary": summary,
                "tasks_completed": tasks,
                "status": status,
                "hr_comments": "Good progress!" if status == "REVIEWED" else ""
            }
        )

    print("6. Seeding Performance Review...")
    EmployeePerformance.objects.get_or_create(
        employee=employee,
        review_period="Q1 2025 Review",
        defaults={
            "score": 4.3,
            "rating": "GOOD",
            "comments": "You are doing a great job. Keep up the good work!"
        }
    )

    print("7. Seeding Announcements...")
    Announcement.objects.get_or_create(
        title="Annual Day Celebration",
        defaults={
            "content": "All employees are invited to the Annual Day Celebration at the main auditorium.",
            "announcement_type": "GENERAL",
            "is_published": True,
            "published_at": timezone.now()
        }
    )
    Announcement.objects.get_or_create(
        title="New Leave Policy Updates",
        defaults={
            "content": "Please review the updated leave policy document.",
            "announcement_type": "HR",
            "is_published": True,
            "published_at": timezone.now()
        }
    )
    Announcement.objects.get_or_create(
        title="Office Holiday - May Day",
        defaults={
            "content": "The office will remain closed on 1st May in observance of May Day.",
            "announcement_type": "HOLIDAY",
            "is_published": True,
            "published_at": timezone.now()
        }
    )

    print("8. Seeding Notifications...")
    sample_notifications = [
        ("Weekly Report Reminder", "Please submit your weekly work report before Friday 5 PM.", "REPORT_REMINDER"),
        ("HR Feedback", "Your report for Week 3 has been reviewed by HR Manager.", "HR_FEEDBACK"),
        ("Performance Warning", "Please ensure punctuality for morning standup meetings.", "WARNING"),
        ("Company Announcement", "New company policy guidelines have been published.", "ANNOUNCEMENT"),
        ("Profile Update", "Your profile information was updated successfully.", "PROFILE_UPDATE"),
    ]
    for title, msg, n_type in sample_notifications:
        Notification.objects.get_or_create(
            employee=employee,
            title=title,
            defaults={
                "message": msg,
                "notification_type": n_type,
                "is_read": False
            }
        )

    print("\n=======================================================")
    print(" SUCCESS! Demo Employee Account Created & Verified!")
    print("-------------------------------------------------------")
    print(f" Email:    {email}")
    print(f" Password: {password}")
    print("=======================================================\n")


if __name__ == "__main__":
    seed_data()

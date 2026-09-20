import sys
from django.contrib.auth.hashers import make_password
from django.db import migrations


def seed_departments_and_teams(apps, schema_editor):
    if "test" in sys.argv:
        return

    User = apps.get_model("users", "User")
    Department = apps.get_model("admin_module", "Department")
    Team = apps.get_model("employees", "Team")

    def get_or_create_user(email, name, role="Employee"):
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create(
                email=email,
                name=name,
                role=role,
                status="Active",
                is_active=True,
                password=make_password("Password123!"),
            )
        return user

    rahul = get_or_create_user("rahul.mathew@hrms.com", "Rahul Mathew", role="Employee")
    anjali = get_or_create_user("anjali.thomas@hrms.com", "Anjali Thomas", role="HR")
    joseph = get_or_create_user("joseph.mathew@hrms.com", "Joseph Mathew", role="Employee")
    arun = get_or_create_user("arun.joseph@hrms.com", "Arun Joseph", role="Employee")
    vishnu = get_or_create_user("vishnu.kumar@hrms.com", "Vishnu Kumar", role="Employee")
    neeraj = get_or_create_user("neeraj.thomas@hrms.com", "Neeraj Thomas", role="Employee")

    dev_dept, _ = Department.objects.get_or_create(
        name="Development",
        defaults={"description": "Engineering and Software Development"},
    )
    dev_dept.department_leader = rahul
    dev_dept.save()

    hr_dept, _ = Department.objects.get_or_create(
        name="Human Resources",
        defaults={"description": "People Operations and Talent Acquisition"},
    )
    hr_dept.department_leader = anjali
    hr_dept.save()

    fin_dept, _ = Department.objects.get_or_create(
        name="Finance",
        defaults={"description": "Corporate Finance and Accounting"},
    )
    fin_dept.department_leader = joseph
    fin_dept.save()

    t1, _ = Team.objects.get_or_create(
        team_name="Backend Development",
        department=dev_dept,
        defaults={"team_lead": arun, "is_active": True},
    )
    t1.team_lead = arun
    t1.save()

    t2, _ = Team.objects.get_or_create(
        team_name="Frontend Development",
        department=dev_dept,
        defaults={"team_lead": vishnu, "is_active": True},
    )
    t2.team_lead = vishnu
    t2.save()

    t3, _ = Team.objects.get_or_create(
        team_name="Mobile Development",
        department=dev_dept,
        defaults={"team_lead": neeraj, "is_active": True},
    )
    t3.team_lead = neeraj
    t3.save()

    t4, _ = Team.objects.get_or_create(
        team_name="Talent Acquisition",
        department=hr_dept,
        defaults={"team_lead": anjali, "is_active": True},
    )
    t4.team_lead = anjali
    t4.save()


class Migration(migrations.Migration):

    dependencies = [
        ("admin_module", "0005_department_department_leader_and_more"),
        ("employees", "0003_employee_employment_type_employee_team_lead_and_more"),
        ("users", "0003_alter_user_role_user_only_one_admin_user"),
    ]

    operations = [
        migrations.RunPython(seed_departments_and_teams, reverse_code=migrations.RunPython.noop),
    ]

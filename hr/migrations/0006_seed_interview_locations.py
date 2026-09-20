from django.db import migrations


def seed_interview_locations(apps, schema_editor):
    InterviewLocation = apps.get_model("hr", "InterviewLocation")
    locations = [
        {
            "location_name": "Kochi Office",
            "address": "4th Floor, Infopark Phase II, Kakkanad",
            "city": "Kochi",
            "state": "Kerala",
            "is_active": True,
        },
        {
            "location_name": "Trivandrum Office",
            "address": "Module 3, Technopark Campus, Karyavattom",
            "city": "Trivandrum",
            "state": "Kerala",
            "is_active": True,
        },
        {
            "location_name": "Bangalore Office",
            "address": "Tower B, Electronic City Phase 1",
            "city": "Bangalore",
            "state": "Karnataka",
            "is_active": True,
        },
        {
            "location_name": "Chennai Office",
            "address": "Level 5, Tidel Park, Rajiv Gandhi Salai",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "is_active": True,
        },
    ]
    for loc_data in locations:
        InterviewLocation.objects.get_or_create(
            location_name=loc_data["location_name"],
            defaults=loc_data,
        )


def unseed_interview_locations(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("hr", "0005_interviewlocation_interview_attendance_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_interview_locations, unseed_interview_locations),
    ]


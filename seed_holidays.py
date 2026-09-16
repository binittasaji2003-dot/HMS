import os
import django
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from admin_module.models import Holiday

holidays_data = [
    {"name": "Republic Day", "date": date(2026, 1, 26), "holiday_type": "PUBLIC", "description": "National Holiday celebrating the Constitution of India."},
    {"name": "Maha Shivaratri", "date": date(2026, 2, 16), "holiday_type": "PUBLIC", "description": "Hindu festival dedicated to Lord Shiva."},
    {"name": "Eid-ul-Fitr (Ramadan)", "date": date(2026, 3, 20), "holiday_type": "PUBLIC", "description": "Islamic festival marking the end of Ramadan fasting."},
    {"name": "Good Friday", "date": date(2026, 4, 3), "holiday_type": "PUBLIC", "description": "Christian holiday commemorating the crucifixion of Jesus."},
    {"name": "Vishu / Ambedkar Jayanti", "date": date(2026, 4, 14), "holiday_type": "PUBLIC", "description": "Malayalam New Year (Vishu) & Dr. B.R. Ambedkar Jayanti."},
    {"name": "May Day / Labour Day", "date": date(2026, 5, 1), "holiday_type": "PUBLIC", "description": "International Workers' Day."},
    {"name": "Bakrid / Eid al-Adha", "date": date(2026, 5, 27), "holiday_type": "PUBLIC", "description": "Feast of the Sacrifice."},
    {"name": "Muharram", "date": date(2026, 6, 26), "holiday_type": "PUBLIC", "description": "Islamic New Year / Day of Ashura."},
    {"name": "Independence Day", "date": date(2026, 8, 15), "holiday_type": "PUBLIC", "description": "Indian Independence Day."},
    {"name": "Sree Narayana Guru Jayanti", "date": date(2026, 8, 28), "holiday_type": "PUBLIC", "description": "Birthday of saint and social reformer Sree Narayana Guru."},
    {"name": "Thiruvonam (Onam)", "date": date(2026, 9, 4), "holiday_type": "PUBLIC", "description": "Harvest and cultural festival of Kerala."},
    {"name": "Third Onam / Sree Krishna Jayanti", "date": date(2026, 9, 5), "holiday_type": "PUBLIC", "description": "Celebration of Onam and Sri Krishna Jayanti."},
    {"name": "Sree Narayana Guru Samadhi", "date": date(2026, 9, 21), "holiday_type": "PUBLIC", "description": "Remembrance day of Sree Narayana Guru."},
    {"name": "Gandhi Jayanti", "date": date(2026, 10, 2), "holiday_type": "PUBLIC", "description": "Birthday of Mahatma Gandhi, Father of the Nation."},
    {"name": "Mahanavami / Vijayadashami", "date": date(2026, 10, 20), "holiday_type": "PUBLIC", "description": "Dussehra / Pooja holidays."},
    {"name": "Deepavali (Diwali)", "date": date(2026, 11, 8), "holiday_type": "PUBLIC", "description": "Festival of Lights."},
    {"name": "Christmas Day", "date": date(2026, 12, 25), "holiday_type": "PUBLIC", "description": "Christian festival celebrating the birth of Jesus Christ."},
]

created_count = 0
for item in holidays_data:
    obj, created = Holiday.objects.update_or_create(
        name=item["name"],
        date=item["date"],
        defaults={
            "holiday_type": item["holiday_type"],
            "description": item["description"],
            "is_active": True,
        },
    )
    if created:
        created_count += 1

print(f"Seeded {len(holidays_data)} holidays ({created_count} newly created). Total in DB: {Holiday.objects.count()}")


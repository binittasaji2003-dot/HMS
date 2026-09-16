from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from admin_module.models import Announcement, Department, Holiday
from candidates.models import Candidate, JobVacancy
from employees.models import Employee


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Dynamic Open Vacancies
        open_jobs = (
            JobVacancy.objects.filter(status="OPEN")
            .select_related("department")
            .order_by("-posted_date")
        )

        # Metrics
        context["open_jobs"] = open_jobs[:6]
        context["total_open_jobs"] = open_jobs.count()
        context["total_employees"] = (
            Employee.objects.filter(employment_status="ACTIVE").count()
            or Employee.objects.count()
        )
        context["total_departments"] = (
            Department.objects.filter(is_active=True).count()
            or Department.objects.count()
        )

        # Announcements
        context["announcements"] = (
            Announcement.objects.filter(is_active=True, is_published=True)
            .order_by("-created_at")[:3]
        )

        return context


def calendar_events_api(request):
    current_year = timezone.now().year
    events = []

    # 1. Kerala & India Public Holidays
    for h in Holiday.objects.filter(is_active=True):
        events.append({
            "id": f"holiday-{h.holiday_id}",
            "title": h.name,
            "date": h.date.strftime("%Y-%m-%d"),
            "type": "holiday",
            "category": h.holiday_type,
            "description": h.description or "Public Holiday",
            "badgeClass": "bg-danger text-white",
        })

    # 2. Employee Birthdays
    candidates_with_dob = Candidate.objects.filter(date_of_birth__isnull=False)
    for c in candidates_with_dob:
        if c.date_of_birth:
            bday_this_year = f"{current_year}-{c.date_of_birth.month:02d}-{c.date_of_birth.day:02d}"
            name = (
                c.full_name
                or getattr(c.user, "name", "")
                or (c.user.email.split("@")[0] if c.user else "Employee")
            )
            events.append({
                "id": f"bday-{c.candidate_id}",
                "title": f"🎂 {name}'s Birthday",
                "date": bday_this_year,
                "type": "birthday",
                "description": f"Celebrate {name}'s birthday!",
                "badgeClass": "bg-primary text-white",
            })

    return JsonResponse({"status": "success", "events": events})


def dismiss_birthday_popup(request):
    request.session["birthday_greeted"] = True
    return JsonResponse({"status": "success"})

from django.apps import AppConfig


class CandidatesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "candidates"

    def ready(self):
        from .models import JobVacancy

        if not hasattr(JobVacancy, "department_name"):
            JobVacancy.department_name = property(
                lambda self: self.department.name if getattr(self, "department", None) else ""
            )

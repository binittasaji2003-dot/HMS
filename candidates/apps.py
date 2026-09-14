from django.apps import AppConfig


class CandidatesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "candidates"
    verbose_name = "Candidate & Job Portal"

    def ready(self):
        import candidates.signals

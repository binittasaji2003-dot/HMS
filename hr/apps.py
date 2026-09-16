from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr"

    def ready(self):
        from .models import HRManager

        if not hasattr(HRManager, "email"):
            HRManager.email = property(lambda self: self.user.email if self.user else "")
        if not hasattr(HRManager, "name"):
            HRManager.name = property(lambda self: self.user.name if self.user else "")

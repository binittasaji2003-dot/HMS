from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "hr_management_system.users"
    verbose_name = _("Users")

    def ready(self):
        from hr_management_system.users.models import User

        def _get_first_name(self):
            parts = (self.name or "").split()
            return parts[0] if parts else ""
        User.first_name = property(_get_first_name)

        def _get_last_name(self):
            parts = (self.name or "").split()
            return " ".join(parts[1:]) if len(parts) > 1 else ""
        User.last_name = property(_get_last_name)

        User.get_full_name = lambda self: self.name or self.email
        User.get_short_name = lambda self: self.first_name or self.email

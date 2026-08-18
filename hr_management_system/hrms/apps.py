from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HrmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hr_management_system.hrms"
    verbose_name = _("HRMS Core")

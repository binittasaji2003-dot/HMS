from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as static_url
from django.urls import include
from django.urls import path
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from .views import HomeView, calendar_events_api, dismiss_birthday_popup

urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(url=static_url("images/favicons/favicon.ico"), permanent=True),
    ),
    path("", HomeView.as_view(), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    path(
        "accounts/role-select/",
        TemplateView.as_view(template_name="account/role_select.html"),
        name="role_select",
    ),
    path(
        "login-select/",
        TemplateView.as_view(template_name="account/role_select.html"),
        name="login_select",
    ),

    # Calendar & Notification APIs
    path("api/calendar/events/", calendar_events_api, name="calendar_events_api"),
    path("api/birthday/dismiss/", dismiss_birthday_popup, name="dismiss_birthday_popup"),

    # Django admin
    path(settings.ADMIN_URL, admin.site.urls),

    # HR Management System modules
    path("admin-portal/", include("admin_module.urls", namespace="admin_module")),
    path("users/", include("hr_management_system.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path("employees/", include("employees.urls")),
    path("hr/", include("hr.urls", namespace="hr")),
    path("candidates/", include("candidates.urls", namespace="candidates")),

    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "400/",
            TemplateView.as_view(template_name="400.html"),
            name="400",
        ),
        path(
            "403/",
            TemplateView.as_view(template_name="403.html"),
            name="403",
        ),
        path(
            "404/",
            TemplateView.as_view(template_name="404.html"),
            name="404",
        ),
        path(
            "500/",
            TemplateView.as_view(template_name="500.html"),
            name="500",
        ),
    ]
if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
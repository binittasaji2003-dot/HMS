from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views.generic import TemplateView


urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),

    # Django admin
    path(settings.ADMIN_URL, admin.site.urls),

    # HR Management System modules
    path("admin-portal/", include("admin_module.urls", namespace="admin_module")),
    path("users/", include("hr_management_system.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path("employees/", include("employees.urls")),
    path("hr/", include("hr.urls", namespace="hr")),

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
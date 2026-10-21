from allauth.account.forms import LoginForm, SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.forms import EmailField
from django.utils.translation import gettext_lazy as _

from .models import User


class UserLoginForm(LoginForm):
    """
    Unified Login Form supporting:
    - Registered email addresses for Admin, HR, Employee, and Candidate users.
    - Employee codes (e.g. EMP102, EMP0038, EMP-0038, 102).
    - HR manager codes (e.g. HR001, HR-001).
    - Role aliases like 'admin' / 'administrator'.
    - Account username prefixes (e.g. 'binittasaji2003', 'binittasaji', 'amal', 'edwin').
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["login"] = forms.CharField(
            label=_("Email Address or Employee ID"),
            widget=forms.TextInput(
                attrs={
                    "placeholder": _("Enter email, Employee ID (e.g. EMP102), or username"),
                    "autocomplete": "username",
                    "class": "w-full h-11 pl-11 pr-4 text-sm bg-purple-50/40 border border-purple-200 rounded-xl text-slate-900 placeholder:text-slate-400 focus:bg-white focus:border-violet-600 focus:ring-4 focus:ring-violet-500/15 outline-none transition-all",
                }
            ),
            required=True,
        )

    def clean_login(self):
        login_val = (self.cleaned_data.get("login") or "").strip()
        if not login_val:
            return login_val

        # 1. If standard email format, find exact or case-insensitive user match
        if "@" in login_val:
            try:
                matched_user = User.objects.filter(email__iexact=login_val).first()
                if matched_user:
                    return matched_user.email.lower()
            except Exception:
                pass
            return login_val.lower()

        # 2. Administrator alias lookup
        if login_val.lower() in ["admin", "administrator", "superadmin", "root"]:
            try:
                admin_user = (
                    User.objects.filter(role=User.RoleChoices.ADMIN).first()
                    or User.objects.filter(is_superuser=True).first()
                )
                if admin_user and admin_user.email:
                    return admin_user.email.lower()
            except Exception:
                pass

        # 3. Employee Code match (case-insensitive, ignores hyphens and spaces)
        try:
            from employees.models import Employee

            clean_code = login_val.replace("-", "").replace(" ", "")
            emp = Employee.objects.filter(employee_code__iexact=login_val).select_related("user").first()
            if not emp:
                emp = Employee.objects.filter(employee_code__iexact=clean_code).select_related("user").first()
            if not emp and not clean_code.upper().startswith("EMP"):
                emp = Employee.objects.filter(employee_code__iexact=f"EMP{clean_code}").select_related("user").first()
            if not emp and clean_code.isdigit():
                try:
                    emp = Employee.objects.filter(employee_code__iexact=f"EMP{int(clean_code):04d}").select_related("user").first()
                except ValueError:
                    pass

            if emp and emp.user and emp.user.email:
                return emp.user.email.lower()
        except Exception:
            pass

        # 4. HR Manager Code match (case-insensitive)
        try:
            from hr.models import HRManager

            clean_code = login_val.replace("-", "").replace(" ", "")
            hr_mgr = HRManager.objects.filter(employee_code__iexact=login_val).select_related("user").first()
            if not hr_mgr:
                hr_mgr = HRManager.objects.filter(employee_code__iexact=clean_code).select_related("user").first()
            if not hr_mgr and not clean_code.upper().startswith("HR"):
                hr_mgr = HRManager.objects.filter(employee_code__iexact=f"HR{clean_code}").select_related("user").first()

            if hr_mgr and hr_mgr.user and hr_mgr.user.email:
                return hr_mgr.user.email.lower()
        except Exception:
            pass

        # 5. Email username prefix match (e.g. 'binittasaji2003' -> 'binittasaji2003@gmail.com')
        try:
            user_by_prefix = User.objects.filter(email__istartswith=f"{login_val}@").first()
            if user_by_prefix and user_by_prefix.email:
                return user_by_prefix.email.lower()
        except Exception:
            pass

        # 6. User Full Name match
        try:
            user_by_name = User.objects.filter(name__iexact=login_val).first()
            if user_by_name and user_by_name.email:
                return user_by_name.email.lower()
        except Exception:
            pass

        return login_val


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """

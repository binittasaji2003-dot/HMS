from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Department
from .models import Employee
from .models import HRManager

User = get_user_model()


def ensure_default_departments():
    """Populate a few baseline departments so admin assignment forms are usable."""
    defaults = [
        "Engineering",
        "Human Resources",
        "Finance",
        "Operations",
    ]
    for name in defaults:
        Department.objects.get_or_create(
            name=name,
            defaults={"description": "Default department created for admin management workflows."},
        )
    return Department.objects.order_by("name")


class AdminRegistrationForm(forms.ModelForm):
    """Form for creating the single System Administrator account."""

    name = forms.CharField(
        label=_("Full Name"),
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Enter your full name",
                "autocomplete": "name",
            }
        ),
    )

    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "admin@company.com",
                "autocomplete": "email",
            }
        ),
    )

    password = forms.CharField(
        label=_("Password"),
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Create a strong password",
                "autocomplete": "new-password",
            }
        ),
    )

    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Re-enter your password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("name", "email", "password")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("An account with this email address already exists.")
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        # Only one Administrator is allowed.
        if User.objects.filter(
            role=User.RoleChoices.ADMIN
        ).exists():
            raise ValidationError(
                _("A System Administrator account already exists.")
            )

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error(
                    "confirm_password",
                    _("Passwords do not match."),
                )
            else:
                try:
                    validate_password(password)
                except ValidationError as error:
                    self.add_error("password", error)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]
        user.name = self.cleaned_data["name"]

        # Hash the password before storing it.
        user.set_password(self.cleaned_data["password"])

        # Admin role is assigned by the backend.
        # The user never selects this.
        user.role = User.RoleChoices.ADMIN
        user.status = User.StatusChoices.ACTIVE
        user.is_staff = True
        user.is_active = True

        if commit:
            user.save()

        return user


class AdminLoginForm(forms.Form):
    """Admin Login Form with strict role and status verification."""

    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "admin@company.com",
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label=_("Remember this device for 30 days"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").strip().lower()
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(self.request, email=email, password=password)
            if user is None:
                # Check if user exists to provide helpful, secure feedback
                existing_user = User.objects.filter(email__iexact=email).first()
                if existing_user and existing_user.check_password(password):
                    user = existing_user
                else:
                    raise ValidationError(_("Invalid email address or password. Please try again."))

            # Verify Admin role requirement
            if getattr(user, "role", None) != User.RoleChoices.ADMIN:
                raise ValidationError(
                    _("Access restricted: This portal is exclusively for System Administrators. Your role does not have administrative privileges.")
                )

            # Verify Active status requirement
            if getattr(user, "status", None) != User.StatusChoices.ACTIVE or not user.is_active:
                raise ValidationError(
                    _("Account suspended: Your admin account is currently inactive. Please contact system support.")
                )

            self.user_cache = user

        return cleaned_data

    def get_user(self):
        return self.user_cache


class AdminUserCreateFormMixin(forms.Form):
    """Shared validation for admin-created accounts.

    The active custom User model uses email as the unique login credential and does not
    have a persisted username field. We still accept a username input as part of the UX
    flow and validate it against the existing users to avoid duplicate handles.
    """

    username = forms.CharField(
        label=_("Username"),
        required=True,
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Enter a unique username",
                "autocomplete": "username",
            }
        ),
    )
    full_name = forms.CharField(
        label=_("Full Name"),
        required=True,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Enter full name",
                "autocomplete": "name",
            }
        ),
    )
    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "name@company.com",
                "autocomplete": "email",
            }
        ),
    )
    phone = forms.CharField(
        label=_("Phone"),
        required=True,
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Enter phone number",
                "autocomplete": "tel",
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        required=True,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Create a secure password",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise ValidationError(_("Username is required."))
        if User.objects.filter(name__iexact=username).exists():
            raise ValidationError(_("A user with this username already exists."))
        return username

    def clean(self):
        cleaned_data = super().clean()
        username = (cleaned_data.get("username") or "").strip()
        email = (cleaned_data.get("email") or "").strip().lower()
        if username and email and User.objects.filter(name__iexact=username, email__iexact=email).exists():
            self.add_error("username", _("This username is already associated with this email."))
        return cleaned_data

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                raise ValidationError(error.messages) from error
        return password


class EmployeeCreateForm(AdminUserCreateFormMixin, forms.Form):
    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.none(),
        empty_label="Select a department",
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
    )
    designation = forms.CharField(
        label=_("Designation"),
        required=True,
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Example: Software Engineer",
            }
        ),
    )
    hire_date = forms.DateField(
        label=_("Hire Date"),
        required=True,
        widget=forms.DateInput(
            attrs={
                "class": "form-control custom-input",
                "type": "date",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = ensure_default_departments()

    def save(self, admin_user=None):
        cleaned_data = self.cleaned_data
        user = User.objects.create_user(
            email=cleaned_data["email"],
            password=cleaned_data["password"],
            name=cleaned_data["full_name"],
            role=User.RoleChoices.EMPLOYEE,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        employee = Employee.objects.create(
            user=user,
            department=cleaned_data["department"],
            designation=cleaned_data["designation"],
            date_of_joining=cleaned_data["hire_date"],
            status=Employee.StatusChoices.ACTIVE,
        )
        if admin_user is not None:
            employee.user.name = cleaned_data["full_name"]
            employee.user.save(update_fields=["name"])
        return user


class HRManagerCreateForm(AdminUserCreateFormMixin, forms.Form):
    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.none(),
        empty_label="Select a department",
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
    )
    hired_date = forms.DateField(
        label=_("Hired Date"),
        required=True,
        widget=forms.DateInput(
            attrs={
                "class": "form-control custom-input",
                "type": "date",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = ensure_default_departments()

    def save(self, admin_user=None):
        cleaned_data = self.cleaned_data
        user = User.objects.create_user(
            email=cleaned_data["email"],
            password=cleaned_data["password"],
            name=cleaned_data["full_name"],
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )
        HRManager.objects.create(
            user=user,
            department=cleaned_data["department"],
            phone=cleaned_data["phone"],
            office_location="",
        )
        return user


class EmployeeProfileForm(forms.Form):
    full_name = forms.CharField(label=_("Full Name"), max_length=255, required=True)
    email = forms.EmailField(label=_("Email Address"), required=True)
    phone = forms.CharField(label=_("Phone"), max_length=30, required=True)
    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.all(),
        empty_label="Select a department",
        required=True,
    )
    designation = forms.CharField(label=_("Designation"), max_length=150, required=True)
    status = forms.ChoiceField(
        choices=Employee.StatusChoices.choices,
        required=True,
    )
    hire_date = forms.DateField(label=_("Hire Date"), required=True)
    salary = forms.DecimalField(label=_("Salary"), required=False, min_value=0, max_digits=12, decimal_places=2)

    def __init__(self, *args, employee=None, **kwargs):
        self.employee = employee
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = ensure_default_departments()
        if employee:
            self.fields["full_name"].initial = employee.user.name
            self.fields["email"].initial = employee.user.email
            self.fields["phone"].initial = employee.user.email
            self.fields["department"].initial = employee.department
            self.fields["designation"].initial = employee.designation
            self.fields["status"].initial = employee.status
            self.fields["hire_date"].initial = employee.date_of_joining
            self.fields["salary"].initial = employee.salary

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if self.employee and self.employee.user.email.lower() == email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def save(self):
        if not self.employee:
            return None
        user = self.employee.user
        user.name = self.cleaned_data["full_name"]
        user.email = self.cleaned_data["email"]
        user.save(update_fields=["name", "email"])
        self.employee.department = self.cleaned_data["department"]
        self.employee.designation = self.cleaned_data["designation"]
        self.employee.status = self.cleaned_data["status"]
        self.employee.date_of_joining = self.cleaned_data["hire_date"]
        self.employee.salary = self.cleaned_data["salary"]
        self.employee.save()
        return self.employee


class HRManagerProfileForm(forms.Form):
    full_name = forms.CharField(label=_("Full Name"), max_length=255, required=True)
    email = forms.EmailField(label=_("Email Address"), required=True)
    phone = forms.CharField(label=_("Phone"), max_length=30, required=True)
    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.all(),
        empty_label="Select a department",
        required=True,
    )
    status = forms.ChoiceField(choices=User.StatusChoices.choices, required=True)
    hired_date = forms.DateField(label=_("Hired Date"), required=True)

    def __init__(self, *args, manager=None, **kwargs):
        self.manager = manager
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = ensure_default_departments()
        if manager:
            self.fields["full_name"].initial = manager.user.name
            self.fields["email"].initial = manager.user.email
            self.fields["phone"].initial = manager.phone
            self.fields["department"].initial = manager.department
            self.fields["status"].initial = manager.user.status
            self.fields["hired_date"].initial = manager.created_at.date()

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if self.manager and self.manager.user.email.lower() == email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def save(self):
        if not self.manager:
            return None
        user = self.manager.user
        user.name = self.cleaned_data["full_name"]
        user.email = self.cleaned_data["email"]
        user.status = self.cleaned_data["status"]
        user.save(update_fields=["name", "email", "status"])
        self.manager.department = self.cleaned_data["department"]
        self.manager.phone = self.cleaned_data["phone"]
        self.manager.save(update_fields=["department", "phone"])
        return self.manager

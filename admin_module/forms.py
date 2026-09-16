from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Announcement, Department, EmployeeApproval

from employees.models import Employee
from hr.models import HRManager
from candidates.models import Candidate, JobApplication, JobVacancy


User = get_user_model()


def ensure_default_departments():
    """Return active departments ordered by name."""
    defaults = [
        "Engineering",
        "Human Resources",
        "Finance",
        "Operations",
    ]
    for name in defaults:
        Department.objects.get_or_create(
            name=name,
            defaults={"description": f"Default department {name} for organizational workflows.", "is_active": True},
        )
    return Department.objects.filter(is_active=True).order_by("name")


class AdminRegistrationForm(forms.ModelForm):
    """Form for creating the System Administrator account."""

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

        if User.objects.filter(role=User.RoleChoices.ADMIN).exists():
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
        user.set_password(self.cleaned_data["password"])
        user.role = User.RoleChoices.ADMIN
        user.status = User.StatusChoices.ACTIVE
        user.is_staff = True
        user.is_active = True

        if commit:
            user.save()

        return user


class AdminLoginForm(forms.Form):
    """Admin login form with role and status verification."""

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
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        ),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        email = (cleaned_data.get("email") or "").strip().lower()
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(
                self.request,
                email=email,
                password=password,
            )

            if user is None:
                raise ValidationError(
                    _("Invalid email address or password. Please try again.")
                )

            if getattr(user, "role", None) != User.RoleChoices.ADMIN:
                raise ValidationError(
                    _("Access restricted to System Administrators.")
                )

            if (
                getattr(user, "status", None) != User.StatusChoices.ACTIVE
                or not user.is_active
            ):
                raise ValidationError(
                    _("Your administrator account is currently inactive.")
                )

            self.user_cache = user

        return cleaned_data

    def get_user(self):
        return self.user_cache


class AdminUserCreateFormMixin(forms.Form):
    """Common fields and validation for Admin-created user accounts."""

    full_name = forms.CharField(
        label=_("Full Name"),
        max_length=255,
        required=True,
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

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("An account with this email address already exists.")
            )

        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")

        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                raise ValidationError(error.messages) from error

        return password


class EmployeeCreateForm(AdminUserCreateFormMixin):
    """Create a User and corresponding Employee profile."""

    employee_code = forms.CharField(
        label=_("Employee Code"),
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "EMP001",
            }
        ),
    )
    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.none(),
        empty_label="Select a department",
        widget=forms.Select(
            attrs={"class": "form-select custom-input"}
        ),
    )

    designation = forms.CharField(
        label=_("Designation"),
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Example: Software Engineer",
            }
        ),
    )

    joining_date = forms.DateField(
        label=_("Joining Date"),
        required=True,
        widget=forms.DateInput(
            attrs={
                "class": "form-control custom-input",
                "type": "date",
            }
        ),
    )

    employment_status = forms.ChoiceField(
        label=_("Employment Status"),
        choices=Employee.EMPLOYMENT_STATUS,
        initial="ACTIVE",
        widget=forms.Select(
            attrs={"class": "form-select custom-input"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = ensure_default_departments()

    def clean_employee_code(self):
        code = self.cleaned_data["employee_code"].strip()
        if Employee.objects.filter(employee_code__iexact=code).exists():
            raise ValidationError(
                _("An Employee with this employee code already exists.")
            )
        return code

    def save(self, admin_user=None):
        data = self.cleaned_data
        emp_status = data.get("employment_status", "ACTIVE")
        is_active = emp_status not in ["INACTIVE", "TERMINATED"]
        user_status = User.StatusChoices.ACTIVE if is_active else User.StatusChoices.INACTIVE

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            name=data["full_name"],
            role=User.RoleChoices.EMPLOYEE,
            status=user_status,
            is_active=is_active,
        )

        employee = Employee.objects.create(
            user=user,
            employee_code=data["employee_code"],
            department=data["department"],
            designation=data["designation"],
            joining_date=data["joining_date"],
            employment_status=emp_status,
            created_by=admin_user,
        )

        return employee


class HRManagerCreateForm(AdminUserCreateFormMixin):
    """Create a User and corresponding HR Manager profile."""

    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.none(),
        empty_label="Select a department",
        widget=forms.Select(
            attrs={"class": "form-select custom-input"}
        ),
    )

    joining_date = forms.DateField(
        label=_("Joining Date"),
        required=True,
        widget=forms.DateInput(
            attrs={
                "class": "form-control custom-input",
                "type": "date",
            }
        ),
    )

    employee_code = forms.CharField(
        label=_("Employee Code"),
        max_length=50,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "HR001",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = ensure_default_departments()

    def clean_employee_code(self):
        code = self.cleaned_data["employee_code"].strip()

        if HRManager.objects.filter(employee_code__iexact=code).exists():
            raise ValidationError(
                _("An HR Manager with this employee code already exists.")
            )

        return code

    def save(self, admin_user=None):
        data = self.cleaned_data

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            name=data["full_name"],
            role=User.RoleChoices.HR,
            status=User.StatusChoices.ACTIVE,
            is_active=True,
        )

        manager = HRManager.objects.create(
            user=user,
            department=data["department"],
            employee_code=data["employee_code"],
            joining_date=data["joining_date"],
            is_active=True,
        )

        return manager


class EmployeeProfileForm(forms.Form):
    """Edit an existing Employee profile."""

    full_name = forms.CharField(
        label=_("Full Name"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control custom-input"}),
    )

    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control custom-input"}),
    )

    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
    )

    designation = forms.CharField(
        label=_("Designation"),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control custom-input"}),
    )

    employment_status = forms.ChoiceField(
        label=_("Employment Status"),
        choices=Employee.EMPLOYMENT_STATUS,
        required=True,
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
    )

    joining_date = forms.DateField(
        label=_("Joining Date"),
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control custom-input"}),
    )

    def __init__(self, *args, employee=None, **kwargs):
        self.employee = employee
        super().__init__(*args, **kwargs)

        self.fields["department"].queryset = ensure_default_departments()

        if employee:
            self.fields["full_name"].initial = employee.user.name
            self.fields["email"].initial = employee.user.email
            self.fields["department"].initial = employee.department
            self.fields["designation"].initial = employee.designation
            self.fields["employment_status"].initial = (
                employee.employment_status
            )
            self.fields["joining_date"].initial = employee.joining_date

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        if (
            self.employee
            and self.employee.user.email.lower() == email
        ):
            return email

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("An account with this email address already exists.")
            )

        return email

    def save(self):
        if not self.employee:
            return None

        emp_status = self.cleaned_data["employment_status"]
        is_active = emp_status not in ["INACTIVE", "TERMINATED"]
        user_status = User.StatusChoices.ACTIVE if is_active else User.StatusChoices.INACTIVE

        user = self.employee.user
        user.name = self.cleaned_data["full_name"]
        user.email = self.cleaned_data["email"]
        user.is_active = is_active
        user.status = user_status
        user.save(update_fields=["name", "email", "is_active", "status"])

        self.employee.department = self.cleaned_data["department"]
        self.employee.designation = self.cleaned_data["designation"]
        self.employee.employment_status = emp_status
        self.employee.joining_date = self.cleaned_data["joining_date"]

        self.employee.save(
            update_fields=[
                "department",
                "designation",
                "employment_status",
                "joining_date",
                "updated_at",
            ]
        )

        return self.employee


class HRManagerProfileForm(forms.Form):
    """Edit an existing HR Manager profile."""

    full_name = forms.CharField(
        label=_("Full Name"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control custom-input"}),
    )

    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control custom-input"}),
    )

    employee_code = forms.CharField(
        label=_("Employee Code"),
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control custom-input"}),
    )

    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
    )

    joining_date = forms.DateField(
        label=_("Joining Date"),
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control custom-input"}),
    )

    is_active = forms.BooleanField(
        label=_("Active"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, manager=None, **kwargs):
        self.manager = manager
        super().__init__(*args, **kwargs)

        self.fields["department"].queryset = ensure_default_departments()

        if manager:
            self.fields["full_name"].initial = manager.user.name
            self.fields["email"].initial = manager.user.email
            self.fields["employee_code"].initial = manager.employee_code
            self.fields["department"].initial = manager.department
            self.fields["joining_date"].initial = manager.joining_date
            self.fields["is_active"].initial = manager.is_active

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        if (
            self.manager
            and self.manager.user.email.lower() == email
        ):
            return email

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("An account with this email address already exists.")
            )

        return email

    def clean_employee_code(self):
        code = self.cleaned_data["employee_code"].strip()

        queryset = HRManager.objects.filter(
            employee_code__iexact=code
        )

        if self.manager:
            queryset = queryset.exclude(pk=self.manager.pk)

        if queryset.exists():
            raise ValidationError(
                _("An HR Manager with this employee code already exists.")
            )

        return code

    def save(self):
        if not self.manager:
            return None

        user = self.manager.user
        user.name = self.cleaned_data["full_name"]
        user.email = self.cleaned_data["email"]
        user.is_active = self.cleaned_data["is_active"]
        user.save(update_fields=["name", "email", "is_active"])

        self.manager.employee_code = self.cleaned_data["employee_code"]
        self.manager.department = self.cleaned_data["department"]
        self.manager.joining_date = self.cleaned_data["joining_date"]
        self.manager.is_active = self.cleaned_data["is_active"]

        self.manager.save(
            update_fields=[
                "employee_code",
                "department",
                "joining_date",
                "is_active",
            ]
        )

        return self.manager


class DepartmentForm(forms.ModelForm):
    """Create and edit departments."""

    class Meta:
        model = Department
        fields = ("name", "description", "is_active")
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g. Engineering",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control custom-input",
                    "rows": 4,
                    "placeholder": "Brief department description",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()

        if not name:
            raise ValidationError(
                _("Department name is required.")
            )

        queryset = Department.objects.filter(name__iexact=name)

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError(
                _("A department with this name already exists.")
            )

        return name


class AdminDecisionForm(forms.Form):
    """Record the Admin decision on an HR performance recommendation."""

    DECISION_CHOICES = [
        ("CONTINUE", _("Continue Employment")),
        ("ANOTHER_WARNING", _("Give Another Warning")),
        ("TERMINATION", _("Issue Termination Letter")),
    ]

    decision = forms.ChoiceField(
        label=_("Admin Final Decision"),
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(
            attrs={"class": "form-check-input"}
        ),
    )

    admin_comments = forms.CharField(
        label=_("Admin Comments / Rationale"),
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control custom-input",
                "rows": 4,
                "placeholder": "Enter the rationale for this decision...",
            }
        ),
    )

    new_warning_reason = forms.CharField(
        label=_("Reason for New Warning"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control custom-input",
                "rows": 3,
                "placeholder": "State the updated expectations or issues...",
            }
        ),
    )

    confirm_termination = forms.BooleanField(
        label=_("I confirm the termination decision."),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "confirmTerminationCheckbox",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        decision = cleaned_data.get("decision")
        confirmation = cleaned_data.get("confirm_termination")
        warning_reason = (
            cleaned_data.get("new_warning_reason") or ""
        ).strip()

        if decision == "TERMINATION" and not confirmation:
            self.add_error(
                "confirm_termination",
                _("Confirmation is required for termination."),
            )

        if decision == "ANOTHER_WARNING" and not warning_reason:
            cleaned_data["new_warning_reason"] = (
                cleaned_data.get("admin_comments") or ""
            ).strip()

        return cleaned_data


class AdminIssueWarningForm(forms.Form):
    """Form for Admin to issue a formal warning message to an employee based on a PerformanceWarning report."""

    warning_message = forms.CharField(
        label=_("Admin Warning Message"),
        required=True,
        error_messages={"required": _("Warning message cannot be empty.")},
        widget=forms.Textarea(
            attrs={
                "class": "form-control custom-input",
                "rows": 5,
                "placeholder": "Enter the formal warning directive / message to be issued to the employee...",
            }
        ),
    )

    def clean_warning_message(self):
        msg = (self.cleaned_data.get("warning_message") or "").strip()
        if not msg:
            raise ValidationError(_("Warning message cannot be empty."))
        return msg


class AnnouncementForm(forms.ModelForm):
    """Create and edit Admin announcements."""

    AUDIENCE_CHOICES = [
        ("All", _("Company Wide / All Staff")),
        ("Employees", _("Employees Only")),
        ("HR", _("HR Managers Only")),
        ("Candidates", _("Candidates")),
    ]

    target_audience = forms.ChoiceField(
        choices=AUDIENCE_CHOICES,
        required=False,
        initial="All",
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
    )

    class Meta:
        model = Announcement
        fields = (
            "title",
            "announcement_type",
            "target_audience",
            "content",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Announcement title",
                }
            ),
            "announcement_type": forms.Select(
                attrs={"class": "form-select custom-input"}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control custom-input",
                    "rows": 6,
                    "placeholder": "Compose your announcement...",
                }
            ),
        }

    def clean_title(self):
        title = (self.cleaned_data.get("title") or "").strip()

        if not title:
            raise ValidationError(
                _("Announcement title cannot be blank.")
            )

        return title

    def clean_content(self):
        content = (
            self.cleaned_data.get("content") or ""
        ).strip()

        if not content:
            raise ValidationError(
                _("Announcement content cannot be blank.")
            )

        return content



from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AdminRegistrationForm(forms.ModelForm):
    """Admin Registration Form creating an Active Admin user."""

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
        help_text=_("Must contain at least 8 characters."),
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
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", _("Passwords do not match."))
            else:
                try:
                    validate_password(password)
                except ValidationError as e:
                    self.add_error("password", e)

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

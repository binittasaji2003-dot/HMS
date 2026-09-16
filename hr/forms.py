from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from admin_module.models import Department
from candidates.models import Candidate
from employees.models import Employee, EmployeeDocument
from hr.models import HRManager

User = get_user_model()


class HRProfileEditForm(forms.Form):
    """Form to edit all appropriate editable fields for HR Manager profile."""

    full_name = forms.CharField(
        label=_("Full Name"),
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Enter your full name",
            }
        ),
    )

    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "hr@company.com",
            }
        ),
    )

    phone = forms.CharField(
        label=_("Phone Number"),
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "+1 (555) 000-0000",
            }
        ),
    )

    date_of_birth = forms.DateField(
        label=_("Date of Birth"),
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control custom-input",
            }
        ),
    )

    address = forms.CharField(
        label=_("Address"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control custom-input",
                "placeholder": "Enter street address, city, state, postal code...",
            }
        ),
    )

    department = forms.ModelChoiceField(
        label=_("Department"),
        queryset=Department.objects.all().order_by("name"),
        required=False,
        empty_label="-- Select Department --",
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
    )

    profile_photo = forms.ImageField(
        label=_("Profile Photo"),
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control custom-input"}),
    )

    def __init__(self, *args, user=None, hr_profile=None, linked_employee=None, linked_candidate=None, **kwargs):
        self.user = user
        self.hr_profile = hr_profile
        self.linked_employee = linked_employee
        self.linked_candidate = linked_candidate
        super().__init__(*args, **kwargs)

        if user:
            self.fields["full_name"].initial = user.name or ""
            self.fields["email"].initial = user.email or ""

        if hr_profile and hr_profile.department:
            self.fields["department"].initial = hr_profile.department

        if linked_candidate:
            if not self.fields["full_name"].initial and (linked_candidate.first_name or linked_candidate.last_name):
                self.fields["full_name"].initial = f"{linked_candidate.first_name} {linked_candidate.last_name}".strip()
            self.fields["phone"].initial = linked_candidate.phone or ""
            self.fields["date_of_birth"].initial = linked_candidate.date_of_birth
            self.fields["address"].initial = linked_candidate.address or ""

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if self.user and self.user.email.lower() == email:
            return email

        exclude_pk = self.user.pk if self.user else None
        if User.objects.filter(email__iexact=email).exclude(pk=exclude_pk).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def save(self, user=None, hr_profile=None):
        user = user or self.user
        hr_profile = hr_profile or self.hr_profile
        data = self.cleaned_data

        # 1. Update User
        user.name = data["full_name"].strip()
        user.email = data["email"].strip().lower()
        user.save(update_fields=["name", "email"])

        # 2. Update HRManager
        dept = data.get("department")
        if dept is not None:
            hr_profile.department = dept
            hr_profile.save(update_fields=["department"])

        # 3. Update or create Employee profile
        photo = data.get("profile_photo")
        linked_employee = getattr(user, "employee_profile", None)
        if not linked_employee:
            linked_employee = Employee.objects.create(
                user=user,
                employee_code=hr_profile.employee_code or f"HR-{user.id:04d}",
                department=dept or hr_profile.department or Department.objects.first(),
                designation="HR Manager",
                joining_date=hr_profile.joining_date or timezone.now().date(),
                employment_status="ACTIVE",
            )
        else:
            if dept:
                linked_employee.department = dept
                linked_employee.save(update_fields=["department"])

        if photo:
            linked_employee.profile_photo = photo
            linked_employee.save(update_fields=["profile_photo"])

        # 4. Update or create Candidate profile
        name_parts = data["full_name"].strip().split(" ", 1)
        first_name = name_parts[0] if name_parts else "HR"
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        linked_candidate = getattr(user, "candidate_profile", None) or (
            getattr(linked_employee, "candidate", None) if linked_employee else None
        )
        if not linked_candidate:
            linked_candidate = Candidate.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name or "Manager",
                phone=data.get("phone") or "",
                date_of_birth=data.get("date_of_birth"),
                address=data.get("address") or "",
            )
            if photo:
                linked_candidate.profile_photo = photo
                linked_candidate.save(update_fields=["profile_photo"])
            if linked_employee and not linked_employee.candidate:
                linked_employee.candidate = linked_candidate
                linked_employee.save(update_fields=["candidate"])
        else:
            linked_candidate.first_name = first_name
            linked_candidate.last_name = last_name or linked_candidate.last_name
            if data.get("phone") is not None:
                linked_candidate.phone = data.get("phone")
            if data.get("date_of_birth") is not None:
                linked_candidate.date_of_birth = data.get("date_of_birth")
            if data.get("address") is not None:
                linked_candidate.address = data.get("address")
            if photo:
                linked_candidate.profile_photo = photo
            linked_candidate.save()

        return hr_profile


class HRDocumentUploadForm(forms.ModelForm):
    """Form for HR Manager to upload professional documents."""

    class Meta:
        model = EmployeeDocument
        fields = ["document_type", "document"]
        widgets = {
            "document_type": forms.Select(attrs={"class": "form-select custom-input"}),
            "document": forms.FileInput(attrs={"class": "form-control custom-input"}),
        }


class AptitudeQuestionForm(forms.ModelForm):
    """Form for adding and editing MCQ aptitude questions."""

    class Meta:
        from hr.models import AptitudeQuestion
        model = AptitudeQuestion
        fields = [
            "question",
            "category",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "is_active",
        ]
        widgets = {
            "question": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "Type question text...",
                    "required": "required",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "option_a": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Enter Option A",
                    "required": "required",
                }
            ),
            "option_b": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Enter Option B",
                    "required": "required",
                }
            ),
            "option_c": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Enter Option C",
                    "required": "required",
                }
            ),
            "option_d": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Enter Option D",
                    "required": "required",
                }
            ),
            "correct_answer": forms.Select(
                choices=[
                    ("", "-- Select Correct Option --"),
                    ("A", "Option A"),
                    ("B", "Option B"),
                    ("C", "Option C"),
                    ("D", "Option D"),
                ],
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                },
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def clean_question(self):
        q = self.cleaned_data.get("question", "").strip()
        if not q:
            raise ValidationError("Question text is required.")
        return q

    def clean_option_a(self):
        opt = self.cleaned_data.get("option_a", "").strip()
        if not opt:
            raise ValidationError("Option A is required.")
        return opt

    def clean_option_b(self):
        opt = self.cleaned_data.get("option_b", "").strip()
        if not opt:
            raise ValidationError("Option B is required.")
        return opt

    def clean_option_c(self):
        opt = self.cleaned_data.get("option_c", "").strip()
        if not opt:
            raise ValidationError("Option C is required.")
        return opt

    def clean_option_d(self):
        opt = self.cleaned_data.get("option_d", "").strip()
        if not opt:
            raise ValidationError("Option D is required.")
        return opt

    def clean_correct_answer(self):
        ans = self.cleaned_data.get("correct_answer", "").strip().upper()
        if ans not in ["A", "B", "C", "D"]:
            raise ValidationError("Please select a valid correct answer (Option A, B, C, or D).")
        return ans

    def clean_category(self):
        cat = self.cleaned_data.get("category", "").strip()
        if cat not in ["QUANTITATIVE", "LOGICAL", "VERBAL"]:
            raise ValidationError("Please select a valid category.")
        return cat


class AptitudeTestForm(forms.ModelForm):
    """Form to create and edit Aptitude Tests."""

    class Meta:
        from hr.models import AptitudeTest
        model = AptitudeTest
        fields = [
            "title",
            "description",
            "duration_minutes",
            "total_questions",
            "pass_percentage",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control custom-input", "placeholder": "e.g., General Technical Aptitude Test"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 3, "class": "form-control custom-input", "placeholder": "Test instructions and description"}
            ),
            "duration_minutes": forms.NumberInput(
                attrs={"class": "form-control custom-input", "min": 5, "max": 180}
            ),
            "total_questions": forms.NumberInput(
                attrs={"class": "form-control custom-input", "min": 3, "max": 100}
            ),
            "pass_percentage": forms.NumberInput(
                attrs={"class": "form-control custom-input", "min": 1, "max": 100}
            ),
            "status": forms.Select(
                attrs={"class": "form-select custom-input"}
            ),
        }



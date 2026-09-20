from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeExperience,
    EmployeeReport,
    PerformanceReview,
)

User = get_user_model()


class EmployeePersonalInfoForm(forms.ModelForm):
    """Form for employee to edit personal and contact information."""

    email = forms.EmailField(
        label=_("Work/Login Email"),
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "employee@company.com",
            }
        ),
    )

    class Meta:
        model = Employee
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "personal_email",
            "address",
            "city",
            "state",
            "pincode",
            "profile_photo",
        ]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Enter first name",
                    "required": "required",
                }
            ),
            "middle_name": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Enter middle name (optional)",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Enter last name",
                    "required": "required",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control custom-input",
                }
            ),
            "gender": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "+1 (555) 000-0000 or 10-digit number",
                }
            ),
            "personal_email": forms.EmailInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "personal.email@example.com (optional)",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "Enter residential address, street, apartment...",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Kochi, Bangalore, Mumbai",
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Kerala, Karnataka, Maharashtra",
                }
            ),
            "pincode": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., 682001",
                }
            ),
            "profile_photo": forms.FileInput(
                attrs={
                    "class": "form-control custom-input",
                    "accept": "image/*",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user or (kwargs.get("instance").user if kwargs.get("instance") else None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["email"].initial = self.user.email or ""
            if not self.initial.get("first_name") and self.user.name:
                parts = self.user.name.strip().split(" ", 1)
                self.fields["first_name"].initial = parts[0]
                if len(parts) > 1 and not self.initial.get("last_name"):
                    self.fields["last_name"].initial = parts[1]

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if self.user and self.user.email.lower() == email:
            return email

        exclude_pk = self.user.pk if self.user else None
        if User.objects.filter(email__iexact=email).exclude(pk=exclude_pk).exists():
            raise ValidationError(_("An account with this email address already exists."))
        return email

    def save(self, commit=True):
        employee = super().save(commit=False)
        user = self.user or employee.user

        if user:
            full_name = employee.full_name
            if full_name:
                user.name = full_name
            email = self.cleaned_data.get("email")
            if email:
                user.email = email
            user.save(update_fields=["name", "email"])

        if commit:
            employee.save()
            # Also sync linked candidate if present
            linked_candidate = getattr(user, "candidate_profile", None)
            if linked_candidate:
                if employee.first_name:
                    linked_candidate.first_name = employee.first_name
                if employee.last_name:
                    linked_candidate.last_name = employee.last_name
                if employee.phone:
                    linked_candidate.phone = employee.phone
                if employee.date_of_birth:
                    linked_candidate.date_of_birth = employee.date_of_birth
                if employee.address:
                    linked_candidate.address = employee.address
                if employee.profile_photo:
                    linked_candidate.profile_photo = employee.profile_photo
                linked_candidate.save()

        return employee


# Kept for backward compatibility
EmployeeProfileForm = EmployeePersonalInfoForm


class EmployeeEducationForm(forms.ModelForm):
    """Form to add and edit employee educational background records."""

    class Meta:
        model = EmployeeEducation
        fields = [
            "degree",
            "institution",
            "university_board",
            "year_of_passing",
            "grade_percentage",
        ]
        widgets = {
            "degree": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., B.Tech Computer Science, MCA, B.Sc",
                    "required": "required",
                }
            ),
            "institution": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., National Institute of Technology, Model Engineering College",
                    "required": "required",
                }
            ),
            "university_board": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., APJ Abdul Kalam Technological University, CBSE, State Board",
                    "required": "required",
                }
            ),
            "year_of_passing": forms.NumberInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., 2022",
                    "min": 1960,
                    "max": 2035,
                    "required": "required",
                }
            ),
            "grade_percentage": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., 85% or 8.5 CGPA or First Class with Distinction",
                    "required": "required",
                }
            ),
        }

    def clean_year_of_passing(self):
        year = self.cleaned_data.get("year_of_passing")
        current_year = timezone.now().year + 5
        if year and (year < 1950 or year > current_year):
            raise ValidationError(f"Please enter a valid year between 1950 and {current_year}.")
        return year


class EmployeeExperienceForm(forms.ModelForm):
    """Form to add and edit employee work experience records."""

    class Meta:
        model = EmployeeExperience
        fields = [
            "company_name",
            "designation",
            "start_date",
            "end_date",
            "is_current",
            "responsibilities",
        ]
        widgets = {
            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Infosys, TCS, Global Solutions Inc.",
                    "required": "required",
                }
            ),
            "designation": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Software Engineer, Associate Developer",
                    "required": "required",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control custom-input",
                    "required": "required",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control custom-input",
                }
            ),
            "is_current": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "id": "id_is_current",
                }
            ),
            "responsibilities": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "Describe key job duties, projects handled, tech stack, and achievements...",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        is_current = cleaned_data.get("is_current")

        if is_current:
            cleaned_data["end_date"] = None
        elif not end_date:
            self.add_error("end_date", "Please provide an end date or check 'Currently Working Here'.")
        elif start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be earlier than start date.")

        return cleaned_data


class EmployeeDocumentForm(forms.ModelForm):
    """Form for employee to upload identity, educational, and professional documents."""

    class Meta:
        model = EmployeeDocument
        fields = ["document_type", "document"]
        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "document": forms.FileInput(
                attrs={
                    "class": "form-control custom-input",
                    "required": "required",
                    "accept": ".pdf,.doc,.docx,.jpg,.jpeg,.png",
                }
            ),
        }


class EmployeeWeeklyReportForm(forms.ModelForm):
    """Complete Weekly Performance Report Form for Employees."""

    class Meta:
        model = EmployeeReport
        fields = [
            "title",
            "week_start_date",
            "week_end_date",
            "progress_status",
            "work_summary",
            "tasks_completed",
            "achievements",
            "challenges",
            "challenges_handling",
            "pending_tasks",
            "next_week_plan",
            "skills_technologies_used",
            "additional_comments",
            "declaration_accepted",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Weekly Progress & Performance Report - Week 4",
                    "required": "required",
                }
            ),
            "week_start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control custom-input",
                    "required": "required",
                }
            ),
            "week_end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control custom-input",
                    "required": "required",
                }
            ),
            "progress_status": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "work_summary": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control custom-input",
                    "placeholder": "Comprehensive overview of primary tasks, key contributions, and overall weekly progress...",
                    "required": "required",
                }
            ),
            "tasks_completed": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control custom-input",
                    "placeholder": "• Implemented employee profile CRUD endpoints\n• Fixed authentication token refresh issue\n• Conducted code review for team modules...",
                    "required": "required",
                }
            ),
            "achievements": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "• Delivered sprint milestone 2 days ahead of schedule\n• Resolved high priority production bug #1042...",
                }
            ),
            "challenges": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "• Third-party API rate limiting caused testing delays\n• Missing specification for edge case reporting...",
                }
            ),
            "challenges_handling": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "• Implemented request throttling and local caching to mitigate API limits\n• Coordinated with Team Lead to clarify specifications...",
                }
            ),
            "pending_tasks": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "• Finalize automated integration test suite\n• Refactor legacy template styling...",
                }
            ),
            "next_week_plan": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "• Begin Phase 2 feature development\n• Coordinate with HR on department review meeting...",
                    "required": "required",
                }
            ),
            "skills_technologies_used": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Python, Django, PostgreSQL, Docker, Bootstrap 5, Git",
                }
            ),
            "additional_comments": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "form-control custom-input",
                    "placeholder": "Any other notes, support required from team lead/HR, or observations (optional)...",
                }
            ),
            "declaration_accepted": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "id": "id_declaration_accepted",
                }
            ),
        }

    def __init__(self, *args, employee=None, **kwargs):
        self.employee = employee
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("week_start_date")
        end = cleaned_data.get("week_end_date")

        if start and end:
            if start > end:
                self.add_error("week_end_date", "Week End Date cannot be earlier than Week Start Date.")

            if self.employee:
                qs = EmployeeReport.objects.filter(
                    employee=self.employee,
                    week_start_date=start,
                    week_end_date=end,
                )
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    self.add_error("week_start_date", f"A weekly report for period {start} to {end} already exists.")

        return cleaned_data


# Keep legacy alias for backward compatibility
EmployeeReportForm = EmployeeWeeklyReportForm


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control custom-input",
                "placeholder": "Enter your registered email address",
            },
        ),
    )


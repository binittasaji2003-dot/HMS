from django import forms
from django.contrib.auth import get_user_model
from .models import Employee, EmployeeReport, EmployeeDocument

User = get_user_model()


class EmployeeReportForm(forms.ModelForm):
    class Meta:
        model = EmployeeReport
        fields = [
            "title",
            "week_start_date",
            "week_end_date",
            "work_summary",
            "tasks_completed",
            "achievements",
            "challenges",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Weekly Work Report - Week 4",
            }),
            "week_start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "week_end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "work_summary": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Brief summary of your work this week...",
            }),
            "tasks_completed": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "List tasks completed...",
            }),
            "achievements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Key achievements or milestones (optional)...",
            }),
            "challenges": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Any blockers or challenges faced (optional)...",
            }),
        }


class EmployeeProfileForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Employee
        fields = ["profile_photo"]
        widgets = {
            "profile_photo": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["name"].initial = getattr(self.instance.user, "name", "")
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        employee = super().save(commit=commit)
        user = employee.user
        user.name = self.cleaned_data["name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return employee


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ["document_type", "document"]
        widgets = {
            "document_type": forms.Select(attrs={"class": "form-select"}),
            "document": forms.FileInput(attrs={"class": "form-control"}),
        }


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your registered email address",
        }),
    )


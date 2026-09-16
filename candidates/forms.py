from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Candidate, JobApplication

User = get_user_model()


class CandidateRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}),
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email Address"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
    )
    password_confirm = forms.CharField(
        label="Confirm Password",
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"}),
    )
    policy_agreement = forms.BooleanField(
        required=True,
        label="I agree to the terms and data privacy policy.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists. Please sign in.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned_data

    def save(self):
        first_name = self.cleaned_data["first_name"].strip()
        last_name = self.cleaned_data["last_name"].strip()
        email = self.cleaned_data["email"].strip().lower()
        phone = self.cleaned_data.get("phone", "").strip()
        password = self.cleaned_data["password"]
        policy_agreement = self.cleaned_data.get("policy_agreement", False)

        user = User.objects.create_user(
            email=email,
            password=password,
            name=f"{first_name} {last_name}".strip(),
            role=User.RoleChoices.CANDIDATE,
            is_active=True,
        )

        candidate = Candidate.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            policy_agreement=policy_agreement,
            profile_completed=False,
        )
        return candidate


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "phone",
            "address",
            "profile_photo",
            "resume",
            "id_proof",
            "tenth_certificate",
            "twelfth_certificate",
            "tenth_marklist",
            "twelfth_marklist",
            "policy_agreement",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "middle_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "profile_photo": forms.FileInput(attrs={"class": "form-control"}),
            "resume": forms.FileInput(attrs={"class": "form-control"}),
            "id_proof": forms.FileInput(attrs={"class": "form-control"}),
            "tenth_certificate": forms.FileInput(attrs={"class": "form-control"}),
            "twelfth_certificate": forms.FileInput(attrs={"class": "form-control"}),
            "tenth_marklist": forms.FileInput(attrs={"class": "form-control"}),
            "twelfth_marklist": forms.FileInput(attrs={"class": "form-control"}),
            "policy_agreement": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["applied_resume"]
        widgets = {
            "applied_resume": forms.FileInput(attrs={"class": "form-control"}),
        }


class JobApplicationSubmitForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter first name"}),
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter last name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter email address"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone number"}),
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    highest_education = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., B.Tech / MCA / B.Sc Computer Science"}),
    )
    experience = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Fresher, 1-2 years, 3+ years (Optional)"}),
    )
    resume = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.doc,.docx"}),
    )
    terms_agreement = forms.BooleanField(
        required=True,
        label="I declare that all provided details are accurate and agree to the recruitment terms and conditions.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def __init__(self, *args, candidate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate = candidate
        if candidate:
            user = getattr(candidate, "user", None)
            if user:
                first_name_init = candidate.first_name or (user.name.split()[0] if user.name else "")
                last_name_init = candidate.last_name or (" ".join(user.name.split()[1:]) if user.name and len(user.name.split()) > 1 else "")
                self.fields["first_name"].initial = first_name_init
                self.fields["last_name"].initial = last_name_init
                self.fields["email"].initial = user.email
            self.fields["phone"].initial = candidate.phone
            self.fields["date_of_birth"].initial = candidate.date_of_birth
            self.fields["terms_agreement"].initial = candidate.policy_agreement
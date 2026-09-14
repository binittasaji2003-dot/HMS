from django import forms

from .models import Candidate, JobApplication


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
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"})}


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["applied_resume"]
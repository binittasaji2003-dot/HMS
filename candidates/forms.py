"""Forms for Candidate profile, education, skills, and documents."""
from django import forms
from .models import Candidate, CandidateEducation, CandidateSkill, CandidateDocument, Application, Job
from .validators import validate_document_file


class CandidateProfileForm(forms.ModelForm):
    """Form for candidate personal details and preferences."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "candidate@example.com"}),
    )
    skills_comma = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Python, Django, PostgreSQL, REST API, HTML5, CSS3, JavaScript, Git",
            }
        ),
        help_text="Comma-separated skill list",
    )

    # Education: Degree
    degree_qualification = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Master of Computer Applications (MCA) or B.Tech CS"}),
    )
    degree_institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Cochin University of Science and Technology (CUSAT)"}),
    )
    degree_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 2024 - 2026 or 2026"}),
    )
    degree_percentage_or_cgpa = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 8.8 CGPA"}),
    )

    # Education: 12th
    twelfth_institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. St. Joseph's Higher Secondary School"}),
    )
    twelfth_board = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. State Board / CBSE"}),
    )
    twelfth_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 2021"}),
    )
    twelfth_percentage_or_cgpa = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 92.4%"}),
    )

    # Education: 10th
    tenth_institution = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Carmel English Medium School"}),
    )
    tenth_board = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. State Board / ICSE / CBSE"}),
    )
    tenth_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 2019"}),
    )
    tenth_percentage_or_cgpa = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 94.0%"}),
    )

    class Meta:
        model = Candidate
        fields = [
            "full_name",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "city",
            "state",
            "pincode",
            "experience_level",
            "preferred_job_type",
            "preferred_locations",
            "notice_period",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "phone": forms.TextInput(attrs={"class": "form-control", "type": "tel", "required": True}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date", "required": True}),
            "gender": forms.Select(attrs={"class": "form-select", "required": True}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "pincode": forms.TextInput(attrs={"class": "form-control"}),
            "experience_level": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_job_type": forms.TextInput(attrs={"class": "form-control"}),
            "preferred_locations": forms.TextInput(attrs={"class": "form-control"}),
            "notice_period": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.user:
                self.fields["email"].initial = self.instance.user.email

            # Populate comma-separated skills
            skills = list(self.instance.skills.values_list("skill_name", flat=True))
            if skills:
                self.fields["skills_comma"].initial = ", ".join(skills)

            # Populate Educations
            for edu in self.instance.educations.all():
                q = (edu.qualification_type or "").lower()
                if any(k in q for k in ["degree", "bachelor", "master", "mca", "b.sc", "b.tech", "btech", "m.tech", "be", "b.e"]):
                    self.fields["degree_qualification"].initial = edu.qualification_type
                    self.fields["degree_institution"].initial = edu.institution
                    self.fields["degree_year"].initial = edu.year
                    self.fields["degree_percentage_or_cgpa"].initial = edu.percentage_or_cgpa
                elif any(k in q for k in ["12th", "higher secondary", "hsc", "plus two", "+2", "intermediate"]):
                    self.fields["twelfth_institution"].initial = edu.institution
                    self.fields["twelfth_board"].initial = edu.board_or_university
                    self.fields["twelfth_year"].initial = edu.year
                    self.fields["twelfth_percentage_or_cgpa"].initial = edu.percentage_or_cgpa
                elif ("10th" in q or "sslc" in q or "matric" in q or ("secondary" in q and "higher" not in q)):
                    self.fields["tenth_institution"].initial = edu.institution
                    self.fields["tenth_board"].initial = edu.board_or_university
                    self.fields["tenth_year"].initial = edu.year
                    self.fields["tenth_percentage_or_cgpa"].initial = edu.percentage_or_cgpa

    def save(self, commit=True):
        candidate = super().save(commit=commit)
        email = self.cleaned_data.get("email")
        if email and candidate.user and candidate.user.email != email:
            candidate.user.email = email
            candidate.user.save(update_fields=["email"])

        # Sync skills
        skills_raw = self.cleaned_data.get("skills_comma", "")
        if skills_raw is not None:
            skill_names = [s.strip() for s in skills_raw.split(",") if s.strip()]
            # Remove deleted
            candidate.skills.exclude(skill_name__in=skill_names).delete()
            # Add new
            existing = set(candidate.skills.values_list("skill_name", flat=True))
            for name in skill_names:
                if name not in existing:
                    CandidateSkill.objects.create(candidate=candidate, skill_name=name)

        # Sync Educations
        self._sync_education(
            candidate,
            check_func=lambda q: any(k in q for k in ["degree", "mca", "b.sc", "bachelor", "master"]),
            default_qual=self.cleaned_data.get("degree_qualification") or "Master of Computer Applications (MCA)",
            inst=self.cleaned_data.get("degree_institution"),
            board="",
            year=self.cleaned_data.get("degree_year"),
            score=self.cleaned_data.get("degree_percentage_or_cgpa"),
        )
        self._sync_education(
            candidate,
            check_func=lambda q: any(k in q for k in ["12th", "higher secondary", "hsc", "plus two", "+2"]),
            default_qual="Higher Secondary (12th)",
            inst=self.cleaned_data.get("twelfth_institution"),
            board=self.cleaned_data.get("twelfth_board"),
            year=self.cleaned_data.get("twelfth_year"),
            score=self.cleaned_data.get("twelfth_percentage_or_cgpa"),
        )
        self._sync_education(
            candidate,
            check_func=lambda q: ("10th" in q or "sslc" in q or "matric" in q or ("secondary" in q and "higher" not in q and "12" not in q)),
            default_qual="Secondary School Leaving Certificate (10th)",
            inst=self.cleaned_data.get("tenth_institution"),
            board=self.cleaned_data.get("tenth_board"),
            year=self.cleaned_data.get("tenth_year"),
            score=self.cleaned_data.get("tenth_percentage_or_cgpa"),
        )

        # Recalculate profile completion dynamically
        candidate.update_profile_completion()
        return candidate

    def _sync_education(self, candidate, check_func, default_qual, inst, board, year, score):
        if not inst and not year and not score:
            return  # Empty entry

        matched_edu = None
        for edu in candidate.educations.all():
            q = (edu.qualification_type or "").lower()
            if check_func(q):
                matched_edu = edu
                break


        if matched_edu:
            matched_edu.qualification_type = default_qual
            matched_edu.institution = inst or matched_edu.institution
            matched_edu.board_or_university = board or matched_edu.board_or_university
            matched_edu.year = year or matched_edu.year
            matched_edu.percentage_or_cgpa = score or matched_edu.percentage_or_cgpa
            matched_edu.save()
        else:
            CandidateEducation.objects.create(
                candidate=candidate,
                qualification_type=default_qual,
                institution=inst or "Institution",
                board_or_university=board or "",
                year=year or "",
                percentage_or_cgpa=score or "",
            )


class CandidateEducationForm(forms.ModelForm):
    class Meta:
        model = CandidateEducation
        fields = ["qualification_type", "institution", "board_or_university", "year", "percentage_or_cgpa"]
        widgets = {
            "qualification_type": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "institution": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "board_or_university": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.TextInput(attrs={"class": "form-control", "required": True}),
            "percentage_or_cgpa": forms.TextInput(attrs={"class": "form-control", "required": True}),
        }


class CandidateSkillForm(forms.ModelForm):
    class Meta:
        model = CandidateSkill
        fields = ["skill_name"]
        widgets = {
            "skill_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Django", "required": True}),
        }


class DocumentUploadForm(forms.Form):
    """Form to securely upload or replace a candidate document."""
    DOCUMENT_CHOICES = [
        (item[0], item[1]) for item in CandidateDocument.DOCUMENT_DEFINITIONS
    ]
    document_type = forms.ChoiceField(
        choices=DOCUMENT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "documentTypeSelect"}),
    )
    document_file = forms.FileField(
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={"class": "form-control", "id": "documentFileInput"}),
    )


class JobApplicationForm(forms.ModelForm):
    """Form for candidate job applications."""
    custom_resume = forms.FileField(
        required=False,
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={"class": "form-control", "id": "customResumeInput"}),
    )

    class Meta:
        model = Application
        fields = ["cover_note"]
        widgets = {
            "cover_note": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 4,
                    "placeholder": "Describe your relevant Python projects, Django experience, or any key achievements...",
                }
            ),
        }


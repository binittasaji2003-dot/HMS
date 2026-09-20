import os
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Candidate, CandidateEducation, JobApplication

User = get_user_model()


def validate_file_extension_and_size(file_obj, allowed_extensions, max_size_mb=10, label="File"):
    if not file_obj:
        return
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in allowed_extensions:
        allowed_str = ", ".join(allowed_extensions)
        raise ValidationError(f"{label} format not supported. Allowed formats: {allowed_str}")
    if file_obj.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"{label} size exceeds {max_size_mb}MB limit.")


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
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "First Name"}),
    )
    middle_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Middle Name (Optional)"}),
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Last Name"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. +91 9876543210"}),
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Current Residential Address"}),
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "State / Province"}),
    )
    country = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Country"}),
    )
    skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Python, Django, SQL, React"}),
        help_text="Comma-separated skills list",
    )

    # 10th Details
    tenth_board = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CBSE / ICSE / State Board"}),
    )
    tenth_school = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "School name"}),
    )
    tenth_percentage = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 88% or 9.2 CGPA"}),
    )
    tenth_passing_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Passing Year (e.g. 2018)"}),
    )

    # 12th Details
    twelfth_board = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CBSE / ISC / State Board"}),
    )
    twelfth_school = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Junior college / High school"}),
    )
    twelfth_stream = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Select Stream"),
            ("Science", "Science (PCM / PCB)"),
            ("Computer Science", "Computer Science"),
            ("Commerce", "Commerce"),
            ("Humanities", "Humanities / Arts"),
            ("Other", "Other"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    twelfth_percentage = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 85% or 8.8 CGPA"}),
    )
    twelfth_passing_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Passing Year (e.g. 2020)"}),
    )

    # Experience
    is_fresher = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_is_fresher"}),
    )
    total_experience_years = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "50"}),
    )
    total_experience_months = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "11"}),
    )
    current_employment_status = forms.ChoiceField(
        required=False,
        choices=[
            ("Currently Employed", "Currently Employed"),
            ("Not Currently Employed", "Not Currently Employed"),
            ("Self Employed", "Self Employed"),
            ("Internship", "Internship"),
            ("Other", "Other"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    current_organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Company / Organization Name"}),
    )
    current_designation = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Current Job Title"}),
    )
    joining_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    class Meta:
        model = Candidate
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "phone",
            "address",
            "state",
            "country",
            "skills",
            "profile_photo",
            "resume",
            "id_proof",
            "tenth_board",
            "tenth_school",
            "tenth_percentage",
            "tenth_passing_year",
            "tenth_certificate",
            "twelfth_board",
            "twelfth_school",
            "twelfth_stream",
            "twelfth_percentage",
            "twelfth_passing_year",
            "twelfth_certificate",
            "is_fresher",
            "total_experience_years",
            "total_experience_months",
            "current_employment_status",
            "current_organization",
            "current_designation",
            "joining_date",
            "policy_agreement",
        ]
        widgets = {
            "profile_photo": forms.FileInput(attrs={"class": "form-control", "accept": "image/jpeg,image/png,image/jpg"}),
            "resume": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.doc,.docx"}),
            "id_proof": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}),
            "tenth_certificate": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}),
            "twelfth_certificate": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}),
            "policy_agreement": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if photo and hasattr(photo, "size"):
            validate_file_extension_and_size(photo, [".jpg", ".jpeg", ".png"], max_size_mb=5, label="Profile Photo")
        return photo

    def clean_resume(self):
        resume = self.cleaned_data.get("resume")
        if resume and hasattr(resume, "size"):
            validate_file_extension_and_size(resume, [".pdf", ".doc", ".docx"], max_size_mb=10, label="Resume")
        return resume

    def clean_tenth_certificate(self):
        cert = self.cleaned_data.get("tenth_certificate")
        if cert and hasattr(cert, "size"):
            validate_file_extension_and_size(cert, [".pdf", ".jpg", ".jpeg", ".png"], max_size_mb=10, label="10th Certificate")
        return cert

    def clean_twelfth_certificate(self):
        cert = self.cleaned_data.get("twelfth_certificate")
        if cert and hasattr(cert, "size"):
            validate_file_extension_and_size(cert, [".pdf", ".jpg", ".jpeg", ".png"], max_size_mb=10, label="12th Certificate")
        return cert


class CandidateEducationForm(forms.ModelForm):
    class Meta:
        model = CandidateEducation
        fields = [
            "education_level",
            "degree_program",
            "field_of_study",
            "institution",
            "university_board",
            "education_status",
            "completion_year",
            "percentage_or_cgpa",
            "certificate",
        ]
        widgets = {
            "education_level": forms.Select(attrs={"class": "form-select"}),
            "degree_program": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. BCA, MCA, B.Tech, B.Sc"}),
            "field_of_study": forms.Select(attrs={"class": "form-select"}),
            "institution": forms.TextInput(attrs={"class": "form-control", "placeholder": "College / Institute Name"}),
            "university_board": forms.TextInput(attrs={"class": "form-control", "placeholder": "University / Affiliated Body"}),
            "education_status": forms.Select(attrs={"class": "form-select"}),
            "completion_year": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Graduation Year (e.g. 2026)"}),
            "percentage_or_cgpa": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 8.5 CGPA or 82%"}),
            "certificate": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}),
        }

    def clean_certificate(self):
        cert = self.cleaned_data.get("certificate")
        if cert and hasattr(cert, "size"):
            validate_file_extension_and_size(cert, [".pdf", ".jpg", ".jpeg", ".png"], max_size_mb=10, label="Degree Certificate")
        return cert


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["applied_resume"]
        widgets = {
            "applied_resume": forms.FileInput(attrs={"class": "form-control"}),
        }


class JobApplicationSubmitForm(forms.Form):
    YES_NO_CHOICES = [
        ("", "Select"),
        ("Yes", "Yes"),
        ("No", "No"),
    ]

    INFORMATION_SOURCES = [
        ("PROFILE", "Use My Profile"),
        ("RESUME", "Autofill From Resume"),
        ("MANUAL", "Enter Manually"),
    ]

    information_source = forms.ChoiceField(
        choices=INFORMATION_SOURCES,
        initial="PROFILE",
        required=False,
    )

    # 1. Personal Information
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_first_name", "placeholder": "First Name"}),
    )
    middle_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_middle_name", "placeholder": "Middle Name (Optional)"}),
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_last_name", "placeholder": "Last Name"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "id": "id_email", "placeholder": "Email Address"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_phone", "placeholder": "Phone Number"}),
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control", "id": "id_date_of_birth"}),
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "id": "id_address", "rows": 2, "placeholder": "Residential Address"}),
    )
    current_state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_current_state", "placeholder": "State / Province"}),
    )
    current_country = forms.CharField(
        max_length=100,
        required=False,
        initial="India",
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_current_country", "placeholder": "Country"}),
    )

    # 2. 10th Standard Education
    tenth_board = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_tenth_board", "placeholder": "e.g. CBSE / ICSE / State Board"}),
    )
    tenth_school = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_tenth_school", "placeholder": "School Name"}),
    )
    tenth_percentage = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_tenth_percentage", "placeholder": "e.g. 88% or 9.2 CGPA"}),
    )
    tenth_passing_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_tenth_passing_year", "placeholder": "e.g. 2018"}),
    )

    # 3. 12th Standard Education
    twelfth_board = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_twelfth_board", "placeholder": "e.g. CBSE / ISC / State Board"}),
    )
    twelfth_school = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_twelfth_school", "placeholder": "Junior College / High School"}),
    )
    twelfth_stream = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Select Stream"),
            ("Science", "Science (PCM / PCB)"),
            ("Computer Science", "Computer Science"),
            ("Commerce", "Commerce"),
            ("Humanities", "Humanities / Arts"),
            ("Other", "Other"),
        ],
        widget=forms.Select(attrs={"class": "form-select", "id": "id_twelfth_stream"}),
    )
    twelfth_percentage = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_twelfth_percentage", "placeholder": "e.g. 85% or 8.8 CGPA"}),
    )
    twelfth_passing_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_twelfth_passing_year", "placeholder": "e.g. 2020"}),
    )

    # 4. Higher Education
    education_level = forms.ChoiceField(
        required=False,
        choices=[("", "Select Education Level")] + CandidateEducation.EDUCATION_LEVELS,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_education_level"}),
    )
    degree_program = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_degree_program", "placeholder": "e.g. BCA, B.Tech, MCA, B.Sc"}),
    )
    field_of_study = forms.ChoiceField(
        required=False,
        choices=[("", "Select Field of Study")] + CandidateEducation.FIELD_OF_STUDY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_field_of_study"}),
    )
    institution = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_institution", "placeholder": "College / Institute Name"}),
    )
    university_board = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_university_board", "placeholder": "University / Board Name"}),
    )
    education_status = forms.ChoiceField(
        required=False,
        choices=[("", "Select Status")] + CandidateEducation.EDUCATION_STATUSES,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_education_status"}),
    )
    completion_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_completion_year", "placeholder": "Passing Year (e.g. 2024)"}),
    )
    percentage_or_cgpa = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_percentage_or_cgpa", "placeholder": "e.g. 8.5 CGPA or 85%"}),
    )
    higher_education_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_higher_education_json"}),
    )

    # 5. Experience Details
    is_fresher = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=False,
        initial="Yes",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_is_fresher_select"}),
    )
    total_experience_years = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_total_experience_years", "min": "0", "max": "50"}),
    )
    total_experience_months = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_total_experience_months", "min": "0", "max": "11"}),
    )
    current_organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_current_organization", "placeholder": "Current Organization"}),
    )
    current_designation = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_current_designation", "placeholder": "Current Designation"}),
    )
    notice_period_days = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_notice_period_days", "placeholder": "Notice period in days (e.g. 30)"}),
    )

    # 6. Additional Application Questions
    is_currently_employed = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=False,
        initial="No",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_is_currently_employed_select"}),
    )
    willing_to_relocate = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=False,
        initial="Yes",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_willing_to_relocate_select"}),
    )
    is_past_employee = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=False,
        initial="No",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_is_past_employee_select"}),
    )
    past_employee_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_past_employee_id", "placeholder": "Previous Employee ID"}),
    )
    past_designation = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_past_designation", "placeholder": "Previous Designation"}),
    )
    past_employment_period = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_past_employment_period", "placeholder": "e.g. Jan 2022 - Dec 2023"}),
    )
    legally_authorized = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=False,
        initial="Yes",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_legally_authorized_select"}),
    )
    requires_visa_sponsorship = forms.ChoiceField(
        choices=YES_NO_CHOICES,
        required=False,
        initial="No",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_requires_visa_select"}),
    )
    visa_status = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_visa_status", "placeholder": "Visa Status / Type"}),
    )

    # 7. Compensation & Skills
    current_salary = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_current_salary", "placeholder": "Current CTC (Optional)"}),
    )
    expected_salary = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_expected_salary", "placeholder": "e.g. 600000", "min": "0"}),
    )
    applied_skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "id_applied_skills", "placeholder": "e.g. Python, Django, PostgreSQL, REST APIs"}),
        help_text="Primary technical and domain skills",
    )
    available_joining_days = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_available_joining_days", "placeholder": "Days to join (e.g. 15 or 30)"}),
    )
    why_interested = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "id": "id_why_interested", "rows": 2, "placeholder": "Statement of interest / Notes"}),
    )

    # 8. Documents & Final Declaration
    resume = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"class": "form-control", "id": "id_resume_file", "accept": ".pdf,.doc,.docx"}),
    )
    terms_agreement = forms.BooleanField(
        required=True,
        label="I confirm that all information provided in this application is accurate.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_terms_agreement"}),
    )

    def __init__(self, *args, candidate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate = candidate
        if candidate and not self.is_bound:
            user = getattr(candidate, "user", None)
            if user:
                first_name_init = candidate.first_name or (user.name.split()[0] if user.name else "")
                last_name_init = candidate.last_name or (" ".join(user.name.split()[1:]) if user.name and len(user.name.split()) > 1 else "")
                self.fields["first_name"].initial = first_name_init
                self.fields["middle_name"].initial = candidate.middle_name or ""
                self.fields["last_name"].initial = last_name_init
                self.fields["email"].initial = user.email
            self.fields["phone"].initial = candidate.phone
            self.fields["date_of_birth"].initial = candidate.date_of_birth
            self.fields["address"].initial = candidate.address
            self.fields["current_state"].initial = candidate.state
            self.fields["current_country"].initial = candidate.country or "India"

            # 10th
            self.fields["tenth_board"].initial = candidate.tenth_board
            self.fields["tenth_school"].initial = candidate.tenth_school
            self.fields["tenth_percentage"].initial = candidate.tenth_percentage
            self.fields["tenth_passing_year"].initial = candidate.tenth_passing_year

            # 12th
            self.fields["twelfth_board"].initial = candidate.twelfth_board
            self.fields["twelfth_school"].initial = candidate.twelfth_school
            self.fields["twelfth_stream"].initial = candidate.twelfth_stream
            self.fields["twelfth_percentage"].initial = candidate.twelfth_percentage
            self.fields["twelfth_passing_year"].initial = candidate.twelfth_passing_year

            # Highest education
            highest_edu = candidate.highest_education_record
            if highest_edu:
                self.fields["education_level"].initial = highest_edu.education_level
                self.fields["degree_program"].initial = highest_edu.degree_program
                self.fields["field_of_study"].initial = highest_edu.field_of_study
                self.fields["institution"].initial = highest_edu.institution
                self.fields["university_board"].initial = highest_edu.university_board
                self.fields["education_status"].initial = highest_edu.education_status
                self.fields["completion_year"].initial = highest_edu.completion_year
                self.fields["percentage_or_cgpa"].initial = highest_edu.percentage_or_cgpa

            # Experience & skills
            self.fields["applied_skills"].initial = candidate.skills
            self.fields["is_fresher"].initial = "Yes" if candidate.is_fresher else "No"
            self.fields["total_experience_years"].initial = candidate.total_experience_years
            self.fields["total_experience_months"].initial = candidate.total_experience_months
            self.fields["current_organization"].initial = candidate.current_organization
            self.fields["current_designation"].initial = candidate.current_designation
            self.fields["terms_agreement"].initial = candidate.policy_agreement

    def get_bool(self, field_name, default=False):
        val = self.cleaned_data.get(field_name)
        if val in ["Yes", "yes", True, "true", "True", 1, "1"]:
            return True
        if val in ["No", "no", False, "false", "False", 0, "0"]:
            return False
        return default

    def clean_resume(self):
        resume = self.cleaned_data.get("resume")
        if resume and hasattr(resume, "size"):
            validate_file_extension_and_size(resume, [".pdf", ".doc", ".docx"], max_size_mb=10, label="Resume")
        return resume
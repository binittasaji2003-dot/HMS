from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from admin_module.models import Department
from candidates.models import Candidate
from employees.models import (
    Employee,
    EmployeeDocument,
    EmployeeReport,
    PerformanceReview as EmployeePerformanceReview,
)
from hr.models import (
    HRDocument,
    HREducation,
    HRExperience,
    HRManager,
    HRPerformanceReview,
    HRWeeklyReport,
)

User = get_user_model()


class HRProfileEditForm(forms.ModelForm):
    """Form to edit personal information and experience status for HR Manager profile."""

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

    class Meta:
        model = HRManager
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "phone",
            "address",
            "city",
            "state",
            "pincode",
            "profile_photo",
            "has_no_experience",
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
            "address": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "Enter street address, building, apartment...",
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
            "has_no_experience": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "id": "id_has_no_experience",
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
        hr_manager = super().save(commit=False)
        user = self.user or hr_manager.user

        # Synchronize User model
        if user:
            full_name = hr_manager.full_name
            if full_name:
                user.name = full_name
            email = self.cleaned_data.get("email")
            if email:
                user.email = email
            user.save(update_fields=["name", "email"])

        if commit:
            hr_manager.save()
            hr_manager.update_profile_completion_status()

            # Sync linked candidate and employee photo/details if present
            linked_employee = getattr(user, "employee_profile", None)
            if linked_employee and hr_manager.profile_photo:
                linked_employee.profile_photo = hr_manager.profile_photo
                linked_employee.save(update_fields=["profile_photo"])

            linked_candidate = getattr(user, "candidate_profile", None)
            if linked_candidate:
                if hr_manager.first_name:
                    linked_candidate.first_name = hr_manager.first_name
                if hr_manager.last_name:
                    linked_candidate.last_name = hr_manager.last_name
                if hr_manager.phone:
                    linked_candidate.phone = hr_manager.phone
                if hr_manager.date_of_birth:
                    linked_candidate.date_of_birth = hr_manager.date_of_birth
                if hr_manager.address:
                    linked_candidate.address = hr_manager.address
                if hr_manager.profile_photo:
                    linked_candidate.profile_photo = hr_manager.profile_photo
                linked_candidate.save()

        return hr_manager


class HREducationForm(forms.ModelForm):
    """Form to add and edit HR educational background records."""

    class Meta:
        model = HREducation
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
                    "placeholder": "e.g., MBA Human Resource Management, B.Tech CS, BBA",
                    "required": "required",
                }
            ),
            "institution": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., National Institute of Technology, St. Teresa's College",
                    "required": "required",
                }
            ),
            "university_board": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., APJ Abdul Kalam Technological University, CBSE",
                    "required": "required",
                }
            ),
            "year_of_passing": forms.NumberInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., 2021",
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


class HRExperienceForm(forms.ModelForm):
    """Form to add and edit HR work experience records."""

    class Meta:
        model = HRExperience
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
                    "placeholder": "e.g., Infosys, TCS, Global Tech Solutions",
                    "required": "required",
                }
            ),
            "designation": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Senior HR Associate, Talent Acquisition Specialist",
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
                    "placeholder": "Describe key job duties, recruitment milestones, team leadership, etc.",
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


class HRDocumentUploadForm(forms.ModelForm):
    """Form for HR Manager to upload identity, educational, and professional documents."""

    class Meta:
        model = HRDocument
        fields = ["document_type", "title", "document_file"]
        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Degree Certificate / Aadhaar Card / Offer Letter",
                }
            ),
            "document_file": forms.FileInput(
                attrs={
                    "class": "form-control custom-input",
                    "required": "required",
                    "accept": ".pdf,.doc,.docx,.jpg,.jpeg,.png",
                }
            ),
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


class JobVacancyForm(forms.ModelForm):
    """Form for HR to create and manage Job Vacancies / Postings."""

    class Meta:
        from candidates.models import JobVacancy
        model = JobVacancy
        fields = [
            "title",
            "role_designation",
            "department",
            "description",
            "responsibilities",
            "skills_required",
            "preferred_skills",
            "qualifications",
            "minimum_qualification",
            "required_field_of_study",
            "graduation_year_min",
            "graduation_year_max",
            "experience_required_bool",
            "minimum_experience",
            "maximum_experience",
            "employment_type",
            "location",
            "state",
            "country",
            "work_mode",
            "number_of_openings",
            "closing_date",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Senior Full Stack Python Developer",
                    "required": "required",
                }
            ),
            "role_designation": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Software Engineer, Tech Lead, HR Associate",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control custom-input",
                    "placeholder": "Describe the position, mission, team context, and key objectives...",
                    "required": "required",
                }
            ),
            "responsibilities": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "form-control custom-input",
                    "placeholder": "- Design and implement scalable services\n- Participate in agile sprints\n- Mentor junior team members...",
                }
            ),
            "skills_required": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "Python, Django, PostgreSQL, REST APIs, Git (comma-separated)",
                    "required": "required",
                }
            ),
            "preferred_skills": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "Docker, Kubernetes, AWS, Redis, Celery (comma-separated)",
                }
            ),
            "qualifications": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control custom-input",
                    "placeholder": "B.Tech/BE/MCA/BCA in Computer Science or related IT field...",
                }
            ),
            "minimum_qualification": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "required_field_of_study": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                }
            ),
            "graduation_year_min": forms.NumberInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., 2020",
                    "min": 1980,
                    "max": 2035,
                }
            ),
            "graduation_year_max": forms.NumberInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., 2026",
                    "min": 1980,
                    "max": 2035,
                }
            ),
            "experience_required_bool": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "id": "id_experience_required_bool",
                }
            ),
            "minimum_experience": forms.NumberInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "0",
                    "min": 0,
                    "step": 0.5,
                }
            ),
            "maximum_experience": forms.NumberInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "Optional max years",
                    "min": 0,
                    "step": 0.5,
                }
            ),
            "employment_type": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Bangalore, Kochi, Mumbai",
                    "required": "required",
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "e.g., Karnataka, Kerala, Maharashtra",
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control custom-input",
                    "placeholder": "India",
                }
            ),
            "work_mode": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                    "required": "required",
                }
            ),
            "number_of_openings": forms.NumberInput(
                attrs={
                    "class": "form-control custom-input",
                    "min": 1,
                    "required": "required",
                }
            ),
            "closing_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control custom-input",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select custom-input",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        exp_required = cleaned_data.get("experience_required_bool")
        min_exp = cleaned_data.get("minimum_experience")
        max_exp = cleaned_data.get("maximum_experience")
        grad_min = cleaned_data.get("graduation_year_min")
        grad_max = cleaned_data.get("graduation_year_max")
        closing_date = cleaned_data.get("closing_date")
        status = cleaned_data.get("status")

        # Experience validation
        if not exp_required:
            cleaned_data["minimum_experience"] = 0.0
            cleaned_data["maximum_experience"] = None
        else:
            if min_exp is None or min_exp < 0:
                self.add_error("minimum_experience", "Please specify a valid minimum years of experience.")
            if max_exp is not None and min_exp is not None and max_exp < min_exp:
                self.add_error("maximum_experience", "Maximum experience cannot be less than minimum experience.")

        # Graduation year validation
        if grad_min and grad_max and grad_max < grad_min:
            self.add_error("graduation_year_max", "Maximum graduation year cannot be earlier than minimum graduation year.")

        # Closing date validation
        if closing_date:
            today = timezone.localdate()
            if closing_date < today and status == "OPEN":
                self.add_error("closing_date", f"Deadline cannot be in the past (must be on or after {today}).")

        # Format experience_required summary string
        if not exp_required or (cleaned_data.get("minimum_experience", 0) == 0 and not cleaned_data.get("maximum_experience")):
            cleaned_data["experience_required"] = "Fresher / No Experience Required"
        elif cleaned_data.get("maximum_experience"):
            cleaned_data["experience_required"] = f"{cleaned_data['minimum_experience']:g} - {cleaned_data['maximum_experience']:g} Years"
        else:
            cleaned_data["experience_required"] = f"{cleaned_data.get('minimum_experience', 0):g}+ Years"

        return cleaned_data


class HRWeeklyReportForm(forms.ModelForm):
    class Meta:
        model = HRWeeklyReport
        fields = [
            "week_start_date",
            "week_end_date",
            "work_summary",
            "tasks_completed",
            "achievements",
            "challenges",
            "pending_tasks",
            "next_week_plan",
            "vacancies_worked",
            "candidates_screened",
            "candidates_shortlisted",
            "aptitude_tests",
            "interviews",
            "candidates_selected",
        ]
        widgets = {
            "week_start_date": forms.DateInput(attrs={"type": "date", "class": "form-control custom-input"}),
            "week_end_date": forms.DateInput(attrs={"type": "date", "class": "form-control custom-input"}),
            "work_summary": forms.Textarea(attrs={"rows": 4, "class": "form-control custom-input", "placeholder": "Overview of your primary focus, responsibilities, and key initiatives this week..."}),
            "tasks_completed": forms.Textarea(attrs={"rows": 4, "class": "form-control custom-input", "placeholder": "• Screened candidate resumes\n• Scheduled interviews\n• Coordinated aptitude tests..."}),
            "achievements": forms.Textarea(attrs={"rows": 3, "class": "form-control custom-input", "placeholder": "• Completed screening for assigned vacancies\n• Updated recruitment records..."}),
            "challenges": forms.Textarea(attrs={"rows": 3, "class": "form-control custom-input", "placeholder": "• Delayed candidate responses\n• Interview rescheduling..."}),
            "pending_tasks": forms.Textarea(attrs={"rows": 3, "class": "form-control custom-input", "placeholder": "• Follow up with remaining candidates..."}),
            "next_week_plan": forms.Textarea(attrs={"rows": 3, "class": "form-control custom-input", "placeholder": "• Complete pending candidate follow-ups\n• Schedule remaining interviews..."}),
            "vacancies_worked": forms.NumberInput(attrs={"class": "form-control custom-input", "min": "0"}),
            "candidates_screened": forms.NumberInput(attrs={"class": "form-control custom-input", "min": "0"}),
            "candidates_shortlisted": forms.NumberInput(attrs={"class": "form-control custom-input", "min": "0"}),
            "aptitude_tests": forms.NumberInput(attrs={"class": "form-control custom-input", "min": "0"}),
            "interviews": forms.NumberInput(attrs={"class": "form-control custom-input", "min": "0"}),
            "candidates_selected": forms.NumberInput(attrs={"class": "form-control custom-input", "min": "0"}),
        }

    def __init__(self, *args, hr_manager=None, **kwargs):
        self.hr_manager = hr_manager
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("week_start_date")
        end = cleaned_data.get("week_end_date")

        if start and end:
            if start > end:
                self.add_error("week_end_date", "Week End Date cannot be earlier than Week Start Date.")
            
            if self.hr_manager:
                qs = HRWeeklyReport.objects.filter(
                    hr_manager=self.hr_manager,
                    week_start_date=start,
                    week_end_date=end,
                )
                if self.instance and self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    self.add_error("week_start_date", f"A weekly report for {start} to {end} already exists.")

        return cleaned_data


class HRPerformanceReviewForm(forms.ModelForm):
    status_decision = forms.ChoiceField(
        choices=[("REVIEWED", "Mark as Reviewed & Approved"), ("NEEDS_IMPROVEMENT", "Return for Improvement")],
        widget=forms.Select(attrs={"class": "form-select custom-input"}),
        initial="REVIEWED",
    )

    class Meta:
        model = HRPerformanceReview
        fields = [
            "task_completion", "task_completion_remarks",
            "quality_of_work", "quality_of_work_remarks",
            "recruitment_coordination", "recruitment_coordination_remarks",
            "timeliness", "timeliness_remarks",
            "documentation", "documentation_remarks",
            "communication", "communication_remarks",
            "problem_solving", "problem_solving_remarks",
            "weekly_goal_achievement", "weekly_goal_achievement_remarks",
            "overall_feedback",
            "strengths",
            "areas_for_improvement",
            "recommendations",
            "next_week_expectations",
        ]
        widgets = {
            "task_completion": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "task_completion"}),
            "quality_of_work": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "quality_of_work"}),
            "recruitment_coordination": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "recruitment_coordination"}),
            "timeliness": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "timeliness"}),
            "documentation": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "documentation"}),
            "communication": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "communication"}),
            "problem_solving": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "problem_solving"}),
            "weekly_goal_achievement": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "weekly_goal_achievement"}),
            "task_completion_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Completed assigned tasks on time"}),
            "quality_of_work_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., High quality and accuracy"}),
            "recruitment_coordination_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Well coordinated candidate interactions"}),
            "timeliness_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Reports and schedules delivered promptly"}),
            "documentation_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Maintained thorough documentation"}),
            "communication_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Clear and effective communication"}),
            "problem_solving_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Handled scheduling conflicts proactively"}),
            "weekly_goal_achievement_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Met all key target deliverables"}),
            "overall_feedback": forms.Textarea(attrs={"rows": 3, "class": "form-control custom-input", "placeholder": "Overall feedback on performance during this week..."}),
            "strengths": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Key observed strengths and positive contributions..."}),
            "areas_for_improvement": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Identified areas requiring attention or refinement..."}),
            "recommendations": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Actionable recommendations and guidance..."}),
            "next_week_expectations": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Specific goals and expectations for next week..."}),
        }


class EmployeePerformanceEvaluationForm(forms.ModelForm):
    """Form for HR to evaluate Employee weekly reports with 8-criteria rating matrix."""

    status_decision = forms.ChoiceField(
        choices=[
            ("REVIEWED", "Approve & Mark as Reviewed"),
            ("NEEDS_CORRECTION", "Request Correction / Needs Revision"),
        ],
        widget=forms.Select(attrs={"class": "form-select custom-input", "id": "id_status_decision"}),
        initial="REVIEWED",
    )

    class Meta:
        model = EmployeePerformanceReview
        fields = [
            "task_completion", "task_completion_remarks",
            "quality_of_work", "quality_of_work_remarks",
            "technical_skills", "technical_skills_remarks",
            "problem_solving", "problem_solving_remarks",
            "timeliness", "timeliness_remarks",
            "team_collaboration", "team_collaboration_remarks",
            "communication", "communication_remarks",
            "goal_achievement", "goal_achievement_remarks",
            "overall_feedback",
            "strengths",
            "areas_for_improvement",
            "recommendations",
            "next_week_expectations",
        ]
        widgets = {
            "task_completion": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "task_completion"}),
            "quality_of_work": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "quality_of_work"}),
            "technical_skills": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "technical_skills"}),
            "problem_solving": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "problem_solving"}),
            "timeliness": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "timeliness"}),
            "team_collaboration": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "team_collaboration"}),
            "communication": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "communication"}),
            "goal_achievement": forms.Select(attrs={"class": "form-select matrix-rating", "data-criterion": "goal_achievement"}),
            "task_completion_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Successfully closed all planned sprint items"}),
            "quality_of_work_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Code clean, tested and well documented"}),
            "technical_skills_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Strong grasp of tech stack and design principles"}),
            "problem_solving_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Effectively debugged difficult async race conditions"}),
            "timeliness_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Met all deadlines punctually"}),
            "team_collaboration_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Great teamwork and supportive during code reviews"}),
            "communication_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Clear updates in standups and weekly reports"}),
            "goal_achievement_remarks": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Exceeded weekly delivery targets"}),
            "overall_feedback": forms.Textarea(attrs={"rows": 3, "class": "form-control custom-input", "placeholder": "Comprehensive feedback on performance this week..."}),
            "strengths": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Key observed technical and interpersonal strengths..."}),
            "areas_for_improvement": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Targeted areas requiring growth or fine-tuning..."}),
            "recommendations": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Actionable steps or learning resources suggested..."}),
            "next_week_expectations": forms.Textarea(attrs={"rows": 2, "class": "form-control custom-input", "placeholder": "Specific deliverables and goals for the upcoming week..."}),
        }





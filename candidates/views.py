from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CandidateProfileForm, JobApplicationForm
from .models import Candidate, JobApplication, JobVacancy


def _candidate_for(user):
	first_name, _, last_name = (getattr(user, "name", "") or "").partition(" ")
	candidate, _ = Candidate.objects.get_or_create(
		user=user,
		defaults={
			"first_name": first_name or "Candidate",
			"last_name": last_name or first_name or "User",
		},
	)
	return candidate


@login_required
def dashboard(request):
	candidate = _candidate_for(request.user)
	applications = candidate.applications.select_related("vacancy").order_by("-applied_at")
	return render(
		request,
		"candidates/dashboard.html",
		{
			"candidate": candidate,
			"applications": applications[:5],
			"application_count": applications.count(),
			"open_jobs": JobVacancy.objects.filter(status="OPEN").count(),
		},
	)


def job_list(request):
	jobs = JobVacancy.objects.filter(status="OPEN").select_related("department")
	query = request.GET.get("q", "").strip()
	if query:
		jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query))
	return render(request, "candidates/job_list.html", {"jobs": jobs, "query": query})


def job_detail(request, vacancy_id):
	job = get_object_or_404(JobVacancy.objects.select_related("department"), vacancy_id=vacancy_id)
	applied = False
	if request.user.is_authenticated:
		applied = JobApplication.objects.filter(candidate__user=request.user, vacancy=job).exists()
	return render(request, "candidates/job_detail.html", {"job": job, "applied": applied})


@login_required
def apply(request, vacancy_id):
	candidate = _candidate_for(request.user)
	job = get_object_or_404(JobVacancy, vacancy_id=vacancy_id, status="OPEN")
	existing_application = JobApplication.objects.filter(candidate=candidate, vacancy=job).first()
	if existing_application:
		messages.info(request, "You have already applied for this vacancy.")
		return redirect("candidates:applications")
	if request.method == "POST":
		form = JobApplicationForm(request.POST, request.FILES)
		if form.is_valid():
			application = form.save(commit=False)
			application.candidate = candidate
			application.vacancy = job
			application.save()
			messages.success(request, "Your application was submitted.")
			return redirect("candidates:applications")
	else:
		form = JobApplicationForm(instance=application)
	return render(request, "candidates/apply.html", {"job": job, "form": form})


@login_required
def applications(request):
	candidate = _candidate_for(request.user)
	applications = candidate.applications.select_related("vacancy", "vacancy__department")
	return render(request, "candidates/applications.html", {"applications": applications})


@login_required
def profile(request):
	candidate = _candidate_for(request.user)
	if request.method == "POST":
		form = CandidateProfileForm(request.POST, request.FILES, instance=candidate)
		if form.is_valid():
			form.save()
			messages.success(request, "Profile updated.")
			return redirect("candidates:profile")
	else:
		form = CandidateProfileForm(instance=candidate)
	return render(request, "candidates/profile.html", {"candidate": candidate, "form": form})

from django.shortcuts import render
from .models import Employee


def homepage(request):
    employees = Employee.objects.all()

    return render(
        request,
        "employees/homepage.html",
        {"employees": employees}
    )
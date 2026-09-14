# HRMS Candidate & Job Portal Module

> **Production-Grade Candidate & Recruitment Portal for Enterprise Human Resource Management Systems (HRMS)**  
> *Designed for MCA Final-Year Project & Commercial Recruitment Deployments*

---

## 🚀 Overview

This repository contains the complete frontend UI, client-side interactions, and template architecture for the **Candidate / Job Portal Module** of an enterprise HRMS. Built strictly to match the visual design language, spacing philosophy, colors, card architecture, and typography of the corporate Employee Dashboard.

### Core Tech Stack:
- **Frontend**: Semantic HTML5, CSS3 Custom Properties (Tokens), Modern Vanilla JavaScript (ES6+)
- **Typography**: Inter Sans-Serif font family
- **Vector Graphics**: Clean line SVG icons and embedded illustrations (zero bulky third-party font dependencies)
- **Backend Compatibility**: Pre-configured for **Django 4.2+ / 5.x** and **Cookiecutter Django** with PostgreSQL

---

## 🎨 Visual Design System

| Element | Specification / Hex | Usage |
|---|---|---|
| **Primary Blue** | `#1976F3` | Active sidebar item, primary CTA buttons, links, progress indicators |
| **Dark Navy** | `#172033` | Primary headings, table text, card titles |
| **Secondary Text** | `#667085` | Subtitles, labels, metadata, muted descriptions |
| **Page Background** | `#F7F9FC` | Clean neutral application shell canvas |
| **White** | `#FFFFFF` | Card backgrounds, top header, input fields |
| **Border Color** | `#E8EDF3` | Crisp 1px container dividers and borders |
| **Light Blue** | `#EAF3FF` | Active tags, applied status, avatar rings |
| **Success Green** | `#20A47A` | Shortlisted status, test passed badge, success states |
| **Warning Orange** | `#F5A623` | Under review badge, test countdown warnings |
| **Light Purple** | `#F4EEFF` | Aptitude test badges, assessment icons |
| **Danger Red** | `#E53935` | Rejection badge, critical alerts, logout |

---

## 📂 Project Directory Structure

```
Alan Porject/
│
├── index.html                           # Master Directory & Live Preview Hub
├── README.md                            # Comprehensive Architecture & Integration Guide
│
├── static/
│   ├── css/
│   │   ├── base.css                     # Variables, reset, typography, utilities
│   │   ├── layout.css                   # App shell, 260px sidebar, top header, responsive drawer
│   │   ├── components.css               # Buttons, cards, stats, badges, forms, tables, stepper, modals
│   │   └── pages.css                    # Dashboard hero, aptitude runner, documents dropzone
│   └── js/
│       ├── main.js                      # Sidebar toggle, dropdowns, modal controller, toasts
│       ├── forms.js                     # Password eye toggle, drag-and-drop file upload preview
│       ├── jobs.js                      # Live job filter by keyword/dept/exp, apply modal
│       ├── aptitude.js                  # 20-question test runner, 24:35 countdown timer, navigator grid
│       └── notifications.js             # Category tabs, mark-all-as-read interaction
│
└── templates/
    ├── base.html                        # Django Master Shell for Authenticated Pages
    ├── base_auth.html                   # Django Master Shell for Authentication
    ├── includes/
    │   ├── sidebar.html                 # Left navigation sidebar with SVG icons & active states
    │   ├── header.html                  # Sticky top navigation with search & candidate profile
    │   ├── modals.html                  # Reusable Apply Job & Success State modals
    │   └── toast.html                   # Floating toast alerts
    │
    ├── authentication/
    │   ├── login.html                   # Page 01: Candidate Login (Split layout)
    │   ├── register.html                # Page 02: Candidate Registration
    │   └── forgot_password.html         # Page 03: Forgot Password
    │
    ├── candidate/
    │   ├── dashboard.html               # Page 04: Candidate Dashboard (Hero, 4 Stats, Split, Jobs)
    │   ├── profile.html                 # Page 05: My Profile (Personal, Professional, Education)
    │   ├── edit_profile.html            # Page 06: Edit Profile Form
    │   ├── documents.html               # Page 07: My Documents (Drag & drop upload, 7 document cards)
    │   ├── settings.html                # Page 19: Candidate Settings (Notifications, Privacy)
    │   └── change_password.html         # Page 20: Change Password
    │
    ├── jobs/
    │   ├── job_list.html                # Page 08: Job Vacancies (Search, multi-filters, job cards)
    │   ├── job_details.html             # Page 09: Job Details (Job specs, summary sidebar, similar jobs)
    │   └── apply.html                   # Page 10: Apply for Job (Dedicated flow & success card)
    │
    ├── applications/
    │   ├── my_applications.html         # Page 11: My Applications (4 Stats, filter tabs, table)
    │   └── application_details.html     # Page 12: Application Details (6-step Stepper, outcomes)
    │
    ├── aptitude/
    │   ├── aptitude_list.html           # Page 13: Aptitude Tests (Available, upcoming, completed)
    │   ├── test.html                    # Page 14: Distraction-free Test (Timer, 20-question grid)
    │   └── result.html                  # Page 15: Test Result (85% PASSED circle gauge, breakdown)
    │
    ├── interviews/
    │   ├── interview_list.html          # Page 16: Interview Schedule (Featured round, history table)
    │   └── interview_details.html       # Page 17: Interview Details (Google Meet CTA, preparation)
    │
    ├── notifications/
    │   └── notifications.html           # Page 18: Notifications (Category tabs, mark-as-read)
    │
    └── components/
        └── empty_states.html            # Page 21: Reusable Empty States Showcase
```

---

## ⚡ How to Run & Preview

### Method 1: Instant Browser Preview
Simply double click `index.html` in your file explorer (or right-click and choose **Open with Google Chrome / Microsoft Edge**).  
The master directory provides 1-click links to all 21 pages.

### Method 2: Local Python Server (Recommended)
Open PowerShell or your terminal in this directory and run:
```bash
python -m http.server 8000
```
Then visit in your browser:
```
http://127.0.0.1:8000
```

---

## 🔌 Connecting to Cookiecutter Django Later

This frontend has been purposely structured with **clean semantic HTML and Django-compatible blocks**:

1. **Static Files**:
   Copy the `static/css/` and `static/js/` folders into your Django project's `{{ project_slug }}/static/` directory.
   In templates, replace `../../static/css/base.css` with:
   ```html
   {% load static %}
   <link rel="stylesheet" href="{% static 'css/base.css' %}">
   ```

2. **Template Inheritance**:
   - For all authenticated candidate views, extend `base.html`:
     ```html
     {% extends 'base.html' %}
     {% block title %}Dashboard | HRMS{% endblock %}
     {% block content %}
     <!-- Page content here -->
     {% endblock %}
     ```
   - For login, register, and forgot password, extend `base_auth.html`:
     ```html
     {% extends 'base_auth.html' %}
     {% block content %}
     <!-- Auth form here -->
     {% endblock %}
     ```

3. **Backend Model Data Mapping**:
   The static dummy data maps directly to standard Django models:
   - `candidate.name` ➔ `Alan Shaji`
   - `candidate.email` ➔ `alan.shaji@example.com`
   - `job.title` ➔ `Python Developer`
   - `application.status` ➔ `Shortlisted`
   - `application.status_timeline` ➔ Step 1 to Step 6 in `application_details.html`
   - `test.score` ➔ `85%` in `result.html`

---

## 🌟 Key Features Highlight

1. **Distraction-Free Aptitude Test Runner (`test.html`)**:
   - Active MM:SS countdown timer (24:35)
   - 20-question navigator matrix with state indicators:
     - Blue: Answered
     - Bordered: Current
     - White/Gray: Not Answered
   - Immediate submission calculation and redirect to `result.html`
2. **Interactive Drag-and-Drop Document Uploader (`documents.html`)**:
   - Interactive dropzone supporting PDF, DOCX, JPG with real-time size computation
3. **Reactive Job Filtering (`job_list.html`)**:
   - Instant client-side filtering by keyword, department, experience, and job type
4. **6-Stage Recruitment Stepper (`application_details.html`)**:
   - Applied ➔ Resume Review ➔ Shortlisted ➔ Aptitude Test ➔ Interview Scheduled ➔ Final Decision

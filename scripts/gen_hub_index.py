import os

index_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HRMS Candidate / Job Portal Module - Master Directory</title>
  <link rel="stylesheet" href="static/css/base.css">
  <link rel="stylesheet" href="static/css/layout.css">
  <link rel="stylesheet" href="static/css/components.css">
  <link rel="stylesheet" href="static/css/pages.css">
  <style>
    .hub-container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 48px 24px 80px;
    }
    .hub-hero {
      background: linear-gradient(135deg, #172033 0%, #0F172A 100%);
      border-radius: var(--radius-xl);
      padding: 48px;
      color: #FFFFFF;
      margin-bottom: 40px;
      box-shadow: 0 12px 32px rgba(23, 32, 51, 0.15);
      position: relative;
      overflow: hidden;
    }
    .hub-hero::after {
      content: '';
      position: absolute;
      top: -100px;
      right: -100px;
      width: 400px;
      height: 400px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(25, 118, 243, 0.3) 0%, rgba(25, 118, 243, 0) 70%);
      pointer-events: none;
    }
    .badge-mca {
      background: rgba(25, 118, 243, 0.2);
      color: #93C5FD;
      border: 1px solid rgba(147, 197, 253, 0.3);
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 16px;
    }
    .color-chip {
      width: 100%;
      height: 52px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      padding: 6px;
      font-size: 0.65rem;
      font-weight: 700;
    }
    .category-section-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--dark-navy);
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 36px 0 18px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border-color);
    }
    .page-index-card {
      background: #FFFFFF;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: var(--shadow-card);
      transition: all var(--transition-fast);
    }
    .page-index-card:hover {
      transform: translateY(-3px);
      border-color: var(--primary-blue);
      box-shadow: var(--shadow-hover);
    }
    .page-num-pill {
      font-size: 0.688rem;
      font-weight: 700;
      color: var(--primary-blue);
      background: var(--primary-blue-light);
      padding: 2px 8px;
      border-radius: var(--radius-pill);
      align-self: flex-start;
      margin-bottom: 10px;
    }
    .page-name {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--dark-navy);
      margin-bottom: 4px;
    }
    .page-path {
      font-family: monospace;
      font-size: 0.75rem;
      color: var(--secondary-text);
      background: var(--page-bg);
      padding: 3px 6px;
      border-radius: var(--radius-xs);
      display: inline-block;
      margin-bottom: 12px;
    }
    .page-features-list {
      list-style: none;
      padding: 0;
      margin: 0 0 18px 0;
      font-size: 0.813rem;
      color: var(--secondary-text);
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .page-features-list li::before {
      content: '✓ ';
      color: var(--success);
      font-weight: bold;
    }
  </style>
</head>
<body>

  <div class="hub-container">
    <!-- Hero Header -->
    <header class="hub-hero">
      <div style="position: relative; z-index: 2; max-width: 780px;">
        <span class="badge-mca">Final Year MCA Project • Production-Grade HRMS Architecture</span>
        <h1 style="font-size: 2.25rem; font-weight: 800; color: #FFFFFF; line-height: 1.2; margin-bottom: 12px; letter-spacing: -0.02em;">
          Candidate & Job Portal Module
        </h1>
        <p style="font-size: 1.05rem; color: #CBD5E1; line-height: 1.6; margin-bottom: 24px;">
          A complete, unified recruitment and job seeker portal built to seamlessly integrate with your enterprise Human Resource Management System. Features 21 production-ready frontend pages, interactive client-side assessment runner, document manager, application timeline stepper, and Cookiecutter Django-ready template structure.
        </p>

        <div class="d-flex gap-3 flex-wrap">
          <a href="templates/candidate/dashboard.html" class="btn btn-primary btn-lg">
            <span>Launch Candidate Dashboard</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
          </a>
          <a href="templates/authentication/login.html" class="btn btn-outline btn-lg" style="background: rgba(255,255,255,0.1); color: #FFF; border-color: rgba(255,255,255,0.3);">
            <span>Candidate Login Page</span>
          </a>
          <a href="templates/aptitude/test.html" class="btn btn-outline btn-lg" style="background: rgba(255,255,255,0.1); color: #FFF; border-color: rgba(255,255,255,0.3);">
            <span>Interactive Aptitude Test</span>
          </a>
        </div>
      </div>
    </header>

    <!-- Visual Design System Swatches -->
    <section class="card mb-5">
      <div class="card-header">
        <div>
          <h3 class="card-title">Corporate HRMS Visual Design System</h3>
          <p class="card-subtitle">Exact color tokens, typography scale, and pastel status indicators</p>
        </div>
        <span class="badge badge-applied">Design Spec v1.0</span>
      </div>

      <div class="grid-4 mb-4">
        <div class="color-chip" style="background: #1976F3; color: #FFF;">
          Primary Blue: #1976F3
        </div>
        <div class="color-chip" style="background: #172033; color: #FFF;">
          Dark Navy: #172033
        </div>
        <div class="color-chip" style="background: #667085; color: #FFF;">
          Secondary: #667085
        </div>
        <div class="color-chip" style="background: #F7F9FC; color: #172033;">
          Page Background: #F7F9FC
        </div>
        <div class="color-chip" style="background: #20A47A; color: #FFF;">
          Success Green: #20A47A
        </div>
        <div class="color-chip" style="background: #F5A623; color: #FFF;">
          Warning Orange: #F5A623
        </div>
        <div class="color-chip" style="background: #7C3AED; color: #FFF;">
          Purple: #7C3AED
        </div>
        <div class="color-chip" style="background: #E53935; color: #FFF;">
          Danger Red: #E53935
        </div>
      </div>

      <div class="d-flex align-items-center gap-2 flex-wrap">
        <span class="text-xs font-bold text-navy">Application Status Badges:</span>
        <span class="badge badge-applied"><span class="badge-dot"></span>Applied</span>
        <span class="badge badge-review"><span class="badge-dot"></span>Resume Under Review</span>
        <span class="badge badge-shortlisted"><span class="badge-dot"></span>Shortlisted</span>
        <span class="badge badge-aptitude"><span class="badge-dot"></span>Aptitude Test</span>
        <span class="badge badge-interview"><span class="badge-dot"></span>Interview Scheduled</span>
        <span class="badge badge-selected"><span class="badge-dot"></span>Selected</span>
        <span class="badge badge-rejected"><span class="badge-dot"></span>Rejected</span>
      </div>
    </section>

    <!-- 1. AUTHENTICATION MODULE -->
    <div class="category-section-title">
      <span>1. Authentication Module</span>
    </div>
    <div class="grid-3 mb-5">
      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 01</span>
          <h3 class="page-name">Candidate Login</h3>
          <span class="page-path">templates/authentication/login.html</span>
          <ul class="page-features-list">
            <li>Split layout with HR recruitment vector artwork</li>
            <li>Password visibility toggle (eye icon)</li>
            <li>Remember me & Forgot password links</li>
          </ul>
        </div>
        <a href="templates/authentication/login.html" class="btn btn-outline btn-block">Open Login Page →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 02</span>
          <h3 class="page-name">Candidate Registration</h3>
          <span class="page-path">templates/authentication/register.html</span>
          <ul class="page-features-list">
            <li>Full Name, Email, Phone, Password inputs</li>
            <li>Confirm Password with matching validation UI</li>
            <li>Terms and Conditions agreement checkbox</li>
          </ul>
        </div>
        <a href="templates/authentication/register.html" class="btn btn-outline btn-block">Open Registration →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 03</span>
          <h3 class="page-name">Forgot Password</h3>
          <span class="page-path">templates/authentication/forgot_password.html</span>
          <ul class="page-features-list">
            <li>Email recovery input with instruction alert</li>
            <li>Send reset link simulation action</li>
            <li>Back to login navigation</li>
          </ul>
        </div>
        <a href="templates/authentication/forgot_password.html" class="btn btn-outline btn-block">Open Forgot Password →</a>
      </div>
    </div>

    <!-- 2. CANDIDATE CORE MODULE -->
    <div class="category-section-title">
      <span>2. Candidate Core Module</span>
    </div>
    <div class="grid-3 mb-5">
      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 04</span>
          <h3 class="page-name">Candidate Dashboard</h3>
          <span class="page-path">templates/candidate/dashboard.html</span>
          <ul class="page-features-list">
            <li>Hero banner with greeting, completion meter & graphic</li>
            <li>4 Statistic cards (Total, Shortlisted, Interviews, Alerts)</li>
            <li>Split columns: Recent Applications & Upcoming Interview</li>
            <li>Recommended Jobs grid & Company announcements</li>
          </ul>
        </div>
        <a href="templates/candidate/dashboard.html" class="btn btn-primary btn-block">Open Dashboard →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 05</span>
          <h3 class="page-name">My Profile</h3>
          <span class="page-path">templates/candidate/profile.html</span>
          <ul class="page-features-list">
            <li>Profile header with avatar, ID, 85% progress bar</li>
            <li>Personal Information detailed data grid</li>
            <li>Professional information and skills chips</li>
            <li>Academic education history table (10th, 12th, Degree, MCA)</li>
          </ul>
        </div>
        <a href="templates/candidate/profile.html" class="btn btn-outline btn-block">Open Profile →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 06</span>
          <h3 class="page-name">Edit Profile</h3>
          <span class="page-path">templates/candidate/edit_profile.html</span>
          <ul class="page-features-list">
            <li>Breadcrumb navigation</li>
            <li>Sectioned forms with validation states</li>
            <li>Education and skills update fields</li>
          </ul>
        </div>
        <a href="templates/candidate/edit_profile.html" class="btn btn-outline btn-block">Open Edit Profile →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 07</span>
          <h3 class="page-name">Candidate Documents</h3>
          <span class="page-path">templates/candidate/documents.html</span>
          <ul class="page-features-list">
            <li>Modern drag-and-drop file upload zone</li>
            <li>Live file preview box with size calculation</li>
            <li>Document cards (Resume, Photo, ID, Marksheets, Certificates)</li>
          </ul>
        </div>
        <a href="templates/candidate/documents.html" class="btn btn-outline btn-block">Open Documents →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 19</span>
          <h3 class="page-name">Candidate Settings</h3>
          <span class="page-path">templates/candidate/settings.html</span>
          <ul class="page-features-list">
            <li>Notification toggles (Email, status updates, test reminders)</li>
            <li>Profile visibility to HR recruiters</li>
            <li>Quick links to change password & security</li>
          </ul>
        </div>
        <a href="templates/candidate/settings.html" class="btn btn-outline btn-block">Open Settings →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 20</span>
          <h3 class="page-name">Change Password</h3>
          <span class="page-path">templates/candidate/change_password.html</span>
          <ul class="page-features-list">
            <li>Current password, New password, Confirm password</li>
            <li>Password visibility toggles on every field</li>
            <li>Password complexity rules hint</li>
          </ul>
        </div>
        <a href="templates/candidate/change_password.html" class="btn btn-outline btn-block">Open Change Password →</a>
      </div>
    </div>

    <!-- 3. JOB VACANCIES & APPLICATIONS -->
    <div class="category-section-title">
      <span>3. Job Vacancies & Application Workflow</span>
    </div>
    <div class="grid-3 mb-5">
      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 08</span>
          <h3 class="page-name">Job Vacancies (List)</h3>
          <span class="page-path">templates/jobs/job_list.html</span>
          <ul class="page-features-list">
            <li>Live client-side keyword search input</li>
            <li>Multi-select filters (Department, Experience, Job Type)</li>
            <li>"24 Available Jobs" reactive counter</li>
            <li>Job cards with salary tags, chips, and quick apply</li>
          </ul>
        </div>
        <a href="templates/jobs/job_list.html" class="btn btn-primary btn-block">Open Job Vacancies →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 09</span>
          <h3 class="page-name">Job Details</h3>
          <span class="page-path">templates/jobs/job_details.html</span>
          <ul class="page-features-list">
            <li>Breadcrumb & comprehensive role overview</li>
            <li>Key responsibilities, qualifications, required skills</li>
            <li>Sticky application summary card with deadline</li>
            <li>Similar jobs section</li>
          </ul>
        </div>
        <a href="templates/jobs/job_details.html" class="btn btn-outline btn-block">Open Job Details →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 10</span>
          <h3 class="page-name">Apply for Job</h3>
          <span class="page-path">templates/jobs/apply.html</span>
          <ul class="page-features-list">
            <li>Selected job summary banner</li>
            <li>Prefilled candidate contact details</li>
            <li>Resume selector with replace action</li>
            <li>Interactive submission & success state card</li>
          </ul>
        </div>
        <a href="templates/jobs/apply.html" class="btn btn-outline btn-block">Open Apply Page →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 11</span>
          <h3 class="page-name">My Applications</h3>
          <span class="page-path">templates/applications/my_applications.html</span>
          <ul class="page-features-list">
            <li>Top metrics (Total, Under Review, Shortlisted, Selected)</li>
            <li>Status filter tabs (All, Applied, Shortlisted, etc.)</li>
            <li>Clean responsive table with status badges</li>
          </ul>
        </div>
        <a href="templates/applications/my_applications.html" class="btn btn-outline btn-block">Open My Applications →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 12</span>
          <h3 class="page-name">Application Details</h3>
          <span class="page-path">templates/applications/application_details.html</span>
          <ul class="page-features-list">
            <li>6-step Visual Application Stepper (✓ Completed, ● Current, ○ Upcoming)</li>
            <li>Prominent current status notice banner</li>
            <li>Recruitment activity log with timestamps</li>
            <li>Preview of positive Selection and Rejection states</li>
          </ul>
        </div>
        <a href="templates/applications/application_details.html" class="btn btn-outline btn-block">Open Application Details →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 21</span>
          <h3 class="page-name">Reusable Empty States</h3>
          <span class="page-path">templates/components/empty_states.html</span>
          <ul class="page-features-list">
            <li>Showcase of all 5 empty states</li>
            <li>No Applications, No Notifications, No Interviews</li>
            <li>No Aptitude Tests, No Jobs Found</li>
          </ul>
        </div>
        <a href="templates/components/empty_states.html" class="btn btn-outline btn-block">Open Empty States →</a>
      </div>
    </div>

    <!-- 4. ASSESSMENTS & INTERVIEWS -->
    <div class="category-section-title">
      <span>4. Assessments & Interview Modules</span>
    </div>
    <div class="grid-3 mb-5">
      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 13</span>
          <h3 class="page-name">Aptitude Tests (Listing)</h3>
          <span class="page-path">templates/aptitude/aptitude_list.html</span>
          <ul class="page-features-list">
            <li>Tabs: Available Tests, Upcoming Tests, Completed Tests</li>
            <li>Test cards with duration, question count, and score criteria</li>
            <li>Start Test & View Result buttons</li>
          </ul>
        </div>
        <a href="templates/aptitude/aptitude_list.html" class="btn btn-outline btn-block">Open Aptitude List →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 14</span>
          <h3 class="page-name">Live Aptitude Test</h3>
          <span class="page-path">templates/aptitude/test.html</span>
          <ul class="page-features-list">
            <li>Distraction-free test environment with countdown timer</li>
            <li>Single-choice selectable radio option cards</li>
            <li>20-question interactive grid navigator (Answered/Current)</li>
            <li>Confirmation modal with score calculation redirect</li>
          </ul>
        </div>
        <a href="templates/aptitude/test.html" class="btn btn-primary btn-block">Open Test Runner →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 15</span>
          <h3 class="page-name">Test Result Card</h3>
          <span class="page-path">templates/aptitude/result.html</span>
          <ul class="page-features-list">
            <li>Large circular score gauge (85% PASSED)</li>
            <li>Detailed metrics (Correct, Incorrect, Total, Time Taken)</li>
            <li>Topic-wise performance progress breakdown</li>
          </ul>
        </div>
        <a href="templates/aptitude/result.html" class="btn btn-outline btn-block">Open Test Result →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 16</span>
          <h3 class="page-name">Interview Schedule</h3>
          <span class="page-path">templates/interviews/interview_list.html</span>
          <ul class="page-features-list">
            <li>Featured upcoming interview hero card with Google Meet link</li>
            <li>Date, time window, panel details, and guidelines</li>
            <li>Previous interviews history table</li>
          </ul>
        </div>
        <a href="templates/interviews/interview_list.html" class="btn btn-outline btn-block">Open Interview Schedule →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 17</span>
          <h3 class="page-name">Interview Details</h3>
          <span class="page-path">templates/interviews/interview_details.html</span>
          <ul class="page-features-list">
            <li>Comprehensive meeting specification & Join CTA</li>
            <li>Required verification documents checklist</li>
            <li>Technical preparation instructions</li>
          </ul>
        </div>
        <a href="templates/interviews/interview_details.html" class="btn btn-outline btn-block">Open Interview Details →</a>
      </div>

      <div class="page-index-card">
        <div>
          <span class="page-num-pill">PAGE 18</span>
          <h3 class="page-name">Notifications Center</h3>
          <span class="page-path">templates/notifications/notifications.html</span>
          <ul class="page-features-list">
            <li>Filter tabs (All, Applications, Interviews, Aptitude, Notices)</li>
            <li>Interactive "Mark all as read" button</li>
            <li>Pastel category icons and unread status indicators</li>
          </ul>
        </div>
        <a href="templates/notifications/notifications.html" class="btn btn-outline btn-block">Open Notifications →</a>
      </div>
    </div>

    <!-- Django Integration Guide Card -->
    <section class="card" style="background: #F0F7FF; border: 1px solid #BFDBFE;">
      <h3 class="card-title" style="color: var(--primary-blue); margin-bottom: 8px;">Django & Cookiecutter Django Architecture</h3>
      <p class="text-sm text-navy mb-3">
        All templates are built with semantic HTML and include annotations for Django template tags (<code>{{% extends 'base.html' %}}</code>, <code>{{% block content %}}</code>, <code>{{% static %}}</code>, and context variables like <code>{{ candidate.name }}</code>). The modular structure allows instant copy-paste or migration into your Cookiecutter Django project's <code>templates/</code> and <code>static/</code> directories.
      </p>
      <div class="d-flex gap-2">
        <span class="badge badge-applied">Django 4.2+ / 5.x</span>
        <span class="badge badge-applied">PostgreSQL Ready</span>
        <span class="badge badge-applied">Zero External Dependencies</span>
      </div>
    </section>
  </div>

</body>
</html>
"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(index_content)

print("Master Index Hub generated successfully.")

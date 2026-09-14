import os
from build_common_shell import get_sidebar_html, get_header_html

aptitude_list_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aptitude Tests - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="aptitude", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Aptitude & Technical Assessments</h1>
            <p class="page-subtitle">Take assigned skill evaluations and view verified scores</p>
          </div>
        </div>

        <!-- Filter Tabs -->
        <div class="nav-tabs">
          <button class="nav-tab-btn active">Available Tests (1)</button>
          <button class="nav-tab-btn">Upcoming Tests (1)</button>
          <button class="nav-tab-btn">Completed Tests (1)</button>
        </div>

        <div class="grid-3 mb-4">
          <!-- Card 1: Available Test -->
          <div class="card" style="border-top: 4px solid var(--primary-blue);">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge badge-applied">Available Now</span>
              <span class="text-xs text-muted">Deadline: 10 Sep 2026</span>
            </div>
            <h3 class="card-title" style="font-size: 1.1rem; margin-top: 4px;">Python Technical Assessment</h3>
            <p class="text-xs text-muted mb-3">Job: Python Developer (#APP-2026-8841)</p>
            
            <div style="background: var(--page-bg); border-radius: var(--radius-md); padding: 12px; margin-bottom: 20px;">
              <div class="d-flex justify-content-between text-xs mb-1">
                <span class="text-muted">Questions:</span>
                <span class="font-semibold text-navy">20 MCQs</span>
              </div>
              <div class="d-flex justify-content-between text-xs mb-1">
                <span class="text-muted">Duration:</span>
                <span class="font-semibold text-navy">30 Minutes</span>
              </div>
              <div class="d-flex justify-content-between text-xs">
                <span class="text-muted">Passing Score:</span>
                <span class="font-semibold text-success">60%</span>
              </div>
            </div>

            <a href="test.html" class="btn btn-primary btn-block">
              <span>Start Assessment</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            </a>
          </div>

          <!-- Card 2: Upcoming Test -->
          <div class="card" style="border-top: 4px solid var(--warning);">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge badge-review">Upcoming</span>
              <span class="text-xs text-muted">Opens: 18 Sep 2026</span>
            </div>
            <h3 class="card-title" style="font-size: 1.1rem; margin-top: 4px;">Data Analysis & SQL Evaluation</h3>
            <p class="text-xs text-muted mb-3">Job: Data Analyst (#APP-2026-8794)</p>
            
            <div style="background: var(--page-bg); border-radius: var(--radius-md); padding: 12px; margin-bottom: 20px;">
              <div class="d-flex justify-content-between text-xs mb-1">
                <span class="text-muted">Questions:</span>
                <span class="font-semibold text-navy">25 MCQs</span>
              </div>
              <div class="d-flex justify-content-between text-xs mb-1">
                <span class="text-muted">Duration:</span>
                <span class="font-semibold text-navy">35 Minutes</span>
              </div>
              <div class="d-flex justify-content-between text-xs">
                <span class="text-muted">Passing Score:</span>
                <span class="font-semibold text-success">65%</span>
              </div>
            </div>

            <button class="btn btn-secondary btn-block" disabled>Scheduled</button>
          </div>

          <!-- Card 3: Completed Test -->
          <div class="card" style="border-top: 4px solid var(--success);">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge badge-shortlisted">Completed</span>
              <span class="text-xs text-muted">Taken on 04 Sep 2026</span>
            </div>
            <h3 class="card-title" style="font-size: 1.1rem; margin-top: 4px;">General Aptitude & Logical Reasoning</h3>
            <p class="text-xs text-muted mb-3">Job: Associate Software Engineer</p>
            
            <div style="background: var(--page-bg); border-radius: var(--radius-md); padding: 12px; margin-bottom: 20px;">
              <div class="d-flex justify-content-between text-xs mb-1">
                <span class="text-muted">Score:</span>
                <span class="font-bold text-success">85% (17/20 Correct)</span>
              </div>
              <div class="d-flex justify-content-between text-xs mb-1">
                <span class="text-muted">Result:</span>
                <span class="badge badge-shortlisted">PASSED</span>
              </div>
              <div class="d-flex justify-content-between text-xs">
                <span class="text-muted">Time Taken:</span>
                <span class="font-semibold text-navy">21m 40s</span>
              </div>
            </div>

            <a href="result.html" class="btn btn-outline-primary btn-block">View Result Card</a>
          </div>
        </div>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
</body>
</html>
"""

test_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aptitude Assessment - Python Developer - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body style="background-color: var(--page-bg);" id="aptitudeTestArea">
  <!-- Distraction-Free Top Bar -->
  <header class="test-top-header">
    <div class="d-flex align-items-center gap-3">
      <div class="brand-icon" style="width: 32px; height: 32px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
      </div>
      <div>
        <h2 style="font-size: 1.05rem; font-weight: 700; color: var(--dark-navy);">Python Developer Aptitude Assessment</h2>
        <div class="text-xs text-muted">20 Questions • 30 Minutes • Passing Score: 60%</div>
      </div>
    </div>

    <div class="d-flex align-items-center gap-4">
      <div class="test-timer-badge">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        <span>Time Remaining: <span id="timeRemaining">24:35</span></span>
      </div>

      <button type="button" class="btn btn-sm btn-danger" id="submitTestBtn">Submit Test</button>
    </div>
  </header>

  <!-- Main Test Content (Split layout) -->
  <div class="test-layout">
    <!-- Left: Question & Options Area -->
    <div class="card" style="padding: 32px;">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <span class="badge badge-applied" id="currentQuestionNumber">Question 1 of 20</span>
        <span class="text-xs text-muted">Single Choice MCQ</span>
      </div>

      <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--dark-navy); margin-bottom: 24px; line-height: 1.4;" id="currentQuestionText">
        Which of the following is used to define a function in Python?
      </h3>

      <div id="questionOptionsList">
        <!-- Interactive options rendered dynamically by static/js/aptitude.js -->
        <div class="question-option selected">
          <div style="width: 22px; height: 22px; border-radius: 50%; border: 2px solid #1976F3; display: flex; align-items: center; justify-content: center; background: #1976F3;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #FFF;"></div>
          </div>
          <span>def</span>
        </div>
        <div class="question-option">
          <div style="width: 22px; height: 22px; border-radius: 50%; border: 2px solid #CBD5E1;"></div>
          <span>function</span>
        </div>
        <div class="question-option">
          <div style="width: 22px; height: 22px; border-radius: 50%; border: 2px solid #CBD5E1;"></div>
          <span>func</span>
        </div>
        <div class="question-option">
          <div style="width: 22px; height: 22px; border-radius: 50%; border: 2px solid #CBD5E1;"></div>
          <span>define</span>
        </div>
      </div>

      <!-- Navigation buttons -->
      <div class="d-flex justify-content-between align-items-center mt-5 pt-3" style="border-top: 1px solid var(--border-light);">
        <button type="button" class="btn btn-outline" id="prevQuestionBtn">← Previous</button>
        <button type="button" class="btn btn-primary" id="nextQuestionBtn">Next Question →</button>
      </div>
    </div>

    <!-- Right: Question Palette / Navigator -->
    <div class="card">
      <div class="card-header" style="padding-bottom: 12px;">
        <h4 class="card-title" style="font-size: 0.95rem;">Question Navigator</h4>
        <span class="text-xs text-muted"><span id="answeredQuestionsCount">1</span> / 20 Answered</span>
      </div>

      <!-- Legend -->
      <div class="d-flex gap-3 text-xs mb-3 flex-wrap">
        <span class="d-flex align-items-center gap-1">
          <span style="width: 12px; height: 12px; background: var(--primary-blue); border-radius: 2px;"></span> Answered
        </span>
        <span class="d-flex align-items-center gap-1">
          <span style="width: 12px; height: 12px; border: 2px solid var(--primary-blue); border-radius: 2px; background: #FFF;"></span> Current
        </span>
        <span class="d-flex align-items-center gap-1">
          <span style="width: 12px; height: 12px; border: 1px solid var(--border-color); border-radius: 2px; background: #FFF;"></span> Not Answered
        </span>
      </div>

      <!-- 20 Question Matrix -->
      <div class="question-nav-grid" id="questionNavGrid">
        <!-- Rendered by static/js/aptitude.js -->
      </div>
    </div>
  </div>

  <!-- Submission Confirmation Modal -->
  <div class="modal-overlay" id="submitConfirmModal">
    <div class="modal-dialog" style="max-width: 480px; text-align: center;">
      <div class="modal-body" style="padding: 32px 24px;">
        <h3 class="modal-title mb-2">Submit Aptitude Assessment?</h3>
        <p class="text-sm text-muted mb-4" id="submitSummaryText">
          You have answered questions. Once submitted, you cannot change your answers.
        </p>
        <div class="d-flex justify-content-center gap-3">
          <button type="button" class="btn btn-secondary" data-modal-close>Review Questions</button>
          <button type="button" class="btn btn-primary" id="confirmFinalSubmitBtn">Confirm & Submit</button>
        </div>
      </div>
    </div>
  </div>

  <script src="../../static/js/main.js"></script>
  <script src="../../static/js/aptitude.js"></script>
</body>
</html>
"""

result_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aptitude Test Result - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="aptitude", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="breadcrumb">
          <a href="aptitude_list.html">Aptitude Tests</a>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">Python Developer Assessment Result</span>
        </div>

        <div class="page-header">
          <div>
            <h1 class="page-title">Aptitude Test Result</h1>
            <p class="page-subtitle">Detailed scoring performance and assessment breakdown</p>
          </div>
        </div>

        <!-- Large Visual Score Card -->
        <div class="result-hero-box">
          <div class="score-circle">
            <div class="score-circle-inner">
              <div class="score-number">85%</div>
              <div class="score-total">Score</div>
            </div>
          </div>

          <span class="badge badge-shortlisted" style="font-size: 0.95rem; padding: 6px 18px; margin-bottom: 12px;">
            <span class="badge-dot"></span>STATUS: PASSED
          </span>

          <h2 style="font-size: 1.5rem; font-weight: 700; color: var(--dark-navy); margin-bottom: 6px;">Python Technical Assessment</h2>
          <p class="text-sm text-muted mb-4">Completed on 06 September 2026 • Time Taken: 21 mins 40 secs</p>

          <!-- Key Metrics Grid -->
          <div class="grid-4 mb-4" style="text-align: left;">
            <div style="background: var(--page-bg); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
              <div class="text-xs text-muted">Total Questions</div>
              <div class="font-bold text-navy" style="font-size: 1.3rem;">20</div>
            </div>
            <div style="background: var(--success-light); padding: 14px; border-radius: var(--radius-md); border: 1px solid #B8EBD6;">
              <div class="text-xs" style="color: var(--success);">Correct Answers</div>
              <div class="font-bold text-success" style="font-size: 1.3rem;">17</div>
            </div>
            <div style="background: var(--danger-light); padding: 14px; border-radius: var(--radius-md); border: 1px solid #FFD1D1;">
              <div class="text-xs" style="color: var(--danger);">Incorrect Answers</div>
              <div class="font-bold text-danger" style="font-size: 1.3rem;">3</div>
            </div>
            <div style="background: var(--page-bg); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
              <div class="text-xs text-muted">Passing Criteria</div>
              <div class="font-bold text-navy" style="font-size: 1.3rem;">60%</div>
            </div>
          </div>

          <!-- Actions -->
          <div class="d-flex justify-content-center gap-3">
            <a href="../applications/application_details.html" class="btn btn-primary">View Application</a>
            <a href="aptitude_list.html" class="btn btn-outline">Back to Tests</a>
          </div>
        </div>

        <!-- Section-wise Breakdown -->
        <div class="card" style="max-width: 680px; margin: 0 auto;">
          <h3 class="card-title mb-3">Topic Performance Breakdown</h3>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            <div>
              <div class="d-flex justify-content-between text-xs font-semibold mb-1">
                <span>Python Syntax & Data Types</span>
                <span>90% (9/10)</span>
              </div>
              <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 90%;"></div></div>
            </div>

            <div>
              <div class="d-flex justify-content-between text-xs font-semibold mb-1">
                <span>Control Flow & Loops</span>
                <span>80% (4/5)</span>
              </div>
              <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 80%;"></div></div>
            </div>

            <div>
              <div class="d-flex justify-content-between text-xs font-semibold mb-1">
                <span>Functions, OOP & Modules</span>
                <span>80% (4/5)</span>
              </div>
              <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: 80%;"></div></div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
</body>
</html>
"""

interview_list_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Interview Schedule - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="interviews", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Interview Schedule</h1>
            <p class="page-subtitle">View your upcoming and previous interview rounds</p>
          </div>
        </div>

        <!-- Stats -->
        <div class="grid-3 mb-4">
          <div class="stat-card">
            <div class="stat-icon blue">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">1</div>
              <div class="stat-label">Upcoming Interview</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon green">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">2</div>
              <div class="stat-label">Completed Interviews</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon orange">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">0</div>
              <div class="stat-label">Pending Reschedule</div>
            </div>
          </div>
        </div>

        <!-- Main Featured Upcoming Card -->
        <div class="card mb-5" style="border-left: 6px solid var(--primary-blue);">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-3">
            <div>
              <span class="badge badge-interview mb-1">Featured Upcoming Round</span>
              <h2 style="font-size: 1.4rem; font-weight: 700; color: var(--dark-navy);">Python Developer - Technical Interview</h2>
              <p class="text-xs text-muted mt-1">Application ID: #APP-2026-8841 • IT Engineering</p>
            </div>
            <span class="badge badge-shortlisted">Confirmed by HR</span>
          </div>

          <div class="grid-3 mb-4" style="background: var(--page-bg); padding: 18px; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
            <div>
              <div class="text-xs text-muted mb-1">Date & Time</div>
              <div class="font-bold text-navy">15 September 2026</div>
              <div class="text-xs text-primary font-semibold">11:00 AM - 11:45 AM (IST)</div>
            </div>
            <div>
              <div class="text-xs text-muted mb-1">Interview Mode</div>
              <div class="font-bold text-navy">Online Video Call</div>
              <div class="text-xs text-muted">Google Meet Platform</div>
            </div>
            <div>
              <div class="text-xs text-muted mb-1">Interviewer Panel</div>
              <div class="font-bold text-navy">HR Recruitment Team</div>
              <div class="text-xs text-muted">Technical Lead: Rajesh Menon</div>
            </div>
          </div>

          <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div class="text-xs text-muted">
              Meeting link will become active 10 minutes prior to the scheduled start time.
            </div>
            <div class="d-flex gap-2">
              <a href="interview_details.html" class="btn btn-outline">View Full Round Details</a>
              <a href="https://meet.google.com" target="_blank" class="btn btn-primary">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                <span>Join Interview</span>
              </a>
            </div>
          </div>
        </div>

        <!-- Previous Interviews History Table -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Previous Interviews</h3>
          </div>

          <div class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Round</th>
                  <th>Date & Time</th>
                  <th>Mode</th>
                  <th>Interviewer</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="font-semibold">Associate Software Engineer</td>
                  <td>Round 1: HR Screening</td>
                  <td>12 Aug 2026 • 2:30 PM</td>
                  <td>Phone Call</td>
                  <td>Anjali Nair (Senior HR)</td>
                  <td><span class="badge badge-shortlisted">Completed</span></td>
                </tr>
                <tr>
                  <td class="font-semibold">Associate Software Engineer</td>
                  <td>Round 2: Technical Discussion</td>
                  <td>18 Aug 2026 • 10:00 AM</td>
                  <td>Google Meet</td>
                  <td>Praveen Kumar (Tech Lead)</td>
                  <td><span class="badge badge-selected">Cleared</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
</body>
</html>
"""

interview_details_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Interview Details - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="interviews", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="breadcrumb">
          <a href="interview_list.html">Interview Schedule</a>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">Technical Interview Details</span>
        </div>

        <div class="card mb-4">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-3">
            <div>
              <span class="badge badge-interview mb-1">Interview Round 1</span>
              <h1 class="page-title mt-1">Python Developer - Technical Interview</h1>
              <div class="text-xs text-muted mt-1">
                Candidate: <strong>Alan Shaji</strong> (#CAN-2026-884) • IT Engineering
              </div>
            </div>
            <a href="https://meet.google.com" target="_blank" class="btn btn-primary btn-lg">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
              <span>Join Interview</span>
            </a>
          </div>
        </div>

        <div class="grid-2 mb-4">
          <!-- Session Schedule Spec -->
          <div class="card">
            <h3 class="card-title mb-3">Meeting Details</h3>
            <div style="display: flex; flex-direction: column; gap: 12px;">
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Date:</span>
                <span class="text-xs font-semibold text-navy">15 September 2026</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Time Window:</span>
                <span class="text-xs font-semibold text-primary">11:00 AM - 11:45 AM (IST)</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Mode:</span>
                <span class="text-xs font-semibold text-navy">Online Video Call</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Platform:</span>
                <span class="text-xs font-semibold text-navy">Google Meet</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Meeting URL:</span>
                <span class="text-xs font-semibold text-primary">https://meet.google.com/xyz-hrms-job</span>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-xs text-muted">Interview Panel:</span>
                <span class="text-xs font-semibold text-navy">HR Team & Senior Tech Lead</span>
              </div>
            </div>
          </div>

          <!-- Required Documents -->
          <div class="card">
            <h3 class="card-title mb-3">Required Documents for Verification</h3>
            <ul style="margin-left: 20px; font-size: var(--font-size-sm); color: var(--secondary-text); line-height: 1.8;">
              <li>Government Issued Photo ID (Original Aadhaar Card / Passport).</li>
              <li>Degree Marksheets & Certificates for MCA / B.Sc CS.</li>
              <li>Digital copy of your latest resume: <code>Alan_Shaji_Resume_2026.pdf</code>.</li>
              <li>Active GitHub profile or code repository links for walkthrough.</li>
            </ul>
          </div>
        </div>

        <!-- Instructions & Preparation -->
        <div class="card">
          <h3 class="card-title mb-3">Interview Instructions & Guidelines</h3>
          <ul style="margin-left: 20px; font-size: var(--font-size-sm); color: var(--secondary-text); line-height: 1.8;">
            <li>Please log in at least <strong>10 minutes</strong> before the scheduled interview time.</li>
            <li>Ensure a quiet, well-lit environment with a stable high-speed internet connection.</li>
            <li>Keep your webcam and microphone active throughout the interview session.</li>
            <li>You may be requested to share your screen for live coding and technical problem solving.</li>
          </ul>
        </div>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
</body>
</html>
"""

os.makedirs('templates/aptitude', exist_ok=True)
os.makedirs('templates/interviews', exist_ok=True)

with open('templates/aptitude/aptitude_list.html', 'w', encoding='utf-8') as f:
    f.write(aptitude_list_html)
with open('templates/aptitude/test.html', 'w', encoding='utf-8') as f:
    f.write(test_html)
with open('templates/aptitude/result.html', 'w', encoding='utf-8') as f:
    f.write(result_html)
with open('templates/interviews/interview_list.html', 'w', encoding='utf-8') as f:
    f.write(interview_list_html)
with open('templates/interviews/interview_details.html', 'w', encoding='utf-8') as f:
    f.write(interview_details_html)

print("Aptitude and Interview templates generated successfully.")

import os
from build_common_shell import get_sidebar_html, get_header_html

notif_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Notifications - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
  <style>
    .notification-item-card {{
      background: #FFFFFF;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 18px 20px;
      margin-bottom: 12px;
      display: flex;
      align-items: flex-start;
      gap: 16px;
      transition: all var(--transition-fast);
      position: relative;
    }}
    .notification-item-card:hover {{
      border-color: var(--primary-blue);
      box-shadow: var(--shadow-hover);
    }}
    .notification-item-card.unread {{
      background: #F6FAFF;
      border-color: #D1E5FF;
    }}
    .notif-icon-box {{
      width: 44px;
      height: 44px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .unread-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--primary-blue);
      margin-left: auto;
      flex-shrink: 0;
      margin-top: 4px;
    }}
  </style>
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="notifications", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Notifications</h1>
            <p class="page-subtitle">Stay updated with your job applications and recruitment activities</p>
          </div>
          <button type="button" class="btn btn-outline" id="markAllReadBtn">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span>Mark all as read</span>
          </button>
        </div>

        <!-- Filter Category Tabs -->
        <div class="nav-tabs">
          <button class="nav-tab-btn notification-tab-btn active" data-category="all">All Notifications (5)</button>
          <button class="nav-tab-btn notification-tab-btn" data-category="apps">Applications (2)</button>
          <button class="nav-tab-btn notification-tab-btn" data-category="interviews">Interviews (1)</button>
          <button class="nav-tab-btn notification-tab-btn" data-category="aptitude">Aptitude Tests (1)</button>
          <button class="nav-tab-btn notification-tab-btn" data-category="announcements">Announcements (1)</button>
        </div>

        <div id="notificationsContainer">
          <!-- Item 1: Interview Scheduled (Unread) -->
          <div class="notification-item-card unread" data-category="interviews">
            <div class="notif-icon-box" style="background: var(--status-interview-bg); color: var(--status-interview-text);">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex align-items-center gap-2 mb-1">
                <span class="badge badge-interview">Interview Scheduled</span>
                <span class="text-xs text-muted">2 hours ago</span>
              </div>
              <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--dark-navy);">Technical Interview Scheduled for Python Developer</h4>
              <p class="text-sm text-muted mt-1">Your online technical interview has been confirmed for 15 September 2026 at 11:00 AM IST on Google Meet.</p>
              <div class="mt-2">
                <a href="../interviews/interview_details.html" class="btn btn-sm btn-primary">Join / View Round</a>
              </div>
            </div>
            <div class="unread-dot"></div>
          </div>

          <!-- Item 2: Application Shortlisted (Unread) -->
          <div class="notification-item-card unread" data-category="apps">
            <div class="notif-icon-box" style="background: var(--status-shortlisted-bg); color: var(--status-shortlisted-text);">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex align-items-center gap-2 mb-1">
                <span class="badge badge-shortlisted">Application Shortlisted</span>
                <span class="text-xs text-muted">1 day ago</span>
              </div>
              <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--dark-navy);">Congratulations! You have been shortlisted</h4>
              <p class="text-sm text-muted mt-1">Your resume for <strong>Python Developer</strong> (#APP-2026-8841) was reviewed and approved by the hiring committee.</p>
              <div class="mt-2">
                <a href="../applications/application_details.html" class="btn btn-sm btn-outline">Track Application</a>
              </div>
            </div>
            <div class="unread-dot"></div>
          </div>

          <!-- Item 3: Aptitude Test Available (Unread) -->
          <div class="notification-item-card unread" data-category="aptitude">
            <div class="notif-icon-box" style="background: var(--status-aptitude-bg); color: var(--status-aptitude-text);">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex align-items-center gap-2 mb-1">
                <span class="badge badge-aptitude">Aptitude Test Ready</span>
                <span class="text-xs text-muted">2 days ago</span>
              </div>
              <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--dark-navy);">Python Developer Assessment is now available</h4>
              <p class="text-sm text-muted mt-1">Please complete your 20-question online technical assessment before the deadline on 10 September 2026.</p>
              <div class="mt-2">
                <a href="../aptitude/test.html" class="btn btn-sm btn-primary">Take Test Now</a>
              </div>
            </div>
            <div class="unread-dot"></div>
          </div>

          <!-- Item 4: Application Submitted -->
          <div class="notification-item-card" data-category="apps">
            <div class="notif-icon-box" style="background: var(--status-applied-bg); color: var(--status-applied-text);">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex align-items-center gap-2 mb-1">
                <span class="badge badge-applied">Application Submitted</span>
                <span class="text-xs text-muted">5 days ago</span>
              </div>
              <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--dark-navy);">Application for Python Developer successfully submitted</h4>
              <p class="text-sm text-muted mt-1">Your application has been assigned tracking number <strong>#APP-2026-8841</strong>.</p>
            </div>
          </div>

          <!-- Item 5: Announcement -->
          <div class="notification-item-card" data-category="announcements">
            <div class="notif-icon-box" style="background: var(--warning-light); color: var(--warning);">
              <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex align-items-center gap-2 mb-1">
                <span class="badge badge-review">HR Notice</span>
                <span class="text-xs text-muted">1 week ago</span>
              </div>
              <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--dark-navy);">HRMS Campus Recruitment Drive 2026 Guidelines</h4>
              <p class="text-sm text-muted mt-1">Ensure your educational marksheets and identity proofs are verified in the Documents tab prior to technical rounds.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
  <script src="../../static/js/notifications.js"></script>
</body>
</html>
"""

empty_states_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Empty States Showcase - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="dashboard", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Reusable Empty States</h1>
            <p class="page-subtitle">Production empty state components across all candidate module views</p>
          </div>
        </div>

        <div class="grid-2 mb-4">
          <!-- 1. No Applications -->
          <div class="card">
            <h4 class="text-xs font-bold text-muted uppercase mb-3">1. No Applications Yet</h4>
            <div class="empty-state">
              <div class="empty-icon-wrap">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
              </div>
              <h3 class="empty-title">No applications yet</h3>
              <p class="empty-desc">Start exploring available jobs and apply for your next career opportunity today.</p>
              <a href="../jobs/job_list.html" class="btn btn-primary">Browse Jobs</a>
            </div>
          </div>

          <!-- 2. No Notifications -->
          <div class="card">
            <h4 class="text-xs font-bold text-muted uppercase mb-3">2. No Notifications</h4>
            <div class="empty-state">
              <div class="empty-icon-wrap" style="background: var(--purple-light); color: var(--purple);">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
              </div>
              <h3 class="empty-title">All caught up!</h3>
              <p class="empty-desc">You don't have any unread notifications right now. Check back later for recruitment updates.</p>
              <a href="../candidate/dashboard.html" class="btn btn-outline">Back to Dashboard</a>
            </div>
          </div>

          <!-- 3. No Interviews -->
          <div class="card">
            <h4 class="text-xs font-bold text-muted uppercase mb-3">3. No Interviews Scheduled</h4>
            <div class="empty-state">
              <div class="empty-icon-wrap" style="background: var(--warning-light); color: var(--warning);">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
              </div>
              <h3 class="empty-title">No interviews scheduled</h3>
              <p class="empty-desc">When the HR team schedules an interview round with you, meeting invitations will appear here.</p>
              <a href="../applications/my_applications.html" class="btn btn-outline">Check Applications</a>
            </div>
          </div>

          <!-- 4. No Aptitude Tests -->
          <div class="card">
            <h4 class="text-xs font-bold text-muted uppercase mb-3">4. No Aptitude Tests</h4>
            <div class="empty-state">
              <div class="empty-icon-wrap" style="background: var(--success-light); color: var(--success);">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
              </div>
              <h3 class="empty-title">No active tests</h3>
              <p class="empty-desc">You currently have no pending online skill assessments or aptitude tests assigned.</p>
              <a href="../jobs/job_list.html" class="btn btn-primary">Find More Jobs</a>
            </div>
          </div>
        </div>

        <!-- 5. No Jobs Found -->
        <div class="card">
          <h4 class="text-xs font-bold text-muted uppercase mb-3">5. No Jobs Matching Search Criteria</h4>
          <div class="empty-state">
            <div class="empty-icon-wrap">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </div>
            <h3 class="empty-title">No jobs found matching your filters</h3>
            <p class="empty-desc">Try searching for other keywords, expanding your department preferences, or clearing filters.</p>
            <a href="../jobs/job_list.html" class="btn btn-outline">Reset Search & Filters</a>
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

os.makedirs('templates/notifications', exist_ok=True)
os.makedirs('templates/components', exist_ok=True)

with open('templates/notifications/notifications.html', 'w', encoding='utf-8') as f:
    f.write(notif_html)
with open('templates/components/empty_states.html', 'w', encoding='utf-8') as f:
    f.write(empty_states_html)

print("Notifications and Empty States generated successfully.")

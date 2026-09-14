import os
from build_common_shell import get_sidebar_html, get_header_html, get_modals_html

HERO_SVG = """
<svg viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg" style="max-height: 150px; width: auto;">
  <rect x="20" y="20" width="200" height="140" rx="14" fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>
  <circle cx="65" cy="65" r="22" fill="#FFFFFF"/>
  <path d="M53 82 C53 72 59 66 65 66 C71 66 77 72 77 82" fill="#1976F3"/>
  <circle cx="65" cy="58" r="8" fill="#1976F3"/>
  <rect x="100" y="52" width="95" height="10" rx="5" fill="#FFFFFF"/>
  <rect x="100" y="70" width="65" height="8" rx="4" fill="rgba(255,255,255,0.7)"/>
  <rect x="35" y="105" width="170" height="36" rx="8" fill="#FFFFFF" filter="drop-shadow(0 4px 10px rgba(0,0,0,0.15))"/>
  <circle cx="55" cy="123" r="10" fill="#E8F8F2"/>
  <path d="M51 123 L54 126 L60 119" stroke="#20A47A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="75" y="117" width="70" height="6" rx="3" fill="#172033"/>
  <rect x="75" y="127" width="45" height="5" rx="2.5" fill="#667085"/>
  <rect x="160" y="115" width="35" height="16" rx="8" fill="#EAF3FF"/>
  <text x="165" y="126" fill="#1976F3" font-size="8" font-family="Inter, sans-serif" font-weight="700">ACTIVE</text>
</svg>
"""

content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Candidate Dashboard - HRMS Portal</title>
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
        <!-- Hero Section -->
        <section class="dashboard-hero">
          <div class="hero-text">
            <h1 class="hero-title">Good Morning, Alan Shaji! 👋</h1>
            <p class="hero-subtitle">Welcome back to your candidate portal. Track your recruitment status, test scores, and interview updates in one place.</p>
            
            <div class="hero-metrics">
              <div class="hero-metric-item">
                <div class="hero-metric-label">Profile Completion</div>
                <div class="hero-metric-val">85%</div>
                <div class="hero-profile-bar">
                  <div class="hero-profile-fill"></div>
                </div>
              </div>
              <div class="hero-metric-item">
                <div class="hero-metric-label">Applications</div>
                <div class="hero-metric-val">8 Active</div>
              </div>
              <div class="hero-metric-item">
                <div class="hero-metric-label">Upcoming Interview</div>
                <div class="hero-metric-val">15 Sep 2026</div>
              </div>
            </div>
          </div>

          <div class="hero-illustration">
            {HERO_SVG}
          </div>
        </section>

        <!-- 4 Statistic Cards -->
        <section class="grid-4 mb-5">
          <div class="stat-card">
            <div class="stat-icon blue">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">8</div>
              <div class="stat-label">Total Applications</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon green">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">3</div>
              <div class="stat-label">Shortlisted</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon orange">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">2</div>
              <div class="stat-label">Interviews</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon purple">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">5</div>
              <div class="stat-label">Unread Alerts</div>
            </div>
          </div>
        </section>

        <!-- Two Column Section -->
        <section class="dashboard-split">
          <!-- LEFT: Recent Applications -->
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Recent Applications</h3>
                <p class="card-subtitle">Your latest recruitment submissions and status</p>
              </div>
              <a href="../applications/my_applications.html" class="btn btn-sm btn-outline">View All</a>
            </div>

            <div class="recent-apps-list">
              <div class="recent-app-item">
                <div class="d-flex align-items-center">
                  <div class="app-icon">PY</div>
                  <div class="app-info">
                    <div class="app-title">Python Developer</div>
                    <div class="app-meta">Applied on 01 Sep 2026 • IT Engineering</div>
                  </div>
                </div>
                <div class="d-flex align-items-center gap-3">
                  <span class="badge badge-shortlisted"><span class="badge-dot"></span>Shortlisted</span>
                  <a href="../applications/application_details.html" class="btn btn-sm btn-outline">Details</a>
                </div>
              </div>

              <div class="recent-app-item">
                <div class="d-flex align-items-center">
                  <div class="app-icon">UI</div>
                  <div class="app-info">
                    <div class="app-title">UI/UX Designer</div>
                    <div class="app-meta">Applied on 28 Aug 2026 • Product & Design</div>
                  </div>
                </div>
                <div class="d-flex align-items-center gap-3">
                  <span class="badge badge-review"><span class="badge-dot"></span>Under Review</span>
                  <a href="../applications/application_details.html" class="btn btn-sm btn-outline">Details</a>
                </div>
              </div>

              <div class="recent-app-item">
                <div class="d-flex align-items-center">
                  <div class="app-icon">DA</div>
                  <div class="app-info">
                    <div class="app-title">Data Analyst</div>
                    <div class="app-meta">Applied on 25 Aug 2026 • Business Analytics</div>
                  </div>
                </div>
                <div class="d-flex align-items-center gap-3">
                  <span class="badge badge-aptitude"><span class="badge-dot"></span>Aptitude Test</span>
                  <a href="../aptitude/aptitude_list.html" class="btn btn-sm btn-primary">Take Test</a>
                </div>
              </div>
            </div>
          </div>

          <!-- RIGHT: Upcoming Interviews -->
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Upcoming Interviews</h3>
                <p class="card-subtitle">Scheduled rounds with the HR team</p>
              </div>
              <a href="../interviews/interview_list.html" class="btn btn-sm btn-outline">All (2)</a>
            </div>

            <div class="upcoming-interview-card">
              <div class="interview-header-info">
                <div>
                  <div class="interview-job">Python Developer</div>
                  <div class="interview-type">Round 1: Technical Interview</div>
                </div>
                <span class="badge badge-interview">Online</span>
              </div>

              <div class="interview-time-box">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span>15 Sep 2026 • 11:00 AM - 11:45 AM</span>
              </div>

              <div class="d-flex justify-content-between align-items-center">
                <span class="text-xs text-muted">Platform: Google Meet</span>
                <a href="../interviews/interview_details.html" class="btn btn-sm btn-primary">Join Interview</a>
              </div>
            </div>

            <!-- Announcements -->
            <div class="mt-4 pt-3" style="border-top: 1px solid var(--border-light);">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <h4 style="font-size: 0.875rem; font-weight: 700;">Company Announcements</h4>
                <span class="badge badge-neutral">Notice</span>
              </div>
              <div class="announcement-item">
                <div class="announcement-title">Annual Recruitment Drive 2026</div>
                <div class="announcement-date">Assessment window open until 20 September 2026</div>
              </div>
            </div>
          </div>
        </section>

        <!-- Recommended Jobs -->
        <section class="card">
          <div class="card-header">
            <div>
              <h3 class="card-title">Recommended Jobs</h3>
              <p class="card-subtitle">Opportunities matching your skills in Python, Django, and SQL</p>
            </div>
            <a href="../jobs/job_list.html" class="btn btn-sm btn-primary">Explore All Jobs</a>
          </div>

          <div class="grid-3">
            <div class="job-card">
              <div class="job-card-header">
                <span class="job-dept-badge">IT Engineering</span>
                <span class="text-xs text-muted">2 days ago</span>
              </div>
              <h4 class="job-title">Python Developer</h4>
              <div class="job-meta-list">
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                  Kochi (Hybrid)
                </span>
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                  0-2 Years
                </span>
              </div>
              <p class="job-desc-snippet">Build scalable backend microservices, REST APIs, and database schemas with Django and PostgreSQL.</p>
              <div class="job-tags">
                <span class="job-tag">Python</span>
                <span class="job-tag">Django</span>
                <span class="job-tag">PostgreSQL</span>
              </div>
              <div class="job-card-footer">
                <span class="job-salary-tag">₹6 - 8.5 LPA</span>
                <div class="d-flex gap-2">
                  <a href="../jobs/job_details.html" class="btn btn-sm btn-outline">Details</a>
                  <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="Python Developer" data-job-dept="IT Engineering">Apply</button>
                </div>
              </div>
            </div>

            <div class="job-card">
              <div class="job-card-header">
                <span class="job-dept-badge">IT Engineering</span>
                <span class="text-xs text-muted">3 days ago</span>
              </div>
              <h4 class="job-title">Frontend Developer</h4>
              <div class="job-meta-list">
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                  Remote
                </span>
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                  1-3 Years
                </span>
              </div>
              <p class="job-desc-snippet">Develop modern, responsive web interfaces with vanilla JavaScript, HTML5, CSS3, and design systems.</p>
              <div class="job-tags">
                <span class="job-tag">HTML5/CSS3</span>
                <span class="job-tag">JavaScript</span>
                <span class="job-tag">UI/UX</span>
              </div>
              <div class="job-card-footer">
                <span class="job-salary-tag">₹7 - 9.5 LPA</span>
                <div class="d-flex gap-2">
                  <a href="../jobs/job_details.html" class="btn btn-sm btn-outline">Details</a>
                  <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="Frontend Developer" data-job-dept="IT Engineering">Apply</button>
                </div>
              </div>
            </div>

            <div class="job-card">
              <div class="job-card-header">
                <span class="job-dept-badge">Analytics</span>
                <span class="text-xs text-muted">5 days ago</span>
              </div>
              <h4 class="job-title">Junior Data Analyst</h4>
              <div class="job-meta-list">
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                  Bangalore
                </span>
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                  0-2 Years
                </span>
              </div>
              <p class="job-desc-snippet">Analyze user behavior and recruitment metrics using SQL, Pandas, and generate interactive dashboards.</p>
              <div class="job-tags">
                <span class="job-tag">SQL</span>
                <span class="job-tag">Python</span>
                <span class="job-tag">Tableau</span>
              </div>
              <div class="job-card-footer">
                <span class="job-salary-tag">₹5.5 - 7.5 LPA</span>
                <div class="d-flex gap-2">
                  <a href="../jobs/job_details.html" class="btn btn-sm btn-outline">Details</a>
                  <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="Junior Data Analyst" data-job-dept="Analytics">Apply</button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>

  {get_modals_html(rel_prefix="..")}

  <!-- DJANGO: {{% endblock %}} -->
  <script src="../../static/js/main.js"></script>
  <script src="../../static/js/jobs.js"></script>
</body>
</html>
"""

os.makedirs('templates/candidate', exist_ok=True)
with open('templates/candidate/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Dashboard created successfully.")

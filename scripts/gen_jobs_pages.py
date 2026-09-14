import os
from build_common_shell import get_sidebar_html, get_header_html, get_modals_html

job_list_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Vacancies - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="jobs", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Job Vacancies</h1>
            <p class="page-subtitle">Find the right opportunity for your career and apply in one click</p>
          </div>
        </div>

        <!-- Search & Filter Card -->
        <div class="job-search-card">
          <div class="job-filter-row">
            <div class="input-group">
              <input type="text" id="jobSearchInput" class="form-control" placeholder="Search jobs by title, skills or keywords...">
            </div>

            <select id="deptFilter" class="form-select">
              <option value="">All Departments</option>
              <option value="it">IT & Engineering</option>
              <option value="design">Product & Design</option>
              <option value="analytics">Business Analytics</option>
              <option value="hr">Human Resources</option>
            </select>

            <select id="expFilter" class="form-select">
              <option value="">All Experience</option>
              <option value="0-2">0 - 2 Years</option>
              <option value="1-3">1 - 3 Years</option>
              <option value="3-5">3 - 5 Years</option>
            </select>

            <select id="typeFilter" class="form-select">
              <option value="">All Job Types</option>
              <option value="full-time">Full Time</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
            </select>

            <button type="button" class="btn btn-primary" onclick="window.showToast('Filtered', 'Filters applied to jobs', 'info');">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <span>Search</span>
            </button>
          </div>
        </div>

        <!-- Available Jobs Counter -->
        <div class="d-flex justify-content-between align-items-center mb-4">
          <h2 style="font-size: 1.15rem; font-weight: 700; color: var(--dark-navy);" id="availableJobsCount">24 Available Jobs</h2>
          <div class="d-flex align-items-center gap-2">
            <span class="text-xs text-muted">Sort by:</span>
            <select class="form-select" style="height: 34px; width: 140px; font-size: 0.75rem; padding: 4px 10px;">
              <option>Latest First</option>
              <option>Highest Salary</option>
              <option>Experience</option>
            </select>
          </div>
        </div>

        <!-- Job Cards Grid -->
        <div class="grid-3" id="jobsGridContainer">
          <!-- Job 1 -->
          <div class="job-card job-card-item" data-title="python developer" data-dept="it" data-exp="0-2" data-type="hybrid" data-tags="python django postgresql">
            <div class="job-card-header">
              <span class="job-dept-badge">IT Engineering</span>
              <span class="text-xs text-muted">2 days ago</span>
            </div>
            <h3 class="job-title">Python Developer</h3>
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
              <span class="job-salary-tag">₹6.0 - 8.5 LPA</span>
              <div class="d-flex gap-2">
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
                <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="Python Developer" data-job-dept="IT Engineering">Apply Now</button>
              </div>
            </div>
          </div>

          <!-- Job 2 -->
          <div class="job-card job-card-item" data-title="software developer" data-dept="it" data-exp="1-3" data-type="full-time" data-tags="python react node fullstack">
            <div class="job-card-header">
              <span class="job-dept-badge">IT Engineering</span>
              <span class="text-xs text-muted">3 days ago</span>
            </div>
            <h3 class="job-title">Software Developer</h3>
            <div class="job-meta-list">
              <span class="job-meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                Bangalore
              </span>
              <span class="job-meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                1-3 Years
              </span>
            </div>
            <p class="job-desc-snippet">Full-stack development of enterprise web solutions using modern component frameworks and relational databases.</p>
            <div class="job-tags">
              <span class="job-tag">Python</span>
              <span class="job-tag">React</span>
              <span class="job-tag">SQL</span>
            </div>
            <div class="job-card-footer">
              <span class="job-salary-tag">₹8.0 - 12.0 LPA</span>
              <div class="d-flex gap-2">
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
                <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="Software Developer" data-job-dept="IT Engineering">Apply Now</button>
              </div>
            </div>
          </div>

          <!-- Job 3 -->
          <div class="job-card job-card-item" data-title="ui/ux designer" data-dept="design" data-exp="1-3" data-type="remote" data-tags="figma wireframe design ui ux">
            <div class="job-card-header">
              <span class="job-dept-badge" style="background: var(--purple-light); color: var(--purple);">Product & Design</span>
              <span class="text-xs text-muted">4 days ago</span>
            </div>
            <h3 class="job-title">UI/UX Designer</h3>
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
            <p class="job-desc-snippet">Design clean user flows, component libraries, and interactive SaaS dashboard experiences.</p>
            <div class="job-tags">
              <span class="job-tag">Figma</span>
              <span class="job-tag">Design Systems</span>
              <span class="job-tag">Wireframing</span>
            </div>
            <div class="job-card-footer">
              <span class="job-salary-tag">₹6.5 - 9.0 LPA</span>
              <div class="d-flex gap-2">
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
                <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="UI/UX Designer" data-job-dept="Product & Design">Apply Now</button>
              </div>
            </div>
          </div>

          <!-- Job 4 -->
          <div class="job-card job-card-item" data-title="data analyst" data-dept="analytics" data-exp="0-2" data-type="full-time" data-tags="sql python tableau analytics">
            <div class="job-card-header">
              <span class="job-dept-badge" style="background: var(--warning-light); color: var(--warning);">Business Analytics</span>
              <span class="text-xs text-muted">5 days ago</span>
            </div>
            <h3 class="job-title">Data Analyst</h3>
            <div class="job-meta-list">
              <span class="job-meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                Kochi
              </span>
              <span class="job-meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                0-2 Years
              </span>
            </div>
            <p class="job-desc-snippet">Query relational databases, evaluate recruitment metrics, and produce automated insight reports.</p>
            <div class="job-tags">
              <span class="job-tag">SQL</span>
              <span class="job-tag">Python</span>
              <span class="job-tag">PowerBI</span>
            </div>
            <div class="job-card-footer">
              <span class="job-salary-tag">₹5.5 - 7.5 LPA</span>
              <div class="d-flex gap-2">
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
                <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="Data Analyst" data-job-dept="Business Analytics">Apply Now</button>
              </div>
            </div>
          </div>

          <!-- Job 5 -->
          <div class="job-card job-card-item" data-title="frontend developer" data-dept="it" data-exp="1-3" data-type="remote" data-tags="javascript html5 css3 react frontend">
            <div class="job-card-header">
              <span class="job-dept-badge">IT Engineering</span>
              <span class="text-xs text-muted">1 week ago</span>
            </div>
            <h3 class="job-title">Frontend Developer</h3>
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
              <span class="job-salary-tag">₹7.0 - 10.0 LPA</span>
              <div class="d-flex gap-2">
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
                <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="Frontend Developer" data-job-dept="IT Engineering">Apply Now</button>
              </div>
            </div>
          </div>

          <!-- Job 6 -->
          <div class="job-card job-card-item" data-title="hr executive" data-dept="hr" data-exp="0-2" data-type="full-time" data-tags="recruitment hr screening onboarding">
            <div class="job-card-header">
              <span class="job-dept-badge" style="background: var(--success-light); color: var(--success);">Human Resources</span>
              <span class="text-xs text-muted">1 week ago</span>
            </div>
            <h3 class="job-title">HR Executive</h3>
            <div class="job-meta-list">
              <span class="job-meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                Kochi
              </span>
              <span class="job-meta-item">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                0-2 Years
              </span>
            </div>
            <p class="job-desc-snippet">Coordinate candidate screenings, aptitude tests, interview scheduling, and employee onboarding flows.</p>
            <div class="job-tags">
              <span class="job-tag">Talent Acquisition</span>
              <span class="job-tag">HRMS</span>
              <span class="job-tag">Communication</span>
            </div>
            <div class="job-card-footer">
              <span class="job-salary-tag">₹4.5 - 6.0 LPA</span>
              <div class="d-flex gap-2">
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
                <button type="button" class="btn btn-sm btn-primary btn-apply-job" data-job-title="HR Executive" data-job-dept="Human Resources">Apply Now</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty state (hidden by default) -->
        <div id="jobsEmptyState" style="display: none; margin-top: 30px;">
          <div class="empty-state">
            <div class="empty-icon-wrap">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            </div>
            <h3 class="empty-title">No Jobs Found</h3>
            <p class="empty-desc">We could not find any job vacancies matching your selected filters. Try searching for different keywords or resetting filters.</p>
            <button type="button" class="btn btn-outline" onclick="location.reload();">Reset Filters</button>
          </div>
        </div>

        <!-- Pagination -->
        <div class="pagination">
          <button class="page-btn" disabled>‹</button>
          <button class="page-btn active">1</button>
          <button class="page-btn">2</button>
          <button class="page-btn">3</button>
          <button class="page-btn">›</button>
        </div>
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

job_details_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Details: Python Developer - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="jobs", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="breadcrumb">
          <a href="job_list.html">Job Vacancies</a>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">Python Developer</span>
        </div>

        <!-- Job Details Hero Banner -->
        <div class="card mb-4">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-3">
            <div>
              <span class="job-dept-badge">IT Engineering</span>
              <h1 class="page-title mt-2">Python Developer</h1>
              <div class="job-meta-list">
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                  Kochi (Hybrid)
                </span>
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                  0 - 2 Years
                </span>
                <span class="job-meta-item">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                  Full Time
                </span>
                <span class="job-meta-item text-muted">Posted 2 days ago</span>
              </div>
            </div>

            <div class="d-flex gap-2">
              <a href="apply.html" class="btn btn-primary btn-lg">Apply Now</a>
              <button type="button" class="btn btn-outline" onclick="window.showToast('Link Copied', 'Job link copied to clipboard', 'info');">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                Share
              </button>
            </div>
          </div>
        </div>

        <!-- Main Layout: 2 Columns -->
        <div class="job-details-layout">
          <!-- Left Main Card -->
          <div class="card">
            <h3 class="card-title mb-3">Job Description</h3>
            <p class="mb-4">
              We are seeking a talented and proactive <strong>Python Developer</strong> to join our engineering division in Kochi. In this role, you will design, develop, and maintain clean, high-performance web applications, REST APIs, and database schemas that power our enterprise Human Resource Management System.
            </p>

            <h3 class="card-title mb-3">Key Responsibilities</h3>
            <ul style="margin-left: 20px; color: var(--secondary-text); margin-bottom: 24px; line-height: 1.7;">
              <li>Design, build, and deploy RESTful microservices and backend logic using Python and Django.</li>
              <li>Write efficient SQL queries, manage database migrations, and optimize PostgreSQL schemas.</li>
              <li>Collaborate closely with frontend developers and UI/UX designers to integrate modern web clients.</li>
              <li>Implement robust automated unit and integration test suites to ensure high code quality.</li>
              <li>Participate in code reviews, CI/CD pipeline improvements, and sprint planning meetings.</li>
            </ul>

            <h3 class="card-title mb-3">Requirements & Qualifications</h3>
            <ul style="margin-left: 20px; color: var(--secondary-text); margin-bottom: 24px; line-height: 1.7;">
              <li>MCA / B.Tech / B.Sc in Computer Science, Information Technology, or relevant engineering field.</li>
              <li>0 to 2 years of practical experience working with Python 3 and Django or FastAPI frameworks.</li>
              <li>Solid understanding of Object-Oriented Programming (OOP) principles and relational databases.</li>
              <li>Familiarity with Git, Linux environments, and container basics (Docker).</li>
              <li>Strong logical thinking, problem-solving skills, and clear technical communication.</li>
            </ul>

            <h3 class="card-title mb-3">Required Technical Skills</h3>
            <div class="d-flex flex-wrap gap-2 mb-4">
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Python 3.x</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Django / DRF</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">PostgreSQL</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">REST APIs</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Git & GitHub</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Docker</span>
            </div>

            <h3 class="card-title mb-3">Benefits & Perks</h3>
            <ul style="margin-left: 20px; color: var(--secondary-text); line-height: 1.7;">
              <li>Competitive compensation package with annual performance incentives.</li>
              <li>Comprehensive medical insurance coverage for self and family.</li>
              <li>Flexible hybrid working model (2 days remote, 3 days office).</li>
              <li>Continuous learning stipend and professional certification sponsorship.</li>
            </ul>
          </div>

          <!-- Right Sidebar Summary Card -->
          <div>
            <div class="card job-summary-card">
              <h3 class="card-title">Application Summary</h3>
              
              <div class="summary-spec-list">
                <div class="summary-spec-item">
                  <span class="summary-spec-label">Salary Range</span>
                  <span class="summary-spec-val text-primary">₹6.0 - 8.5 LPA</span>
                </div>
                <div class="summary-spec-item">
                  <span class="summary-spec-label">Location</span>
                  <span class="summary-spec-val">Kochi, Kerala (Hybrid)</span>
                </div>
                <div class="summary-spec-item">
                  <span class="summary-spec-label">Experience</span>
                  <span class="summary-spec-val">0 - 2 Years</span>
                </div>
                <div class="summary-spec-item">
                  <span class="summary-spec-label">Job Type</span>
                  <span class="summary-spec-val">Full Time</span>
                </div>
                <div class="summary-spec-item">
                  <span class="summary-spec-label">Department</span>
                  <span class="summary-spec-val">IT Engineering</span>
                </div>
                <div class="summary-spec-item">
                  <span class="summary-spec-label">Deadline</span>
                  <span class="summary-spec-val text-danger">30 Sep 2026</span>
                </div>
              </div>

              <a href="apply.html" class="btn btn-primary btn-block btn-lg mb-3">Apply For This Position</a>
              <p class="text-xs text-muted text-center">Applications are reviewed on a rolling basis.</p>
            </div>
          </div>
        </div>

        <!-- Similar Jobs -->
        <div class="mt-5">
          <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--dark-navy); margin-bottom: 16px;">Similar Job Opportunities</h2>
          <div class="grid-3">
            <div class="job-card">
              <div class="job-card-header">
                <span class="job-dept-badge">IT Engineering</span>
                <span class="text-xs text-muted">3 days ago</span>
              </div>
              <h3 class="job-title">Software Developer</h3>
              <div class="job-meta-list">
                <span class="job-meta-item">Bangalore</span>
                <span class="job-meta-item">1-3 Years</span>
              </div>
              <p class="job-desc-snippet">Full-stack software engineering for enterprise web applications.</p>
              <div class="job-card-footer">
                <span class="job-salary-tag">₹8 - 12 LPA</span>
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
              </div>
            </div>

            <div class="job-card">
              <div class="job-card-header">
                <span class="job-dept-badge">IT Engineering</span>
                <span class="text-xs text-muted">1 week ago</span>
              </div>
              <h3 class="job-title">Frontend Developer</h3>
              <div class="job-meta-list">
                <span class="job-meta-item">Remote</span>
                <span class="job-meta-item">1-3 Years</span>
              </div>
              <p class="job-desc-snippet">Responsive client-side architecture using HTML5, CSS3, and JavaScript.</p>
              <div class="job-card-footer">
                <span class="job-salary-tag">₹7 - 10 LPA</span>
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
              </div>
            </div>

            <div class="job-card">
              <div class="job-card-header">
                <span class="job-dept-badge" style="background: var(--warning-light); color: var(--warning);">Business Analytics</span>
                <span class="text-xs text-muted">5 days ago</span>
              </div>
              <h3 class="job-title">Data Analyst</h3>
              <div class="job-meta-list">
                <span class="job-meta-item">Kochi</span>
                <span class="job-meta-item">0-2 Years</span>
              </div>
              <p class="job-desc-snippet">Data pipelines, SQL queries, and interactive reporting dashboards.</p>
              <div class="job-card-footer">
                <span class="job-salary-tag">₹5.5 - 7.5 LPA</span>
                <a href="job_details.html" class="btn btn-sm btn-outline">View Details</a>
              </div>
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

os.makedirs('templates/jobs', exist_ok=True)
with open('templates/jobs/job_list.html', 'w', encoding='utf-8') as f:
    f.write(job_list_html)
with open('templates/jobs/job_details.html', 'w', encoding='utf-8') as f:
    f.write(job_details_html)

print("Job list and Job details generated.")

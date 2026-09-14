import os
from build_common_shell import get_sidebar_html, get_header_html

apply_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Apply For Job - HRMS Portal</title>
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
          <a href="job_details.html">Python Developer</a>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">Apply for Job</span>
        </div>

        <div class="page-header">
          <div>
            <h1 class="page-title">Submit Job Application</h1>
            <p class="page-subtitle">Confirm your details and submit your application to the HR team</p>
          </div>
        </div>

        <div style="max-width: 800px; margin: 0 auto;">
          <!-- Selected Job Card -->
          <div class="card mb-4" style="background: var(--primary-blue-subtle); border-color: #C6DEFF;">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
              <div>
                <span class="badge badge-applied mb-1">Applying For Position</span>
                <h2 style="font-size: 1.35rem; font-weight: 700; color: var(--dark-navy);">Python Developer</h2>
                <div class="text-xs text-muted mt-1">
                  IT Engineering • Kochi, Kerala (Hybrid) • 0-2 Years • ₹6.0 - 8.5 LPA
                </div>
              </div>
              <a href="job_details.html" class="btn btn-sm btn-outline">View Job Specs</a>
            </div>
          </div>

          <!-- Application Form -->
          <form id="standaloneApplyForm" class="card" onsubmit="event.preventDefault(); document.getElementById('applySuccessBlock').style.display='block'; this.style.display='none';">
            <h3 class="card-title mb-4">Candidate Information</h3>

            <div class="form-group">
              <label class="form-label">Full Name</label>
              <input type="text" class="form-control" value="Alan Shaji" readonly style="background: var(--page-bg);">
            </div>

            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">Email Address</label>
                <input type="email" class="form-control" value="alan.shaji@example.com" readonly style="background: var(--page-bg);">
              </div>
              <div class="form-group">
                <label class="form-label">Phone Number</label>
                <input type="tel" class="form-control" value="+91 98765 43210" readonly style="background: var(--page-bg);">
              </div>
            </div>

            <!-- Resume Selection -->
            <div class="form-group">
              <label class="form-label">Attached Resume</label>
              <div style="display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border: 1px solid var(--border-color); border-radius: var(--radius-md); background: #FFF;">
                <div class="d-flex align-items-center gap-3">
                  <div style="width: 40px; height: 40px; border-radius: var(--radius-sm); background: var(--danger-light); color: var(--danger); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.8rem;">PDF</div>
                  <div>
                    <div class="font-semibold text-navy">Alan_Shaji_Resume_2026.pdf</div>
                    <div class="text-xs text-muted">2.4 MB • Verified Profile Resume</div>
                  </div>
                </div>
                <a href="../candidate/documents.html" class="btn btn-sm btn-outline">Replace Resume</a>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Cover Note / Why are you a good fit? (Optional)</label>
              <textarea class="form-textarea" placeholder="Describe your relevant Python projects, Django experience, or any key achievements..."></textarea>
            </div>

            <div class="mb-4">
              <label class="form-check">
                <input type="checkbox" class="form-check-input" required checked>
                <span class="form-check-label">I confirm that the information provided is accurate and represents my true qualifications.</span>
              </label>
            </div>

            <div class="d-flex justify-content-end gap-3 pt-3" style="border-top: 1px solid var(--border-light);">
              <a href="job_details.html" class="btn btn-secondary">Cancel</a>
              <button type="submit" class="btn btn-primary btn-lg">
                <span>Submit Application</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
              </button>
            </div>
          </form>

          <!-- Success State Block (Revealed upon submit) -->
          <div id="applySuccessBlock" class="card" style="display: none; text-align: center; padding: 48px 32px;">
            <div style="width: 72px; height: 72px; border-radius: 50%; background: var(--success-light); color: var(--success); display: flex; align-items: center; justify-content: center; margin: 0 auto 20px;">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            <h2 style="font-size: 1.6rem; font-weight: 700; color: var(--dark-navy); margin-bottom: 8px;">Application Submitted Successfully!</h2>
            <p class="text-muted text-sm" style="max-width: 480px; margin: 0 auto 24px;">
              Your application for <strong>Python Developer</strong> has been registered in the HRMS recruitment pipeline.
            </p>

            <div style="background: var(--page-bg); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 18px; max-width: 420px; margin: 0 auto 28px; text-align: left;">
              <div class="d-flex justify-content-between mb-2">
                <span class="text-xs text-muted">Application ID:</span>
                <span class="text-xs font-bold text-navy">APP-2026-8841</span>
              </div>
              <div class="d-flex justify-content-between mb-2">
                <span class="text-xs text-muted">Applied Date:</span>
                <span class="text-xs font-semibold text-navy">06 September 2026</span>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-xs text-muted">Current Status:</span>
                <span class="badge badge-applied">Applied</span>
              </div>
            </div>

            <div class="d-flex justify-content-center gap-3">
              <a href="../applications/my_applications.html" class="btn btn-primary">Go to My Applications</a>
              <a href="job_list.html" class="btn btn-outline">Explore More Jobs</a>
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

my_apps_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Applications - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="applications", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">My Applications</h1>
            <p class="page-subtitle">Track all your job applications and recruitment milestones in one place</p>
          </div>
          <a href="../jobs/job_list.html" class="btn btn-primary">Explore More Jobs</a>
        </div>

        <!-- Top Statistics Cards -->
        <div class="grid-4 mb-5">
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
            <div class="stat-icon orange">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">2</div>
              <div class="stat-label">Under Review</div>
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
            <div class="stat-icon purple">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">1</div>
              <div class="stat-label">Selected</div>
            </div>
          </div>
        </div>

        <!-- Filter Tabs & Table Card -->
        <div class="card">
          <!-- Status Filter Tabs -->
          <div class="nav-tabs">
            <button class="nav-tab-btn active">All (8)</button>
            <button class="nav-tab-btn">Applied (1)</button>
            <button class="nav-tab-btn">Under Review (2)</button>
            <button class="nav-tab-btn">Shortlisted (3)</button>
            <button class="nav-tab-btn">Aptitude Test (1)</button>
            <button class="nav-tab-btn">Interview (1)</button>
            <button class="nav-tab-btn">Selected (1)</button>
            <button class="nav-tab-btn">Rejected (0)</button>
          </div>

          <!-- Applications Table -->
          <div class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>Job Position</th>
                  <th>Department</th>
                  <th>Location</th>
                  <th>Applied Date</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <div class="font-semibold text-navy">Python Developer</div>
                    <div class="text-xs text-muted">ID: #APP-2026-8841</div>
                  </td>
                  <td>IT Engineering</td>
                  <td>Kochi (Hybrid)</td>
                  <td>01 Sep 2026</td>
                  <td><span class="badge badge-shortlisted"><span class="badge-dot"></span>Shortlisted</span></td>
                  <td>
                    <a href="application_details.html" class="btn btn-sm btn-outline">View Details</a>
                  </td>
                </tr>

                <tr>
                  <td>
                    <div class="font-semibold text-navy">UI/UX Designer</div>
                    <div class="text-xs text-muted">ID: #APP-2026-8820</div>
                  </td>
                  <td>Product & Design</td>
                  <td>Remote</td>
                  <td>28 Aug 2026</td>
                  <td><span class="badge badge-review"><span class="badge-dot"></span>Resume Under Review</span></td>
                  <td>
                    <a href="application_details.html" class="btn btn-sm btn-outline">View Details</a>
                  </td>
                </tr>

                <tr>
                  <td>
                    <div class="font-semibold text-navy">Data Analyst</div>
                    <div class="text-xs text-muted">ID: #APP-2026-8794</div>
                  </td>
                  <td>Business Analytics</td>
                  <td>Kochi</td>
                  <td>25 Aug 2026</td>
                  <td><span class="badge badge-aptitude"><span class="badge-dot"></span>Aptitude Test Scheduled</span></td>
                  <td>
                    <a href="application_details.html" class="btn btn-sm btn-outline">View Details</a>
                  </td>
                </tr>

                <tr>
                  <td>
                    <div class="font-semibold text-navy">Frontend Developer</div>
                    <div class="text-xs text-muted">ID: #APP-2026-8751</div>
                  </td>
                  <td>IT Engineering</td>
                  <td>Remote</td>
                  <td>20 Aug 2026</td>
                  <td><span class="badge badge-interview"><span class="badge-dot"></span>Interview Scheduled</span></td>
                  <td>
                    <a href="application_details.html" class="btn btn-sm btn-outline">View Details</a>
                  </td>
                </tr>

                <tr>
                  <td>
                    <div class="font-semibold text-navy">Associate Software Engineer</div>
                    <div class="text-xs text-muted">ID: #APP-2026-8690</div>
                  </td>
                  <td>IT Engineering</td>
                  <td>Bangalore</td>
                  <td>10 Aug 2026</td>
                  <td><span class="badge badge-selected"><span class="badge-dot"></span>Selected</span></td>
                  <td>
                    <a href="application_details.html" class="btn btn-sm btn-outline">View Details</a>
                  </td>
                </tr>

                <tr>
                  <td>
                    <div class="font-semibold text-navy">Cloud Support Associate</div>
                    <div class="text-xs text-muted">ID: #APP-2026-8640</div>
                  </td>
                  <td>IT Support</td>
                  <td>Kochi</td>
                  <td>05 Aug 2026</td>
                  <td><span class="badge badge-applied"><span class="badge-dot"></span>Applied</span></td>
                  <td>
                    <a href="application_details.html" class="btn btn-sm btn-outline">View Details</a>
                  </td>
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

app_details_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Application Details - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="applications", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="breadcrumb">
          <a href="my_applications.html">My Applications</a>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">Application #APP-2026-8841</span>
        </div>

        <!-- Application Hero Header Card -->
        <div class="card mb-4">
          <div class="d-flex justify-content-between align-items-start flex-wrap gap-3">
            <div>
              <span class="job-dept-badge">IT Engineering</span>
              <h1 class="page-title mt-2">Python Developer</h1>
              <div class="text-xs text-muted mt-1">
                Application ID: <strong>#APP-2026-8841</strong> • Applied on 01 Sep 2026 • Kochi (Hybrid)
              </div>
            </div>
            <div>
              <span class="badge badge-interview" style="font-size: 0.875rem; padding: 6px 14px;"><span class="badge-dot"></span>Interview Scheduled</span>
            </div>
          </div>
        </div>

        <!-- Application Status Stepper -->
        <div class="card mb-4">
          <h3 class="card-title mb-3">Application Progress Stepper</h3>
          <div class="stepper-wrapper">
            <div class="stepper">
              <!-- Step 1 -->
              <div class="stepper-step completed">
                <div class="step-circle">✓</div>
                <div class="step-content">
                  <div class="step-title">Applied</div>
                  <div class="step-date">01 Sep 2026</div>
                </div>
              </div>

              <!-- Step 2 -->
              <div class="stepper-step completed">
                <div class="step-circle">✓</div>
                <div class="step-content">
                  <div class="step-title">Resume Review</div>
                  <div class="step-date">02 Sep 2026</div>
                </div>
              </div>

              <!-- Step 3 -->
              <div class="stepper-step completed">
                <div class="step-circle">✓</div>
                <div class="step-content">
                  <div class="step-title">Shortlisted</div>
                  <div class="step-date">03 Sep 2026</div>
                </div>
              </div>

              <!-- Step 4 -->
              <div class="stepper-step completed">
                <div class="step-circle">✓</div>
                <div class="step-content">
                  <div class="step-title">Aptitude Test</div>
                  <div class="step-date">Score: 85% (Passed)</div>
                </div>
              </div>

              <!-- Step 5 -->
              <div class="stepper-step current">
                <div class="step-circle">●</div>
                <div class="step-content">
                  <div class="step-title">Interview Scheduled</div>
                  <div class="step-date">15 Sep 2026</div>
                </div>
              </div>

              <!-- Step 6 -->
              <div class="stepper-step upcoming">
                <div class="step-circle">○</div>
                <div class="step-content">
                  <div class="step-title">Final Decision</div>
                  <div class="step-date">Pending</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Prominent Current Status Banner -->
        <div class="card mb-4" style="border-left: 5px solid var(--primary-blue); background: var(--primary-blue-subtle);">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div>
              <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--dark-navy);">Technical Interview Scheduled</h3>
              <p class="text-sm text-navy mt-1">
                Your Technical Interview with the Engineering Recruitment panel is confirmed for <strong>15 September 2026 at 11:00 AM IST</strong>.
              </p>
            </div>
            <a href="../interviews/interview_details.html" class="btn btn-primary">View Interview Details</a>
          </div>
        </div>

        <div class="grid-2 mb-4">
          <!-- Submission Info -->
          <div class="card">
            <h3 class="card-title mb-3">Submitted Application Data</h3>
            <div style="display: flex; flex-direction: column; gap: 14px;">
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Candidate Name:</span>
                <span class="text-xs font-semibold text-navy">Alan Shaji</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Email:</span>
                <span class="text-xs font-semibold text-navy">alan.shaji@example.com</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Phone:</span>
                <span class="text-xs font-semibold text-navy">+91 98765 43210</span>
              </div>
              <div class="d-flex justify-content-between border-bottom pb-2">
                <span class="text-xs text-muted">Highest Degree:</span>
                <span class="text-xs font-semibold text-navy">Master of Computer Applications (MCA)</span>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-xs text-muted">Resume Used:</span>
                <span class="text-xs font-semibold text-primary">Alan_Shaji_Resume_2026.pdf</span>
              </div>
            </div>
          </div>

          <!-- Recruitment Activity Log -->
          <div class="card">
            <h3 class="card-title mb-3">Recruitment Activity Updates</h3>
            <div style="display: flex; flex-direction: column; gap: 14px;">
              <div class="d-flex gap-3">
                <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--primary-blue); margin-top: 6px;"></div>
                <div>
                  <div class="text-xs font-semibold text-navy">Interview invite dispatched</div>
                  <div class="text-xs text-muted">Google Meet invitation sent by HR Team • 05 Sep 2026</div>
                </div>
              </div>
              <div class="d-flex gap-3">
                <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--success); margin-top: 6px;"></div>
                <div>
                  <div class="text-xs font-semibold text-navy">Aptitude Test evaluated</div>
                  <div class="text-xs text-muted">Candidate scored 85% (Passing criteria: 60%) • 04 Sep 2026</div>
                </div>
              </div>
              <div class="d-flex gap-3">
                <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--success); margin-top: 6px;"></div>
                <div>
                  <div class="text-xs font-semibold text-navy">Profile shortlisted by HR Lead</div>
                  <div class="text-xs text-muted">Skills match candidate requirements • 03 Sep 2026</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Showcase: Selection & Rejection Mockup Cards -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Outcome States Reference</h3>
            <span class="text-xs text-muted">UI States for Final Decision Stage</span>
          </div>

          <div class="grid-2">
            <!-- Selected Card -->
            <div style="background: var(--status-selected-bg); border: 1px solid #B8EBD6; border-radius: var(--radius-md); padding: 20px;">
              <div class="d-flex align-items-center gap-2 mb-2">
                <div style="width: 24px; height: 24px; border-radius: 50%; background: var(--success); color: #FFF; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700;">✓</div>
                <h4 style="color: var(--success); font-weight: 700; font-size: 1rem;">Candidate Selected State</h4>
              </div>
              <p class="text-xs" style="color: #172033; line-height: 1.5; margin-bottom: 12px;">
                Congratulations! You have been selected for the position of Python Developer. Our HR Operations team will reach out with the official offer letter and onboarding packet.
              </p>
              <button class="btn btn-sm btn-success">View Offer Letter</button>
            </div>

            <!-- Rejected Card -->
            <div style="background: var(--status-rejected-bg); border: 1px solid #FFD1D1; border-radius: var(--radius-md); padding: 20px;">
              <div class="d-flex align-items-center gap-2 mb-2">
                <div style="width: 24px; height: 24px; border-radius: 50%; background: var(--danger); color: #FFF; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700;">✕</div>
                <h4 style="color: var(--danger); font-weight: 700; font-size: 1rem;">Professional Rejection State</h4>
              </div>
              <p class="text-xs" style="color: #172033; line-height: 1.5; margin-bottom: 12px;">
                Thank you for your interest in joining our team. While we were impressed by your background, we have decided to proceed with other candidates whose experience more closely fits the role requirements.
              </p>
              <a href="../jobs/job_list.html" class="btn btn-sm btn-outline">Explore Other Roles</a>
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

with open('templates/jobs/apply.html', 'w', encoding='utf-8') as f:
    f.write(apply_html)
with open('templates/applications/my_applications.html', 'w', encoding='utf-8') as f:
    f.write(my_apps_html)
with open('templates/applications/application_details.html', 'w', encoding='utf-8') as f:
    f.write(app_details_html)

print("Apply, My Applications, and Application Details generated successfully.")

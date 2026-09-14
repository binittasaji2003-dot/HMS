import os
from build_common_shell import get_sidebar_html, get_header_html

profile_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Profile - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="profile", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Candidate Profile</h1>
            <p class="page-subtitle">Manage your personal, professional, and academic information</p>
          </div>
          <div class="d-flex gap-2">
            <a href="edit_profile.html" class="btn btn-primary">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
              <span>Edit Profile</span>
            </a>
            <a href="change_password.html" class="btn btn-outline">Change Password</a>
          </div>
        </div>

        <!-- Top Profile Hero Card -->
        <section class="profile-hero-card">
          <div class="d-flex align-items-center gap-4 flex-wrap">
            <div class="profile-avatar-large">AS</div>
            <div class="profile-details-main">
              <h2 class="profile-name">Alan Shaji</h2>
              <span class="profile-id-badge">Candidate ID: #CAN-2026-884 • Verified Candidate</span>
              <div class="profile-contact-chips">
                <span>📧 alan.shaji@example.com</span>
                <span>📱 +91 98765 43210</span>
                <span>📍 Kochi, Kerala, India</span>
              </div>
            </div>
          </div>

          <div class="profile-completion-box">
            <div class="d-flex justify-content-between mb-1">
              <span class="text-xs font-semibold text-navy">Profile Completion</span>
              <span class="text-xs font-bold text-primary">85%</span>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width: 85%;"></div>
            </div>
            <div class="text-xs text-muted mt-2">Add your Degree Provisional certificate to reach 100%.</div>
          </div>
        </section>

        <!-- Personal Information Section -->
        <section class="card mb-4">
          <div class="card-header">
            <div>
              <h3 class="card-title">Personal Information</h3>
              <p class="card-subtitle">Verified contact and demographic records</p>
            </div>
          </div>

          <div class="grid-3">
            <div>
              <label class="form-label text-muted">Full Name</label>
              <div class="font-semibold text-navy">Alan Shaji</div>
            </div>
            <div>
              <label class="form-label text-muted">Date of Birth</label>
              <div class="font-semibold text-navy">14 May 2002</div>
            </div>
            <div>
              <label class="form-label text-muted">Gender</label>
              <div class="font-semibold text-navy">Male</div>
            </div>
            <div>
              <label class="form-label text-muted">Phone Number</label>
              <div class="font-semibold text-navy">+91 98765 43210</div>
            </div>
            <div>
              <label class="form-label text-muted">Email Address</label>
              <div class="font-semibold text-navy">alan.shaji@example.com</div>
            </div>
            <div>
              <label class="form-label text-muted">Residential Address</label>
              <div class="font-semibold text-navy">42 Palm Grove, Marine Drive</div>
            </div>
            <div>
              <label class="form-label text-muted">City</label>
              <div class="font-semibold text-navy">Kochi</div>
            </div>
            <div>
              <label class="form-label text-muted">State</label>
              <div class="font-semibold text-navy">Kerala</div>
            </div>
            <div>
              <label class="form-label text-muted">Pincode</label>
              <div class="font-semibold text-navy">682011</div>
            </div>
          </div>
        </section>

        <!-- Professional Information -->
        <section class="card mb-4">
          <div class="card-header">
            <div>
              <h3 class="card-title">Professional Information</h3>
              <p class="card-subtitle">Technical skills, work experience, and job preferences</p>
            </div>
          </div>

          <div class="grid-2 mb-4">
            <div>
              <label class="form-label text-muted">Experience Level</label>
              <div class="font-semibold text-navy">Fresher / 0-1 Years Experience</div>
            </div>
            <div>
              <label class="form-label text-muted">Preferred Job Type</label>
              <div class="font-semibold text-navy">Full Time (Hybrid or Remote)</div>
            </div>
            <div>
              <label class="form-label text-muted">Preferred Locations</label>
              <div class="font-semibold text-navy">Kochi, Bangalore, Trivandrum, Remote</div>
            </div>
            <div>
              <label class="form-label text-muted">Notice Period</label>
              <div class="font-semibold text-navy">Immediate Joiner (0 Days)</div>
            </div>
          </div>

          <div>
            <label class="form-label text-muted mb-2">Technical Skills & Tools</label>
            <div class="d-flex flex-wrap gap-2">
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Python 3</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Django</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">PostgreSQL</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">JavaScript</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">HTML5 & CSS3</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">REST APIs</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Git & GitHub</span>
              <span class="badge badge-applied" style="font-size: 0.813rem; padding: 6px 12px;">Docker (Basic)</span>
            </div>
          </div>
        </section>

        <!-- Education History Section -->
        <section class="card">
          <div class="card-header">
            <div>
              <h3 class="card-title">Education History</h3>
              <p class="card-subtitle">Academic degrees and qualifications</p>
            </div>
          </div>

          <div class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>Degree / Course</th>
                  <th>Institution / Board</th>
                  <th>Graduation Year</th>
                  <th>Score / CGPA</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="font-semibold">Master of Computer Applications (MCA)</td>
                  <td>Cochin University of Science and Technology (CUSAT)</td>
                  <td>2024 - 2026</td>
                  <td class="font-bold text-navy">8.8 CGPA</td>
                  <td><span class="badge badge-shortlisted">Final Year</span></td>
                </tr>
                <tr>
                  <td class="font-semibold">Bachelor of Science in Computer Science (B.Sc CS)</td>
                  <td>Mahatma Gandhi University</td>
                  <td>2021 - 2024</td>
                  <td class="font-bold text-navy">86.5%</td>
                  <td><span class="badge badge-shortlisted">Completed</span></td>
                </tr>
                <tr>
                  <td class="font-semibold">Higher Secondary (12th) - Computer Science</td>
                  <td>St. Joseph's Higher Secondary School</td>
                  <td>2021</td>
                  <td class="font-bold text-navy">92.4%</td>
                  <td><span class="badge badge-shortlisted">Completed</span></td>
                </tr>
                <tr>
                  <td class="font-semibold">Secondary School Leaving Certificate (10th)</td>
                  <td>Carmel English Medium School</td>
                  <td>2019</td>
                  <td class="font-bold text-navy">94.0%</td>
                  <td><span class="badge badge-shortlisted">Completed</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
</body>
</html>
"""

edit_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Edit Profile - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="profile", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="breadcrumb">
          <a href="dashboard.html">Dashboard</a>
          <span class="breadcrumb-separator">/</span>
          <a href="profile.html">My Profile</a>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">Edit Profile</span>
        </div>

        <div class="page-header">
          <div>
            <h1 class="page-title">Edit Candidate Profile</h1>
            <p class="page-subtitle">Update your personal, professional, and academic records</p>
          </div>
        </div>

        <form action="profile.html" method="GET" onsubmit="alert('Profile changes saved successfully!');">
          <div class="card mb-4">
            <div class="card-header">
              <h3 class="card-title">1. Personal Information</h3>
            </div>
            
            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">Full Name <span class="required">*</span></label>
                <input type="text" class="form-control" value="Alan Shaji" required>
              </div>
              <div class="form-group">
                <label class="form-label">Date of Birth <span class="required">*</span></label>
                <input type="date" class="form-control" value="2002-05-14" required>
              </div>
              <div class="form-group">
                <label class="form-label">Gender <span class="required">*</span></label>
                <select class="form-select" required>
                  <option value="Male" selected>Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Phone Number <span class="required">*</span></label>
                <input type="tel" class="form-control" value="+91 98765 43210" required>
              </div>
              <div class="form-group">
                <label class="form-label">Email Address <span class="required">*</span></label>
                <input type="email" class="form-control" value="alan.shaji@example.com" required>
              </div>
              <div class="form-group">
                <label class="form-label">Residential Address</label>
                <input type="text" class="form-control" value="42 Palm Grove, Marine Drive">
              </div>
              <div class="form-group">
                <label class="form-label">City</label>
                <input type="text" class="form-control" value="Kochi">
              </div>
              <div class="form-group">
                <label class="form-label">State</label>
                <input type="text" class="form-control" value="Kerala">
              </div>
              <div class="form-group">
                <label class="form-label">Pincode</label>
                <input type="text" class="form-control" value="682011">
              </div>
            </div>
          </div>

          <div class="card mb-4">
            <div class="card-header">
              <h3 class="card-title">2. Professional Information & Preferences</h3>
            </div>
            
            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">Total Experience</label>
                <select class="form-select">
                  <option value="Fresher" selected>Fresher (0 - 1 Year)</option>
                  <option value="1-3">1 - 3 Years</option>
                  <option value="3-5">3 - 5 Years</option>
                  <option value="5+">5+ Years</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Preferred Job Type</label>
                <select class="form-select">
                  <option value="Full Time" selected>Full Time</option>
                  <option value="Part Time">Part Time</option>
                  <option value="Internship">Internship</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Preferred Location</label>
                <input type="text" class="form-control" value="Kochi, Bangalore, Remote">
              </div>
              <div class="form-group">
                <label class="form-label">Skills (Comma separated)</label>
                <input type="text" class="form-control" value="Python, Django, PostgreSQL, REST API, HTML5, CSS3, JavaScript, Git">
              </div>
            </div>
          </div>

          <div class="card mb-4">
            <div class="card-header">
              <h3 class="card-title">3. Education & Degree</h3>
            </div>
            
            <div class="grid-2">
              <div class="form-group">
                <label class="form-label">Highest Degree</label>
                <input type="text" class="form-control" value="Master of Computer Applications (MCA)">
              </div>
              <div class="form-group">
                <label class="form-label">University / College</label>
                <input type="text" class="form-control" value="Cochin University of Science and Technology (CUSAT)">
              </div>
              <div class="form-group">
                <label class="form-label">Graduation Year</label>
                <input type="number" class="form-control" value="2026">
              </div>
              <div class="form-group">
                <label class="form-label">Percentage / CGPA</label>
                <input type="text" class="form-control" value="8.8 CGPA">
              </div>
            </div>
          </div>

          <div class="d-flex justify-content-end gap-3 mb-5">
            <a href="profile.html" class="btn btn-secondary">Cancel</a>
            <button type="submit" class="btn btn-primary">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
</body>
</html>
"""

with open('templates/candidate/profile.html', 'w', encoding='utf-8') as f:
    f.write(profile_html)
with open('templates/candidate/edit_profile.html', 'w', encoding='utf-8') as f:
    f.write(edit_html)
print("Profile and Edit Profile generated successfully.")

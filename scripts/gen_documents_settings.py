import os
from build_common_shell import get_sidebar_html, get_header_html

docs_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Documents - HRMS Portal</title>
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
            <h1 class="page-title">My Documents</h1>
            <p class="page-subtitle">Manage your resume and required verification documents</p>
          </div>
        </div>

        <div class="dropzone" id="documentDropzone">
          <svg class="dropzone-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
          <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--dark-navy); margin-bottom: 4px;">Drag and drop your document here</h3>
          <p class="text-sm text-muted mb-3">Supports PDF, DOCX, PNG, JPG up to 10MB</p>
          <button type="button" class="btn btn-primary btn-sm">Browse Files</button>
          <input type="file" id="documentFileInput" style="display: none;">
        </div>

        <div id="uploadPreviewBox" style="display: none; align-items: center; justify-content: space-between; background: #FFF; border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 14px 20px; margin-bottom: 24px;">
          <div class="d-flex align-items-center gap-3">
            <div style="width: 38px; height: 38px; border-radius: var(--radius-sm); background: var(--primary-blue-light); color: var(--primary-blue); display: flex; align-items: center; justify-content: center; font-weight: 700;">NEW</div>
            <div>
              <div class="preview-file-name font-semibold text-navy">Document.pdf</div>
              <div class="preview-file-size text-xs text-muted">2.1 MB</div>
            </div>
          </div>
          <button type="button" class="btn btn-sm btn-success" onclick="alert('Document uploaded successfully!'); this.parentElement.style.display='none';">Upload Now</button>
        </div>

        <section>
          <h3 class="mb-3" style="font-size: 1.1rem; font-weight: 700;">Uploaded Documents (7)</h3>

          <div class="document-card">
            <div class="doc-info-group">
              <div class="doc-icon">PDF</div>
              <div>
                <div class="font-semibold text-navy">Resume / Curriculum Vitae</div>
                <div class="text-xs text-muted">Alan_Shaji_Resume_2026.pdf • 2.4 MB • Uploaded on 01 Sep 2026</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="badge badge-shortlisted"><span class="badge-dot"></span>Verified</span>
              <button class="btn btn-sm btn-outline" onclick="alert('Viewing Resume PDF');">View</button>
              <button class="btn btn-sm btn-outline" onclick="alert('Downloading Alan_Shaji_Resume_2026.pdf');">Download</button>
              <button class="btn btn-sm btn-secondary" onclick="document.getElementById('documentFileInput').click();">Replace</button>
            </div>
          </div>

          <div class="document-card">
            <div class="doc-info-group">
              <div class="doc-icon" style="background: var(--primary-blue-light); color: var(--primary-blue);">JPG</div>
              <div>
                <div class="font-semibold text-navy">Profile Photo (Formal)</div>
                <div class="text-xs text-muted">Alan_Photo_Formal.jpg • 1.1 MB • Uploaded on 01 Sep 2026</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="badge badge-shortlisted"><span class="badge-dot"></span>Verified</span>
              <button class="btn btn-sm btn-outline">View</button>
              <button class="btn btn-sm btn-outline">Download</button>
              <button class="btn btn-sm btn-secondary">Replace</button>
            </div>
          </div>

          <div class="document-card">
            <div class="doc-info-group">
              <div class="doc-icon">PDF</div>
              <div>
                <div class="font-semibold text-navy">Identity Proof (Aadhaar Card)</div>
                <div class="text-xs text-muted">Aadhaar_Card_Alan.pdf • 1.8 MB • Uploaded on 02 Sep 2026</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="badge badge-shortlisted"><span class="badge-dot"></span>Verified</span>
              <button class="btn btn-sm btn-outline">View</button>
              <button class="btn btn-sm btn-outline">Download</button>
              <button class="btn btn-sm btn-secondary">Replace</button>
            </div>
          </div>

          <div class="document-card">
            <div class="doc-info-group">
              <div class="doc-icon">PDF</div>
              <div>
                <div class="font-semibold text-navy">10th Standard Marksheet / Certificate</div>
                <div class="text-xs text-muted">10th_Certificate.pdf • 1.5 MB • Uploaded on 02 Sep 2026</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="badge badge-shortlisted"><span class="badge-dot"></span>Verified</span>
              <button class="btn btn-sm btn-outline">View</button>
              <button class="btn btn-sm btn-outline">Download</button>
              <button class="btn btn-sm btn-secondary">Replace</button>
            </div>
          </div>

          <div class="document-card">
            <div class="doc-info-group">
              <div class="doc-icon">PDF</div>
              <div>
                <div class="font-semibold text-navy">12th Standard Marksheet / Certificate</div>
                <div class="text-xs text-muted">12th_Certificate.pdf • 1.6 MB • Uploaded on 02 Sep 2026</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="badge badge-shortlisted"><span class="badge-dot"></span>Verified</span>
              <button class="btn btn-sm btn-outline">View</button>
              <button class="btn btn-sm btn-outline">Download</button>
              <button class="btn btn-sm btn-secondary">Replace</button>
            </div>
          </div>

          <div class="document-card">
            <div class="doc-info-group">
              <div class="doc-icon">PDF</div>
              <div>
                <div class="font-semibold text-navy">Degree Certificate / Provisional</div>
                <div class="text-xs text-muted">MCA_Provisional_Letter.pdf • 2.1 MB • Uploaded on 02 Sep 2026</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="badge badge-review"><span class="badge-dot"></span>Pending Review</span>
              <button class="btn btn-sm btn-outline">View</button>
              <button class="btn btn-sm btn-outline">Download</button>
              <button class="btn btn-sm btn-secondary">Replace</button>
            </div>
          </div>

          <div class="document-card">
            <div class="doc-info-group">
              <div class="doc-icon">PDF</div>
              <div>
                <div class="font-semibold text-navy">Certifications (Python & Django Specialization)</div>
                <div class="text-xs text-muted">Python_Cert_Coursera.pdf • 850 KB • Uploaded on 03 Sep 2026</div>
              </div>
            </div>
            <div class="d-flex align-items-center gap-3">
              <span class="badge badge-shortlisted"><span class="badge-dot"></span>Verified</span>
              <button class="btn btn-sm btn-outline">View</button>
              <button class="btn btn-sm btn-outline">Download</button>
              <button class="btn btn-sm btn-secondary">Replace</button>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
  <script src="../../static/js/forms.js"></script>
</body>
</html>
"""

settings_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Settings - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="settings", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Candidate Settings</h1>
            <p class="page-subtitle">Configure your portal preferences, notifications, and security</p>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">
            <h3 class="card-title">Notification Preferences</h3>
          </div>
          <div style="display: flex; flex-direction: column; gap: 16px;">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <div class="font-semibold text-navy">Email Alerts for Interview Schedules</div>
                <div class="text-xs text-muted">Receive meeting invites and calendar links directly via email</div>
              </div>
              <input type="checkbox" class="form-check-input" checked>
            </div>
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <div class="font-semibold text-navy">Application Status Updates</div>
                <div class="text-xs text-muted">Get notified whenever your application status changes (e.g., Shortlisted, Selected)</div>
              </div>
              <input type="checkbox" class="form-check-input" checked>
            </div>
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <div class="font-semibold text-navy">Aptitude Test Reminders</div>
                <div class="text-xs text-muted">Receive reminders 24 hours before test expiration</div>
              </div>
              <input type="checkbox" class="form-check-input" checked>
            </div>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">
            <h3 class="card-title">Privacy & Profile Visibility</h3>
          </div>
          <div style="display: flex; flex-direction: column; gap: 16px;">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <div class="font-semibold text-navy">Profile Visibility to Internal Recruiters</div>
                <div class="text-xs text-muted">Allow HR recruiters across all departments to view your resume for open roles</div>
              </div>
              <input type="checkbox" class="form-check-input" checked>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Security & Password</h3>
          </div>
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <div class="font-semibold text-navy">Account Password</div>
              <div class="text-xs text-muted">Last updated 3 months ago</div>
            </div>
            <a href="change_password.html" class="btn btn-outline-primary">Change Password</a>
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

pass_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Change Password - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/layout.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="app-shell">
    {get_sidebar_html(active_item="settings", rel_prefix="..")}

    <div class="main-wrapper">
      {get_header_html(rel_prefix="..")}

      <main class="main-content">
        <div class="breadcrumb">
          <a href="dashboard.html">Dashboard</a>
          <span class="breadcrumb-separator">/</span>
          <a href="settings.html">Settings</a>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">Change Password</span>
        </div>

        <div class="page-header">
          <div>
            <h1 class="page-title">Change Password</h1>
            <p class="page-subtitle">Ensure your candidate account stays safe and secure</p>
          </div>
        </div>

        <div class="card" style="max-width: 580px;">
          <form action="settings.html" method="GET" onsubmit="alert('Password updated successfully!');">
            <div class="form-group">
              <label class="form-label" for="currPass">Current Password <span class="required">*</span></label>
              <div class="input-group">
                <input type="password" id="currPass" class="form-control" placeholder="Enter current password" required>
                <button type="button" class="input-icon-btn toggle-password-btn" aria-label="Toggle password">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                </button>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label" for="newPass">New Password <span class="required">*</span></label>
              <div class="input-group">
                <input type="password" id="newPass" class="form-control" placeholder="Enter new password" required>
                <button type="button" class="input-icon-btn toggle-password-btn" aria-label="Toggle password">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                </button>
              </div>
              <span class="form-hint">Must contain at least 8 characters, one number, and one symbol.</span>
            </div>

            <div class="form-group">
              <label class="form-label" for="confPass">Confirm New Password <span class="required">*</span></label>
              <div class="input-group">
                <input type="password" id="confPass" class="form-control" placeholder="Confirm new password" required>
                <button type="button" class="input-icon-btn toggle-password-btn" aria-label="Toggle password">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                </button>
              </div>
            </div>

            <div class="d-flex justify-content-end gap-3 mt-4">
              <a href="settings.html" class="btn btn-secondary">Cancel</a>
              <button type="submit" class="btn btn-primary">Update Password</button>
            </div>
          </form>
        </div>
      </main>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
  <script src="../../static/js/forms.js"></script>
</body>
</html>
"""

with open('templates/candidate/documents.html', 'w', encoding='utf-8') as f:
    f.write(docs_html)
with open('templates/candidate/settings.html', 'w', encoding='utf-8') as f:
    f.write(settings_html)
with open('templates/candidate/change_password.html', 'w', encoding='utf-8') as f:
    f.write(pass_html)

print("Documents, Settings, and Change Password templates generated.")

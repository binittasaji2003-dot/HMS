# build_common_shell.py
import os

def get_sidebar_html(active_item="dashboard", rel_prefix=".."):
    items = [
        ("dashboard", "Dashboard", f"{rel_prefix}/candidate/dashboard.html", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>""", None),
        ("profile", "My Profile", f"{rel_prefix}/candidate/profile.html", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>""", None),
        ("jobs", "Job Vacancies", f"{rel_prefix}/jobs/job_list.html", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>""", "24"),
        ("applications", "My Applications", f"{rel_prefix}/applications/my_applications.html", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>""", "8"),
        ("aptitude", "Aptitude Tests", f"{rel_prefix}/aptitude/aptitude_list.html", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>""", None),
        ("interviews", "Interviews", f"{rel_prefix}/interviews/interview_list.html", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>""", "2"),
        ("notifications", "Notifications", f"{rel_prefix}/notifications/notifications.html", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>""", "5")
    ]

    html = f'''<!-- DJANGO: {{% include 'includes/sidebar.html' %}} -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <a href="{rel_prefix}/candidate/dashboard.html" class="brand-logo">
          <div class="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
          </div>
          <span class="brand-text">HRMS <span>Portal</span></span>
        </a>
      </div>

      <div class="sidebar-content">
        <div class="nav-section-title">Candidate Menu</div>
        <nav class="nav-group">
'''
    for key, label, url, icon, badge in items:
        is_active = "active" if key == active_item else ""
        badge_html = f'<span class="nav-badge">{badge}</span>' if badge else ''
        html += f'''          <a href="{url}" class="nav-item {is_active}">
            {icon}
            <span>{label}</span>
            {badge_html}
          </a>
'''

    html += f'''        </nav>

        <div class="sidebar-divider"></div>
        <div class="nav-section-title">Account & Help</div>
        <nav class="nav-group">
          <a href="{rel_prefix}/candidate/settings.html" class="nav-item {'active' if active_item == 'settings' else ''}">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            <span>Settings</span>
          </a>
          <a href="#" class="nav-item" onclick="alert('HRMS Support: Contact recruitment@company.com or call +91 (0484) 288-9900'); return false;">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <span>Help & Support</span>
          </a>
          <a href="{rel_prefix}/authentication/login.html" class="nav-item" style="color: var(--danger);">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            <span>Logout</span>
          </a>
        </nav>
      </div>

      <div class="sidebar-footer">
        <div class="user-quick-profile">
          <div class="user-avatar-sm">AS</div>
          <div class="user-details" style="display: block;">
            <div class="user-name">Alan Shaji</div>
            <div class="user-role">ID: #CAN-2026-884</div>
          </div>
        </div>
      </div>
    </aside>
    <div class="sidebar-backdrop"></div>
'''
    return html

def get_header_html(rel_prefix=".."):
    return f'''<!-- DJANGO: {{% include 'includes/header.html' %}} -->
    <header class="top-header">
      <div class="header-left">
        <button class="sidebar-toggle-btn" aria-label="Toggle navigation drawer">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
        </button>

        <div class="header-search">
          <svg class="header-search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <input type="text" class="header-search-input" placeholder="Search jobs, tests, applications...">
        </div>
      </div>

      <div class="header-right">
        <a href="{rel_prefix}/notifications/notifications.html" class="header-btn" title="Notifications">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
          <span class="header-badge-dot"></span>
        </a>

        <div class="header-divider"></div>

        <div class="user-profile-menu">
          <button class="user-profile-trigger">
            <div class="user-avatar">AS</div>
            <div class="user-details">
              <div class="user-name">Alan Shaji</div>
              <div class="user-role">Candidate</div>
            </div>
            <svg class="user-dropdown-arrow" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>

          <div class="user-dropdown-menu">
            <a href="{rel_prefix}/candidate/profile.html" class="dropdown-item">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              <span>My Profile</span>
            </a>
            <a href="{rel_prefix}/candidate/edit_profile.html" class="dropdown-item">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
              <span>Edit Profile</span>
            </a>
            <a href="{rel_prefix}/candidate/documents.html" class="dropdown-item">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
              <span>My Documents</span>
            </a>
            <a href="{rel_prefix}/candidate/change_password.html" class="dropdown-item">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              <span>Change Password</span>
            </a>
            <a href="{rel_prefix}/candidate/settings.html" class="dropdown-item">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
              <span>Settings</span>
            </a>
            <div class="dropdown-divider"></div>
            <a href="{rel_prefix}/authentication/login.html" class="dropdown-item" style="color: var(--danger);">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              <span>Logout</span>
            </a>
          </div>
        </div>
      </div>
    </header>
'''

def get_modals_html(rel_prefix=".."):
    return f'''<!-- DJANGO: {{% include 'includes/modals.html' %}} -->
  <!-- Apply Job Modal -->
  <div class="modal-overlay" id="applyJobModal">
    <div class="modal-dialog">
      <div class="modal-header">
        <div>
          <h3 class="modal-title">Apply for Job</h3>
          <p class="text-xs text-muted">Submit your application to the HR recruitment team</p>
        </div>
        <button type="button" class="modal-close-btn" data-modal-close aria-label="Close">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
      <form id="quickApplyForm">
        <div class="modal-body">
          <!-- Selected Job Summary Banner -->
          <div style="background: var(--primary-blue-light); border: 1px solid #C2DCFF; border-radius: var(--radius-md); padding: 14px 16px; margin-bottom: 20px;">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <span class="badge badge-applied" style="margin-bottom: 4px;">Job Application</span>
                <h4 id="modalJobTitle" style="color: var(--dark-navy); font-size: 1.05rem; margin-top: 2px;">Python Developer</h4>
                <div style="font-size: 0.75rem; color: var(--secondary-text); margin-top: 2px;">
                  <span id="modalJobDept">IT Engineering</span> • Kochi (Hybrid) • 0-2 Years
                </div>
              </div>
            </div>
          </div>

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

          <!-- Resume Attachment -->
          <div class="form-group">
            <label class="form-label">Active Resume</label>
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border: 1px solid var(--border-color); border-radius: var(--radius-md); background: #FFF;">
              <div class="d-flex align-items-center gap-3">
                <div style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: var(--danger-light); color: var(--danger); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem;">PDF</div>
                <div>
                  <div style="font-size: 0.844rem; font-weight: 600; color: var(--dark-navy);">Alan_Shaji_Resume_2026.pdf</div>
                  <div style="font-size: 0.7rem; color: var(--secondary-text);">2.4 MB • Updated on 01 Sep 2026</div>
                </div>
              </div>
              <a href="{rel_prefix}/candidate/documents.html" class="btn btn-sm btn-outline">Replace Resume</a>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Cover Note / Remarks (Optional)</label>
            <textarea class="form-textarea" placeholder="Highlight any specific projects, GitHub profile, or availability..."></textarea>
          </div>

          <div>
            <label class="form-check">
              <input type="checkbox" class="form-check-input" required checked>
              <span class="form-check-label">I confirm that the information provided is accurate and represents my true qualifications.</span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-modal-close>Cancel</button>
          <button type="submit" class="btn btn-primary">
            <span>Submit Application</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Application Success State Modal -->
  <div class="modal-overlay" id="applySuccessModal">
    <div class="modal-dialog" style="max-width: 480px; text-align: center;">
      <div class="modal-body" style="padding: 36px 28px;">
        <div style="width: 64px; height: 64px; border-radius: 50%; background: var(--success-light); color: var(--success); display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;">
          <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
        </div>
        <h3 class="modal-title" style="margin-bottom: 8px;">Application Submitted!</h3>
        <p class="text-sm text-muted" style="margin-bottom: 20px;">
          Your application has been received by the recruitment department. You can track updates and interview schedules in your candidate portal.
        </p>
        
        <div style="background: var(--page-bg); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 14px; margin-bottom: 24px; text-align: left;">
          <div class="d-flex justify-content-between mb-2">
            <span class="text-xs text-muted">Application ID:</span>
            <span class="text-xs font-bold text-navy" id="successApplicationId">APP-2026-8841</span>
          </div>
          <div class="d-flex justify-content-between mb-2">
            <span class="text-xs text-muted">Submission Date:</span>
            <span class="text-xs font-semibold text-navy">06 Sep 2026</span>
          </div>
          <div class="d-flex justify-content-between">
            <span class="text-xs text-muted">Initial Status:</span>
            <span class="badge badge-applied">Applied</span>
          </div>
        </div>

        <div class="d-flex justify-content-center gap-3">
          <a href="{rel_prefix}/applications/my_applications.html" class="btn btn-primary">View My Applications</a>
          <button type="button" class="btn btn-outline" data-modal-close>Close</button>
        </div>
      </div>
    </div>
  </div>
'''

os.makedirs('templates/includes', exist_ok=True)
with open('templates/includes/sidebar.html', 'w', encoding='utf-8') as f:
    f.write(get_sidebar_html())
with open('templates/includes/header.html', 'w', encoding='utf-8') as f:
    f.write(get_header_html())
with open('templates/includes/modals.html', 'w', encoding='utf-8') as f:
    f.write(get_modals_html())

print("Common shell components created.")

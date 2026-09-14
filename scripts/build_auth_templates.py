# build_auth_templates.py
import os

AUTH_SVG_ILLUSTRATION = """
<svg viewBox="0 0 500 380" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 100%; max-width: 400px; height: auto;">
  <rect x="40" y="40" width="420" height="290" rx="16" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
  <rect x="70" y="75" width="220" height="14" rx="7" fill="rgba(255,255,255,0.7)"/>
  <rect x="70" y="105" width="140" height="10" rx="5" fill="rgba(255,255,255,0.4)"/>
  
  <!-- Candidate Card Mockup -->
  <rect x="70" y="145" width="360" height="75" rx="12" fill="#FFFFFF" filter="drop-shadow(0 8px 16px rgba(0,0,0,0.15))"/>
  <circle cx="110" cy="182" r="22" fill="#EAF3FF"/>
  <path d="M100 195 C100 185 106 180 110 180 C114 180 120 185 120 195" fill="#1976F3"/>
  <circle cx="110" cy="174" r="7" fill="#1976F3"/>
  <rect x="145" y="168" width="120" height="10" rx="5" fill="#172033"/>
  <rect x="145" y="186" width="80" height="8" rx="4" fill="#667085"/>
  <rect x="330" y="172" width="80" height="22" rx="11" fill="#E8F8F2"/>
  <text x="345" y="187" fill="#20A47A" font-size="10" font-family="Inter, sans-serif" font-weight="700">SHORTLISTED</text>
  
  <!-- Second Card -->
  <rect x="70" y="235" width="360" height="65" rx="12" fill="rgba(255,255,255,0.9)"/>
  <circle cx="110" cy="267" r="18" fill="#F4EEFF"/>
  <rect x="145" y="258" width="110" height="9" rx="4" fill="#172033"/>
  <rect x="145" y="273" width="70" height="7" rx="3" fill="#667085"/>
  <rect x="330" y="256" width="80" height="22" rx="11" fill="#EAF3FF"/>
  <text x="347" y="271" fill="#1976F3" font-size="10" font-family="Inter, sans-serif" font-weight="700">INTERVIEW</text>

  <!-- Floating Elements -->
  <circle cx="430" cy="90" r="28" fill="#20A47A" opacity="0.2"/>
  <circle cx="430" cy="90" r="18" fill="#20A47A"/>
  <path d="M424 90 L428 94 L437 85" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

LOGIN_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Candidate Login - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="auth-wrapper">
    <!-- Left Column: Form -->
    <div class="auth-form-side">
      <a href="../../index.html" class="auth-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
        </div>
        <span class="brand-text">HRMS <span>Portal</span></span>
      </a>

      <div class="auth-header">
        <h1 class="auth-title">Welcome Back 👋</h1>
        <p class="auth-subtitle">Sign in with your registered email to access your candidate dashboard.</p>
      </div>

      <form action="../candidate/dashboard.html" method="GET">
        <div class="form-group">
          <label class="form-label" for="loginEmail">Email Address <span class="required">*</span></label>
          <input type="email" id="loginEmail" name="email" class="form-control" placeholder="candidate@example.com" value="alan.shaji@example.com" required>
        </div>

        <div class="form-group">
          <div class="d-flex justify-content-between align-items-center mb-1">
            <label class="form-label m-0" for="loginPassword">Password <span class="required">*</span></label>
            <a href="forgot_password.html" class="text-sm">Forgot Password?</a>
          </div>
          <div class="input-group">
            <input type="password" id="loginPassword" name="password" class="form-control" placeholder="Enter your password" value="password123" required>
            <button type="button" class="input-icon-btn toggle-password-btn" aria-label="Toggle password visibility">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            </button>
          </div>
        </div>

        <div class="d-flex justify-content-between align-items-center mb-4">
          <label class="form-check">
            <input type="checkbox" class="form-check-input" checked>
            <span class="form-check-label">Remember me for 30 days</span>
          </label>
        </div>

        <button type="submit" class="btn btn-primary btn-block btn-lg">
          <span>Login to Account</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </button>
      </form>

      <div class="mt-5 text-center">
        <p class="text-sm">Don't have an account yet? <a href="register.html" class="font-semibold text-primary">Create an Account</a></p>
      </div>
      
      <div class="mt-4 pt-3 text-center" style="border-top: 1px solid var(--border-light);">
        <a href="../../index.html" class="text-xs text-muted">← Back to Portal Hub & Overview</a>
      </div>
    </div>

    <!-- Right Column: HRMS Banner -->
    <div class="auth-banner-side">
      <div class="auth-illustration-container">
        {AUTH_SVG_ILLUSTRATION}
      </div>
      <div class="auth-banner-content">
        <h2 class="auth-banner-title">Advance Your Career With HRMS</h2>
        <p class="auth-banner-desc">Explore verified job opportunities, schedule technical interviews, take online skill assessments, and track every application status in real-time.</p>
        <div class="auth-features-list">
          <span class="auth-feature-tag">✓ Direct Recruiter Connect</span>
          <span class="auth-feature-tag">✓ Instant Status Updates</span>
          <span class="auth-feature-tag">✓ Online Aptitude Tests</span>
        </div>
      </div>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
  <script src="../../static/js/forms.js"></script>
</body>
</html>
"""

REGISTER_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Candidate Registration - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="auth-wrapper">
    <!-- Left Column: Form -->
    <div class="auth-form-side">
      <a href="../../index.html" class="auth-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
        </div>
        <span class="brand-text">HRMS <span>Portal</span></span>
      </a>

      <div class="auth-header">
        <h1 class="auth-title">Create Candidate Account</h1>
        <p class="auth-subtitle">Join our talent network and apply directly to verified openings.</p>
      </div>

      <form action="../candidate/dashboard.html" method="GET">
        <div class="form-group">
          <label class="form-label" for="regName">Full Name <span class="required">*</span></label>
          <input type="text" id="regName" name="name" class="form-control" placeholder="e.g. Alan Shaji" value="Alan Shaji" required>
        </div>

        <div class="grid-2">
          <div class="form-group">
            <label class="form-label" for="regEmail">Email Address <span class="required">*</span></label>
            <input type="email" id="regEmail" name="email" class="form-control" placeholder="alan@example.com" value="alan.shaji@example.com" required>
          </div>
          <div class="form-group">
            <label class="form-label" for="regPhone">Phone Number <span class="required">*</span></label>
            <input type="tel" id="regPhone" name="phone" class="form-control" placeholder="+91 98765 43210" value="+91 98765 43210" required>
          </div>
        </div>

        <div class="grid-2">
          <div class="form-group">
            <label class="form-label" for="regPassword">Password <span class="required">*</span></label>
            <div class="input-group">
              <input type="password" id="regPassword" name="password" class="form-control" placeholder="Min. 8 characters" value="Password@123" required>
              <button type="button" class="input-icon-btn toggle-password-btn" aria-label="Toggle password">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label" for="regConfirm">Confirm Password <span class="required">*</span></label>
            <div class="input-group">
              <input type="password" id="regConfirm" name="confirm_password" class="form-control" placeholder="Re-enter password" value="Password@123" required>
              <button type="button" class="input-icon-btn toggle-password-btn" aria-label="Toggle password">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
              </button>
            </div>
          </div>
        </div>

        <div class="mb-4">
          <label class="form-check">
            <input type="checkbox" class="form-check-input" required checked>
            <span class="form-check-label">I agree to the <a href="#">Terms & Conditions</a> and <a href="#">Privacy Policy</a></span>
          </label>
        </div>

        <button type="submit" class="btn btn-primary btn-block btn-lg">
          <span>Create Account</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
        </button>
      </form>

      <div class="mt-4 text-center">
        <p class="text-sm">Already have an account? <a href="login.html" class="font-semibold text-primary">Login</a></p>
      </div>
      
      <div class="mt-3 pt-3 text-center" style="border-top: 1px solid var(--border-light);">
        <a href="../../index.html" class="text-xs text-muted">← Back to Portal Hub</a>
      </div>
    </div>

    <!-- Right Column: Banner -->
    <div class="auth-banner-side">
      <div class="auth-illustration-container">
        {AUTH_SVG_ILLUSTRATION}
      </div>
      <div class="auth-banner-content">
        <h2 class="auth-banner-title">Join Our Talent Community</h2>
        <p class="auth-banner-desc">Complete your profile once, upload your verified documents, and unlock tailored career paths matching your tech stack and aspirations.</p>
        <div class="auth-features-list">
          <span class="auth-feature-tag">✓ 1-Click Applications</span>
          <span class="auth-feature-tag">✓ Transparent Hiring</span>
          <span class="auth-feature-tag">✓ Automated Feedback</span>
        </div>
      </div>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
  <script src="../../static/js/forms.js"></script>
</body>
</html>
"""

FORGOT_PASSWORD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Forgot Password - HRMS Portal</title>
  <!-- DJANGO: {{% load static %}} -->
  <link rel="stylesheet" href="../../static/css/base.css">
  <link rel="stylesheet" href="../../static/css/components.css">
  <link rel="stylesheet" href="../../static/css/pages.css">
</head>
<body>
  <!-- DJANGO: {{% block content %}} -->
  <div class="auth-wrapper">
    <!-- Left Column: Form -->
    <div class="auth-form-side">
      <a href="../../index.html" class="auth-brand">
        <div class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
        </div>
        <span class="brand-text">HRMS <span>Portal</span></span>
      </a>

      <div class="auth-header">
        <h1 class="auth-title">Forgot Password?</h1>
        <p class="auth-subtitle">No worries. Enter your registered email address and we will send you a reset link.</p>
      </div>

      <form action="login.html" method="GET" onsubmit="alert('Reset link sent to your email address!'); return true;">
        <div class="form-group">
          <label class="form-label" for="resetEmail">Registered Email Address <span class="required">*</span></label>
          <input type="email" id="resetEmail" name="email" class="form-control" placeholder="candidate@example.com" value="alan.shaji@example.com" required>
          <span class="form-hint">A password recovery link valid for 1 hour will be sent.</span>
        </div>

        <button type="submit" class="btn btn-primary btn-block btn-lg mt-4">
          <span>Send Reset Link</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </form>

      <div class="mt-5 text-center">
        <p class="text-sm">Remembered your password? <a href="login.html" class="font-semibold text-primary">Back to Login</a></p>
      </div>
    </div>

    <!-- Right Column: Banner -->
    <div class="auth-banner-side">
      <div class="auth-illustration-container">
        {AUTH_SVG_ILLUSTRATION}
      </div>
      <div class="auth-banner-content">
        <h2 class="auth-banner-title">Account Security First</h2>
        <p class="auth-banner-desc">We keep your candidate profile, resume credentials, and assessment evaluations securely protected with enterprise encryption.</p>
      </div>
    </div>
  </div>
  <!-- DJANGO: {{% endblock %}} -->

  <script src="../../static/js/main.js"></script>
</body>
</html>
"""

os.makedirs('templates/authentication', exist_ok=True)
with open('templates/authentication/login.html', 'w', encoding='utf-8') as f:
    f.write(LOGIN_HTML)
with open('templates/authentication/register.html', 'w', encoding='utf-8') as f:
    f.write(REGISTER_HTML)
with open('templates/authentication/forgot_password.html', 'w', encoding='utf-8') as f:
    f.write(FORGOT_PASSWORD_HTML)

print("Auth templates generated successfully.")

import os

base_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Candidate Portal - HRMS{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/base.css' %}">
  <link rel="stylesheet" href="{% static 'css/layout.css' %}">
  <link rel="stylesheet" href="{% static 'css/components.css' %}">
  <link rel="stylesheet" href="{% static 'css/pages.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  <div class="app-shell">
    {% include 'includes/sidebar.html' %}

    <div class="main-wrapper">
      {% include 'includes/header.html' %}

      <main class="main-content">
        {% block content %}
        <!-- Page specific content injected here -->
        {% endblock %}
      </main>
    </div>
  </div>

  {% include 'includes/modals.html' %}
  {% include 'includes/toast.html' %}

  <script src="{% static 'js/main.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
"""

base_auth_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}HRMS Candidate Authentication{% endblock %}</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/base.css' %}">
  <link rel="stylesheet" href="{% static 'css/components.css' %}">
  <link rel="stylesheet" href="{% static 'css/pages.css' %}">
  {% block extra_css %}{% endblock %}
</head>
<body>
  <div class="auth-wrapper">
    {% block content %}
    <!-- Auth content injected here -->
    {% endblock %}
  </div>

  <script src="{% static 'js/main.js' %}"></script>
  <script src="{% static 'js/forms.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
"""

toast_html = """<!-- Toast Container for alerts & messages -->
<div class="toast-container" id="globalToastContainer">
  {% if messages %}
    {% for message in messages %}
      <div class="toast toast-{{ message.tags }}">
        <div class="toast-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
        </div>
        <div class="toast-body">
          <div class="toast-title">{{ message.tags|capfirst }}</div>
          <div class="toast-message">{{ message }}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
      </div>
    {% endfor %}
  {% endif %}
</div>
"""

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(base_html)
with open('templates/base_auth.html', 'w', encoding='utf-8') as f:
    f.write(base_auth_html)
with open('templates/includes/toast.html', 'w', encoding='utf-8') as f:
    f.write(toast_html)

print("Base templates and toast partial generated.")

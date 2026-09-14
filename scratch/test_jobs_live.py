"""End-to-end live testing of the Job Application backend using standard library."""
import re
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:8000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def extract_csrf(html):
    match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
    if match:
        return match.group(1)
    # Check cookie
    for cookie in cj:
        if cookie.name == "csrftoken":
            return cookie.value
    return ""

def test_live_workflow():
    print("--- 1. Testing Unauthenticated Job List & Details ---")
    req = urllib.request.Request(f"{BASE_URL}/jobs/")
    with opener.open(req) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "Python Developer" in html
    print("[PASS] Jobs list rendered successfully.")

    req = urllib.request.Request(f"{BASE_URL}/jobs/1/")
    with opener.open(req) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "Python Developer" in html
    print("[PASS] Job details rendered successfully.")

    print("\n--- 2. Logging in as alan_candidate ---")
    req = urllib.request.Request(f"{BASE_URL}/login/")
    with opener.open(req) as resp:
        login_html = resp.read().decode("utf-8")
        csrf_token = extract_csrf(login_html)

    login_data = urllib.parse.urlencode({
        "csrfmiddlewaretoken": csrf_token,
        "email": "alan.shaji@example.com",
        "password": "password123",
    }).encode("utf-8")

    login_req = urllib.request.Request(
        f"{BASE_URL}/login/",
        data=login_data,
        headers={"Referer": f"{BASE_URL}/login/"},
    )
    with opener.open(login_req) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "Alan Shaji" in html or "Candidate Profile" in html
    print("[PASS] Authenticated as alan_candidate.")

    print("\n--- 3. Testing Apply Page for Job 1 ---")
    req = urllib.request.Request(f"{BASE_URL}/jobs/1/apply/")
    with opener.open(req) as resp:
        apply_html = resp.read().decode("utf-8")
        csrf_token = extract_csrf(apply_html)
    print(f"[PASS] Apply page loaded. CSRF present: {bool(csrf_token)}")

    print("\n--- 4. Submitting Application ---")
    if "Already Applied" not in apply_html:
        apply_data = urllib.parse.urlencode({
            "csrfmiddlewaretoken": csrf_token,
            "cover_note": "Applying via automated live verification test for Python Developer.",
        }).encode("utf-8")

        apply_req = urllib.request.Request(
            f"{BASE_URL}/jobs/1/apply/",
            data=apply_data,
            headers={"Referer": f"{BASE_URL}/jobs/1/apply/"},
        )
        with opener.open(apply_req) as resp:
            resp_html = resp.read().decode("utf-8")
            assert "Application Submitted Successfully!" in resp_html or "Already Applied" in resp_html
        print("[PASS] Application submission handled properly.")
    else:
        print("[INFO] Candidate already applied, testing duplicate detection.")

    print("\n--- 5. Verifying My Applications List ---")
    req = urllib.request.Request(f"{BASE_URL}/applications/")
    with opener.open(req) as resp:
        apps_html = resp.read().decode("utf-8")
        assert "Python Developer" in apps_html
        assert "APP-2026-" in apps_html
    print("[PASS] My Applications list contains submitted job.")

    # Find application ID
    match = re.search(r'href="(/applications/(\d+)/)"', apps_html)
    assert match is not None, "Could not find link to application details"
    app_url = match.group(1)
    print(f"[PASS] Found application URL: {app_url}")

    print("\n--- 6. Verifying Application Details Page ---")
    req = urllib.request.Request(f"{BASE_URL}{app_url}")
    with opener.open(req) as resp:
        details_html = resp.read().decode("utf-8")
        assert "Python Developer" in details_html
        assert "Application Progress Stepper" in details_html
        assert "Submitted Application Data" in details_html
    print("[PASS] Application Details page rendered successfully with status stepper.")

    print("\n--- 7. Verifying Duplicate Application Prevention ---")
    req = urllib.request.Request(f"{BASE_URL}/jobs/1/apply/")
    with opener.open(req) as resp:
        dup_html = resp.read().decode("utf-8")
        assert "Already Applied" in dup_html
    print("[PASS] Duplicate application correctly blocked on UI.")

    print("\n>>> ALL 7 LIVE WORKFLOW CHECKS PASSED ON RUNNING SERVER! <<<")

if __name__ == "__main__":
    test_live_workflow()

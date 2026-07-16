#!/usr/bin/env python3
"""
Supabase Auth Migration Test Suite for Admin Endpoints
Tests the new JWT-based authentication for admin routes
"""

import requests
import time
import json

BASE_URL = "https://quiz-compete-15.preview.emergentagent.com/api"

# Admin credentials from env
ADMIN_EMAIL = "admin@blude.local"
ADMIN_PASSWORD = "admin123"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_pass(msg):
    print(f"{GREEN}✓ PASS:{RESET} {msg}")

def log_fail(msg):
    print(f"{RED}✗ FAIL:{RESET} {msg}")

def log_info(msg):
    print(f"{YELLOW}ℹ INFO:{RESET} {msg}")

def log_section(msg):
    print(f"\n{BLUE}{'='*80}")
    print(f"{msg}")
    print(f"{'='*80}{RESET}\n")

# Test counters
tests_passed = 0
tests_failed = 0
test_results = []

def record_result(test_name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        log_pass(f"{test_name} - {details}")
    else:
        tests_failed += 1
        log_fail(f"{test_name} - {details}")
    test_results.append({"test": test_name, "passed": passed, "details": details})

def generate_unique_email():
    return f"test_{int(time.time() * 1000000)}@example.com"

def generate_unique_phone():
    return f"9{int(time.time() * 1000) % 1000000000}"

# ============================================================================
# TEST 1: POST /api/admin/login - Correct credentials with email field
# ============================================================================
def test_admin_login_email_success():
    log_info("TEST 1: Admin login with email field - correct credentials")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Login Email Success", False, f"Expected 200, got {resp.status_code}. Response: {resp.text}")
            return None
        
        data = resp.json()
        
        # Validate response structure
        if data.get("ok") != True:
            record_result("Admin Login Email Success", False, f"Expected ok=true, got {data.get('ok')}")
            return None
        
        if "token" not in data:
            record_result("Admin Login Email Success", False, "Missing 'token' in response")
            return None
        
        token = data["token"]
        
        # Validate JWT token format (should be long, ~800+ chars for ES256)
        if len(token) < 100:
            record_result("Admin Login Email Success", False, f"Token too short ({len(token)} chars), expected JWT ~800+ chars")
            return None
        
        # Validate other fields
        if "refresh_token" not in data:
            record_result("Admin Login Email Success", False, "Missing 'refresh_token' in response")
            return None
        
        if "expires_at" not in data:
            record_result("Admin Login Email Success", False, "Missing 'expires_at' in response")
            return None
        
        if "user" not in data:
            record_result("Admin Login Email Success", False, "Missing 'user' in response")
            return None
        
        user = data["user"]
        if user.get("email") != ADMIN_EMAIL:
            record_result("Admin Login Email Success", False, f"Expected user.email={ADMIN_EMAIL}, got {user.get('email')}")
            return None
        
        if "id" not in user:
            record_result("Admin Login Email Success", False, "Missing 'user.id' in response")
            return None
        
        record_result("Admin Login Email Success", True, f"Login successful, JWT token length={len(token)}, user.email={user['email']}")
        return token
    
    except Exception as e:
        record_result("Admin Login Email Success", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 2: POST /api/admin/login - Legacy username field (backward compat)
# ============================================================================
def test_admin_login_username_success():
    log_info("TEST 2: Admin login with username field (backward compat)")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Login Username Success", False, f"Expected 200, got {resp.status_code}. Response: {resp.text}")
            return None
        
        data = resp.json()
        
        if data.get("ok") != True:
            record_result("Admin Login Username Success", False, f"Expected ok=true, got {data.get('ok')}")
            return None
        
        if "token" not in data or len(data["token"]) < 100:
            record_result("Admin Login Username Success", False, "Missing or invalid token")
            return None
        
        record_result("Admin Login Username Success", True, f"Legacy username field works, token length={len(data['token'])}")
        return data["token"]
    
    except Exception as e:
        record_result("Admin Login Username Success", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 3: POST /api/admin/login - Wrong password
# ============================================================================
def test_admin_login_wrong_password():
    log_info("TEST 3: Admin login - wrong password")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword123"
        }, timeout=10)
        
        if resp.status_code != 401:
            record_result("Admin Login Wrong Password", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if "error" not in data:
            record_result("Admin Login Wrong Password", False, "Missing 'error' in response")
            return
        
        record_result("Admin Login Wrong Password", True, f"Wrong password rejected with error: {data['error']}")
    
    except Exception as e:
        record_result("Admin Login Wrong Password", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 4: POST /api/admin/login - Wrong email
# ============================================================================
def test_admin_login_wrong_email():
    log_info("TEST 4: Admin login - wrong email")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": "wrong@example.com",
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        if resp.status_code not in [401, 403]:
            record_result("Admin Login Wrong Email", False, f"Expected 401 or 403, got {resp.status_code}")
            return
        
        data = resp.json()
        if "error" not in data:
            record_result("Admin Login Wrong Email", False, "Missing 'error' in response")
            return
        
        record_result("Admin Login Wrong Email", True, f"Wrong email rejected with status {resp.status_code}, error: {data['error']}")
    
    except Exception as e:
        record_result("Admin Login Wrong Email", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 5: GET /api/admin/stats - Without Authorization header
# ============================================================================
def test_admin_stats_no_auth():
    log_info("TEST 5: Admin stats - without Authorization header")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/stats", timeout=10)
        
        if resp.status_code != 401:
            record_result("Admin Stats No Auth", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("error") != "Unauthorized":
            record_result("Admin Stats No Auth", False, f"Expected error='Unauthorized', got {data.get('error')}")
            return
        
        record_result("Admin Stats No Auth", True, "Correctly returned 401 Unauthorized")
    
    except Exception as e:
        record_result("Admin Stats No Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 6: GET /api/admin/participants - Without Authorization header
# ============================================================================
def test_admin_participants_no_auth():
    log_info("TEST 6: Admin participants - without Authorization header")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/participants", timeout=10)
        
        if resp.status_code != 401:
            record_result("Admin Participants No Auth", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("error") != "Unauthorized":
            record_result("Admin Participants No Auth", False, f"Expected error='Unauthorized', got {data.get('error')}")
            return
        
        record_result("Admin Participants No Auth", True, "Correctly returned 401 Unauthorized")
    
    except Exception as e:
        record_result("Admin Participants No Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 7: GET /api/admin/leaderboard - Without Authorization header
# ============================================================================
def test_admin_leaderboard_no_auth():
    log_info("TEST 7: Admin leaderboard - without Authorization header")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/leaderboard", timeout=10)
        
        if resp.status_code != 401:
            record_result("Admin Leaderboard No Auth", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("error") != "Unauthorized":
            record_result("Admin Leaderboard No Auth", False, f"Expected error='Unauthorized', got {data.get('error')}")
            return
        
        record_result("Admin Leaderboard No Auth", True, "Correctly returned 401 Unauthorized")
    
    except Exception as e:
        record_result("Admin Leaderboard No Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 8: GET /api/admin/export - Without Authorization header
# ============================================================================
def test_admin_export_no_auth():
    log_info("TEST 8: Admin export - without Authorization header")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/export", timeout=10)
        
        if resp.status_code != 401:
            record_result("Admin Export No Auth", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("error") != "Unauthorized":
            record_result("Admin Export No Auth", False, f"Expected error='Unauthorized', got {data.get('error')}")
            return
        
        record_result("Admin Export No Auth", True, "Correctly returned 401 Unauthorized")
    
    except Exception as e:
        record_result("Admin Export No Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 9: GET /api/admin/stats - With valid token
# ============================================================================
def test_admin_stats_with_auth(token):
    log_info("TEST 9: Admin stats - with valid Authorization token")
    
    if not token:
        record_result("Admin Stats With Auth", False, "No token provided")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Stats With Auth", False, f"Expected 200, got {resp.status_code}. Response: {resp.text}")
            return
        
        data = resp.json()
        
        required_fields = ["total", "in_progress", "completed"]
        for field in required_fields:
            if field not in data:
                record_result("Admin Stats With Auth", False, f"Missing field: {field}")
                return
        
        record_result("Admin Stats With Auth", True, f"Stats retrieved: total={data['total']}, in_progress={data['in_progress']}, completed={data['completed']}")
    
    except Exception as e:
        record_result("Admin Stats With Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 10: GET /api/admin/participants - With valid token
# ============================================================================
def test_admin_participants_with_auth(token):
    log_info("TEST 10: Admin participants - with valid Authorization token")
    
    if not token:
        record_result("Admin Participants With Auth", False, "No token provided")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/admin/participants", headers=headers, timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Participants With Auth", False, f"Expected 200, got {resp.status_code}. Response: {resp.text}")
            return
        
        data = resp.json()
        
        if "rows" not in data:
            record_result("Admin Participants With Auth", False, "Missing 'rows' in response")
            return
        
        rows = data["rows"]
        if not isinstance(rows, list):
            record_result("Admin Participants With Auth", False, "rows is not a list")
            return
        
        record_result("Admin Participants With Auth", True, f"Participants retrieved: {len(rows)} rows")
    
    except Exception as e:
        record_result("Admin Participants With Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 11: GET /api/admin/leaderboard - With valid token
# ============================================================================
def test_admin_leaderboard_with_auth(token):
    log_info("TEST 11: Admin leaderboard - with valid Authorization token")
    
    if not token:
        record_result("Admin Leaderboard With Auth", False, "No token provided")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/admin/leaderboard", headers=headers, timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Leaderboard With Auth", False, f"Expected 200, got {resp.status_code}. Response: {resp.text}")
            return
        
        data = resp.json()
        
        if "rows" not in data:
            record_result("Admin Leaderboard With Auth", False, "Missing 'rows' in response")
            return
        
        rows = data["rows"]
        if not isinstance(rows, list):
            record_result("Admin Leaderboard With Auth", False, "rows is not a list")
            return
        
        record_result("Admin Leaderboard With Auth", True, f"Leaderboard retrieved: {len(rows)} entries")
    
    except Exception as e:
        record_result("Admin Leaderboard With Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 12: GET /api/admin/export - With valid token
# ============================================================================
def test_admin_export_with_auth(token):
    log_info("TEST 12: Admin export - with valid Authorization token")
    
    if not token:
        record_result("Admin Export With Auth", False, "No token provided")
        return
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/admin/export", headers=headers, timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Export With Auth", False, f"Expected 200, got {resp.status_code}. Response: {resp.text}")
            return
        
        # Check Content-Type
        content_type = resp.headers.get("Content-Type", "")
        if "text/csv" not in content_type:
            record_result("Admin Export With Auth", False, f"Expected Content-Type text/csv, got {content_type}")
            return
        
        # Check Content-Disposition
        content_disp = resp.headers.get("Content-Disposition", "")
        if "attachment" not in content_disp:
            record_result("Admin Export With Auth", False, f"Expected Content-Disposition with attachment, got {content_disp}")
            return
        
        csv_text = resp.text
        lines = csv_text.split('\n')
        
        if len(lines) < 1:
            record_result("Admin Export With Auth", False, "CSV has no lines")
            return
        
        record_result("Admin Export With Auth", True, f"CSV export successful, {len(lines)} lines")
    
    except Exception as e:
        record_result("Admin Export With Auth", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 13: GET /api/admin/stats - With invalid token
# ============================================================================
def test_admin_stats_invalid_token():
    log_info("TEST 13: Admin stats - with invalid token")
    
    try:
        headers = {"Authorization": "Bearer INVALID_TOKEN_12345"}
        resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=10)
        
        if resp.status_code != 401:
            record_result("Admin Stats Invalid Token", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("error") != "Unauthorized":
            record_result("Admin Stats Invalid Token", False, f"Expected error='Unauthorized', got {data.get('error')}")
            return
        
        record_result("Admin Stats Invalid Token", True, "Invalid token correctly rejected with 401")
    
    except Exception as e:
        record_result("Admin Stats Invalid Token", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 14: POST /api/register - Participant endpoint (no auth required)
# ============================================================================
def test_participant_register_no_auth():
    log_info("TEST 14: Participant register - no auth required")
    
    email = generate_unique_email()
    phone = generate_unique_phone()
    
    try:
        resp = requests.post(f"{BASE_URL}/register", json={
            "full_name": "Auth Test User",
            "email": email,
            "phone": phone,
            "college": "Test College",
            "department": "Test Dept",
            "year": "1"
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("Participant Register No Auth", False, f"Expected 200, got {resp.status_code}")
            return None
        
        data = resp.json()
        
        if "participant" not in data or "session_token" not in data:
            record_result("Participant Register No Auth", False, "Missing participant or session_token")
            return None
        
        record_result("Participant Register No Auth", True, "Participant registration works without auth")
        return data
    
    except Exception as e:
        record_result("Participant Register No Auth", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 15: POST /api/quiz/start - Participant endpoint (no auth required)
# ============================================================================
def test_participant_quiz_start_no_auth(participant_data):
    log_info("TEST 15: Participant quiz start - no auth required")
    
    if not participant_data:
        record_result("Participant Quiz Start No Auth", False, "No participant data")
        return
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/start", json={
            "participant_id": participant_data["participant"]["id"],
            "session_token": participant_data["session_token"]
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("Participant Quiz Start No Auth", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        
        if "questions" not in data or len(data["questions"]) != 30:
            record_result("Participant Quiz Start No Auth", False, "Invalid quiz start response")
            return
        
        record_result("Participant Quiz Start No Auth", True, "Quiz start works without auth, 30 questions returned")
    
    except Exception as e:
        record_result("Participant Quiz Start No Auth", False, f"Exception: {str(e)}")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def run_all_tests():
    log_section("SUPABASE AUTH MIGRATION TEST SUITE FOR ADMIN ENDPOINTS")
    
    # Section 1: Admin Login Tests
    log_section("SECTION 1: ADMIN LOGIN TESTS")
    valid_token = test_admin_login_email_success()
    test_admin_login_username_success()
    test_admin_login_wrong_password()
    test_admin_login_wrong_email()
    
    # Section 2: Admin Endpoints Without Auth
    log_section("SECTION 2: ADMIN ENDPOINTS WITHOUT AUTHORIZATION (Should Return 401)")
    test_admin_stats_no_auth()
    test_admin_participants_no_auth()
    test_admin_leaderboard_no_auth()
    test_admin_export_no_auth()
    
    # Section 3: Admin Endpoints With Valid Auth
    log_section("SECTION 3: ADMIN ENDPOINTS WITH VALID AUTHORIZATION (Should Return 200)")
    if valid_token:
        test_admin_stats_with_auth(valid_token)
        test_admin_participants_with_auth(valid_token)
        test_admin_leaderboard_with_auth(valid_token)
        test_admin_export_with_auth(valid_token)
    else:
        log_fail("Skipping auth tests - no valid token obtained")
        global tests_failed
        tests_failed += 4
    
    # Section 4: Admin Endpoints With Invalid Token
    log_section("SECTION 4: ADMIN ENDPOINTS WITH INVALID TOKEN (Should Return 401)")
    test_admin_stats_invalid_token()
    
    # Section 5: Participant Endpoints (No Auth Required)
    log_section("SECTION 5: PARTICIPANT ENDPOINTS (No Auth Required)")
    participant_data = test_participant_register_no_auth()
    test_participant_quiz_start_no_auth(participant_data)
    
    # Summary
    log_section("TEST SUMMARY")
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    print(f"{RED}Failed: {tests_failed}{RESET}")
    if tests_passed + tests_failed > 0:
        print(f"Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")
    print("="*80 + "\n")
    
    if tests_failed > 0:
        print(f"{RED}FAILED TESTS:{RESET}")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['test']}: {result['details']}")
        print()
    else:
        print(f"{GREEN}ALL TESTS PASSED! ✓{RESET}\n")
    
    return tests_failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

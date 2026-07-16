#!/usr/bin/env python3
"""
Additional edge case tests for Supabase Auth migration
"""

import requests
import time

BASE_URL = "https://quiz-compete-15.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@blude.local"
ADMIN_PASSWORD = "admin123"

# Color codes
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

tests_passed = 0
tests_failed = 0

def record_result(test_name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        log_pass(f"{test_name} - {details}")
    else:
        tests_failed += 1
        log_fail(f"{test_name} - {details}")

# ============================================================================
# TEST 1: Verify JWT token is ES256 format (long token)
# ============================================================================
def test_jwt_token_format():
    log_info("TEST 1: Verify JWT token format (ES256, ~800+ chars)")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("JWT Token Format", False, f"Login failed: {resp.status_code}")
            return None
        
        data = resp.json()
        token = data.get("token", "")
        
        # JWT should have 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            record_result("JWT Token Format", False, f"JWT should have 3 parts, got {len(parts)}")
            return None
        
        # ES256 tokens are typically 800+ characters
        if len(token) < 700:
            record_result("JWT Token Format", False, f"Token too short for ES256: {len(token)} chars")
            return None
        
        record_result("JWT Token Format", True, f"Valid JWT with {len(token)} chars, 3 parts")
        return token
    
    except Exception as e:
        record_result("JWT Token Format", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 2: Missing Authorization header (no Bearer prefix)
# ============================================================================
def test_missing_bearer_prefix():
    log_info("TEST 2: Authorization header without Bearer prefix")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        token = resp.json().get("token", "")
        
        # Try with token but no Bearer prefix
        headers = {"Authorization": token}
        resp2 = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=10)
        
        if resp2.status_code != 401:
            record_result("Missing Bearer Prefix", False, f"Expected 401, got {resp2.status_code}")
            return
        
        record_result("Missing Bearer Prefix", True, "Correctly rejected token without Bearer prefix")
    
    except Exception as e:
        record_result("Missing Bearer Prefix", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 3: Empty Authorization header
# ============================================================================
def test_empty_auth_header():
    log_info("TEST 3: Empty Authorization header")
    
    try:
        headers = {"Authorization": ""}
        resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=10)
        
        if resp.status_code != 401:
            record_result("Empty Auth Header", False, f"Expected 401, got {resp.status_code}")
            return
        
        record_result("Empty Auth Header", True, "Correctly rejected empty Authorization header")
    
    except Exception as e:
        record_result("Empty Auth Header", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 4: Bearer with empty token
# ============================================================================
def test_bearer_empty_token():
    log_info("TEST 4: Bearer with empty token")
    
    try:
        headers = {"Authorization": "Bearer "}
        resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=10)
        
        if resp.status_code != 401:
            record_result("Bearer Empty Token", False, f"Expected 401, got {resp.status_code}")
            return
        
        record_result("Bearer Empty Token", True, "Correctly rejected Bearer with empty token")
    
    except Exception as e:
        record_result("Bearer Empty Token", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 5: Multiple admin endpoints with same token (token reuse)
# ============================================================================
def test_token_reuse():
    log_info("TEST 5: Token reuse across multiple endpoints")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        token = resp.json().get("token", "")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test multiple endpoints with same token
        endpoints = [
            "/admin/stats",
            "/admin/participants",
            "/admin/leaderboard",
            "/admin/export"
        ]
        
        all_passed = True
        for endpoint in endpoints:
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
            if resp.status_code != 200:
                all_passed = False
                break
        
        if not all_passed:
            record_result("Token Reuse", False, "Token reuse failed on one or more endpoints")
            return
        
        record_result("Token Reuse", True, f"Token successfully reused across {len(endpoints)} endpoints")
    
    except Exception as e:
        record_result("Token Reuse", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 6: Case sensitivity of email in login
# ============================================================================
def test_email_case_sensitivity():
    log_info("TEST 6: Email case sensitivity in login")
    
    try:
        # Try with uppercase email
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": "ADMIN@BLUDE.LOCAL",
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("Email Case Sensitivity", False, f"Uppercase email failed: {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("ok") != True or "token" not in data:
            record_result("Email Case Sensitivity", False, "Login with uppercase email didn't return valid token")
            return
        
        record_result("Email Case Sensitivity", True, "Email is case-insensitive (uppercase worked)")
    
    except Exception as e:
        record_result("Email Case Sensitivity", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 7: Verify refresh_token is returned
# ============================================================================
def test_refresh_token_present():
    log_info("TEST 7: Verify refresh_token is returned in login response")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        data = resp.json()
        
        if "refresh_token" not in data:
            record_result("Refresh Token Present", False, "refresh_token missing from response")
            return
        
        refresh_token = data["refresh_token"]
        if not refresh_token or len(refresh_token) < 10:
            record_result("Refresh Token Present", False, f"Invalid refresh_token: {refresh_token}")
            return
        
        record_result("Refresh Token Present", True, f"refresh_token present, length={len(refresh_token)}")
    
    except Exception as e:
        record_result("Refresh Token Present", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 8: Verify expires_at is returned
# ============================================================================
def test_expires_at_present():
    log_info("TEST 8: Verify expires_at is returned in login response")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        data = resp.json()
        
        if "expires_at" not in data:
            record_result("Expires At Present", False, "expires_at missing from response")
            return
        
        expires_at = data["expires_at"]
        if not expires_at or not isinstance(expires_at, (int, float)):
            record_result("Expires At Present", False, f"Invalid expires_at: {expires_at}")
            return
        
        record_result("Expires At Present", True, f"expires_at present: {expires_at}")
    
    except Exception as e:
        record_result("Expires At Present", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 9: Verify user.id is returned
# ============================================================================
def test_user_id_present():
    log_info("TEST 9: Verify user.id is returned in login response")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        data = resp.json()
        
        if "user" not in data:
            record_result("User ID Present", False, "user object missing from response")
            return
        
        user = data["user"]
        if "id" not in user:
            record_result("User ID Present", False, "user.id missing from response")
            return
        
        user_id = user["id"]
        if not user_id or len(user_id) < 10:
            record_result("User ID Present", False, f"Invalid user.id: {user_id}")
            return
        
        record_result("User ID Present", True, f"user.id present: {user_id}")
    
    except Exception as e:
        record_result("User ID Present", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 10: Malformed JWT token
# ============================================================================
def test_malformed_jwt():
    log_info("TEST 10: Malformed JWT token")
    
    try:
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=10)
        
        if resp.status_code != 401:
            record_result("Malformed JWT", False, f"Expected 401, got {resp.status_code}")
            return
        
        record_result("Malformed JWT", True, "Correctly rejected malformed JWT")
    
    except Exception as e:
        record_result("Malformed JWT", False, f"Exception: {str(e)}")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def run_all_tests():
    print(f"\n{BLUE}{'='*80}")
    print("SUPABASE AUTH EDGE CASE TESTS")
    print(f"{'='*80}{RESET}\n")
    
    test_jwt_token_format()
    test_missing_bearer_prefix()
    test_empty_auth_header()
    test_bearer_empty_token()
    test_token_reuse()
    test_email_case_sensitivity()
    test_refresh_token_present()
    test_expires_at_present()
    test_user_id_present()
    test_malformed_jwt()
    
    # Summary
    print(f"\n{BLUE}{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}{RESET}\n")
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    print(f"{RED}Failed: {tests_failed}{RESET}")
    if tests_passed + tests_failed > 0:
        print(f"Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")
    print("="*80 + "\n")
    
    if tests_failed == 0:
        print(f"{GREEN}ALL EDGE CASE TESTS PASSED! ✓{RESET}\n")
    
    return tests_failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

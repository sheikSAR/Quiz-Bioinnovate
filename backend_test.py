#!/usr/bin/env python3
"""
Comprehensive backend test suite for MCQ Quiz Competition API
Tests all endpoints with various scenarios including edge cases
"""

import requests
import time
import json
import csv
from io import StringIO
from datetime import datetime

BASE_URL = "https://quiz-compete-15.preview.emergentagent.com/api"

# Test data generator
def generate_unique_email():
    return f"test_{int(time.time() * 1000000)}@example.com"

def generate_unique_phone():
    return f"9{int(time.time() * 1000) % 1000000000}"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def log_pass(msg):
    print(f"{GREEN}✓ PASS:{RESET} {msg}")

def log_fail(msg):
    print(f"{RED}✗ FAIL:{RESET} {msg}")

def log_info(msg):
    print(f"{YELLOW}ℹ INFO:{RESET} {msg}")

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

# ============================================================================
# TEST 1: POST /api/register - New participant registration
# ============================================================================
def test_register_new_participant():
    log_info("TEST 1: Register new participant")
    email = generate_unique_email()
    phone = generate_unique_phone()
    
    payload = {
        "full_name": "Alice Johnson",
        "dob": "2000-05-15",
        "email": email,
        "phone": phone,
        "college": "MIT",
        "department": "Computer Science",
        "year": "3"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/register", json=payload, timeout=10)
        
        if resp.status_code != 200:
            record_result("Register New", False, f"Expected 200, got {resp.status_code}")
            return None
        
        data = resp.json()
        
        # Validate response structure
        if "participant" not in data:
            record_result("Register New", False, "Missing 'participant' in response")
            return None
        
        if "session_token" not in data:
            record_result("Register New", False, "Missing 'session_token' in response")
            return None
        
        if data.get("returning") != False:
            record_result("Register New", False, f"Expected returning=false, got {data.get('returning')}")
            return None
        
        participant = data["participant"]
        if "id" not in participant:
            record_result("Register New", False, "Missing participant.id")
            return None
        
        if "assigned_set" not in participant or participant["assigned_set"] not in ["A", "B", "C"]:
            record_result("Register New", False, f"Invalid assigned_set: {participant.get('assigned_set')}")
            return None
        
        record_result("Register New", True, f"Participant created with set {participant['assigned_set']}")
        return {
            "participant_id": participant["id"],
            "session_token": data["session_token"],
            "email": email,
            "phone": phone,
            "assigned_set": participant["assigned_set"]
        }
    
    except Exception as e:
        record_result("Register New", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 2: POST /api/register - Duplicate email (returning user, no submission)
# ============================================================================
def test_register_duplicate_returning():
    log_info("TEST 2: Register duplicate email (returning user)")
    
    # First registration
    email = generate_unique_email()
    phone = generate_unique_phone()
    payload1 = {
        "full_name": "Bob Smith",
        "email": email,
        "phone": phone,
        "college": "Stanford",
        "department": "Engineering",
        "year": "2"
    }
    
    try:
        resp1 = requests.post(f"{BASE_URL}/register", json=payload1, timeout=10)
        if resp1.status_code != 200:
            record_result("Register Duplicate", False, f"First registration failed: {resp1.status_code}")
            return None
        
        # Second registration with same email
        resp2 = requests.post(f"{BASE_URL}/register", json=payload1, timeout=10)
        
        if resp2.status_code != 200:
            record_result("Register Duplicate", False, f"Expected 200, got {resp2.status_code}")
            return None
        
        data2 = resp2.json()
        
        if data2.get("returning") != True:
            record_result("Register Duplicate", False, f"Expected returning=true, got {data2.get('returning')}")
            return None
        
        record_result("Register Duplicate", True, "Returning user detected correctly")
        return resp1.json()
    
    except Exception as e:
        record_result("Register Duplicate", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 3: POST /api/register - Missing required fields
# ============================================================================
def test_register_missing_fields():
    log_info("TEST 3: Register with missing required fields")
    
    payload = {
        "full_name": "Charlie Brown",
        "phone": generate_unique_phone()
        # Missing email
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/register", json=payload, timeout=10)
        
        if resp.status_code != 400:
            record_result("Register Missing Fields", False, f"Expected 400, got {resp.status_code}")
            return
        
        data = resp.json()
        if "error" not in data:
            record_result("Register Missing Fields", False, "Missing 'error' in response")
            return
        
        record_result("Register Missing Fields", True, f"Validation error: {data['error']}")
    
    except Exception as e:
        record_result("Register Missing Fields", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 4: POST /api/quiz/start - Fresh start
# ============================================================================
def test_quiz_start_fresh(participant_data):
    log_info("TEST 4: Quiz start - fresh session")
    
    if not participant_data:
        record_result("Quiz Start Fresh", False, "No participant data provided")
        return None
    
    payload = {
        "participant_id": participant_data["participant_id"],
        "session_token": participant_data["session_token"]
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/start", json=payload, timeout=10)
        
        if resp.status_code != 200:
            record_result("Quiz Start Fresh", False, f"Expected 200, got {resp.status_code}")
            return None
        
        data = resp.json()
        
        # Validate response structure
        if "questions" not in data:
            record_result("Quiz Start Fresh", False, "Missing 'questions' in response")
            return None
        
        questions = data["questions"]
        if len(questions) != 30:
            record_result("Quiz Start Fresh", False, f"Expected 30 questions, got {len(questions)}")
            return None
        
        # Verify questions don't include correct_answer
        for q in questions:
            if "correct_answer" in q:
                record_result("Quiz Start Fresh", False, "Questions include correct_answer field")
                return None
        
        # Verify session data
        if "session" not in data:
            record_result("Quiz Start Fresh", False, "Missing 'session' in response")
            return None
        
        session = data["session"]
        if "ends_at" not in session:
            record_result("Quiz Start Fresh", False, "Missing session.ends_at")
            return None
        
        if "server_time" not in data:
            record_result("Quiz Start Fresh", False, "Missing server_time")
            return None
        
        # Verify set distribution (10 assigned + 10 BONUS_RESEARCH + 10 BONUS_STARTUP)
        assigned_set = participant_data["assigned_set"]
        set_counts = {}
        for q in questions:
            s = q.get("set", "")
            set_counts[s] = set_counts.get(s, 0) + 1
        
        if set_counts.get(assigned_set, 0) != 10:
            record_result("Quiz Start Fresh", False, f"Expected 10 questions from set {assigned_set}, got {set_counts.get(assigned_set, 0)}")
            return None
        
        if set_counts.get("BONUS_RESEARCH", 0) != 10:
            record_result("Quiz Start Fresh", False, f"Expected 10 BONUS_RESEARCH questions, got {set_counts.get('BONUS_RESEARCH', 0)}")
            return None
        
        if set_counts.get("BONUS_STARTUP", 0) != 10:
            record_result("Quiz Start Fresh", False, f"Expected 10 BONUS_STARTUP questions, got {set_counts.get('BONUS_STARTUP', 0)}")
            return None
        
        record_result("Quiz Start Fresh", True, f"30 questions returned, correct set distribution")
        return data
    
    except Exception as e:
        record_result("Quiz Start Fresh", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 5: POST /api/quiz/start - Restart same participant
# ============================================================================
def test_quiz_start_restart(participant_data):
    log_info("TEST 5: Quiz start - restart same participant")
    
    if not participant_data:
        record_result("Quiz Start Restart", False, "No participant data provided")
        return
    
    payload = {
        "participant_id": participant_data["participant_id"],
        "session_token": participant_data["session_token"]
    }
    
    try:
        # Call start again
        resp = requests.post(f"{BASE_URL}/quiz/start", json=payload, timeout=10)
        
        if resp.status_code != 200:
            record_result("Quiz Start Restart", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        
        if len(data.get("questions", [])) != 30:
            record_result("Quiz Start Restart", False, f"Expected 30 questions on restart, got {len(data.get('questions', []))}")
            return
        
        record_result("Quiz Start Restart", True, "Same session returned on restart")
    
    except Exception as e:
        record_result("Quiz Start Restart", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 6: POST /api/quiz/start - Non-existent participant
# ============================================================================
def test_quiz_start_nonexistent():
    log_info("TEST 6: Quiz start - non-existent participant")
    
    payload = {
        "participant_id": "nonexistent-id-12345",
        "session_token": "fake-token"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/start", json=payload, timeout=10)
        
        if resp.status_code != 404:
            record_result("Quiz Start Nonexistent", False, f"Expected 404, got {resp.status_code}")
            return
        
        record_result("Quiz Start Nonexistent", True, "404 returned for non-existent participant")
    
    except Exception as e:
        record_result("Quiz Start Nonexistent", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 7: POST /api/quiz/answer - Save answer
# ============================================================================
def test_quiz_answer_save(participant_data, quiz_data):
    log_info("TEST 7: Quiz answer - save answer")
    
    if not participant_data or not quiz_data:
        record_result("Quiz Answer Save", False, "Missing participant or quiz data")
        return
    
    questions = quiz_data.get("questions", [])
    if not questions:
        record_result("Quiz Answer Save", False, "No questions available")
        return
    
    question_id = questions[0]["id"]
    
    payload = {
        "participant_id": participant_data["participant_id"],
        "session_token": participant_data["session_token"],
        "question_id": question_id,
        "answer": "A"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/answer", json=payload, timeout=10)
        
        if resp.status_code != 200:
            record_result("Quiz Answer Save", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("ok") != True:
            record_result("Quiz Answer Save", False, f"Expected ok=true, got {data}")
            return
        
        record_result("Quiz Answer Save", True, "Answer saved successfully")
    
    except Exception as e:
        record_result("Quiz Answer Save", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 8: POST /api/quiz/answer - Wrong session token
# ============================================================================
def test_quiz_answer_wrong_token(participant_data, quiz_data):
    log_info("TEST 8: Quiz answer - wrong session token")
    
    if not participant_data or not quiz_data:
        record_result("Quiz Answer Wrong Token", False, "Missing participant or quiz data")
        return
    
    questions = quiz_data.get("questions", [])
    if not questions:
        record_result("Quiz Answer Wrong Token", False, "No questions available")
        return
    
    question_id = questions[0]["id"]
    
    payload = {
        "participant_id": participant_data["participant_id"],
        "session_token": "wrong-token-12345",
        "question_id": question_id,
        "answer": "B"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/answer", json=payload, timeout=10)
        
        if resp.status_code != 401:
            record_result("Quiz Answer Wrong Token", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("invalid_session") != True:
            record_result("Quiz Answer Wrong Token", False, f"Expected invalid_session=true, got {data}")
            return
        
        record_result("Quiz Answer Wrong Token", True, "Invalid session detected correctly")
    
    except Exception as e:
        record_result("Quiz Answer Wrong Token", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 9: POST /api/quiz/tabswitch - Increment tracking
# ============================================================================
def test_quiz_tabswitch(participant_data):
    log_info("TEST 9: Quiz tabswitch - increment tracking")
    
    if not participant_data:
        record_result("Quiz Tabswitch", False, "No participant data provided")
        return
    
    payload = {
        "participant_id": participant_data["participant_id"]
    }
    
    try:
        # First switch
        resp1 = requests.post(f"{BASE_URL}/quiz/tabswitch", json=payload, timeout=10)
        
        if resp1.status_code != 200:
            record_result("Quiz Tabswitch", False, f"Expected 200, got {resp1.status_code}")
            return
        
        data1 = resp1.json()
        if data1.get("tab_switches") != 1:
            record_result("Quiz Tabswitch", False, f"Expected tab_switches=1, got {data1.get('tab_switches')}")
            return
        
        # Second switch
        resp2 = requests.post(f"{BASE_URL}/quiz/tabswitch", json=payload, timeout=10)
        data2 = resp2.json()
        
        if data2.get("tab_switches") != 2:
            record_result("Quiz Tabswitch", False, f"Expected tab_switches=2, got {data2.get('tab_switches')}")
            return
        
        record_result("Quiz Tabswitch", True, "Tab switches incremented correctly")
    
    except Exception as e:
        record_result("Quiz Tabswitch", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 10: POST /api/quiz/submit - Submit with score calculation
# ============================================================================
def test_quiz_submit_with_score():
    log_info("TEST 10: Quiz submit - with score calculation")
    
    # Create a new participant for this test
    email = generate_unique_email()
    phone = generate_unique_phone()
    
    try:
        # Register
        reg_resp = requests.post(f"{BASE_URL}/register", json={
            "full_name": "Score Test User",
            "email": email,
            "phone": phone,
            "college": "Test College",
            "department": "Test Dept",
            "year": "1"
        }, timeout=10)
        
        if reg_resp.status_code != 200:
            record_result("Quiz Submit Score", False, f"Registration failed: {reg_resp.status_code}")
            return None
        
        reg_data = reg_resp.json()
        participant_id = reg_data["participant"]["id"]
        session_token = reg_data["session_token"]
        
        # Start quiz
        start_resp = requests.post(f"{BASE_URL}/quiz/start", json={
            "participant_id": participant_id,
            "session_token": session_token
        }, timeout=10)
        
        if start_resp.status_code != 200:
            record_result("Quiz Submit Score", False, f"Quiz start failed: {start_resp.status_code}")
            return None
        
        start_data = start_resp.json()
        questions = start_data["questions"]
        
        # Answer some questions (mix of A, B, C, D)
        answers_given = 0
        for i, q in enumerate(questions[:10]):  # Answer first 10 questions
            answer = ["A", "B", "C", "D"][i % 4]
            ans_resp = requests.post(f"{BASE_URL}/quiz/answer", json={
                "participant_id": participant_id,
                "session_token": session_token,
                "question_id": q["id"],
                "answer": answer
            }, timeout=10)
            if ans_resp.status_code == 200:
                answers_given += 1
        
        # Submit
        submit_resp = requests.post(f"{BASE_URL}/quiz/submit", json={
            "participant_id": participant_id,
            "auto": False
        }, timeout=10)
        
        if submit_resp.status_code != 200:
            record_result("Quiz Submit Score", False, f"Submit failed: {submit_resp.status_code}")
            return None
        
        submit_data = submit_resp.json()
        if submit_data.get("ok") != True:
            record_result("Quiz Submit Score", False, f"Expected ok=true, got {submit_data}")
            return None
        
        # Verify score via admin/participants
        time.sleep(0.5)  # Small delay for DB consistency
        admin_resp = requests.get(f"{BASE_URL}/admin/participants", timeout=10)
        
        if admin_resp.status_code != 200:
            record_result("Quiz Submit Score", False, f"Admin participants fetch failed: {admin_resp.status_code}")
            return None
        
        admin_data = admin_resp.json()
        rows = admin_data.get("rows", [])
        
        participant_row = None
        for row in rows:
            if row["id"] == participant_id:
                participant_row = row
                break
        
        if not participant_row:
            record_result("Quiz Submit Score", False, "Participant not found in admin data")
            return None
        
        if participant_row["status"] != "completed":
            record_result("Quiz Submit Score", False, f"Expected status=completed, got {participant_row['status']}")
            return None
        
        score = participant_row.get("score")
        if score is None:
            record_result("Quiz Submit Score", False, "Score is null after submission")
            return None
        
        if not isinstance(score, int) or score < 0 or score > 30:
            record_result("Quiz Submit Score", False, f"Invalid score: {score}")
            return None
        
        record_result("Quiz Submit Score", True, f"Submission successful, score={score}, answered={answers_given}")
        return {"participant_id": participant_id, "session_token": session_token}
    
    except Exception as e:
        record_result("Quiz Submit Score", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 11: POST /api/quiz/submit - Re-submit
# ============================================================================
def test_quiz_submit_resubmit(submitted_participant):
    log_info("TEST 11: Quiz submit - re-submit")
    
    if not submitted_participant:
        record_result("Quiz Submit Resubmit", False, "No submitted participant data")
        return
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/submit", json={
            "participant_id": submitted_participant["participant_id"],
            "auto": False
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("Quiz Submit Resubmit", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("ok") != True or data.get("already") != True:
            record_result("Quiz Submit Resubmit", False, f"Expected ok=true and already=true, got {data}")
            return
        
        record_result("Quiz Submit Resubmit", True, "Re-submit handled correctly")
    
    except Exception as e:
        record_result("Quiz Submit Resubmit", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 12: POST /api/quiz/start - After submission (should block)
# ============================================================================
def test_quiz_start_after_submit(submitted_participant):
    log_info("TEST 12: Quiz start - after submission (should block)")
    
    if not submitted_participant:
        record_result("Quiz Start After Submit", False, "No submitted participant data")
        return
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/start", json={
            "participant_id": submitted_participant["participant_id"],
            "session_token": submitted_participant["session_token"]
        }, timeout=10)
        
        if resp.status_code != 403:
            record_result("Quiz Start After Submit", False, f"Expected 403, got {resp.status_code}")
            return
        
        data = resp.json()
        if data.get("already_submitted") != True:
            record_result("Quiz Start After Submit", False, f"Expected already_submitted=true, got {data}")
            return
        
        record_result("Quiz Start After Submit", True, "Quiz start blocked after submission")
    
    except Exception as e:
        record_result("Quiz Start After Submit", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 13: POST /api/quiz/answer - After submission (should block)
# ============================================================================
def test_quiz_answer_after_submit(submitted_participant):
    log_info("TEST 13: Quiz answer - after submission (should block)")
    
    if not submitted_participant:
        record_result("Quiz Answer After Submit", False, "No submitted participant data")
        return
    
    try:
        resp = requests.post(f"{BASE_URL}/quiz/answer", json={
            "participant_id": submitted_participant["participant_id"],
            "session_token": submitted_participant["session_token"],
            "question_id": "fake-question-id",
            "answer": "A"
        }, timeout=10)
        
        if resp.status_code != 403:
            record_result("Quiz Answer After Submit", False, f"Expected 403, got {resp.status_code}")
            return
        
        record_result("Quiz Answer After Submit", True, "Answer blocked after submission")
    
    except Exception as e:
        record_result("Quiz Answer After Submit", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 14: POST /api/register - Already submitted user (should block)
# ============================================================================
def test_register_already_submitted():
    log_info("TEST 14: Register - already submitted user (should block)")
    
    # Create, start, and submit a quiz
    email = generate_unique_email()
    phone = generate_unique_phone()
    
    try:
        # Register
        reg_resp = requests.post(f"{BASE_URL}/register", json={
            "full_name": "Already Submitted User",
            "email": email,
            "phone": phone,
            "college": "Test College",
            "department": "Test Dept",
            "year": "2"
        }, timeout=10)
        
        if reg_resp.status_code != 200:
            record_result("Register Already Submitted", False, f"Registration failed: {reg_resp.status_code}")
            return
        
        reg_data = reg_resp.json()
        participant_id = reg_data["participant"]["id"]
        session_token = reg_data["session_token"]
        
        # Start quiz
        requests.post(f"{BASE_URL}/quiz/start", json={
            "participant_id": participant_id,
            "session_token": session_token
        }, timeout=10)
        
        # Submit
        requests.post(f"{BASE_URL}/quiz/submit", json={
            "participant_id": participant_id,
            "auto": False
        }, timeout=10)
        
        # Try to register again with same email
        time.sleep(0.5)
        reg2_resp = requests.post(f"{BASE_URL}/register", json={
            "full_name": "Already Submitted User",
            "email": email,
            "phone": phone,
            "college": "Test College",
            "department": "Test Dept",
            "year": "2"
        }, timeout=10)
        
        if reg2_resp.status_code != 403:
            record_result("Register Already Submitted", False, f"Expected 403, got {reg2_resp.status_code}")
            return
        
        data = reg2_resp.json()
        if data.get("already_submitted") != True:
            record_result("Register Already Submitted", False, f"Expected already_submitted=true, got {data}")
            return
        
        record_result("Register Already Submitted", True, "Already submitted user blocked correctly")
    
    except Exception as e:
        record_result("Register Already Submitted", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 15: POST /api/admin/login - Correct credentials
# ============================================================================
def test_admin_login_success():
    log_info("TEST 15: Admin login - correct credentials")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "username": "admin",
            "password": "admin123"
        }, timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Login Success", False, f"Expected 200, got {resp.status_code}")
            return None
        
        data = resp.json()
        if data.get("ok") != True:
            record_result("Admin Login Success", False, f"Expected ok=true, got {data}")
            return None
        
        if "token" not in data:
            record_result("Admin Login Success", False, "Missing token in response")
            return None
        
        record_result("Admin Login Success", True, f"Login successful, token received")
        return data["token"]
    
    except Exception as e:
        record_result("Admin Login Success", False, f"Exception: {str(e)}")
        return None

# ============================================================================
# TEST 16: POST /api/admin/login - Wrong credentials
# ============================================================================
def test_admin_login_fail():
    log_info("TEST 16: Admin login - wrong credentials")
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/login", json={
            "username": "admin",
            "password": "wrongpassword"
        }, timeout=10)
        
        if resp.status_code != 401:
            record_result("Admin Login Fail", False, f"Expected 401, got {resp.status_code}")
            return
        
        data = resp.json()
        if "error" not in data:
            record_result("Admin Login Fail", False, "Missing error in response")
            return
        
        record_result("Admin Login Fail", True, "Invalid credentials rejected correctly")
    
    except Exception as e:
        record_result("Admin Login Fail", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 17: GET /api/admin/stats - Validate counts
# ============================================================================
def test_admin_stats():
    log_info("TEST 17: Admin stats - validate counts")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/stats", timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Stats", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        
        required_fields = ["total", "in_progress", "completed"]
        for field in required_fields:
            if field not in data:
                record_result("Admin Stats", False, f"Missing field: {field}")
                return
        
        if not isinstance(data["total"], int) or data["total"] < 0:
            record_result("Admin Stats", False, f"Invalid total: {data['total']}")
            return
        
        if not isinstance(data["in_progress"], int) or data["in_progress"] < 0:
            record_result("Admin Stats", False, f"Invalid in_progress: {data['in_progress']}")
            return
        
        if not isinstance(data["completed"], int) or data["completed"] < 0:
            record_result("Admin Stats", False, f"Invalid completed: {data['completed']}")
            return
        
        record_result("Admin Stats", True, f"total={data['total']}, in_progress={data['in_progress']}, completed={data['completed']}")
    
    except Exception as e:
        record_result("Admin Stats", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 18: GET /api/admin/participants - No search
# ============================================================================
def test_admin_participants_no_search():
    log_info("TEST 18: Admin participants - no search")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/participants", timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Participants No Search", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        
        if "rows" not in data:
            record_result("Admin Participants No Search", False, "Missing 'rows' in response")
            return
        
        rows = data["rows"]
        if not isinstance(rows, list):
            record_result("Admin Participants No Search", False, "rows is not a list")
            return
        
        # Validate structure of first row if exists
        if len(rows) > 0:
            row = rows[0]
            required_fields = ["id", "full_name", "email", "phone", "assigned_set", "status"]
            for field in required_fields:
                if field not in row:
                    record_result("Admin Participants No Search", False, f"Missing field in row: {field}")
                    return
        
        record_result("Admin Participants No Search", True, f"Returned {len(rows)} participants")
    
    except Exception as e:
        record_result("Admin Participants No Search", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 19: GET /api/admin/participants - With search
# ============================================================================
def test_admin_participants_with_search():
    log_info("TEST 19: Admin participants - with search")
    
    # Create a participant with unique searchable data
    email = generate_unique_email()
    phone = generate_unique_phone()
    unique_name = f"SearchTest_{int(time.time())}"
    
    try:
        # Register
        requests.post(f"{BASE_URL}/register", json={
            "full_name": unique_name,
            "email": email,
            "phone": phone,
            "college": "Search College",
            "department": "Search Dept",
            "year": "3"
        }, timeout=10)
        
        time.sleep(0.5)
        
        # Search by name
        resp = requests.get(f"{BASE_URL}/admin/participants?search={unique_name}", timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Participants Search", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        rows = data.get("rows", [])
        
        if len(rows) == 0:
            record_result("Admin Participants Search", False, "Search returned no results")
            return
        
        # Verify the searched participant is in results
        found = False
        for row in rows:
            if row["full_name"] == unique_name:
                found = True
                break
        
        if not found:
            record_result("Admin Participants Search", False, f"Searched participant not found in results")
            return
        
        record_result("Admin Participants Search", True, f"Search returned {len(rows)} matching participants")
    
    except Exception as e:
        record_result("Admin Participants Search", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 20: GET /api/admin/leaderboard - Sorting validation
# ============================================================================
def test_admin_leaderboard():
    log_info("TEST 20: Admin leaderboard - sorting validation")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/leaderboard", timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Leaderboard", False, f"Expected 200, got {resp.status_code}")
            return
        
        data = resp.json()
        
        if "rows" not in data:
            record_result("Admin Leaderboard", False, "Missing 'rows' in response")
            return
        
        rows = data["rows"]
        if not isinstance(rows, list):
            record_result("Admin Leaderboard", False, "rows is not a list")
            return
        
        # Validate sorting (score DESC, time_taken ASC)
        if len(rows) > 1:
            for i in range(len(rows) - 1):
                curr = rows[i]
                next_row = rows[i + 1]
                
                # Check rank increments
                if curr.get("rank") != i + 1:
                    record_result("Admin Leaderboard", False, f"Rank mismatch at position {i}")
                    return
                
                # Check sorting: score DESC
                if curr.get("score", 0) < next_row.get("score", 0):
                    record_result("Admin Leaderboard", False, f"Sorting error: score not descending")
                    return
                
                # If scores are equal, time_taken should be ASC
                if curr.get("score") == next_row.get("score"):
                    if curr.get("time_taken_seconds", 0) > next_row.get("time_taken_seconds", 0):
                        record_result("Admin Leaderboard", False, f"Sorting error: time_taken not ascending for equal scores")
                        return
        
        record_result("Admin Leaderboard", True, f"Leaderboard returned {len(rows)} entries, correctly sorted")
    
    except Exception as e:
        record_result("Admin Leaderboard", False, f"Exception: {str(e)}")

# ============================================================================
# TEST 21: GET /api/admin/export - CSV structure
# ============================================================================
def test_admin_export():
    log_info("TEST 21: Admin export - CSV structure")
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/export", timeout=10)
        
        if resp.status_code != 200:
            record_result("Admin Export", False, f"Expected 200, got {resp.status_code}")
            return
        
        # Check Content-Type
        content_type = resp.headers.get("Content-Type", "")
        if "text/csv" not in content_type:
            record_result("Admin Export", False, f"Expected Content-Type text/csv, got {content_type}")
            return
        
        # Check Content-Disposition
        content_disp = resp.headers.get("Content-Disposition", "")
        if "attachment" not in content_disp:
            record_result("Admin Export", False, f"Expected Content-Disposition with attachment, got {content_disp}")
            return
        
        # Parse CSV
        csv_text = resp.text
        csv_reader = csv.reader(StringIO(csv_text))
        rows = list(csv_reader)
        
        if len(rows) < 1:
            record_result("Admin Export", False, "CSV has no rows")
            return
        
        headers = rows[0]
        expected_headers = [
            'Full Name', 'Email', 'Phone', 'College', 'Department', 'Year', 'Assigned Set',
            'Status', 'Score', 'Total Questions', 'Time Taken (sec)', 'Tab Switches',
            'Auto Submitted', 'Started At', 'Submitted At'
        ]
        
        if headers != expected_headers:
            record_result("Admin Export", False, f"CSV headers mismatch. Expected {expected_headers}, got {headers}")
            return
        
        record_result("Admin Export", True, f"CSV export valid with {len(rows)-1} data rows")
    
    except Exception as e:
        record_result("Admin Export", False, f"Exception: {str(e)}")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def run_all_tests():
    print("\n" + "="*80)
    print("MCQ QUIZ BACKEND COMPREHENSIVE TEST SUITE")
    print("="*80 + "\n")
    
    # Test 1-3: Registration tests
    participant1 = test_register_new_participant()
    participant2 = test_register_duplicate_returning()
    test_register_missing_fields()
    
    # Test 4-6: Quiz start tests
    quiz_data = None
    if participant1:
        quiz_data = test_quiz_start_fresh(participant1)
        test_quiz_start_restart(participant1)
    test_quiz_start_nonexistent()
    
    # Test 7-8: Quiz answer tests
    if participant1 and quiz_data:
        test_quiz_answer_save(participant1, quiz_data)
        test_quiz_answer_wrong_token(participant1, quiz_data)
    
    # Test 9: Tab switch test
    if participant1:
        test_quiz_tabswitch(participant1)
    
    # Test 10-13: Submit tests
    submitted_participant = test_quiz_submit_with_score()
    if submitted_participant:
        test_quiz_submit_resubmit(submitted_participant)
        test_quiz_start_after_submit(submitted_participant)
        test_quiz_answer_after_submit(submitted_participant)
    
    # Test 14: Already submitted registration block
    test_register_already_submitted()
    
    # Test 15-16: Admin login tests
    admin_token = test_admin_login_success()
    test_admin_login_fail()
    
    # Test 17-21: Admin endpoints
    test_admin_stats()
    test_admin_participants_no_search()
    test_admin_participants_with_search()
    test_admin_leaderboard()
    test_admin_export()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    print(f"{RED}Failed: {tests_failed}{RESET}")
    print(f"Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")
    print("="*80 + "\n")
    
    if tests_failed > 0:
        print(f"{RED}FAILED TESTS:{RESET}")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['test']}: {result['details']}")
        print()
    
    return tests_failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

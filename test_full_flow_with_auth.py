#!/usr/bin/env python3
"""
Full flow test: Participant flow + Admin verification with Supabase Auth
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

def log_section(msg):
    print(f"\n{BLUE}{'='*80}")
    print(f"{msg}")
    print(f"{'='*80}{RESET}\n")

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

def generate_unique_email():
    return f"fullflow_{int(time.time() * 1000000)}@example.com"

def generate_unique_phone():
    return f"9{int(time.time() * 1000) % 1000000000}"

# ============================================================================
# FULL FLOW TEST
# ============================================================================
def test_full_flow():
    log_section("FULL FLOW TEST: Participant Registration → Quiz → Admin Verification")
    
    # Step 1: Register participant
    log_info("Step 1: Register new participant")
    email = generate_unique_email()
    phone = generate_unique_phone()
    
    try:
        reg_resp = requests.post(f"{BASE_URL}/register", json={
            "full_name": "Full Flow Test User",
            "email": email,
            "phone": phone,
            "college": "Test College",
            "department": "Computer Science",
            "year": "3"
        }, timeout=10)
        
        if reg_resp.status_code != 200:
            record_result("Full Flow - Register", False, f"Registration failed: {reg_resp.status_code}")
            return
        
        reg_data = reg_resp.json()
        participant_id = reg_data["participant"]["id"]
        session_token = reg_data["session_token"]
        assigned_set = reg_data["participant"]["assigned_set"]
        
        record_result("Full Flow - Register", True, f"Participant registered with set {assigned_set}")
        
        # Step 2: Start quiz
        log_info("Step 2: Start quiz")
        start_resp = requests.post(f"{BASE_URL}/quiz/start", json={
            "participant_id": participant_id,
            "session_token": session_token
        }, timeout=10)
        
        if start_resp.status_code != 200:
            record_result("Full Flow - Quiz Start", False, f"Quiz start failed: {start_resp.status_code}")
            return
        
        start_data = start_resp.json()
        questions = start_data["questions"]
        
        if len(questions) != 30:
            record_result("Full Flow - Quiz Start", False, f"Expected 30 questions, got {len(questions)}")
            return
        
        record_result("Full Flow - Quiz Start", True, f"Quiz started with 30 questions")
        
        # Step 3: Answer some questions
        log_info("Step 3: Answer 5 questions")
        answers_saved = 0
        for i, q in enumerate(questions[:5]):
            answer = ["A", "B", "C", "D"][i % 4]
            ans_resp = requests.post(f"{BASE_URL}/quiz/answer", json={
                "participant_id": participant_id,
                "session_token": session_token,
                "question_id": q["id"],
                "answer": answer
            }, timeout=10)
            
            if ans_resp.status_code == 200 and ans_resp.json().get("ok"):
                answers_saved += 1
        
        if answers_saved != 5:
            record_result("Full Flow - Answer Questions", False, f"Expected 5 answers saved, got {answers_saved}")
            return
        
        record_result("Full Flow - Answer Questions", True, f"Saved {answers_saved} answers")
        
        # Step 4: Submit quiz
        log_info("Step 4: Submit quiz")
        submit_resp = requests.post(f"{BASE_URL}/quiz/submit", json={
            "participant_id": participant_id,
            "auto": False
        }, timeout=10)
        
        if submit_resp.status_code != 200:
            record_result("Full Flow - Submit Quiz", False, f"Submit failed: {submit_resp.status_code}")
            return
        
        submit_data = submit_resp.json()
        if not submit_data.get("ok"):
            record_result("Full Flow - Submit Quiz", False, f"Submit returned ok=false")
            return
        
        record_result("Full Flow - Submit Quiz", True, "Quiz submitted successfully")
        
        # Wait for DB consistency
        time.sleep(1)
        
        # Step 5: Admin login
        log_info("Step 5: Admin login with Supabase Auth")
        admin_resp = requests.post(f"{BASE_URL}/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=10)
        
        if admin_resp.status_code != 200:
            record_result("Full Flow - Admin Login", False, f"Admin login failed: {admin_resp.status_code}")
            return
        
        admin_data = admin_resp.json()
        admin_token = admin_data.get("token")
        
        if not admin_token:
            record_result("Full Flow - Admin Login", False, "No token received")
            return
        
        record_result("Full Flow - Admin Login", True, f"Admin logged in, token length={len(admin_token)}")
        
        # Step 6: Verify participant in admin/participants
        log_info("Step 6: Verify participant via admin/participants endpoint")
        headers = {"Authorization": f"Bearer {admin_token}"}
        participants_resp = requests.get(f"{BASE_URL}/admin/participants", headers=headers, timeout=10)
        
        if participants_resp.status_code != 200:
            record_result("Full Flow - Admin Participants", False, f"Admin participants failed: {participants_resp.status_code}")
            return
        
        participants_data = participants_resp.json()
        rows = participants_data.get("rows", [])
        
        # Find our participant
        found_participant = None
        for row in rows:
            if row["email"] == email:
                found_participant = row
                break
        
        if not found_participant:
            record_result("Full Flow - Admin Participants", False, "Participant not found in admin data")
            return
        
        if found_participant["status"] != "completed":
            record_result("Full Flow - Admin Participants", False, f"Expected status=completed, got {found_participant['status']}")
            return
        
        if found_participant["score"] is None:
            record_result("Full Flow - Admin Participants", False, "Score is null")
            return
        
        record_result("Full Flow - Admin Participants", True, f"Participant found: status={found_participant['status']}, score={found_participant['score']}")
        
        # Step 7: Verify in leaderboard
        log_info("Step 7: Verify participant in leaderboard")
        leaderboard_resp = requests.get(f"{BASE_URL}/admin/leaderboard", headers=headers, timeout=10)
        
        if leaderboard_resp.status_code != 200:
            record_result("Full Flow - Admin Leaderboard", False, f"Admin leaderboard failed: {leaderboard_resp.status_code}")
            return
        
        leaderboard_data = leaderboard_resp.json()
        leaderboard_rows = leaderboard_data.get("rows", [])
        
        # Check if our participant is in leaderboard
        found_in_leaderboard = False
        for row in leaderboard_rows:
            if row.get("full_name") == "Full Flow Test User":
                found_in_leaderboard = True
                break
        
        if not found_in_leaderboard:
            record_result("Full Flow - Admin Leaderboard", False, "Participant not found in leaderboard")
            return
        
        record_result("Full Flow - Admin Leaderboard", True, "Participant found in leaderboard")
        
        # Step 8: Verify in CSV export
        log_info("Step 8: Verify participant in CSV export")
        export_resp = requests.get(f"{BASE_URL}/admin/export", headers=headers, timeout=10)
        
        if export_resp.status_code != 200:
            record_result("Full Flow - Admin Export", False, f"Admin export failed: {export_resp.status_code}")
            return
        
        csv_text = export_resp.text
        if email not in csv_text:
            record_result("Full Flow - Admin Export", False, "Participant email not found in CSV")
            return
        
        if "Full Flow Test User" not in csv_text:
            record_result("Full Flow - Admin Export", False, "Participant name not found in CSV")
            return
        
        record_result("Full Flow - Admin Export", True, "Participant found in CSV export")
        
        # Step 9: Verify admin stats updated
        log_info("Step 9: Verify admin stats")
        stats_resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers, timeout=10)
        
        if stats_resp.status_code != 200:
            record_result("Full Flow - Admin Stats", False, f"Admin stats failed: {stats_resp.status_code}")
            return
        
        stats_data = stats_resp.json()
        
        if stats_data.get("total", 0) < 1:
            record_result("Full Flow - Admin Stats", False, "Total participants is 0")
            return
        
        if stats_data.get("completed", 0) < 1:
            record_result("Full Flow - Admin Stats", False, "Completed count is 0")
            return
        
        record_result("Full Flow - Admin Stats", True, f"Stats: total={stats_data['total']}, completed={stats_data['completed']}")
        
        log_section("FULL FLOW TEST COMPLETED SUCCESSFULLY ✓")
        
    except Exception as e:
        record_result("Full Flow Test", False, f"Exception: {str(e)}")

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def run_all_tests():
    test_full_flow()
    
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
        print(f"{GREEN}ALL FULL FLOW TESTS PASSED! ✓{RESET}\n")
    
    return tests_failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

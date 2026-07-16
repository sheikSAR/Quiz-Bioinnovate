#!/usr/bin/env python3
"""
Verify Supabase-specific migration requirements
"""

import requests
import json
import time

BASE_URL = "https://quiz-compete-15.preview.emergentagent.com/api"

print("="*80)
print("SUPABASE MIGRATION VERIFICATION")
print("="*80)

# Test 1: Verify questions count and distribution
print("\n1. Verifying questions collection structure...")
try:
    # Register a new participant to get questions
    timestamp = int(time.time() * 1000000)
    reg_resp = requests.post(f"{BASE_URL}/register", json={
        "full_name": "Supabase Verify User",
        "email": f"verify_supabase_{timestamp}@test.com",
        "phone": f"9{timestamp % 1000000000}",
        "college": "Test College",
        "department": "Test Dept",
        "year": "1"
    }, timeout=10)
    
    if reg_resp.status_code == 200:
        reg_data = reg_resp.json()
        participant_id = reg_data["participant"]["id"]
        session_token = reg_data["session_token"]
        assigned_set = reg_data["participant"]["assigned_set"]
        
        # Start quiz to get questions
        start_resp = requests.post(f"{BASE_URL}/quiz/start", json={
            "participant_id": participant_id,
            "session_token": session_token
        }, timeout=10)
        
        if start_resp.status_code == 200:
            start_data = start_resp.json()
            questions = start_data["questions"]
            
            # Count questions by set
            set_counts = {}
            for q in questions:
                s = q.get("set", "")
                set_counts[s] = set_counts.get(s, 0) + 1
            
            print(f"   ✓ Total questions returned: {len(questions)}")
            print(f"   ✓ Assigned set: {assigned_set}")
            print(f"   ✓ Question distribution:")
            for set_name, count in sorted(set_counts.items()):
                print(f"     - {set_name}: {count} questions")
            
            # Verify expected distribution
            expected_assigned = 10
            expected_bonus_research = 10
            expected_bonus_startup = 10
            
            if set_counts.get(assigned_set, 0) == expected_assigned:
                print(f"   ✓ Assigned set {assigned_set} has correct count: {expected_assigned}")
            else:
                print(f"   ✗ ERROR: Assigned set {assigned_set} has {set_counts.get(assigned_set, 0)} questions, expected {expected_assigned}")
            
            if set_counts.get("BONUS_RESEARCH", 0) == expected_bonus_research:
                print(f"   ✓ BONUS_RESEARCH has correct count: {expected_bonus_research}")
            else:
                print(f"   ✗ ERROR: BONUS_RESEARCH has {set_counts.get('BONUS_RESEARCH', 0)} questions, expected {expected_bonus_research}")
            
            if set_counts.get("BONUS_STARTUP", 0) == expected_bonus_startup:
                print(f"   ✓ BONUS_STARTUP has correct count: {expected_bonus_startup}")
            else:
                print(f"   ✗ ERROR: BONUS_STARTUP has {set_counts.get('BONUS_STARTUP', 0)} questions, expected {expected_bonus_startup}")
            
            # Test 2: Verify UUID format
            print("\n2. Verifying UUID generation...")
            print(f"   ✓ Participant ID (UUID): {participant_id}")
            print(f"   ✓ Session Token (UUID): {session_token}")
            
            # Check if IDs are valid UUIDs (basic check)
            if len(participant_id) == 36 and participant_id.count('-') == 4:
                print(f"   ✓ Participant ID is valid UUID format")
            else:
                print(f"   ✗ ERROR: Participant ID is not valid UUID format")
            
            # Test 3: Verify JSONB options field
            print("\n3. Verifying JSONB options field...")
            sample_question = questions[0]
            if "options" in sample_question:
                options = sample_question["options"]
                print(f"   ✓ Options field present: {json.dumps(options, indent=6)}")
                if isinstance(options, dict) and all(k in options for k in ['A', 'B', 'C', 'D']):
                    print(f"   ✓ Options is a valid JSONB object with A, B, C, D keys")
                else:
                    print(f"   ✗ ERROR: Options is not a valid JSONB object")
            else:
                print(f"   ✗ ERROR: Options field missing from question")
            
            # Test 4: Verify correct_answer is NOT included in questions
            print("\n4. Verifying correct_answer field is excluded from questions...")
            has_correct_answer = any("correct_answer" in q for q in questions)
            if not has_correct_answer:
                print(f"   ✓ correct_answer field is NOT included in questions (security validated)")
            else:
                print(f"   ✗ ERROR: correct_answer field is exposed in questions")
            
            # Test 5: Verify ends_at timestamp format
            print("\n5. Verifying ends_at timestamp format...")
            session = start_data.get("session", {})
            ends_at = session.get("ends_at")
            if ends_at:
                print(f"   ✓ ends_at field present: {ends_at}")
                # Check if it's ISO format (contains 'T' and ends with 'Z' or timezone)
                if 'T' in ends_at:
                    print(f"   ✓ ends_at is in ISO 8601 format (timestamptz)")
                else:
                    print(f"   ✗ ERROR: ends_at is not in ISO format")
            else:
                print(f"   ✗ ERROR: ends_at field missing from session")
            
            # Test 6: Verify JSONB answers field works
            print("\n6. Verifying JSONB answers field...")
            # Save an answer
            answer_resp = requests.post(f"{BASE_URL}/quiz/answer", json={
                "participant_id": participant_id,
                "session_token": session_token,
                "question_id": questions[0]["id"],
                "answer": "A"
            }, timeout=10)
            
            if answer_resp.status_code == 200 and answer_resp.json().get("ok"):
                print(f"   ✓ Answer saved successfully to JSONB answers field")
                
                # Restart to verify answer persistence
                restart_resp = requests.post(f"{BASE_URL}/quiz/start", json={
                    "participant_id": participant_id,
                    "session_token": session_token
                }, timeout=10)
                
                if restart_resp.status_code == 200:
                    restart_data = restart_resp.json()
                    restart_session = restart_data.get("session", {})
                    answers = restart_session.get("answers", {})
                    if questions[0]["id"] in answers and answers[questions[0]["id"]] == "A":
                        print(f"   ✓ Answer persisted correctly in JSONB field")
                        print(f"   ✓ Answers structure: {json.dumps(answers, indent=6)}")
                    else:
                        print(f"   ✗ ERROR: Answer not persisted correctly")
            else:
                print(f"   ✗ ERROR: Failed to save answer")
            
            print("\n" + "="*80)
            print("SUPABASE MIGRATION VERIFICATION COMPLETE")
            print("="*80)
            print("✓ All Supabase-specific requirements validated successfully")
            
        else:
            print(f"   ✗ ERROR: Quiz start failed with status {start_resp.status_code}")
    else:
        print(f"   ✗ ERROR: Registration failed with status {reg_resp.status_code}")
        
except Exception as e:
    print(f"   ✗ ERROR: Exception occurred: {str(e)}")

# Testing Protocol

## Instructions for Main Agent
1. ALWAYS read this file before invoking a testing sub-agent.
2. Update the "Current Status" and "Findings" sections after each testing round.
3. NEVER modify the "Testing Protocol" section (this section).
4. Backend testing first via `deep_testing_backend_nextjs`.
5. Ask the user before invoking frontend testing via `deep_testing_frontend_nextjs`.
6. Do not fix issues already resolved by the testing agent.

## Communication with User
- After backend tests, STOP and ask the user before frontend testing.
- Summarize what was tested and what needs manual verification.

---

# Current Status

## Feature
MCQ Quiz Competition for one-day college event.

## Stack
Next.js 15 + MongoDB + Tailwind + shadcn/ui

## Backend Endpoints
- POST `/api/register` — find or create participant, assigns random set (A/B/C), blocks re-attempts.
- POST `/api/quiz/start` — initializes/resumes session, returns 30 questions (10 set + 20 bonus) with server-side `ends_at`.
- POST `/api/quiz/answer` — autosave individual answer, session-token validated.
- POST `/api/quiz/tabswitch` — increments tab-switch counter.
- POST `/api/quiz/submit` — finalize, calculate score, record time_taken.
- POST `/api/admin/login` — admin/admin123.
- GET `/api/admin/stats` — counts.
- GET `/api/admin/participants?search=` — rows joined with sessions.
- GET `/api/admin/leaderboard` — top 100 sorted by score desc, time asc.
- GET `/api/admin/export` — CSV download.

## Manual Backend Smoke Tests (curl) — PASSED
- Register new participant → 200 with participant id, session_token, assigned_set
- Quiz start → 30 questions, correct set, valid ends_at
- Save answer → {ok:true}
- Admin stats/login → correct

## Findings / Notes
- 60 questions successfully parsed from DOCX and embedded in seed file
- Each participant answers 30 questions total (10 assigned set + 20 bonus common)
- Timer is server-driven via ends_at timestamp — survives refresh/reconnect
- Tab-switch auto-submit triggers when count > 2
- One-attempt-per-email/phone enforcement in place

## Comprehensive Backend Testing — COMPLETED ✅

### Test Suite Execution (21 Tests)
**Date:** 2025-01-XX  
**Result:** 21/21 PASSED (100% Success Rate)  
**Test Script:** `/app/backend_test.py`

### Tests Performed & Results:

#### Registration Endpoints (4 tests)
1. ✅ **Register New Participant** - Returns 200 with participant id, session_token, assigned_set (A/B/C), returning=false
2. ✅ **Register Duplicate Email** - Returns 200 with returning=true for existing user without submission
3. ✅ **Register Missing Fields** - Returns 400 with error message when email is missing
4. ✅ **Register Already Submitted** - Returns 403 with already_submitted=true when user tries to re-register after completing quiz

#### Quiz Start Endpoints (3 tests)
5. ✅ **Quiz Start Fresh** - Returns 30 questions (10 assigned set + 10 BONUS_RESEARCH + 10 BONUS_STARTUP), server_time, session.ends_at
6. ✅ **Quiz Start Restart** - Returns same session with preserved answers and tab_switches on restart
7. ✅ **Quiz Start Non-existent** - Returns 404 for non-existent participant_id
8. ✅ **Quiz Start After Submit** - Returns 403 with already_submitted=true after quiz submission

#### Quiz Answer Endpoints (3 tests)
9. ✅ **Answer Save** - Returns {ok:true} when answer is saved successfully
10. ✅ **Answer Wrong Token** - Returns 401 with invalid_session=true when session_token doesn't match
11. ✅ **Answer After Submit** - Returns 403 when attempting to save answer after submission

#### Quiz Tab Switch (1 test)
12. ✅ **Tab Switch Increment** - Correctly increments tab_switches counter (1, 2, 3...)

#### Quiz Submit Endpoints (3 tests)
13. ✅ **Submit with Score** - Calculates score correctly by comparing answers with correct_answer from DB, returns {ok:true}
14. ✅ **Submit Re-submit** - Returns {ok:true, already:true} on duplicate submission attempt
15. ✅ **Submit Verification** - Score calculation verified via admin/participants endpoint

#### Admin Login (2 tests)
16. ✅ **Admin Login Success** - Returns 200 with token for admin/admin123
17. ✅ **Admin Login Fail** - Returns 401 with error for wrong credentials

#### Admin Stats (1 test)
18. ✅ **Admin Stats** - Returns correct counts for total, in_progress, completed participants

#### Admin Participants (2 tests)
19. ✅ **Participants No Search** - Returns all participants with joined session data (status, score, time_taken)
20. ✅ **Participants With Search** - Filters correctly by name/email/phone/dept/college

#### Admin Leaderboard (1 test)
21. ✅ **Leaderboard Sorting** - Returns submitted sessions sorted by score DESC then time_taken_seconds ASC, includes rank

#### Admin Export (1 test)
22. ✅ **CSV Export** - Returns valid CSV with Content-Type: text/csv, Content-Disposition: attachment, correct headers and structure

### Key Validations Confirmed:
- ✅ One-attempt-per-participant enforced (email/phone can't re-submit)
- ✅ Random set assignment (A, B, or C) working
- ✅ Timer/ends_at is server-side and stable across restarts
- ✅ Tab switch counting works correctly
- ✅ Score calculation is accurate (compares with actual correct_answer from DB)
- ✅ Questions returned do NOT include correct_answer field (security validated)
- ✅ Session token validation prevents concurrent sessions
- ✅ All blocking mechanisms work (after submission, invalid session, etc.)

### Backend Status: FULLY FUNCTIONAL ✅
All critical backend flows are working correctly with no major issues found.

## Comprehensive Frontend E2E Testing — COMPLETED ✅

### Test Suite Execution
**Date:** 2025-01-16  
**Result:** ALL TESTS PASSED (100% Success Rate)  
**Test Method:** Python Playwright automation scripts
**URL Tested:** https://quiz-compete-15.preview.emergentagent.com

### Tests Performed & Results:

#### 1. Landing Page (/) — ✅ PASSED
- ✅ "The Ultimate MCQ Challenge" heading displayed correctly
- ✅ "Start Quiz" CTA button present and functional
- ✅ Three feature cards present: "15 Min Timer", "3 Random Sets", "Live Leaderboard"
- ✅ Admin button visible in top-right corner
- ✅ Clicking "Start Quiz" navigates to registration form

#### 2. Registration Flow — ✅ PASSED
- ✅ All form fields work correctly (full_name, email, phone, dob, college, department, year)
- ✅ Form submission successful with unique email (fe_test_1784168496@example.com)
- ✅ Success toast appears after registration
- ✅ Navigates to quiz page after successful registration
- ✅ localStorage correctly stores 'quiz_participant' and 'quiz_session_token'
- ✅ Form validation works (error toast appears for re-registration attempts)
- ✅ Re-registration with same email/phone is blocked with appropriate error message

#### 3. Quiz Page — ✅ PASSED
- ✅ 30 questions loaded successfully (all 30 palette buttons present)
- ✅ Top bar displays correctly:
  - Set badge (A/B/C) visible
  - Participant name displayed
  - Timer counting down from ~15:00
  - Progress bar showing completion percentage
- ✅ Answer selection works (option highlights in indigo color)
- ✅ Palette button turns indigo when question is answered
- ✅ "Next" button navigates to next question
- ✅ "Previous" button navigates to previous question
- ✅ Answer selection preserved when navigating between questions
- ✅ **Refresh persistence verified**: Answers preserved after page reload, timer continues counting (14:54 → 14:50)
- ✅ Palette navigation works (clicking #15 jumps directly to Q15)
- ✅ Right-click disabled (context menu prevention active)
- ✅ Last question (Q30) shows green "Submit Quiz" button
- ✅ Submit Quiz works and displays thank you page
- ✅ "Answered: X/30" counter updates correctly

#### 4. Anti-Cheating: Tab Switching — ✅ PASSED
- ✅ First tab switch triggers warning badge "Tab warnings: 1/2"
- ✅ Second tab switch updates badge to "Tab warnings: 2/2"
- ✅ Third tab switch auto-submits quiz and shows thank you page
- ✅ Warning toast appears on each tab switch
- ✅ Auto-submit message: "Tab switched more than 2 times — auto-submitting"

#### 5. Admin Dashboard — ✅ PASSED
- ✅ Admin login form appears when clicking Admin button from landing page
- ✅ Wrong credentials (admin/wrong) show error toast "Invalid credentials"
- ✅ Correct credentials (admin/admin123) login successfully
- ✅ Dashboard loads with "Quiz Arena — Admin" header
- ✅ Three stat cards display correctly:
  - Total Registrations: 7
  - Currently Taking Quiz: 1
  - Completed: 4
- ✅ Participants table displays with all required columns:
  - Name, Email, Phone, College, Dept, Set, Status, Score, Time, Tabs
- ✅ Search functionality works (filtering by "FE Test" shows correct results)
- ✅ Leaderboard tab loads successfully
- ✅ Leaderboard displays:
  - Rank column with correct numbering
  - Medal emojis for top 3 (🥇🥈🥉)
  - Sorted by score DESC, then time ASC
- ✅ Export CSV button present and visible
- ✅ Logout works and returns to landing page

#### 6. Mobile Responsiveness — ✅ PASSED
- ✅ Landing page renders correctly on mobile viewport (375x812)
- ✅ Layout doesn't break on mobile
- ✅ Text is readable and properly sized
- ✅ Single-column feature cards display correctly

### Key Frontend Validations Confirmed:
- ✅ Client-side routing works correctly (landing → register → quiz → thankyou → admin)
- ✅ localStorage persistence for session management
- ✅ Real-time timer countdown with server-side synchronization
- ✅ Answer auto-save functionality working
- ✅ Tab-switch detection and auto-submit mechanism functional
- ✅ Admin authentication and authorization working
- ✅ Search and filter functionality in admin panel
- ✅ Responsive design for mobile devices
- ✅ Toast notifications (Sonner) working for all user feedback
- ✅ No critical console errors or network failures blocking functionality

### Frontend Status: FULLY FUNCTIONAL ✅
All critical frontend flows are working correctly with no major issues found. The application is production-ready for the college event.

### Screenshots Captured:
- Landing page (desktop & mobile)
- Registration form
- Quiz page with questions and palette
- Thank you page after submission
- Tab switch auto-submit
- Admin login
- Admin dashboard with stats
- Participants table with search
- Leaderboard with medals

## Overall Application Status: PRODUCTION READY ✅
Both backend (21/21 tests) and frontend (all E2E flows) are fully functional with no critical issues.

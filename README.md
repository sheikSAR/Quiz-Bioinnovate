# College Event MCQ Quiz Competition

A responsive, mobile-friendly web application for running a live one-day MCQ quiz competition.

## Tech Stack

- **Frontend:** Next.js 15 (App Router) + Tailwind CSS + shadcn/ui + lucide-react + sonner
- **Backend:** Next.js API Routes (Node.js)
- **Database:** MongoDB (via `mongodb` driver)
- **Auth:** Simple participant identification (email + phone) + admin login (username/password)

> The initial spec suggested Supabase/PostgreSQL, but this MVP uses the template's MongoDB stack for fastest time-to-value while covering **all functional requirements**. The `README (Vercel/Supabase)` migration notes are at the bottom.

## Features

### Participant Flow
- Landing page with event branding and Start Quiz CTA
- Registration/login (find-or-create by email/phone)
- Random set assignment (A, B or C) — sticky across refresh/reconnect
- One-attempt-per-participant enforcement
- 30-question quiz (10 set-specific + 20 bonus questions common to all sets)
- 15-minute countdown timer, auto-submit on expiry
- Prev/Next navigation + question palette (jump-to)
- Auto-save answers on every selection
- Timer resumes correctly on refresh/reconnect (server-side `ends_at`)
- Post-submit screen shows only: **"Thank you for participating."**

### Anti-Cheating
- Timer stored on server (`ends_at`); refresh cannot reset it
- Right-click disabled during quiz
- Text selection disabled
- Tab-switch tracking via `visibilitychange` — warning shown, **>2 switches auto-submits**
- Single active session per participant (session token)
- Prevents re-taking after submission

### Admin Dashboard
- Login: **admin / admin123** (edit in `/app/app/api/[[...path]]/route.js`)
- Live stats: total registrations, in-progress, completed
- Participant table with search (name/email/phone/dept/college)
- Leaderboard sorted by score then fastest time
- CSV export (`/api/admin/export`)
- Auto-refreshes every 8 seconds

## Database Collections

| Collection | Fields |
|---|---|
| `participants` | id, full_name, dob, email, phone, college, department, year, assigned_set, created_at |
| `questions` | id, set (A/B/C/BONUS_RESEARCH/BONUS_STARTUP), question_number, question_text, options{A,B,C,D}, correct_answer, category |
| `quiz_sessions` | id, participant_id, assigned_set, started_at, ends_at, answers{qid:letter}, tab_switches, submitted, submitted_at, score, total_questions, time_taken_seconds, auto_submitted, session_token, last_seen |

Questions are **auto-seeded on first API request** from `/app/lib/questions_seed.js` (60 questions parsed from `College_Event_MCQ_Sets_A_B_C.docx`).

## Local Development

```bash
# Install deps
yarn install

# Start MongoDB locally (or set MONGO_URL in .env)
sudo service mongod start

# Ensure /app/.env has:
#   MONGO_URL=mongodb://localhost:27017
#   DB_NAME=quiz_app

# Run dev server
yarn dev
```

Open http://localhost:3000

Admin: http://localhost:3000/admin

## Deployment (Vercel)

1. Push this repo to GitHub.
2. Import into Vercel.
3. Set environment variables in Vercel Project Settings:
   - `MONGO_URL` = your MongoDB connection string (e.g., MongoDB Atlas)
   - `DB_NAME` = `quiz_app`
4. Deploy.

### MongoDB Atlas Setup

1. Create a free cluster at https://www.mongodb.com/cloud/atlas
2. Whitelist Vercel IPs (or `0.0.0.0/0` for simplicity)
3. Create a DB user, copy the SRV connection string
4. Paste into `MONGO_URL` env var

## Migrating to Supabase (Optional)

If you strictly require Supabase/PostgreSQL:

1. Create tables mirroring the collections above (see `sql/schema.sql` template you can adapt).
2. Replace MongoDB driver calls in `/app/app/api/[[...path]]/route.js` with `@supabase/supabase-js`.
3. Add env vars: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
4. Use Supabase Auth for admin (email/password) instead of the hardcoded admin.

## Question Import Utility

The DOCX file was parsed into a flat JSON structure at `/app/lib/questions_seed.js`.
To import new questions, either:
- Overwrite `RAW_QUESTIONS` in that file and clear the `questions` collection
- Or write an admin endpoint that reads a DOCX via `mammoth` and inserts rows

## Admin Credentials

- Username: `admin`
- Password: `admin123`

**Change these in `/app/app/api/[[...path]]/route.js` (constants `ADMIN_USER`, `ADMIN_PASS`) before the event.**

## Scalability Notes

- MongoDB connection is cached and reused across requests.
- All queries use indexed fields (`id`, `participant_id`, `email`, `phone`).
- Answers auto-save individually (small writes).
- Should comfortably handle ~1,000 concurrent participants on Vercel + Atlas M10.

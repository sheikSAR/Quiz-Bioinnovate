# BLUDE Quiz - MCQ Competition Platform

A responsive, mobile-friendly web application for a live one-day MCQ quiz competition, ready for 1,000 concurrent participants.

## Tech Stack

- **Frontend:** Next.js 15 (App Router) + Tailwind CSS + shadcn/ui + lucide-react + sonner
- **Backend:** Next.js API Routes (Node.js)
- **Database:** **Supabase (PostgreSQL)** via `@supabase/supabase-js`
- **Auth:** Environment-based admin credentials (`admin` / `admin123` by default)

## Features

### Participant Flow
- Branded landing page (BLUDE logo)
- Register/login (find-or-create by email + phone)
- Random set assignment (A, B or C), sticky across refresh/reconnect
- One attempt per participant, enforced across sessions
- 30-question quiz per participant (10 assigned + 20 bonus common questions)
- 15-minute server-side countdown timer
- Previous / Next navigation + jump-to question palette
- Auto-save on every answer selection
- Timer resumes correctly on refresh/reconnect
- Post-submit screen shows only: **"Thank you for participating."**

### Anti-Cheating
- Timer stored on server (`ends_at`); refresh cannot reset it
- Right-click and text-selection disabled during quiz
- Tab-switch tracking via `visibilitychange`; warning shown, **> 2 switches auto-submits**
- Single active session per participant (session token)
- Prevents re-taking after submission

### Admin Dashboard (`/admin`)
- Login with `admin@blude.local` / `admin123` (overridable via `ADMIN_EMAIL` / `ADMIN_PASSWORD` env vars)
- **Admin auth is powered by Supabase Auth.** The admin user is auto-provisioned on first login with the configured env credentials. All admin API endpoints require a valid Supabase JWT (Bearer token).
- Live stats: total registrations, in-progress, completed (auto-refresh 8s)
- Participant table with search (name, email, phone, department, college)
- Leaderboard sorted by score DESC then time_taken ASC (medals for top 3)
- CSV export (`/api/admin/export`)

## Database Schema

See `supabase/schema.sql`. Four tables:

| Table | Purpose |
|---|---|
| `participants` | Registrations with assigned_set |
| `questions` | 50 questions (10 each of A/B/C + 20 bonus) |
| `quiz_sessions` | Timer + answers + score per participant |
| `admin_users` | Registry of admin usernames |

Questions are **auto-seeded on first API request** from `lib/questions_seed.js` (parsed from the original DOCX).

## Local Development

```bash
# 1. Install dependencies
yarn install

# 2. Set env vars in .env (copy .env.example if provided)
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>

# 3. Run the schema once in Supabase SQL Editor
#    (copy supabase/schema.sql -> Supabase Dashboard -> SQL Editor -> Run)

# 4. Start dev server
yarn dev
```

Open http://localhost:3000
Admin: http://localhost:3000/admin

## Deployment

See **[DEPLOY.md](./DEPLOY.md)** for step-by-step Vercel + Supabase (recommended) or Vercel + MongoDB Atlas (alternative) deployment instructions.

## Question Import

The DOCX questions have been parsed into `lib/questions_seed.js` as a JavaScript array. To swap them:
1. Edit `RAW_QUESTIONS` in `lib/questions_seed.js`
2. In Supabase, run: `TRUNCATE questions;`
3. Hit any API endpoint. The app will auto-seed the new questions.

## Admin Credentials

Default: `admin` / `admin123`. Override in `.env` or Vercel env:

```
ADMIN_USERNAME=your_admin
ADMIN_PASSWORD=your_strong_password
```

## Scalability

- **Supabase Free** handles 500+ concurrent connections
- **Vercel Hobby** supports 100k function invocations/day
- Comfortable for a one-day 1,000-participant event
- Upgrade to Supabase Pro if you expect > 500 concurrent users at peak

## Project Structure

```
/app
├── app/
│   ├── api/[[...path]]/route.js    # All API endpoints
│   ├── admin/page.js               # /admin route
│   ├── layout.js                   # Root layout with BLUDE metadata
│   └── page.js                     # SPA with landing/register/quiz/thankyou/admin views
├── components/ui/                  # shadcn/ui components
├── lib/
│   ├── supabase.js                 # Supabase admin client (server-only)
│   └── questions_seed.js           # 50 quiz questions from DOCX
├── public/
│   └── blude-logo.webp             # BLUDE brand logo
├── supabase/
│   └── schema.sql                  # PostgreSQL schema DDL
├── DEPLOY.md                       # Vercel deployment guide
├── README.md
├── package.json
└── .env
```

## License

Proprietary - BLUDE College Event 2025.

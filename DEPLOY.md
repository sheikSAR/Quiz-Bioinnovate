# BLUDE Quiz - Deployment Guide

This app is currently configured with **Supabase (PostgreSQL)**. This guide covers deployment to Vercel with two database options:

- **Option 1 (Recommended, current stack):** Vercel + Supabase
- **Option 2 (Alternative):** Vercel + MongoDB Atlas — requires reverting the API route to the MongoDB version (see bottom)

---

## Prerequisites

- A GitHub account (to push this repo)
- A Vercel account (free tier is fine): https://vercel.com
- A Supabase project **or** a MongoDB Atlas cluster (pick one)

---

## Option 1: Vercel + Supabase (recommended)

### 1. Push the repo to GitHub

```bash
cd /app
git init
git add .
git commit -m "Initial commit: BLUDE Quiz"
git branch -M main
# Create an empty repo on GitHub, then:
git remote add origin https://github.com/<your-username>/blude-quiz.git
git push -u origin main
```

### 2. Set up Supabase (skip if already done)

1. Go to https://supabase.com/dashboard and create a new project. Pick a strong DB password (save it) and the region closest to your users.
2. Wait ~1 minute for the project to provision.
3. In the sidebar, open **SQL Editor** → **New query**.
4. Paste the contents of `/app/supabase/schema.sql` and click **Run**. You should see "Success. No rows returned".
5. In the sidebar, open **Settings → API** and copy:
   - **Project URL** → will become `SUPABASE_URL`
   - **`service_role` secret** → will become `SUPABASE_SERVICE_ROLE_KEY`
   - **`anon` public key** → will become `NEXT_PUBLIC_SUPABASE_ANON_KEY` (optional, only used if you extend to client-side calls)

> The 50 quiz questions are auto-seeded from `/app/lib/questions_seed.js` on the first API request after deployment; you don't need to seed manually.

### 3. Deploy to Vercel

1. Go to https://vercel.com/new and **Import** your GitHub repo.
2. Framework preset: **Next.js** (auto-detected).
3. **Root directory:** leave as `.` (root).
4. Click **Environment Variables** and add:

   | Name | Value |
   |---|---|
   | `SUPABASE_URL` | `https://<your-project-ref>.supabase.co` |
   | `SUPABASE_SERVICE_ROLE_KEY` | `eyJhbG...` (the service_role key) |
   | `SUPABASE_ANON_KEY` | `eyJhbG...` (the anon key, optional) |
   | `ADMIN_EMAIL` | `admin@blude.local` (or your email) |
   | `ADMIN_PASSWORD` | choose a strong password (min 6 chars) |

   > **Admin authentication uses Supabase Auth.** On the first admin login attempt with the credentials above, the app will automatically create a Supabase Auth user with that email/password. All admin API endpoints require a valid Supabase JWT (issued at login).

5. Click **Deploy**. Wait ~2 minutes.
6. Once deployed, open your Vercel URL. On first load the app will auto-seed the 50 quiz questions.

### 4. Post-deployment sanity checks

- Visit `/` → landing page with BLUDE logo, "Start Quiz" button.
- Visit `/admin` → login with the credentials you set. Dashboard should show `Total: 0`, `In progress: 0`, `Completed: 0`.
- Do one full test registration + quiz submission to confirm end-to-end.

### 5. Custom domain (optional)

In Vercel → Project → **Domains** → add your domain and follow the DNS instructions.

---

## Option 2: Vercel + MongoDB Atlas (alternative)

Only use this if you prefer NoSQL / MongoDB.

### 1. Revert the API route to MongoDB

The MongoDB version of the API route is preserved in git history. To restore it:

```bash
# Show the previous MongoDB version and copy it back
git log --oneline app/api/[[...path]]/route.js
git show <mongo-commit-sha>:app/api/[[...path]]/route.js > app/api/[[...path]]/route.js
```

Or manually revert to using `mongodb` driver. The Mongo version needs env vars:

- `MONGO_URL` = your MongoDB connection string
- `DB_NAME` = `blude_quiz`

### 2. Create MongoDB Atlas cluster

1. Go to https://www.mongodb.com/cloud/atlas and create a free **M0** cluster (choose AWS region closest to Vercel deployment).
2. **Database Access** → Add DB User → username + strong password → role: `readWrite` on your DB.
3. **Network Access** → Add IP → `0.0.0.0/0` (allow from anywhere; Vercel uses dynamic IPs).
4. **Database** → Connect → Drivers → Node.js → copy the SRV URI. It will look like:

   ```
   mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### 3. Deploy to Vercel

Same as Option 1, but set these env vars instead:

| Name | Value |
|---|---|
| `MONGO_URL` | Your MongoDB Atlas SRV URI |
| `DB_NAME` | `blude_quiz` |
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | strong password |

Click **Deploy**. Questions auto-seed on first request.

---

## Environment Variables Reference

| Variable | Required (Supabase) | Required (Mongo) | Purpose |
|---|:---:|:---:|---|
| `SUPABASE_URL` | ✅ | – | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | – | Service role JWT (server-only) |
| `SUPABASE_ANON_KEY` | optional | – | Public anon key |
| `MONGO_URL` | – | ✅ | MongoDB connection string |
| `DB_NAME` | – | ✅ | Mongo database name |
| `ADMIN_USERNAME` | optional | optional | Overrides default `admin` |
| `ADMIN_PASSWORD` | optional | optional | Overrides default `admin123` |
| `NEXT_PUBLIC_BASE_URL` | optional | optional | External URL of the app |

> **Security:** Never commit `.env` files. `NEXT_PUBLIC_` prefixed vars are exposed to the browser — do not put secrets there.

---

## Scaling for 1,000 participants

- **Supabase Free tier:** handles ~500 concurrent connections. Should handle 1,000 participants event fine since API calls are short-lived.
- **Vercel Hobby tier:** 100 GB bandwidth/month, 100k function invocations/day. Sufficient for a one-day 1,000-person event.
- If you expect heavier load, upgrade to Supabase Pro ($25/mo) which gives you a bigger pool.

---

## Troubleshooting

**"Could not find the table 'public.questions' in the schema cache"**
→ You forgot to run `supabase/schema.sql` in the Supabase SQL Editor. Run it, then hit any API endpoint to auto-seed.

**Timer looks off**
→ Ensure your Vercel region and Supabase region are the same continent to minimize clock drift.

**Admin dashboard shows 0 participants but registrations exist**
→ Verify `SUPABASE_URL` matches the project where the schema was created. Check Vercel logs for RLS/permission errors.

**Question re-seeding**
→ To re-seed: delete all rows from `questions` in Supabase, then hit any API endpoint. The app auto-seeds when the table is empty.

---

## Changing Admin Password

Best practice: set `ADMIN_PASSWORD` in Vercel Environment Variables and redeploy. Do **not** commit passwords to the repo.

---

## Live Demo

- Preview (this container): https://quiz-compete-15.preview.emergentagent.com
- Admin: `/admin` — login with `admin` / `admin123` (change in production!)

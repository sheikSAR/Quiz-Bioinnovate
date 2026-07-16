-- ============================================================
-- BLUDE Quiz Competition - Supabase Schema
-- Run this ONCE in your Supabase project SQL Editor
-- (Dashboard -> SQL Editor -> New query -> Paste -> Run)
-- ============================================================

-- Optional cleanup (uncomment if you need a fresh start)
-- DROP TABLE IF EXISTS quiz_sessions CASCADE;
-- DROP TABLE IF EXISTS participants CASCADE;
-- DROP TABLE IF EXISTS questions CASCADE;
-- DROP TABLE IF EXISTS admin_users CASCADE;

-- ============================================================
-- 1. PARTICIPANTS
-- ============================================================
CREATE TABLE IF NOT EXISTS participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    dob TEXT DEFAULT '',
    email TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    college TEXT DEFAULT '',
    department TEXT DEFAULT '',
    year TEXT DEFAULT '',
    assigned_set TEXT NOT NULL CHECK (assigned_set IN ('A','B','C')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_participants_email ON participants(email);
CREATE INDEX IF NOT EXISTS idx_participants_phone ON participants(phone);
CREATE INDEX IF NOT EXISTS idx_participants_created ON participants(created_at DESC);

-- ============================================================
-- 2. QUESTIONS
-- Sets A/B/C = 10 questions each. BONUS_RESEARCH/BONUS_STARTUP = 10 each,
-- shown to everyone (30 total per participant).
-- ============================================================
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set TEXT NOT NULL,
    question_number INT NOT NULL,
    question_text TEXT NOT NULL,
    options JSONB NOT NULL,           -- {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer TEXT NOT NULL CHECK (correct_answer IN ('A','B','C','D')),
    category TEXT DEFAULT '',
    UNIQUE(set, question_number)
);

CREATE INDEX IF NOT EXISTS idx_questions_set ON questions(set);

-- ============================================================
-- 3. QUIZ SESSIONS (one per participant)
-- ============================================================
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id UUID NOT NULL UNIQUE REFERENCES participants(id) ON DELETE CASCADE,
    assigned_set TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ends_at TIMESTAMPTZ NOT NULL,
    answers JSONB DEFAULT '{}'::jsonb, -- {question_id: 'A'/'B'/'C'/'D'}
    tab_switches INT DEFAULT 0,
    submitted BOOLEAN DEFAULT FALSE,
    submitted_at TIMESTAMPTZ,
    score INT,
    total_questions INT,
    time_taken_seconds INT,
    auto_submitted BOOLEAN DEFAULT FALSE,
    session_token TEXT,
    last_seen TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_participant ON quiz_sessions(participant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_submitted ON quiz_sessions(submitted);
CREATE INDEX IF NOT EXISTS idx_sessions_score ON quiz_sessions(score DESC, time_taken_seconds ASC);

-- ============================================================
-- 4. ADMIN USERS (only used for reference; login credential is env-based)
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO admin_users (username) VALUES ('admin') ON CONFLICT (username) DO NOTHING;

-- ============================================================
-- 5. Disable RLS on our tables (since we only use service_role from server)
-- ============================================================
ALTER TABLE participants     DISABLE ROW LEVEL SECURITY;
ALTER TABLE questions        DISABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_sessions    DISABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users      DISABLE ROW LEVEL SECURITY;

-- Done. Questions will be auto-seeded by the app on first API request.

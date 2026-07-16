import { NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';
import { v4 as uuidv4 } from 'uuid';
import { RAW_QUESTIONS } from '@/lib/questions_seed';

const MONGO_URL = process.env.MONGO_URL;
const DB_NAME = process.env.DB_NAME || 'quiz_app';

let cachedClient = null;
async function getDb() {
  if (!cachedClient) {
    cachedClient = new MongoClient(MONGO_URL);
    await cachedClient.connect();
  }
  return cachedClient.db(DB_NAME);
}

const QUIZ_DURATION_SEC = 15 * 60; // 15 minutes
const ADMIN_USER = 'admin';
const ADMIN_PASS = 'admin123';

async function seedIfNeeded(db) {
  const count = await db.collection('questions').countDocuments();
  if (count > 0) return;
  const docs = RAW_QUESTIONS.map((r) => ({
    id: uuidv4(),
    set: r.set,
    question_number: r.n,
    question_text: r.q,
    options: { A: r.a, B: r.b, C: r.c, D: r.d },
    correct_answer: r.ans,
    category: r.cat,
  }));
  await db.collection('questions').insertMany(docs);
}

async function buildQuestionsForSet(db, setLetter) {
  // Return set questions + bonus rounds; strip correct answers
  const setQs = await db
    .collection('questions')
    .find({ set: setLetter })
    .sort({ question_number: 1 })
    .toArray();
  const bonus1 = await db
    .collection('questions')
    .find({ set: 'BONUS_RESEARCH' })
    .sort({ question_number: 1 })
    .toArray();
  const bonus2 = await db
    .collection('questions')
    .find({ set: 'BONUS_STARTUP' })
    .sort({ question_number: 1 })
    .toArray();
  const all = [...setQs, ...bonus1, ...bonus2];
  return all.map((q) => ({
    id: q.id,
    set: q.set,
    question_number: q.question_number,
    question_text: q.question_text,
    options: q.options,
    category: q.category,
  }));
}

function randomSet() {
  const sets = ['A', 'B', 'C'];
  return sets[Math.floor(Math.random() * sets.length)];
}

function sanitizeParticipant(p) {
  if (!p) return null;
  const { _id, ...rest } = p;
  return rest;
}

function sanitizeSession(s) {
  if (!s) return null;
  const { _id, ...rest } = s;
  return rest;
}

async function handler(request, ctx) {
  const db = await getDb();
  await seedIfNeeded(db);

  const url = new URL(request.url);
  const resolvedParams = await ctx.params;
  const pathParts = resolvedParams?.path || [];
  const path = '/' + pathParts.join('/');
  const method = request.method;

  try {
    // Health
    if (path === '/' || path === '') {
      return NextResponse.json({ status: 'ok', service: 'quiz-api' });
    }

    // ---------- PARTICIPANT ----------
    if (path === '/register' && method === 'POST') {
      const body = await request.json();
      const { full_name, dob, email, phone, college, department, year } = body;
      if (!full_name || !email || !phone) {
        return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
      }
      const emailLc = String(email).toLowerCase().trim();
      let participant = await db
        .collection('participants')
        .findOne({ $or: [{ email: emailLc }, { phone: String(phone).trim() }] });

      if (participant) {
        // Check if already submitted
        const existingSession = await db
          .collection('quiz_sessions')
          .findOne({ participant_id: participant.id });
        if (existingSession?.submitted) {
          return NextResponse.json({
            error: 'You have already completed the quiz. Each participant can attempt only once.',
            already_submitted: true,
          }, { status: 403 });
        }
        // Existing session token OR create new one for reconnect
        const session_token = uuidv4();
        if (existingSession) {
          await db.collection('quiz_sessions').updateOne(
            { participant_id: participant.id },
            { $set: { session_token, last_seen: new Date() } }
          );
        }
        return NextResponse.json({
          participant: sanitizeParticipant(participant),
          session_token,
          returning: true,
        });
      }

      // Create new participant
      const assignedSet = randomSet();
      const newParticipant = {
        id: uuidv4(),
        full_name: full_name.trim(),
        dob: dob || '',
        email: emailLc,
        phone: String(phone).trim(),
        college: college || '',
        department: department || '',
        year: year || '',
        assigned_set: assignedSet,
        created_at: new Date(),
      };
      await db.collection('participants').insertOne(newParticipant);
      const session_token = uuidv4();
      return NextResponse.json({
        participant: sanitizeParticipant(newParticipant),
        session_token,
        returning: false,
      });
    }

    // Get or start quiz session for participant
    if (path === '/quiz/start' && method === 'POST') {
      const body = await request.json();
      const { participant_id, session_token } = body;
      const participant = await db
        .collection('participants')
        .findOne({ id: participant_id });
      if (!participant) {
        return NextResponse.json({ error: 'Participant not found' }, { status: 404 });
      }
      let session = await db
        .collection('quiz_sessions')
        .findOne({ participant_id });

      if (session?.submitted) {
        return NextResponse.json({
          error: 'Quiz already submitted',
          already_submitted: true,
        }, { status: 403 });
      }

      if (!session) {
        const now = new Date();
        const ends_at = new Date(now.getTime() + QUIZ_DURATION_SEC * 1000);
        session = {
          id: uuidv4(),
          participant_id,
          assigned_set: participant.assigned_set,
          started_at: now,
          ends_at,
          answers: {},
          tab_switches: 0,
          submitted: false,
          session_token: session_token || uuidv4(),
          last_seen: now,
        };
        await db.collection('quiz_sessions').insertOne(session);
      } else {
        // Update session token to enforce single active session
        await db.collection('quiz_sessions').updateOne(
          { participant_id },
          { $set: { session_token: session_token || session.session_token, last_seen: new Date() } }
        );
        session.session_token = session_token || session.session_token;
      }

      const questions = await buildQuestionsForSet(db, participant.assigned_set);

      return NextResponse.json({
        participant: sanitizeParticipant(participant),
        session: sanitizeSession(session),
        questions,
        server_time: new Date().toISOString(),
      });
    }

    // Autosave a single answer
    if (path === '/quiz/answer' && method === 'POST') {
      const body = await request.json();
      const { participant_id, session_token, question_id, answer } = body;
      const session = await db.collection('quiz_sessions').findOne({ participant_id });
      if (!session) return NextResponse.json({ error: 'No session' }, { status: 404 });
      if (session.submitted) return NextResponse.json({ error: 'Already submitted' }, { status: 403 });
      if (session.session_token && session_token && session.session_token !== session_token) {
        return NextResponse.json({ error: 'Session invalid – opened elsewhere', invalid_session: true }, { status: 401 });
      }
      const update = {};
      update[`answers.${question_id}`] = answer;
      await db.collection('quiz_sessions').updateOne(
        { participant_id },
        { $set: { ...update, last_seen: new Date() } }
      );
      return NextResponse.json({ ok: true });
    }

    // Tab switch increment
    if (path === '/quiz/tabswitch' && method === 'POST') {
      const body = await request.json();
      const { participant_id } = body;
      const session = await db.collection('quiz_sessions').findOne({ participant_id });
      if (!session) return NextResponse.json({ error: 'No session' }, { status: 404 });
      if (session.submitted) return NextResponse.json({ ok: true, submitted: true });
      const newCount = (session.tab_switches || 0) + 1;
      await db.collection('quiz_sessions').updateOne(
        { participant_id },
        { $set: { tab_switches: newCount, last_seen: new Date() } }
      );
      return NextResponse.json({ ok: true, tab_switches: newCount });
    }

    // Submit quiz
    if (path === '/quiz/submit' && method === 'POST') {
      const body = await request.json();
      const { participant_id, auto } = body;
      const session = await db.collection('quiz_sessions').findOne({ participant_id });
      if (!session) return NextResponse.json({ error: 'No session' }, { status: 404 });
      if (session.submitted) return NextResponse.json({ ok: true, already: true });

      // Calculate score
      const questionIds = Object.keys(session.answers || {});
      const allQuestions = await db
        .collection('questions')
        .find({ id: { $in: questionIds } })
        .toArray();
      let score = 0;
      for (const q of allQuestions) {
        if (session.answers[q.id] && session.answers[q.id] === q.correct_answer) score += 1;
      }
      // Total question count for participant's assigned set (set + 20 bonus)
      const totalForSet = await db
        .collection('questions')
        .countDocuments({ set: { $in: [session.assigned_set, 'BONUS_RESEARCH', 'BONUS_STARTUP'] } });

      const submitted_at = new Date();
      const time_taken_seconds = Math.floor((submitted_at - new Date(session.started_at)) / 1000);
      await db.collection('quiz_sessions').updateOne(
        { participant_id },
        {
          $set: {
            submitted: true,
            submitted_at,
            score,
            total_questions: totalForSet,
            time_taken_seconds,
            auto_submitted: !!auto,
          },
        }
      );
      return NextResponse.json({ ok: true });
    }

    // ---------- ADMIN ----------
    if (path === '/admin/login' && method === 'POST') {
      const body = await request.json();
      const { username, password } = body;
      if (username === ADMIN_USER && password === ADMIN_PASS) {
        return NextResponse.json({ ok: true, token: 'admin_' + uuidv4() });
      }
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }

    if (path === '/admin/stats' && method === 'GET') {
      const total = await db.collection('participants').countDocuments();
      const inProgress = await db
        .collection('quiz_sessions')
        .countDocuments({ submitted: false });
      const completed = await db
        .collection('quiz_sessions')
        .countDocuments({ submitted: true });
      return NextResponse.json({ total, in_progress: inProgress, completed });
    }

    if (path === '/admin/participants' && method === 'GET') {
      const search = url.searchParams.get('search') || '';
      const query = {};
      if (search.trim()) {
        const rx = new RegExp(search.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
        query.$or = [
          { full_name: rx },
          { email: rx },
          { phone: rx },
          { department: rx },
          { college: rx },
        ];
      }
      const participants = await db
        .collection('participants')
        .find(query)
        .sort({ created_at: -1 })
        .limit(2000)
        .toArray();

      const ids = participants.map((p) => p.id);
      const sessions = await db
        .collection('quiz_sessions')
        .find({ participant_id: { $in: ids } })
        .toArray();
      const sessionMap = {};
      for (const s of sessions) sessionMap[s.participant_id] = s;

      const rows = participants.map((p) => {
        const s = sessionMap[p.id];
        return {
          id: p.id,
          full_name: p.full_name,
          email: p.email,
          phone: p.phone,
          college: p.college,
          department: p.department,
          year: p.year,
          assigned_set: p.assigned_set,
          status: s ? (s.submitted ? 'completed' : 'in_progress') : 'registered',
          score: s?.score ?? null,
          total_questions: s?.total_questions ?? null,
          time_taken_seconds: s?.time_taken_seconds ?? null,
          tab_switches: s?.tab_switches ?? 0,
          auto_submitted: s?.auto_submitted || false,
          submitted_at: s?.submitted_at ?? null,
          started_at: s?.started_at ?? null,
        };
      });
      return NextResponse.json({ rows });
    }

    if (path === '/admin/leaderboard' && method === 'GET') {
      const sessions = await db
        .collection('quiz_sessions')
        .find({ submitted: true })
        .sort({ score: -1, time_taken_seconds: 1 })
        .limit(100)
        .toArray();
      const pids = sessions.map((s) => s.participant_id);
      const participants = await db
        .collection('participants')
        .find({ id: { $in: pids } })
        .toArray();
      const pMap = {};
      participants.forEach((p) => (pMap[p.id] = p));
      const rows = sessions.map((s, i) => ({
        rank: i + 1,
        full_name: pMap[s.participant_id]?.full_name || '—',
        college: pMap[s.participant_id]?.college || '—',
        department: pMap[s.participant_id]?.department || '—',
        assigned_set: s.assigned_set,
        score: s.score,
        total_questions: s.total_questions,
        time_taken_seconds: s.time_taken_seconds,
      }));
      return NextResponse.json({ rows });
    }

    if (path === '/admin/export' && method === 'GET') {
      const participants = await db.collection('participants').find({}).toArray();
      const sessions = await db.collection('quiz_sessions').find({}).toArray();
      const sMap = {};
      sessions.forEach((s) => (sMap[s.participant_id] = s));
      const headers = [
        'Full Name','Email','Phone','College','Department','Year','Assigned Set',
        'Status','Score','Total Questions','Time Taken (sec)','Tab Switches',
        'Auto Submitted','Started At','Submitted At',
      ];
      const escape = (v) => {
        if (v === null || v === undefined) return '';
        const s = String(v);
        if (s.includes(',') || s.includes('"') || s.includes('\n')) {
          return '"' + s.replace(/"/g, '""') + '"';
        }
        return s;
      };
      const lines = [headers.join(',')];
      for (const p of participants) {
        const s = sMap[p.id];
        lines.push([
          p.full_name, p.email, p.phone, p.college, p.department, p.year,
          p.assigned_set,
          s ? (s.submitted ? 'completed' : 'in_progress') : 'registered',
          s?.score ?? '', s?.total_questions ?? '', s?.time_taken_seconds ?? '',
          s?.tab_switches ?? 0, s?.auto_submitted ? 'yes' : 'no',
          s?.started_at ? new Date(s.started_at).toISOString() : '',
          s?.submitted_at ? new Date(s.submitted_at).toISOString() : '',
        ].map(escape).join(','));
      }
      const csv = lines.join('\n');
      return new Response(csv, {
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="quiz_results.csv"',
        },
      });
    }

    return NextResponse.json({ error: 'Not found', path, method }, { status: 404 });
  } catch (err) {
    console.error('API error:', err);
    return NextResponse.json({ error: 'Server error', detail: String(err?.message || err) }, { status: 500 });
  }
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const DELETE = handler;
export const PATCH = handler;

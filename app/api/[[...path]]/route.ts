import { NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';
import { supabaseAdmin, supabaseAnon } from '@/lib/supabase';
import { RAW_QUESTIONS } from '@/lib/questions_seed';

export const dynamic = 'force-dynamic';

const QUIZ_DURATION_SEC = 15 * 60; // 15 minutes
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@blude.local';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';

let seededOnce = false;

async function seedIfNeeded() {
  if (seededOnce) return;
  const { count, error } = await supabaseAdmin
    .from('questions')
    .select('*', { count: 'exact', head: true });
  if (error) {
    throw new Error('Supabase schema not initialized. Run supabase/schema.sql in the SQL Editor. Detail: ' + error.message);
  }
  if ((count || 0) === 0) {
    const rows = RAW_QUESTIONS.map((r) => ({
      id: uuidv4(),
      set: r.set,
      question_number: r.n,
      question_text: r.q,
      options: { A: r.a, B: r.b, C: r.c, D: r.d },
      correct_answer: r.ans,
      category: r.cat,
    }));
    const { error: insErr } = await supabaseAdmin.from('questions').insert(rows);
    if (insErr) throw new Error('Failed to seed questions: ' + insErr.message);
  }
  seededOnce = true;
}

async function buildQuestionsForSet(setLetter) {
  const sets = [setLetter, 'BONUS_RESEARCH', 'BONUS_STARTUP'];
  const { data, error } = await supabaseAdmin
    .from('questions')
    .select('id,set,question_number,question_text,options,category')
    .in('set', sets)
    .order('set', { ascending: true })
    .order('question_number', { ascending: true });
  if (error) throw error;
  const own = (data || []).filter((q) => q.set === setLetter);
  const bonus = (data || []).filter((q) => q.set !== setLetter);
  return [...own, ...bonus];
}

function randomSet() {
  const sets = ['A', 'B', 'C'];
  return sets[Math.floor(Math.random() * sets.length)];
}

// --------- Supabase Auth helpers for admin ---------
async function ensureAdminUserExists() {
  // Idempotent: try to create the admin user; if it exists, ignore.
  try {
    const { data: list } = await supabaseAdmin.auth.admin.listUsers({ page: 1, perPage: 200 });
    const exists = (list?.users || []).some((u) => u.email === ADMIN_EMAIL);
    if (exists) return;
    await supabaseAdmin.auth.admin.createUser({
      email: ADMIN_EMAIL,
      password: ADMIN_PASSWORD,
      email_confirm: true,
      user_metadata: { role: 'admin' },
    });
  } catch (e) {
    console.warn('ensureAdminUserExists warning:', e?.message || e);
  }
}

async function verifyAdminToken(request) {
  const auth = request.headers.get('authorization') || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null;
  if (!token) return null;
  const { data, error } = await supabaseAdmin.auth.getUser(token);
  if (error || !data?.user) return null;
  if (data.user.email !== ADMIN_EMAIL) return null;
  return data.user;
}

function unauthorized() {
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
}

async function handler(request, ctx) {
  const url = new URL(request.url);
  const resolvedParams = await ctx.params;
  const pathParts = resolvedParams?.path || [];
  const path = '/' + pathParts.join('/');
  const method = request.method;

  try {
    if (path === '/' || path === '') {
      return NextResponse.json({ status: 'ok', service: 'blude-quiz-api', provider: 'supabase', auth: 'supabase' });
    }

    await seedIfNeeded();

    // ---------- PARTICIPANT ----------
    if (path === '/register' && method === 'POST') {
      const body = await request.json();
      const { full_name, dob, email, phone, college, department, year } = body;
      if (!full_name || !email || !phone) {
        return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
      }
      const emailLc = String(email).toLowerCase().trim();
      const phoneStr = String(phone).trim();

      const { data: existingList } = await supabaseAdmin
        .from('participants')
        .select('*')
        .or(`email.eq.${emailLc},phone.eq.${phoneStr}`)
        .limit(1);
      const existing = existingList && existingList[0];

      if (existing) {
        const { data: sess } = await supabaseAdmin
          .from('quiz_sessions')
          .select('*')
          .eq('participant_id', existing.id)
          .maybeSingle();
        if (sess?.submitted) {
          return NextResponse.json({
            error: 'You have already completed the quiz. Each participant can attempt only once.',
            already_submitted: true,
          }, { status: 403 });
        }
        const session_token = uuidv4();
        if (sess) {
          await supabaseAdmin
            .from('quiz_sessions')
            .update({ session_token, last_seen: new Date().toISOString() })
            .eq('participant_id', existing.id);
        }
        return NextResponse.json({
          participant: existing,
          session_token,
          returning: true,
        });
      }

      const assignedSet = randomSet();
      const newP = {
        id: uuidv4(),
        full_name: full_name.trim(),
        dob: dob || '',
        email: emailLc,
        phone: phoneStr,
        college: college || '',
        department: department || '',
        year: year || '',
        assigned_set: assignedSet,
      };
      const { data: inserted, error: insErr } = await supabaseAdmin
        .from('participants')
        .insert(newP)
        .select()
        .single();
      if (insErr) throw insErr;
      return NextResponse.json({
        participant: inserted,
        session_token: uuidv4(),
        returning: false,
      });
    }

    // ---------- QUIZ START ----------
    if (path === '/quiz/start' && method === 'POST') {
      const body = await request.json();
      const { participant_id, session_token } = body;
      const { data: participant } = await supabaseAdmin
        .from('participants')
        .select('*')
        .eq('id', participant_id)
        .maybeSingle();
      if (!participant) return NextResponse.json({ error: 'Participant not found' }, { status: 404 });
      let { data: session } = await supabaseAdmin
        .from('quiz_sessions')
        .select('*')
        .eq('participant_id', participant_id)
        .maybeSingle();

      if (session?.submitted) {
        return NextResponse.json({ error: 'Quiz already submitted', already_submitted: true }, { status: 403 });
      }

      if (!session) {
        const now = new Date();
        const ends_at = new Date(now.getTime() + QUIZ_DURATION_SEC * 1000);
        const row = {
          id: uuidv4(),
          participant_id,
          assigned_set: participant.assigned_set,
          started_at: now.toISOString(),
          ends_at: ends_at.toISOString(),
          answers: {},
          tab_switches: 0,
          submitted: false,
          session_token: session_token || uuidv4(),
          last_seen: now.toISOString(),
        };
        const { data: created, error: e2 } = await supabaseAdmin
          .from('quiz_sessions')
          .insert(row)
          .select()
          .single();
        if (e2) throw e2;
        session = created;
      } else {
        await supabaseAdmin
          .from('quiz_sessions')
          .update({ session_token: session_token || session.session_token, last_seen: new Date().toISOString() })
          .eq('participant_id', participant_id);
        if (session_token) session.session_token = session_token;
      }

      const questions = await buildQuestionsForSet(participant.assigned_set);
      return NextResponse.json({ participant, session, questions, server_time: new Date().toISOString() });
    }

    if (path === '/quiz/answer' && method === 'POST') {
      const body = await request.json();
      const { participant_id, session_token, question_id, answer } = body;
      const { data: session } = await supabaseAdmin
        .from('quiz_sessions')
        .select('*')
        .eq('participant_id', participant_id)
        .maybeSingle();
      if (!session) return NextResponse.json({ error: 'No session' }, { status: 404 });
      if (session.submitted) return NextResponse.json({ error: 'Already submitted' }, { status: 403 });
      if (session.session_token && session_token && session.session_token !== session_token) {
        return NextResponse.json({ error: 'Session invalid. Opened elsewhere.', invalid_session: true }, { status: 401 });
      }
      const newAnswers = { ...(session.answers || {}), [question_id]: answer };
      const { error: eUpd } = await supabaseAdmin
        .from('quiz_sessions')
        .update({ answers: newAnswers, last_seen: new Date().toISOString() })
        .eq('participant_id', participant_id);
      if (eUpd) throw eUpd;
      return NextResponse.json({ ok: true });
    }

    if (path === '/quiz/tabswitch' && method === 'POST') {
      const body = await request.json();
      const { participant_id } = body;
      const { data: session } = await supabaseAdmin
        .from('quiz_sessions')
        .select('*')
        .eq('participant_id', participant_id)
        .maybeSingle();
      if (!session) return NextResponse.json({ error: 'No session' }, { status: 404 });
      if (session.submitted) return NextResponse.json({ ok: true, submitted: true });
      const newCount = (session.tab_switches || 0) + 1;
      await supabaseAdmin
        .from('quiz_sessions')
        .update({ tab_switches: newCount, last_seen: new Date().toISOString() })
        .eq('participant_id', participant_id);
      return NextResponse.json({ ok: true, tab_switches: newCount });
    }

    if (path === '/quiz/submit' && method === 'POST') {
      const body = await request.json();
      const { participant_id, auto } = body;
      const { data: session } = await supabaseAdmin
        .from('quiz_sessions')
        .select('*')
        .eq('participant_id', participant_id)
        .maybeSingle();
      if (!session) return NextResponse.json({ error: 'No session' }, { status: 404 });
      if (session.submitted) return NextResponse.json({ ok: true, already: true });

      const questionIds = Object.keys(session.answers || {});
      let allQuestions = [];
      if (questionIds.length > 0) {
        const { data: qs } = await supabaseAdmin
          .from('questions')
          .select('id,correct_answer')
          .in('id', questionIds);
        allQuestions = qs || [];
      }
      let score = 0;
      for (const q of allQuestions) {
        if (session.answers[q.id] && session.answers[q.id] === q.correct_answer) score += 1;
      }
      const { count: totalForSet } = await supabaseAdmin
        .from('questions')
        .select('*', { count: 'exact', head: true })
        .in('set', [session.assigned_set, 'BONUS_RESEARCH', 'BONUS_STARTUP']);

      const submitted_at = new Date();
      const time_taken_seconds = Math.floor(
        (submitted_at.getTime() - new Date(session.started_at).getTime()) / 1000
      );
      await supabaseAdmin
        .from('quiz_sessions')
        .update({
          submitted: true,
          submitted_at: submitted_at.toISOString(),
          score,
          total_questions: totalForSet || 0,
          time_taken_seconds,
          auto_submitted: !!auto,
        })
        .eq('participant_id', participant_id);
      return NextResponse.json({ ok: true });
    }

    // ---------- ADMIN (Supabase Auth) ----------
    if (path === '/admin/reset-request' && method === 'POST') {
      const body = await request.json();
      const email = String(body.email || '').trim().toLowerCase();
      // Always return ok to prevent email enumeration.
      // Only actually send a reset email if the email matches the configured admin email.
      if (email && email === ADMIN_EMAIL.toLowerCase()) {
        const base = process.env.NEXT_PUBLIC_BASE_URL || '';
        const redirectTo = base.replace(/\/$/, '') + '/admin/reset';
        const { error } = await supabaseAnon.auth.resetPasswordForEmail(email, { redirectTo });
        if (error) console.warn('reset-request error:', error?.message);
      }
      return NextResponse.json({ ok: true });
    }

    if (path === '/admin/login' && method === 'POST') {
      const body = await request.json();
      // Accept both {email,password} and legacy {username,password}
      const email = (body.email || body.username || '').trim().toLowerCase();
      const password = body.password || '';

      // Auto-bootstrap the admin user on first login attempt with matching env creds
      if (email === ADMIN_EMAIL.toLowerCase() && password === ADMIN_PASSWORD) {
        await ensureAdminUserExists();
      }

      const { data, error } = await supabaseAdmin.auth.signInWithPassword({ email, password });
      if (error || !data?.session) {
        return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
      }
      // Guard: only allow the configured admin email to proceed as admin
      if (data.user?.email !== ADMIN_EMAIL) {
        return NextResponse.json({ error: 'Not an admin' }, { status: 403 });
      }
      return NextResponse.json({
        ok: true,
        token: data.session.access_token,
        refresh_token: data.session.refresh_token,
        expires_at: data.session.expires_at,
        user: { email: data.user.email, id: data.user.id },
      });
    }

    // All /admin/* routes below require a valid Supabase Auth JWT
    if (path.startsWith('/admin/')) {
      const adminUser = await verifyAdminToken(request);
      if (!adminUser) return unauthorized();
    }

    if (path === '/admin/stats' && method === 'GET') {
      const [{ count: total }, { count: inProgress }, { count: completed }] = await Promise.all([
        supabaseAdmin.from('participants').select('*', { count: 'exact', head: true }),
        supabaseAdmin.from('quiz_sessions').select('*', { count: 'exact', head: true }).eq('submitted', false),
        supabaseAdmin.from('quiz_sessions').select('*', { count: 'exact', head: true }).eq('submitted', true),
      ]);
      return NextResponse.json({
        total: total || 0,
        in_progress: inProgress || 0,
        completed: completed || 0,
      });
    }

    if (path === '/admin/participants' && method === 'GET') {
      const search = url.searchParams.get('search') || '';
      let query = supabaseAdmin
        .from('participants')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(2000);
      if (search.trim()) {
        const s = search.trim();
        query = query.or(
          `full_name.ilike.%${s}%,email.ilike.%${s}%,phone.ilike.%${s}%,department.ilike.%${s}%,college.ilike.%${s}%`
        );
      }
      const { data: participants, error } = await query;
      if (error) throw error;

      const ids = (participants || []).map((p) => p.id);
      let sessions = [];
      if (ids.length > 0) {
        const { data: sList } = await supabaseAdmin
          .from('quiz_sessions')
          .select('*')
          .in('participant_id', ids);
        sessions = sList || [];
      }
      const sMap = {};
      sessions.forEach((s) => (sMap[s.participant_id] = s));

      const rows = (participants || []).map((p) => {
        const s = sMap[p.id];
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
      const { data: sessions } = await supabaseAdmin
        .from('quiz_sessions')
        .select('*')
        .eq('submitted', true)
        .order('score', { ascending: false })
        .order('time_taken_seconds', { ascending: true })
        .limit(100);
      const pids = (sessions || []).map((s) => s.participant_id);
      let pList = [];
      if (pids.length > 0) {
        const { data } = await supabaseAdmin.from('participants').select('*').in('id', pids);
        pList = data || [];
      }
      const pMap = {};
      pList.forEach((p) => (pMap[p.id] = p));
      const rows = (sessions || []).map((s, i) => ({
        rank: i + 1,
        full_name: pMap[s.participant_id]?.full_name || '-',
        college: pMap[s.participant_id]?.college || '-',
        department: pMap[s.participant_id]?.department || '-',
        assigned_set: s.assigned_set,
        score: s.score,
        total_questions: s.total_questions,
        time_taken_seconds: s.time_taken_seconds,
      }));
      return NextResponse.json({ rows });
    }

    if (path === '/admin/export' && method === 'GET') {
      const { data: participants } = await supabaseAdmin.from('participants').select('*');
      const { data: sessions } = await supabaseAdmin.from('quiz_sessions').select('*');
      const sMap = {};
      (sessions || []).forEach((s) => (sMap[s.participant_id] = s));
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
      for (const p of participants || []) {
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

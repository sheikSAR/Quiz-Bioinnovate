'use client';

import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Brain, Clock, ShieldAlert, Trophy, LogIn, Sparkles, GraduationCap, LockKeyhole, ChevronLeft, ChevronRight, Download, Search, LogOut, CheckCircle2, TimerReset } from 'lucide-react';

const LS_PARTICIPANT = 'quiz_participant';
const LS_TOKEN = 'quiz_session_token';
const LS_ADMIN = 'quiz_admin_token';

function fmtTime(sec) {
  if (sec == null || sec < 0) sec = 0;
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// -------------------- LANDING --------------------
function Landing({ onStart, onAdmin }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-slate-950 dark:via-slate-900 dark:to-purple-950">
      <div className="container mx-auto px-4 py-14 md:py-20">
        <div className="flex items-center justify-between mb-12">
          <div className="flex items-center gap-3">
            <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-slate-900 to-indigo-900 grid place-items-center p-2 shadow-lg">
              <img src="/blude-logo.webp" alt="BLUDE" className="h-full w-full object-contain" />
            </div>
            <div>
              <div className="font-black text-xl leading-none tracking-tight">BLUDE</div>
              <div className="text-xs text-muted-foreground mt-1">College Event 2025</div>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onAdmin}>
            <LockKeyhole className="h-4 w-4 mr-2" /> Admin
          </Button>
        </div>

        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-5" variant="secondary">
            <Sparkles className="h-3 w-3 mr-1" /> One-Day Event · Live Competition
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
            The Ultimate MCQ Challenge
          </h1>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Test your knowledge across Science, Technology, Current Affairs, Research & Innovation.
            <span className="block mt-1 font-medium text-foreground">15 minutes · 30 questions · One chance to shine.</span>
          </p>
          <Button size="lg" className="h-14 px-10 text-base font-semibold" onClick={onStart}>
            <LogIn className="h-5 w-5 mr-2" /> Start Quiz
          </Button>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-16">
            {[
              { icon: Clock, title: '15 Min Timer', desc: 'Fair, timed & fast-paced' },
              { icon: GraduationCap, title: '3 Random Sets', desc: 'A, B or C, assigned randomly' },
              { icon: Trophy, title: 'Live Leaderboard', desc: 'Compete with your peers' },
            ].map((f, i) => (
              <Card key={i} className="border-2">
                <CardContent className="pt-6">
                  <f.icon className="h-8 w-8 mb-3 text-indigo-600 mx-auto" />
                  <div className="font-semibold">{f.title}</div>
                  <div className="text-sm text-muted-foreground mt-1">{f.desc}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// -------------------- REGISTER --------------------
function Register({ onSuccess, onBack }) {
  const [form, setForm] = useState({
    full_name: '', dob: '', email: '', phone: '',
    college: '', department: '', year: '',
  });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.full_name || !form.email || !form.phone) {
      toast.error('Full name, email and phone are required.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) {
        toast.error(data.error || 'Registration failed');
        if (data.already_submitted) {
          setTimeout(() => onBack(), 2500);
        }
        return;
      }
      localStorage.setItem(LS_PARTICIPANT, JSON.stringify(data.participant));
      localStorage.setItem(LS_TOKEN, data.session_token);
      if (data.returning) toast.success('Welcome back! Resuming your session…');
      else toast.success(`Registered! Assigned Set ${data.participant.assigned_set}`);
      onSuccess(data.participant, data.session_token);
    } catch (err) {
      toast.error('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-slate-950 dark:to-purple-950 py-10">
      <div className="container mx-auto px-4 max-w-2xl">
        <Button variant="ghost" size="sm" onClick={onBack} className="mb-4">
          <ChevronLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <Card className="border-2 shadow-xl">
          <CardHeader>
            <CardTitle className="text-2xl">Participant Registration</CardTitle>
            <CardDescription>Fill in your details to begin the quiz. Each participant can attempt only once.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label>Full Name *</Label>
                <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Priya Sharma" required />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Date of Birth</Label>
                  <Input type="date" value={form.dob} onChange={(e) => setForm({ ...form, dob: e.target.value })} />
                </div>
                <div>
                  <Label>Phone Number *</Label>
                  <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="9876543210" required />
                </div>
              </div>
              <div>
                <Label>Email *</Label>
                <Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@college.edu" required />
              </div>
              <div>
                <Label>College Name</Label>
                <Input value={form.college} onChange={(e) => setForm({ ...form, college: e.target.value })} placeholder="XYZ Institute of Technology" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Department</Label>
                  <Input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} placeholder="CSE" />
                </div>
                <div>
                  <Label>Year of Study</Label>
                  <Select value={form.year} onValueChange={(v) => setForm({ ...form, year: v })}>
                    <SelectTrigger><SelectValue placeholder="Select year" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1st">1st Year</SelectItem>
                      <SelectItem value="2nd">2nd Year</SelectItem>
                      <SelectItem value="3rd">3rd Year</SelectItem>
                      <SelectItem value="4th">4th Year</SelectItem>
                      <SelectItem value="PG">Post Graduate</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button type="submit" size="lg" className="w-full" disabled={loading}>
                {loading ? 'Please wait…' : 'Continue to Quiz'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// -------------------- QUIZ --------------------
function Quiz({ participant, sessionToken, onSubmitted }) {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [idx, setIdx] = useState(0);
  const [endsAt, setEndsAt] = useState(null);
  const [remaining, setRemaining] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [tabSwitches, setTabSwitches] = useState(0);
  const tabSwitchRef = useRef(0);
  const submittedRef = useRef(false);

  // Load session
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/quiz/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ participant_id: participant.id, session_token: sessionToken }),
        });
        const data = await res.json();
        if (!res.ok) {
          if (data.already_submitted) {
            toast.info('You have already completed this quiz.');
            onSubmitted();
            return;
          }
          toast.error(data.error || 'Failed to start');
          return;
        }
        setQuestions(data.questions);
        setAnswers(data.session.answers || {});
        setEndsAt(new Date(data.session.ends_at).getTime());
        setTabSwitches(data.session.tab_switches || 0);
        tabSwitchRef.current = data.session.tab_switches || 0;
      } catch (e) {
        toast.error('Failed to load quiz');
      } finally {
        setLoading(false);
      }
    })();
  }, [participant.id, sessionToken, onSubmitted]);

  // Timer
  useEffect(() => {
    if (!endsAt) return;
    const tick = () => {
      const rem = Math.max(0, Math.floor((endsAt - Date.now()) / 1000));
      setRemaining(rem);
      if (rem <= 0 && !submittedRef.current) {
        submittedRef.current = true;
        doSubmit(true);
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line
  }, [endsAt]);

  // Anti-cheat: right-click disable
  useEffect(() => {
    const prevent = (e) => e.preventDefault();
    document.addEventListener('contextmenu', prevent);
    return () => document.removeEventListener('contextmenu', prevent);
  }, []);

  // Anti-cheat: tab visibility
  useEffect(() => {
    const onVis = async () => {
      if (document.hidden && !submittedRef.current) {
        try {
          const res = await fetch('/api/quiz/tabswitch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ participant_id: participant.id }),
          });
          const data = await res.json();
          if (data.tab_switches != null) {
            tabSwitchRef.current = data.tab_switches;
            setTabSwitches(data.tab_switches);
            if (data.tab_switches > 2 && !submittedRef.current) {
              submittedRef.current = true;
              toast.error('Tab switched more than 2 times. Auto-submitting.');
              doSubmit(true);
            } else {
              toast.warning(`Warning: leaving the tab is not allowed (${data.tab_switches}/2)`);
            }
          }
        } catch {}
      }
    };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, [participant.id]);

  const saveAnswer = useCallback(async (qid, value) => {
    setAnswers((prev) => ({ ...prev, [qid]: value }));
    try {
      await fetch('/api/quiz/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          participant_id: participant.id,
          session_token: sessionToken,
          question_id: qid,
          answer: value,
        }),
      });
    } catch {}
  }, [participant.id, sessionToken]);

  const doSubmit = async (auto = false) => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await fetch('/api/quiz/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ participant_id: participant.id, auto }),
      });
      onSubmitted();
    } catch (e) {
      toast.error('Failed to submit');
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen grid place-items-center"><div className="text-muted-foreground">Loading your quiz…</div></div>;
  }
  if (!questions.length) {
    return <div className="min-h-screen grid place-items-center"><div className="text-muted-foreground">No questions available.</div></div>;
  }

  const q = questions[idx];
  const answeredCount = Object.keys(answers).length;
  const progressPct = ((idx + 1) / questions.length) * 100;
  const isLast = idx === questions.length - 1;
  const timerCritical = remaining <= 60;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 select-none" style={{ userSelect: 'none' }}>
      {/* Top bar */}
      <div className="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <Badge variant="outline">Set {participant.assigned_set}</Badge>
            <div className="text-sm text-muted-foreground truncate">{participant.full_name}</div>
          </div>
          <div className="flex items-center gap-3">
            {tabSwitches > 0 && (
              <Badge variant="destructive" className="gap-1">
                <ShieldAlert className="h-3 w-3" /> Tab warnings: {tabSwitches}/2
              </Badge>
            )}
            <div className={`flex items-center gap-2 font-mono font-bold text-lg px-3 py-1.5 rounded-md ${timerCritical ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300 animate-pulse' : 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300'}`}>
              <Clock className="h-4 w-4" /> {fmtTime(remaining)}
            </div>
          </div>
        </div>
        <Progress value={progressPct} className="h-1 rounded-none" />
      </div>

      <div className="container mx-auto px-4 py-6 max-w-3xl">
        <div className="flex items-center justify-between text-sm text-muted-foreground mb-3">
          <span>Question {idx + 1} of {questions.length}</span>
          <span>Answered: {answeredCount}/{questions.length}</span>
        </div>

        <Card className="border-2">
          <CardHeader>
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="secondary">{q.category}</Badge>
            </div>
            <CardTitle className="text-xl leading-snug">{q.question_text}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {['A', 'B', 'C', 'D'].map((letter) => {
                const selected = answers[q.id] === letter;
                return (
                  <button
                    key={letter}
                    type="button"
                    onClick={() => saveAnswer(q.id, letter)}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all flex items-start gap-3 hover:border-indigo-400 ${selected ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-950/50' : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900'}`}
                  >
                    <div className={`flex-shrink-0 h-8 w-8 rounded-full grid place-items-center font-bold text-sm ${selected ? 'bg-indigo-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}`}>
                      {letter}
                    </div>
                    <div className="pt-1 text-sm md:text-base">{q.options[letter]}</div>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-between mt-6 gap-3">
          <Button variant="outline" onClick={() => setIdx(Math.max(0, idx - 1))} disabled={idx === 0}>
            <ChevronLeft className="h-4 w-4 mr-1" /> Previous
          </Button>

          {isLast ? (
            <Button size="lg" onClick={() => doSubmit(false)} disabled={submitting} className="bg-green-600 hover:bg-green-700">
              {submitting ? 'Submitting…' : 'Submit Quiz'} <CheckCircle2 className="h-4 w-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={() => setIdx(Math.min(questions.length - 1, idx + 1))}>
              Next <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          )}
        </div>

        {/* Question palette */}
        <div className="mt-8">
          <div className="text-sm text-muted-foreground mb-2">Jump to question:</div>
          <div className="grid grid-cols-10 gap-1.5">
            {questions.map((qq, i) => {
              const a = answers[qq.id];
              return (
                <button
                  key={qq.id}
                  onClick={() => setIdx(i)}
                  className={`aspect-square rounded text-xs font-semibold border transition ${i === idx ? 'ring-2 ring-indigo-500' : ''} ${a ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600'}`}
                >{i + 1}</button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// -------------------- THANK YOU --------------------
function ThankYou() {
  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-br from-green-50 via-white to-emerald-50 dark:from-slate-950 dark:to-emerald-950 px-4">
      <Card className="max-w-md w-full text-center border-2 shadow-xl">
        <CardContent className="pt-10 pb-10">
          <div className="h-20 w-20 rounded-full bg-green-100 dark:bg-green-950 grid place-items-center mx-auto mb-6">
            <CheckCircle2 className="h-10 w-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold mb-3">Thank you for participating.</h1>
          <p className="text-muted-foreground">Your responses have been recorded. Results will be announced by the event organisers.</p>
        </CardContent>
      </Card>
    </div>
  );
}

// -------------------- ADMIN --------------------
function AdminLogin({ onSuccess, onBack }) {
  const [email, setEmail] = useState('');
  const [p, setP] = useState('');
  const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: p }),
      });
      const data = await res.json();
      if (!res.ok) { toast.error(data.error || 'Login failed'); return; }
      localStorage.setItem(LS_ADMIN, data.token);
      toast.success('Signed in as ' + (data.user?.email || 'admin'));
      onSuccess();
    } finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen grid place-items-center bg-slate-100 dark:bg-slate-950 px-4">
      <Card className="w-full max-w-md border-2 shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><LockKeyhole className="h-5 w-5" /> Admin Login</CardTitle>
          <CardDescription>Restricted access. Event organizers only.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div><Label>Email</Label><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@blude.local" required /></div>
            <div><Label>Password</Label><Input type="password" value={p} onChange={(e) => setP(e.target.value)} required /></div>
            <Button type="submit" className="w-full" disabled={loading}>{loading ? 'Signing in...' : 'Sign In'}</Button>
            <Button type="button" variant="ghost" className="w-full" onClick={onBack}>Back to home</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
  return (
    <div className="min-h-screen grid place-items-center bg-slate-100 dark:bg-slate-950 px-4">
      <Card className="w-full max-w-md border-2 shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><LockKeyhole className="h-5 w-5" /> Admin Login</CardTitle>
          <CardDescription>Restricted access. Event organizers only.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div><Label>Username</Label><Input value={u} onChange={(e) => setU(e.target.value)} required /></div>
            <div><Label>Password</Label><Input type="password" value={p} onChange={(e) => setP(e.target.value)} required /></div>
            <Button type="submit" className="w-full" disabled={loading}>{loading ? 'Signing in…' : 'Sign In'}</Button>
            <Button type="button" variant="ghost" className="w-full" onClick={onBack}>Back to home</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function AdminDashboard({ onLogout }) {
  const [stats, setStats] = useState({ total: 0, in_progress: 0, completed: 0 });
  const [rows, setRows] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState('participants');

  const loadAll = useCallback(async () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem(LS_ADMIN) : '';
    const authHeaders = { headers: { Authorization: 'Bearer ' + (token || '') } };
    const [s, p, lb] = await Promise.all([
      fetch('/api/admin/stats', authHeaders).then((r) => r.json()),
      fetch('/api/admin/participants?search=' + encodeURIComponent(search), authHeaders).then((r) => r.json()),
      fetch('/api/admin/leaderboard', authHeaders).then((r) => r.json()),
    ]);
    if (s?.error === 'Unauthorized' || p?.error === 'Unauthorized') {
      localStorage.removeItem(LS_ADMIN);
      toast.error('Session expired. Please sign in again.');
      window.location.reload();
      return;
    }
    setStats(s);
    setRows(p.rows || []);
    setLeaderboard(lb.rows || []);
  }, [search]);

  useEffect(() => {
    loadAll();
    const id = setInterval(loadAll, 8000);
    return () => clearInterval(id);
  }, [loadAll]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <div className="bg-white dark:bg-slate-900 border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-lg bg-gradient-to-br from-slate-900 to-indigo-900 grid place-items-center p-1.5 shadow">
              <img src="/blude-logo.webp" alt="BLUDE" className="h-full w-full object-contain" />
            </div>
            <div>
              <div className="font-bold">BLUDE Admin</div>
              <div className="text-xs text-muted-foreground">Live event dashboard</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={async () => {
              const token = localStorage.getItem(LS_ADMIN);
              const res = await fetch('/api/admin/export', { headers: { Authorization: 'Bearer ' + (token || '') } });
              if (!res.ok) { toast.error('Export failed. Please re-login.'); return; }
              const blob = await res.blob();
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url; a.download = 'quiz_results.csv';
              document.body.appendChild(a); a.click(); a.remove();
              URL.revokeObjectURL(url);
            }}>
              <Download className="h-4 w-4 mr-2" /> Export CSV
            </Button>
            <Button variant="ghost" onClick={onLogout}><LogOut className="h-4 w-4 mr-1" /> Logout</Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard title="Total Registrations" value={stats.total} icon={GraduationCap} color="indigo" />
          <StatCard title="Currently Taking Quiz" value={stats.in_progress} icon={TimerReset} color="amber" />
          <StatCard title="Completed" value={stats.completed} icon={CheckCircle2} color="green" />
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-4">
          <Button variant={tab === 'participants' ? 'default' : 'outline'} onClick={() => setTab('participants')}>Participants</Button>
          <Button variant={tab === 'leaderboard' ? 'default' : 'outline'} onClick={() => setTab('leaderboard')}><Trophy className="h-4 w-4 mr-1" /> Leaderboard</Button>
        </div>

        {tab === 'participants' && (
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center gap-3 justify-between">
                <CardTitle>All Participants</CardTitle>
                <div className="relative w-full md:w-80">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search name, email, phone, dept, college…" className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-muted-foreground border-b">
                    <tr>
                      <th className="py-2 pr-3">Name</th>
                      <th className="py-2 pr-3">Email</th>
                      <th className="py-2 pr-3">Phone</th>
                      <th className="py-2 pr-3">College</th>
                      <th className="py-2 pr-3">Dept</th>
                      <th className="py-2 pr-3">Set</th>
                      <th className="py-2 pr-3">Status</th>
                      <th className="py-2 pr-3">Score</th>
                      <th className="py-2 pr-3">Time</th>
                      <th className="py-2 pr-3">Tabs</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr key={r.id} className="border-b hover:bg-muted/40">
                        <td className="py-2 pr-3 font-medium">{r.full_name}</td>
                        <td className="py-2 pr-3">{r.email}</td>
                        <td className="py-2 pr-3">{r.phone}</td>
                        <td className="py-2 pr-3">{r.college}</td>
                        <td className="py-2 pr-3">{r.department}</td>
                        <td className="py-2 pr-3"><Badge variant="outline">{r.assigned_set}</Badge></td>
                        <td className="py-2 pr-3">
                          <Badge variant={r.status === 'completed' ? 'default' : r.status === 'in_progress' ? 'secondary' : 'outline'}>
                            {r.status}
                          </Badge>
                        </td>
                        <td className="py-2 pr-3">{r.score != null ? `${r.score}/${r.total_questions}` : '-'}</td>
                        <td className="py-2 pr-3">{r.time_taken_seconds != null ? fmtTime(r.time_taken_seconds) : '-'}</td>
                        <td className="py-2 pr-3">{r.tab_switches}{r.auto_submitted && <span className="text-red-500 ml-1">(auto)</span>}</td>
                      </tr>
                    ))}
                    {rows.length === 0 && (
                      <tr><td colSpan={10} className="py-8 text-center text-muted-foreground">No participants yet.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {tab === 'leaderboard' && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Trophy className="h-5 w-5 text-amber-500" /> Live Leaderboard</CardTitle>
              <CardDescription>Ranked by score, then by fastest time.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-muted-foreground border-b">
                    <tr>
                      <th className="py-2 pr-3">Rank</th>
                      <th className="py-2 pr-3">Name</th>
                      <th className="py-2 pr-3">College</th>
                      <th className="py-2 pr-3">Dept</th>
                      <th className="py-2 pr-3">Set</th>
                      <th className="py-2 pr-3">Score</th>
                      <th className="py-2 pr-3">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboard.map((r) => (
                      <tr key={r.rank} className="border-b hover:bg-muted/40">
                        <td className="py-2 pr-3 font-bold">
                          {r.rank === 1 && '🥇 '}
                          {r.rank === 2 && '🥈 '}
                          {r.rank === 3 && '🥉 '}
                          {r.rank}
                        </td>
                        <td className="py-2 pr-3 font-medium">{r.full_name}</td>
                        <td className="py-2 pr-3">{r.college}</td>
                        <td className="py-2 pr-3">{r.department}</td>
                        <td className="py-2 pr-3"><Badge variant="outline">{r.assigned_set}</Badge></td>
                        <td className="py-2 pr-3 font-semibold">{r.score}/{r.total_questions}</td>
                        <td className="py-2 pr-3">{fmtTime(r.time_taken_seconds)}</td>
                      </tr>
                    ))}
                    {leaderboard.length === 0 && (
                      <tr><td colSpan={7} className="py-8 text-center text-muted-foreground">No completed submissions yet.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color }) {
  const colors = {
    indigo: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400',
    amber: 'bg-amber-100 text-amber-600 dark:bg-amber-950 dark:text-amber-400',
    green: 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400',
  };
  return (
    <Card className="border-2">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-muted-foreground">{title}</div>
            <div className="text-3xl font-bold mt-1">{value}</div>
          </div>
          <div className={`h-12 w-12 rounded-lg grid place-items-center ${colors[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// -------------------- APP ROOT --------------------
function App() {
  const [view, setView] = useState('landing'); // landing | register | quiz | thankyou | admin-login | admin-dash
  const [participant, setParticipant] = useState(null);
  const [sessionToken, setSessionToken] = useState(null);

  useEffect(() => {
    // Restore from LS
    if (typeof window === 'undefined') return;
    // If URL is /admin
    if (window.location.pathname.startsWith('/admin')) {
      const t = localStorage.getItem(LS_ADMIN);
      setView(t ? 'admin-dash' : 'admin-login');
      return;
    }
    const p = localStorage.getItem(LS_PARTICIPANT);
    const t = localStorage.getItem(LS_TOKEN);
    if (p && t) {
      try {
        const parsed = JSON.parse(p);
        setParticipant(parsed);
        setSessionToken(t);
        setView('quiz');
      } catch {}
    }
  }, []);

  const goAdmin = () => {
    window.history.pushState({}, '', '/admin');
    const t = localStorage.getItem(LS_ADMIN);
    setView(t ? 'admin-dash' : 'admin-login');
  };

  const goHome = () => {
    window.history.pushState({}, '', '/');
    setView('landing');
  };

  if (view === 'landing') return <Landing onStart={() => setView('register')} onAdmin={goAdmin} />;
  if (view === 'register') return <Register onBack={() => setView('landing')} onSuccess={(p, tok) => { setParticipant(p); setSessionToken(tok); setView('quiz'); }} />;
  if (view === 'quiz' && participant) return <Quiz participant={participant} sessionToken={sessionToken} onSubmitted={() => {
    localStorage.removeItem(LS_PARTICIPANT);
    localStorage.removeItem(LS_TOKEN);
    setView('thankyou');
  }} />;
  if (view === 'thankyou') return <ThankYou />;
  if (view === 'admin-login') return <AdminLogin onBack={goHome} onSuccess={() => setView('admin-dash')} />;
  if (view === 'admin-dash') return <AdminDashboard onLogout={() => { localStorage.removeItem(LS_ADMIN); goHome(); }} />;
  return null;
}

export default App;

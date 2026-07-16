// Shared TypeScript types for BLUDE Quiz

export type SetLetter = 'A' | 'B' | 'C';
export type QuestionSet = SetLetter | 'BONUS_RESEARCH' | 'BONUS_STARTUP';
export type AnswerLetter = 'A' | 'B' | 'C' | 'D';

export interface Participant {
  id: string;
  full_name: string;
  dob: string;
  email: string;
  phone: string;
  college: string;
  department: string;
  year: string;
  assigned_set: SetLetter;
  created_at?: string;
}

export interface Question {
  id: string;
  set: QuestionSet;
  question_number: number;
  question_text: string;
  options: Record<AnswerLetter, string>;
  correct_answer?: AnswerLetter; // never sent to client
  category: string;
}

export interface QuizSession {
  id: string;
  participant_id: string;
  assigned_set: SetLetter;
  started_at: string;
  ends_at: string;
  answers: Record<string, AnswerLetter>;
  tab_switches: number;
  submitted: boolean;
  submitted_at?: string | null;
  score?: number | null;
  total_questions?: number | null;
  time_taken_seconds?: number | null;
  auto_submitted?: boolean;
  session_token?: string;
  last_seen?: string;
}

export interface AdminLoginResponse {
  ok: true;
  token: string;
  refresh_token: string;
  expires_at: number;
  user: { email: string; id: string };
}

export interface ParticipantRow {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  college: string;
  department: string;
  year: string;
  assigned_set: SetLetter;
  status: 'registered' | 'in_progress' | 'completed';
  score: number | null;
  total_questions: number | null;
  time_taken_seconds: number | null;
  tab_switches: number;
  auto_submitted: boolean;
  submitted_at: string | null;
  started_at: string | null;
}

export interface LeaderboardRow {
  rank: number;
  full_name: string;
  college: string;
  department: string;
  assigned_set: SetLetter;
  score: number;
  total_questions: number;
  time_taken_seconds: number;
}

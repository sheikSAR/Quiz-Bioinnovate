import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl: string = process.env.SUPABASE_URL || '';
const supabaseServiceKey: string = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
const supabaseAnonKey: string = process.env.SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing Supabase environment variables. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.');
}

// Server-side admin client (bypasses RLS)
export const supabaseAdmin: SupabaseClient = createClient(supabaseUrl, supabaseServiceKey, {
  auth: { persistSession: false, autoRefreshToken: false },
});

// Server-side anon client (used for calls that must obey RLS or be treated as "the user",
// e.g. resetPasswordForEmail which requires the anon role)
export const supabaseAnon: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey || supabaseServiceKey, {
  auth: { persistSession: false, autoRefreshToken: false },
});

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing Supabase environment variables. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.');
}

// Server-side only client with service role (bypasses RLS)
export const supabaseAdmin = createClient(supabaseUrl || '', supabaseServiceKey || '', {
  auth: { persistSession: false, autoRefreshToken: false },
});

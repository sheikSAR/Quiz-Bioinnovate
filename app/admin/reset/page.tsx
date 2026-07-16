'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { toast } from 'sonner';
import { LockKeyhole, CheckCircle2, KeyRound } from 'lucide-react';
import { getSupabaseBrowser } from '@/lib/supabase-browser';

type ResetStage = 'loading' | 'ready' | 'success' | 'invalid';

export default function ResetPasswordPage() {
  const [stage, setStage] = useState<ResetStage>('loading');
  const [password, setPassword] = useState<string>('');
  const [confirm, setConfirm] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // Supabase sends the recovery token in the URL hash: #access_token=...&refresh_token=...&type=recovery
    if (typeof window === 'undefined') return;
    const hash = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : window.location.hash;
    const params = new URLSearchParams(hash);
    const access_token = params.get('access_token');
    const refresh_token = params.get('refresh_token');
    const type = params.get('type');

    if (!access_token || !refresh_token || type !== 'recovery') {
      setStage('invalid');
      return;
    }

    (async () => {
      try {
        const supabase = getSupabaseBrowser();
        const { error } = await supabase.auth.setSession({ access_token, refresh_token });
        if (error) {
          setStage('invalid');
          toast.error('Invalid or expired reset link.');
        } else {
          setStage('ready');
        }
      } catch (e) {
        setStage('invalid');
      }
    })();
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirm) {
      toast.error('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      const supabase = getSupabaseBrowser();
      const { error } = await supabase.auth.updateUser({ password });
      if (error) {
        toast.error(error.message || 'Failed to update password.');
        return;
      }
      setStage('success');
      toast.success('Password updated. Please sign in with your new password.');
      // Clear hash to prevent re-triggering
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, '', '/admin/reset');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-slate-100 dark:bg-slate-950 px-4">
      <Card className="w-full max-w-md border-2 shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="h-5 w-5" /> Reset Password
          </CardTitle>
          <CardDescription>Set a new admin password.</CardDescription>
        </CardHeader>
        <CardContent>
          {stage === 'loading' && (
            <div className="text-sm text-muted-foreground">Verifying reset link...</div>
          )}

          {stage === 'invalid' && (
            <div className="space-y-4">
              <div className="text-sm text-red-600 dark:text-red-400">
                The reset link is invalid or has expired. Please request a new one from the admin login page.
              </div>
              <Button className="w-full" onClick={() => (window.location.href = '/admin')}>
                Back to Admin Login
              </Button>
            </div>
          )}

          {stage === 'ready' && (
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label>New Password</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  required
                />
              </div>
              <div>
                <Label>Confirm New Password</Label>
                <Input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Updating...' : 'Update Password'}
              </Button>
            </form>
          )}

          {stage === 'success' && (
            <div className="space-y-4 text-center">
              <CheckCircle2 className="h-10 w-10 mx-auto text-green-600" />
              <div className="text-sm text-muted-foreground">
                Your password has been updated successfully.
              </div>
              <Button className="w-full" onClick={() => (window.location.href = '/admin')}>
                <LockKeyhole className="h-4 w-4 mr-2" /> Go to Admin Login
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

import './globals.css';
import { Toaster } from '@/components/ui/sonner';

export const metadata = {
  title: 'College Event Quiz 2025',
  description: 'MCQ Quiz Competition — Test your knowledge across Science, Tech, Innovation & Current Affairs.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
        <Toaster position="top-center" richColors />
      </body>
    </html>
  );
}

import { useState } from 'react';
import { WizardData } from '@/types';
import { generateJobDescription } from '@/lib/api';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

interface UrlInputStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
}

export function UrlInputStep({ data, onUpdate, onNext }: UrlInputStepProps) {
  const router = useRouter();
  const [url, setUrl] = useState(data.url);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateUrl = (url: string) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return; // Prevent rapid double-clicks
  
    if (!url.trim()) {
      setError('Please enter a job posting URL');
      return;
    }
  
    if (!validateUrl(url)) {
      setError('Please enter a valid URL');
      return;
    }
  
    setIsSubmitting(true);
    setError('');

    try {
      const result = await generateJobDescription({ job_url: url.trim() });
      
      if (result.warning) {
        toast.warning('Application Already Exists', {
          description: result.warning,
          duration: 15000,
          action: {
            label: 'View Application →',
            onClick: () => router.push(`/applications/${result.id}`),
          },
        });
        setIsSubmitting(false);
        return; // STAY in the first step as per user request
      }

      // Success - update data and move to next step
      onUpdate({ 
        url: url.trim(),
        extractedData: {
          company: result.company,
          title: result.title,
          jd_text: result.jd_text,
        },
        application: result,
      });
      onNext();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to extract job details';
      setError(msg);
      toast.error('Extraction Failed', {
        description: msg,
      });
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-xl shadow-black/5 p-8 md:p-12 space-y-8">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 italic">
            Job Posting URL
          </h2>
          <p className="text-zinc-500 dark:text-zinc-400">
            Paste the URL of the job posting you want to apply for
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="url" className="block text-sm font-semibold text-zinc-900 dark:text-zinc-100 px-1">
              Job URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://linkedin.com/jobs/..."
              className="w-full px-4 py-4 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all text-lg"
              required
            />
            {error && (
              <p className="mt-1 text-sm text-red-500 font-medium px-1">{error}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 py-4 px-6 rounded-2xl font-bold text-lg hover:scale-[1.02] active:scale-[0.98] transition-all shadow-xl disabled:opacity-50 disabled:hover:scale-100"
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin text-xl">⏳</span> Processing...
              </span>
            ) : (
              'Extract Job Details ✨'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

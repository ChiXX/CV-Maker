import { useState } from 'react';
import { WizardData } from '@/types';
import { generateJobDescription, createApplication } from '@/lib/api';
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
  const [isManual, setIsManual] = useState(false);
  const [manualData, setManualData] = useState({
    company: '',
    title: '',
    jd_text: '',
  });
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateUrl = (url: string) => {
    try {
      if (!url.startsWith('http')) return false;
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    if (!url.trim()) {
      setError('Please enter a job posting URL');
      return;
    }

    if (!validateUrl(url.trim())) {
      setError('Please enter a valid URL (including http/https)');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const result = await generateJobDescription({ job_url: url.trim() });
      
      if (result.warning) {
        if (result.id) {
          // It's a duplicate
          toast.warning('Application Already Exists', {
            description: result.warning,
            duration: 15000,
            action: {
              label: 'View Application →',
              onClick: () => router.push(`/applications/${result.id}`),
            },
          });
          setIsSubmitting(false);
          return;
        } else {
          // It's an extraction failure
          toast.error('Extraction Failed', {
            description: result.warning,
          });
          setIsManual(true);
          setIsSubmitting(false);
          return;
        }
      }

      // Success - update data and move to next step
      onUpdate({ 
        url: url.trim(),
        extractedData: {
          company: result.company,
          title: result.title,
          jd_text: result.jd_text,
        },
        application: result as any, // Cast because id is optional in response but required in JobApplication
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

  const handleManualSubmit = async (e: React.FormEvent, skipGeneration = false) => {
    e.preventDefault();
    if (isSubmitting) return;

    if (!manualData.company || !manualData.title || !manualData.jd_text) {
      setError('Please fill in all fields');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const result = await createApplication({
        job_url: url.trim() || 'https://manual-entry.com/' + Date.now(),
        ...manualData
      });

      if (skipGeneration) {
        toast.success('Application Saved');
        router.push('/applications');
        return;
      }

      onUpdate({
        url: result.job_url,
        extractedData: {
          company: result.company,
          title: result.title,
          jd_text: result.jd_text,
        },
        application: result,
      });
      onNext();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to create application';
      setError(msg);
      toast.error('Creation Failed', {
        description: msg,
      });
      setIsSubmitting(false);
    }
  };

  if (isManual) {
    return (
      <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-xl p-8 md:p-12 space-y-8">
          <div className="flex justify-between items-center">
            <div className="space-y-2">
              <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 italic">Manual Entry</h2>
              <p className="text-zinc-500 dark:text-zinc-400">Enter the job details manually to proceed.</p>
            </div>
            <button 
              onClick={() => setIsManual(false)}
              className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-white underline underline-offset-4"
            >
              Back to URL
            </button>
          </div>

          <form onSubmit={(e) => handleManualSubmit(e)} className="grid gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold px-1">Job URL</label>
              <input
                type="url"
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://..."
                className="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all"
              />
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold px-1">Company</label>
                <input
                  type="text"
                  value={manualData.company}
                  onChange={e => setManualData(prev => ({ ...prev, company: e.target.value }))}
                  placeholder="e.g. Google"
                  className="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold px-1">Job Title</label>
                <input
                  type="text"
                  value={manualData.title}
                  onChange={e => setManualData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="e.g. Software Engineer"
                  className="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold px-1">Job Description</label>
              <textarea
                value={manualData.jd_text}
                onChange={e => setManualData(prev => ({ ...prev, jd_text: e.target.value }))}
                placeholder="Paste the full job description here..."
                rows={8}
                className="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white transition-all resize-none"
                required
              />
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 py-4 rounded-2xl font-bold text-lg hover:scale-[1.01] transition-all shadow-xl disabled:opacity-50"
              >
                Save & Continue to Selection ✨
              </button>
              <button
                type="button"
                onClick={(e) => handleManualSubmit(e, true)}
                disabled={isSubmitting}
                className="sm:w-1/3 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white py-4 rounded-2xl font-bold border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-all disabled:opacity-50"
              >
                Just Save
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

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

          <div className="space-y-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 py-4 px-6 rounded-2xl font-bold text-lg hover:scale-[1.02] active:scale-[0.98] transition-all shadow-xl disabled:opacity-50"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin text-xl">⏳</span> Processing...
                </span>
              ) : (
                'Extract Job Details ✨'
              )}
            </button>

            <button
              type="button"
              onClick={() => setIsManual(true)}
              className="w-full py-4 text-zinc-500 hover:text-zinc-900 dark:hover:text-white font-semibold transition-all"
            >
              Or Create Manually ✍️
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { WizardData } from '@/types';

interface UrlInputStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
}

export function UrlInputStep({ data, onUpdate, onNext }: UrlInputStepProps) {
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

  const handleSubmit = (e: React.FormEvent) => {
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
    onUpdate({ url: url.trim() });
    onNext();
  };

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Job Posting URL
          </h2>
          <p className="text-gray-600">
            Paste the URL of the job posting you want to apply for
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
              Job URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/job-posting"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            {error && (
              <p className="mt-1 text-sm text-red-600">{error}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isSubmitting ? 'Processing...' : 'Extract Job Details'}
          </button>
        </form>
      </div>
    </div>
  );
}

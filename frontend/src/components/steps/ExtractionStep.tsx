import { useMutation } from '@tanstack/react-query';
import { WizardData } from '@/types';
import { regenerateJobDescription } from '@/lib/api';
import { JobExtractionResponse } from '@/types';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

interface ExtractionStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export function ExtractionStep({ data, onUpdate, onNext, onPrev }: ExtractionStepProps) {
  const router = useRouter();
  // 1. Regenerate Mutation
  // Used for manual actions that change data on the server
  const { mutate: handleRegenerate, isPending: isRegenerating } = useMutation({
    mutationFn: () => regenerateJobDescription(data.application!.id),
    onSuccess: (result: JobExtractionResponse) => {
      onUpdate({
        extractedData: {
          company: result.company,
          title: result.title,
          jd_text: result.jd_text,
        },
        application: {
          ...data.application!,
          company: result.company,
          title: result.title,
          jd_text: result.jd_text,
        },
        cvGeneration: undefined,
        clGeneration: undefined,
      });
    },
  });

  const isLoading = isRegenerating;

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-12 text-center space-y-4 shadow-xl">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-zinc-900 dark:border-white mx-auto"></div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 italic">Regenerating Details...</h2>
            <p className="text-zinc-500 dark:text-zinc-400">We're re-processing the job posting for better accuracy.</p>
          </div>
        </div>
      </div>
    );
  }

  if (!data.extractedData) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-xl shadow-black/5 p-8 md:p-12 space-y-10">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 italic">Job Details Extracted</h2>
          <p className="text-zinc-500 dark:text-zinc-400">Review the extracted information before proceeding to generate documents.</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-500 px-1">Company</h3>
            <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100 bg-zinc-50 dark:bg-zinc-950 p-4 rounded-2xl border border-zinc-100 dark:border-zinc-800">{data.extractedData.company}</p>
          </div>
          <div className="space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-500 px-1">Job Title</h3>
            <p className="text-xl font-bold text-zinc-900 dark:text-zinc-100 bg-zinc-50 dark:bg-zinc-950 p-4 rounded-2xl border border-zinc-100 dark:border-zinc-800">{data.extractedData.title}</p>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-500 px-1">Job Description</h3>
          <div className="bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 p-8 rounded-3xl max-h-[500px] overflow-y-auto shadow-inner">
            <div className="prose prose-zinc dark:prose-invert max-w-none text-zinc-800 dark:text-zinc-300">
              {data.extractedData.jd_text.split('\n').map((paragraph, index) => {
                const trimmed = paragraph.trim();
                if (!trimmed) return null;
                const isBullet = trimmed.match(/^[-•*]\s/);
                const isNumbered = trimmed.match(/^\d+\.\s/);

                if (isBullet) {
                  return (
                    <div key={index} className="flex items-start mb-3">
                      <span className="text-zinc-900 dark:text-white mr-3 mt-2 text-xs">●</span>
                      <span className="flex-1 leading-relaxed">{trimmed.substring(2)}</span>
                    </div>
                  );
                } else if (isNumbered) {
                  const match = trimmed.match(/^\d+/);
                  return (
                    <div key={index} className="flex items-start mb-3">
                      <span className="text-zinc-900 dark:text-white mr-3 mt-1.5 text-sm font-black min-w-[1.5rem]">
                        {match ? match[0] : ''}.
                      </span>
                      <span className="flex-1 leading-relaxed">{trimmed.replace(/^\d+\.\s/, '')}</span>
                    </div>
                  );
                }
                return <p key={index} className="mb-6 leading-relaxed last:mb-0">{trimmed}</p>;
              }).filter(Boolean)}
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-4 border-t border-zinc-100 dark:border-zinc-800">
          <button 
            onClick={onPrev} 
            className="w-full sm:w-auto px-8 py-3 bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-2xl font-bold hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all"
          >
            ← Back
          </button>
          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <button
              onClick={() => handleRegenerate()}
              disabled={isLoading}
              className="px-8 py-3 bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800 rounded-2xl font-bold hover:text-zinc-900 dark:hover:text-white hover:border-zinc-900 dark:hover:border-white transition-all disabled:opacity-50"
            >
              🔄 Regenerate
            </button>
            <button
              type="button"
              onClick={() => {
                toast.success('Application Saved');
                router.push('/applications');
              }}
              className="px-8 py-3 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white border border-zinc-200 dark:border-zinc-800 rounded-2xl font-bold hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-all"
            >
              Just Save & Finish
            </button>
            <button 
              onClick={onNext} 
              className="px-10 py-3 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-2xl font-bold hover:scale-105 transition-all shadow-xl"
            >
              Continue to CV ✨
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
import { useMutation } from '@tanstack/react-query';
import { WizardData } from '@/types';
import { regenerateJobDescription } from '@/lib/api';
import { JobExtractionResponse } from '@/types';

interface ExtractionStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export function ExtractionStep({ data, onUpdate, onNext, onPrev }: ExtractionStepProps) {
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
        application: result,
        cvGeneration: undefined,
        clGeneration: undefined,
      });
    },
  });

  const isLoading = isRegenerating;

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Regenerating Details...
            </h2>
            <p className="text-gray-600">
              We're processing the job posting details
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!data.extractedData) return null;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Job Details Extracted</h2>
          <p className="text-gray-600">Review the extracted information before proceeding</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Company</h3>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-md">{data.extractedData.company}</p>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Job Title</h3>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-md">{data.extractedData.title}</p>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Job Description</h3>
          <div className="bg-white border border-gray-200 p-6 rounded-lg max-h-96 overflow-y-auto shadow-sm">
            <div className="prose prose-sm max-w-none text-gray-800">
              {data.extractedData.jd_text.split('\n').map((paragraph, index) => {
                const trimmed = paragraph.trim();
                if (!trimmed) return null;
                const isBullet = trimmed.match(/^[-•*]\s/);
                const isNumbered = trimmed.match(/^\d+\.\s/);

                if (isBullet) {
                  return (
                    <div key={index} className="flex items-start mb-2">
                      <span className="text-blue-500 mr-2 mt-1.5 text-xs">•</span>
                      <span className="flex-1 leading-relaxed">{trimmed.substring(2)}</span>
                    </div>
                  );
                } else if (isNumbered) {
                  const match = trimmed.match(/^\d+/);
                  return (
                    <div key={index} className="flex items-start mb-2">
                      <span className="text-blue-600 mr-2 mt-1.5 text-xs font-medium min-w-[1.5rem]">
                        {match ? match[0] : ''}.
                      </span>
                      <span className="flex-1 leading-relaxed">{trimmed.replace(/^\d+\.\s/, '')}</span>
                    </div>
                  );
                }
                return <p key={index} className="mb-4 leading-relaxed last:mb-0">{trimmed}</p>;
              }).filter(Boolean)}
            </div>
          </div>
        </div>

        <div className="flex justify-between">
          <button onClick={onPrev} className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
            Back
          </button>
          <div className="flex space-x-4">
            <button
              onClick={() => handleRegenerate()}
              className="px-4 py-2 border border-orange-300 text-orange-700 rounded-md hover:bg-orange-50 disabled:opacity-50"
              disabled={isLoading}
            >
              Regenerate
            </button>
            <button onClick={onNext} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
              Continue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
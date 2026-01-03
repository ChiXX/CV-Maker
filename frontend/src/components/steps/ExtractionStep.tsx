'use client';

import { useState, useEffect } from 'react';
import { WizardData } from '@/types';
import { extractJobDetails as apiExtractJobDetails, regenerateJobDetails } from '@/lib/api';

interface ExtractionStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export function ExtractionStep({ data, onUpdate, onNext, onPrev }: ExtractionStepProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (data.url && !data.extractedData && !isLoading) {
      handleExtractJobDetails();
    }
  }, [data.url]);

  const handleExtractJobDetails = async () => {
    setIsLoading(true);
    setError('');

    try {
      const extractionResult = await apiExtractJobDetails({ job_url: data.url });

      onUpdate({
        extractedData: {
          company: extractionResult.company,
          title: extractionResult.title,
          jd_text: extractionResult.jd_text,
        },
        application: extractionResult,
      });

      setIsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extract job details');
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!data.application?.id) return;

    setIsLoading(true);
    setError('');

    try {
      const extractionResult = await regenerateJobDetails(data.application.id);

      onUpdate({
        extractedData: {
          company: extractionResult.company,
          title: extractionResult.title,
          jd_text: extractionResult.jd_text,
        },
        application: extractionResult,
        // Clear CV and CL generation data since JD changed
        cvGeneration: undefined,
        clGeneration: undefined,
      });

      setIsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate job details');
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    handleExtractJobDetails();
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Extracting Job Details
            </h2>
            <p className="text-gray-600">
              We're fetching and analyzing the job posting from {data.url}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <div className="text-red-600 mb-4">
              <svg className="w-12 h-12 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Extraction Failed
            </h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <div className="flex space-x-4 justify-center">
              <button
                onClick={onPrev}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Go Back
              </button>
              <button
                onClick={handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!data.extractedData) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Job Details Extracted
          </h2>
          <p className="text-gray-600">
            Review the extracted information before proceeding
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Company</h3>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-md">
              {data.extractedData.company}
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Job Title</h3>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-md">
              {data.extractedData.title}
            </p>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Job Description</h3>
          <div className="bg-gray-50 p-4 rounded-md max-h-96 overflow-y-auto">
            <pre className="whitespace-pre-wrap text-gray-700 text-sm">
              {data.extractedData.jd_text}
            </pre>
          </div>
        </div>

        <div className="flex justify-between">
          <button
            onClick={onPrev}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
          <div className="flex space-x-4">
            <button
              onClick={handleRegenerate}
              className="px-4 py-2 border border-orange-300 text-orange-700 rounded-md hover:bg-orange-50"
              disabled={isLoading}
            >
              Regenerate
            </button>
            <button
              onClick={onNext}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Continue
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

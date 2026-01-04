'use client';

import { useState, useEffect } from 'react';
import { WizardData } from '@/types';
import * as api from '@/lib/api';
import { generateCv, regenerateCv, compilePdf as compilePdfServer } from '@/lib/api';

interface CvGenerationStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
  onPrev: () => void;
}

type GenerationStep = 'planning' | 'executing' | 'rendering' | 'complete';

interface ProcessStep {
  id: GenerationStep;
  label: string;
  status: 'pending' | 'loading' | 'completed' | 'error';
}

export function CvGenerationStep({ data, onUpdate, onNext, onPrev }: CvGenerationStepProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cvPdfUrl, setCvPdfUrl] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<GenerationStep>('planning');

  // processSteps will be derived from backend plan when available
  const dynamicPlanSteps = (data.cvGeneration as any)?.planSteps;
  const processSteps: ProcessStep[] = dynamicPlanSteps
    ? dynamicPlanSteps.map((label: string, idx: number) => ({
        id: (['planning', 'executing', 'rendering', 'complete'][Math.min(idx, 3)] as GenerationStep),
        label,
        status: 'pending' as const,
      }))
    : [
        { id: 'planning', label: 'Generating plans', status: 'pending' },
        { id: 'executing', label: 'Executing plan steps', status: 'pending' },
        { id: 'rendering', label: 'Rendering PDF', status: 'pending' },
        { id: 'complete', label: 'CV generation complete', status: 'pending' },
      ];

  useEffect(() => {
    if (data.application?.cv_latex && !data.cvGeneration) {
      // CV is already generated, show completed state
      setCurrentStep('complete');
      renderPdf();
    } else if (!data.cvGeneration && data.application && !data.application.cv_latex) {
      // Start CV generation process
      generateCV();
    }
  }, [data.application, data.cvGeneration]);

  const generateCV = async () => {
    if (!data.application?.id) return;

    setIsLoading(true);
    setError(null);
    setCurrentStep('planning');

    try {
      // Step 1: Planning
      setCurrentStep('planning');
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate planning time

      // Step 2: Executing plan (this is where cv_generator.py:111 runs)
      setCurrentStep('executing');
      const result = await generateCv({ application_id: data.application.id });
      // result contains plan_steps; start polling backend progress
      onUpdate({
        cvGeneration: {
          isLoading: true,
          result: undefined,
          planSteps: result.plan_steps,
          currentStep: 0,
        } as any,
      });

      // start polling
      const pollInterval = 1000;
      let pollHandle: number | undefined;
      const startPolling = () => {
        pollHandle = window.setInterval(async () => {
          try {
            const status = await (api as any).getGenerationProgress(data.application!.id);
            const current = status.current || 0;
            onUpdate({
              cvGeneration: {
                isLoading: status.state === 'running',
                result: undefined,
                planSteps: status.plan || result.plan_steps,
                currentStep: current,
              } as any,
            });
            if (status.state === 'completed') {
              // fetch updated application
              const app = await (api as any).getApplication(data.application!.id);
              onUpdate({
                cvGeneration: {
                  isLoading: false,
                  result: app.cv_latex,
                  planSteps: status.plan,
                  currentStep: status.current,
                } as any,
                application: app,
              });
              if (pollHandle) window.clearInterval(pollHandle);
            } else if (status.state === 'failed') {
              onUpdate({
                cvGeneration: {
                  isLoading: false,
                  error: status.error || 'Generation failed',
                  planSteps: status.plan,
                  currentStep: status.current,
                } as any,
              });
              if (pollHandle) window.clearInterval(pollHandle);
            }
          } catch (e) {
            // ignore transient errors
          }
        }, pollInterval);
      };
      startPolling();

      // Step 3: Rendering PDF
      setCurrentStep('rendering');
      await renderPdf();

      // Complete
      setCurrentStep('complete');

      onUpdate({
        cvGeneration: {
          isLoading: false,
          result: result.cv_latex,
          planSteps: result.plan_steps,
        } as any,
        application: {
          ...data.application,
          cv_latex: result.cv_latex,
        },
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate CV';
      setError(errorMessage);
      setCurrentStep('planning'); // Reset on error

      onUpdate({
        cvGeneration: {
          isLoading: false,
          error: errorMessage,
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!data.application?.id) return;

    setIsLoading(true);
    setError(null);
    setCurrentStep('planning');
    onUpdate({ cvGeneration: undefined });

    // Clear previous PDF
    if (cvPdfUrl) {
      URL.revokeObjectURL(cvPdfUrl);
      setCvPdfUrl(null);
    }

    try {
      // Step 1: Planning
      setCurrentStep('planning');
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Step 2: Executing plan
      setCurrentStep('executing');
      const result = await regenerateCv(data.application.id);
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Step 3: Rendering PDF
      setCurrentStep('rendering');
      await renderPdf();

      // Complete
      setCurrentStep('complete');

      onUpdate({
        cvGeneration: {
          isLoading: false,
          result: result.cv_latex,
        },
        application: {
          ...data.application,
          cv_latex: result.cv_latex,
        },
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to regenerate CV';
      setError(errorMessage);
      setCurrentStep('planning');

      onUpdate({
        cvGeneration: {
          isLoading: false,
          error: errorMessage,
        },
      });
    } finally {
      setIsLoading(false);
    }
  };

  const renderPdf = async () => {
    if (!data.application?.id) return;
    try {
      const blob = await compilePdfServer(data.application.id, 'cv');
      const url = URL.createObjectURL(blob);
      if (cvPdfUrl) URL.revokeObjectURL(cvPdfUrl);
      setCvPdfUrl(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to render PDF';
      setError(msg);
      throw err; // Re-throw to be handled by caller
    }
  };

  const handleDownload = () => {
    if (cvPdfUrl) {
      const link = document.createElement('a');
      link.href = cvPdfUrl;
      link.download = `CV_${data.application?.company}_${data.application?.title}.pdf`;
      link.click();
    }
  };

  const getStepStatus = (stepId: GenerationStep) => {
    const stepOrder: GenerationStep[] = ['planning', 'executing', 'rendering', 'complete'];
    const currentIndex = stepOrder.indexOf(currentStep);
    const stepIndex = stepOrder.indexOf(stepId);

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex && isLoading) return 'loading';
    if (stepIndex === currentIndex && !isLoading && !error) return 'completed';
    if (error && stepId === 'planning') return 'error';
    return 'pending';
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            CV Generation
          </h2>
          <p className="text-gray-600">
            Creating a customized CV for the {data.extractedData?.title} position
          </p>
        </div>

        {/* Generation Process Steps */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Generation Process</h3>
          <div className="space-y-3">
            {processSteps.slice(0, -1).map((step) => {
              const status = getStepStatus(step.id);
              return (
                <div key={step.id} className="flex items-center space-x-3">
                  <div className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center ${
                    status === 'completed' ? 'bg-green-500' :
                    status === 'loading' ? 'bg-blue-500' :
                    status === 'error' ? 'bg-red-500' : 'bg-gray-300'
                  }`}>
                    {status === 'loading' && (
                      <div className="animate-spin rounded-full h-3 w-3 border border-white border-t-transparent"></div>
                    )}
                    {status === 'completed' && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                    {status === 'error' && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <span className={`text-sm ${
                    status === 'completed' ? 'text-green-700' :
                    status === 'loading' ? 'text-blue-700' :
                    status === 'error' ? 'text-red-700' : 'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Generation Failed</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PDF Display */}
        {cvPdfUrl && currentStep === 'complete' && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Generated CV</h3>
            <div className="bg-white p-2 rounded-md border">
              <object data={cvPdfUrl} type="application/pdf" width="100%" height="600">
                <p>Your browser does not support embedded PDFs. <a href={cvPdfUrl}>Download PDF</a>.</p>
              </object>
            </div>
            <div className="mt-4 flex justify-center space-x-4">
              <button
                onClick={handleDownload}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586 14.293 5.293a1 1 0 111.414 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span>Download</span>
              </button>
              <button
                onClick={handleRegenerate}
                className="flex items-center space-x-2 px-4 py-2 border border-orange-300 text-orange-700 rounded-md hover:bg-orange-50"
                disabled={isLoading}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                </svg>
                <span>Redo</span>
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between">
          <button
            onClick={onPrev}
            className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
          {currentStep === 'complete' && (
            <button
              onClick={onNext}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

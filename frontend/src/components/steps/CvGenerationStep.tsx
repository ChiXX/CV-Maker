'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { WizardData } from '@/types';
import { generateCv, regenerateCv, compilePdf as compilePdfServer, getApplication } from '@/lib/api';

interface CvGenerationStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
  onPrev: () => void;
}

type GenerationStep = 'planning' | 'executing' | 'editing' | 'rendering' | 'complete';

interface ProcessStep {
  id: GenerationStep;
  label: string;
  status: 'pending' | 'loading' | 'completed' | 'error';
}

export function CvGenerationStep({ data, onUpdate, onNext, onPrev }: CvGenerationStepProps) {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState<GenerationStep>(
    data.application?.cv_latex ? 'complete' : 'planning'
  );
  const [latexContent, setLatexContent] = useState<string>(data.application?.cv_latex || '');
  const hasSyncedRef = useRef(false);

  // 0. Fetch application data to ensure we have cv_latex if it exists
  const { data: applicationData } = useQuery({
    queryKey: ['application', data.application?.id],
    queryFn: () => getApplication(data.application!.id),
    enabled: !!data.application?.id,
    staleTime: Infinity,
  });

  // Sync application data to wizard state
  useEffect(() => {
    if (applicationData && applicationData.cv_latex !== data.application?.cv_latex) {
      onUpdate({
        application: applicationData,
      });
    }
  }, [applicationData]);

  // 1. Initial CV Generation Query
  const { 
    data: generationResult,
    isLoading: isGenerating,
    error: genError 
  } = useQuery({
    queryKey: ['generate-cv', data.application?.id],
    queryFn: async () => {
      setCurrentStep('executing');
      return await generateCv({ application_id: data.application!.id });
    },
    enabled: !!data.application?.id && !data.application?.cv_latex,
    staleTime: Infinity,
  });

  // 2. Manual Redo Mutation
  const regenerateCvMutation = useMutation({
    mutationFn: async (applicationId: number) => {
      setCurrentStep('planning');
      onUpdate({ cvGeneration: undefined });
      await new Promise(resolve => setTimeout(resolve, 500));
      setCurrentStep('executing');
      return await regenerateCv(applicationId);
    },
    onSuccess: (result) => {
      onUpdate({
        cvGeneration: {
          result: result?.raw_content,
          planSteps: result?.plan_steps || [],
          currentStep: result?.plan_steps?.length || 0,
        } as any,
      });
      setLatexContent(result?.raw_content || '');
      setCurrentStep('editing');
    },
  });

  // 3. PDF Compilation Mutation (handles raw content rendering)
  const compilePdfMutation = useMutation({
    mutationFn: async (rawContent?: string) => {
      if (!data.application?.id) return;
      return await compilePdfServer(data.application.id, 'cv', rawContent);
    },
    onSuccess: (blob) => {
      queryClient.setQueryData(['cv-pdf', data.application?.id, data.application?.cv_latex], blob);
      setCurrentStep('complete');
    },
  });

  // 4. PDF Compilation Query (for existing view)
  const {
    data: cvPdfBlob,
    isLoading: isPdfLoading,
    error: pdfError
  } = useQuery({
    queryKey: ['cv-pdf', data.application?.id, data.application?.cv_latex],
    queryFn: () => compilePdfServer(data.application!.id, 'cv'),
    enabled: !!data.application?.id && !!data.application?.cv_latex,
    staleTime: Infinity,
  });

  // Sync auto-generation result to parent wizard state
  useEffect(() => {
    if (generationResult && generationResult.raw_content && !data.application?.cv_latex && !hasSyncedRef.current) {
      hasSyncedRef.current = true;
      onUpdate({
        cvGeneration: {
          result: generationResult.raw_content,
          planSteps: generationResult.plan_steps || [],
          isLoading: false 
        } as any,
      });
      setLatexContent(generationResult.raw_content);
      setCurrentStep('editing');
    }
  }, [generationResult, data.application?.cv_latex]);

  // If cv_latex exists, ensure we're in complete state
  useEffect(() => {
    if (data.application?.cv_latex && currentStep !== 'complete') {
      setCurrentStep('complete');
    }
  }, [data.application?.cv_latex, currentStep]);

  // Update step to 'complete' once PDF is ready (for existing view)
  useEffect(() => {
    if (cvPdfBlob && currentStep === 'rendering') {
      setCurrentStep('complete');
    }
  }, [cvPdfBlob, currentStep]);

  const activePdfBlob = cvPdfBlob || compilePdfMutation.data;

  const handleRegenerate = () => {
    if (!data.application?.id || isGenerating || regenerateCvMutation.isPending) return;
    regenerateCvMutation.mutate(data.application.id);
  };

  const handleDownload = () => {
    if (activePdfBlob) {
      const url = URL.createObjectURL(activePdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `CV_${data.extractedData?.company || 'My'}_${data.extractedData?.title || 'CV'}.pdf`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 100);
    }
  };

  const handleRender = () => {
    setCurrentStep('rendering');
    compilePdfMutation.mutate(latexContent);
  };

  // Derived states
  const isLoading = isGenerating || regenerateCvMutation.isPending || compilePdfMutation.isPending || isPdfLoading;
  const error = genError?.message || regenerateCvMutation.error?.message || compilePdfMutation.error?.message || (pdfError as Error)?.message;

  const processSteps: ProcessStep[] = [
    { id: 'planning', label: 'Analyzing Job Description', status: 'pending' },
    { id: 'executing', label: 'Tailoring Content', status: 'pending' },
    { id: 'editing', label: 'Review & Edit Content', status: 'pending' },
    { id: 'rendering', label: 'Compiling PDF Document', status: 'pending' },
  ];

  const getStepStatus = (stepId: GenerationStep) => {
    const stepOrder: GenerationStep[] = ['planning', 'executing', 'editing', 'rendering', 'complete'];
    const currentIndex = stepOrder.indexOf(currentStep);
    const stepIndex = stepOrder.indexOf(stepId);

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex && isLoading) return 'loading';
    if (stepIndex === currentIndex && !isLoading && !error) return 'completed';
    if (error && stepIndex === currentIndex) return 'error';
    return 'pending';
  };

  const isEditing = currentStep === 'editing';
  const previewUrl = useMemo(() => activePdfBlob ? URL.createObjectURL(activePdfBlob) : null, [activePdfBlob]);

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

        {/* Generation Process Steps - only show during generation, not for existing PDFs */}
        {!data.application?.cv_latex && (
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
        )}

        {/* Editor Display */}
        {isEditing && (
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-medium text-gray-900">Review & Edit Content</h3>
              <button
                onClick={handleRender}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
              >
                {isLoading ? (
                   <div className="animate-spin rounded-full h-4 w-4 border border-white border-t-transparent"></div>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
                <span>Render PDF</span>
              </button>
            </div>
            <div className="border rounded-md overflow-hidden">
              <textarea
                value={latexContent}
                onChange={(e) => setLatexContent(e.target.value)}
                className="w-full h-96 p-4 font-mono text-sm bg-gray-50 focus:outline-none focus:bg-white transition-colors resize-none"
                spellCheck={false}
              />
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
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
        {activePdfBlob && currentStep === 'complete' && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Generated CV</h3>
            <div className="bg-white p-2 rounded-md border">
              <object data={previewUrl!} type="application/pdf" width="100%" height="600">
                <p>Your browser does not support embedded PDFs. <a href={previewUrl!}>Download PDF</a>.</p>
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

'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { WizardData } from '@/types';
import { generateCoverLetter, regenerateCoverLetter, compilePdf as compilePdfServer } from '@/lib/api';

interface ClGenerationStepProps {
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

export function ClGenerationStep({ data, onUpdate, onNext, onPrev }: ClGenerationStepProps) {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState<GenerationStep>('planning');
  const [latexContent, setLatexContent] = useState<string>('');
  const hasSyncedRef = useRef(false);

  // 1. Initial Cover Letter Generation Query
  const { 
    data: generationResult,
    isLoading: isGenerating,
    error: genError 
  } = useQuery({
    queryKey: ['generate-cl', data.application?.id],
    queryFn: async () => {
      setCurrentStep('executing');
      return await generateCoverLetter({ application_id: data.application!.id });
    },
    enabled: !!data.application?.id,
    staleTime: Infinity,
  });

  // 2. Manual Regeneration Mutation
  const regenerateClMutation = useMutation({
    mutationFn: async (applicationId: number) => {
      setCurrentStep('planning');
      onUpdate({ clGeneration: undefined });
      await new Promise(resolve => setTimeout(resolve, 500));
      setCurrentStep('executing');
      return await regenerateCoverLetter(applicationId);
    },
    onSuccess: (result) => {
      onUpdate({
        clGeneration: {
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
      return await compilePdfServer(data.application.id, 'cl', rawContent);
    },
    onSuccess: (blob) => {
      queryClient.setQueryData(['cl-pdf', data.application?.id], blob);
      setCurrentStep('complete');
    },
  });

  // Sync auto-generation result to parent state
  useEffect(() => {
    if (generationResult && generationResult.raw_content && !hasSyncedRef.current) {
      hasSyncedRef.current = true;
      onUpdate({
        clGeneration: {
          result: generationResult.raw_content,
          planSteps: generationResult.plan_steps || [],
          isLoading: false 
        } as any,
      });
      setLatexContent(generationResult.raw_content);
      setCurrentStep('editing');
    }
  }, [generationResult]);

  const activePdfBlob = compilePdfMutation.data;

  const handleRegenerate = () => {
    if (!data.application?.id || isGenerating || regenerateClMutation.isPending) return;
    regenerateClMutation.mutate(data.application.id);
  };

  const handleDownload = () => {
    if (activePdfBlob) {
      const url = URL.createObjectURL(activePdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `CoverLetter_${data.extractedData?.company || 'My'}_${data.extractedData?.title || 'CL'}.pdf`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 100);
    }
  };

  const handleRender = () => {
    setCurrentStep('rendering');
    compilePdfMutation.mutate(latexContent);
  };

  const isLoading = isGenerating || regenerateClMutation.isPending || compilePdfMutation.isPending;
  const error = genError?.message || regenerateClMutation.error?.message || compilePdfMutation.error?.message;

  const processSteps: ProcessStep[] = [
    { id: 'planning', label: 'Drafting Cover Letter', status: 'pending' },
    { id: 'executing', label: 'Tailoring Content', status: 'pending' },
    { id: 'editing', label: 'Review & Edit Content', status: 'pending' },
    { id: 'rendering', label: 'Generating PDF Document', status: 'pending' },
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
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-xl shadow-black/5 p-8 md:p-12 space-y-10">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 italic">
            Cover Letter Generation
          </h2>
          <p className="text-zinc-500 dark:text-zinc-400">
            Creating a tailored cover letter for the <span className="text-zinc-900 dark:text-white font-bold">{data.extractedData?.title}</span> position
          </p>
        </div>

        {/* Generation Process Steps */}
        <div className="bg-zinc-50 dark:bg-zinc-950 p-6 rounded-3xl border border-zinc-100 dark:border-zinc-800">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-500 mb-6 px-1">Generation Process</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {processSteps.slice(0, -1).map((step) => {
              const status = getStepStatus(step.id);
              return (
                <div key={step.id} className="flex items-center space-x-3 p-3 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 shadow-sm">
                  <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                    status === 'completed' ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900' :
                    status === 'loading' ? 'bg-zinc-100 dark:bg-zinc-800 animate-pulse' :
                    status === 'error' ? 'bg-red-500 text-white' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-300'
                  }`}>
                    {status === 'loading' && (
                      <div className="animate-spin rounded-full h-3 w-3 border-2 border-zinc-900 dark:border-white border-t-transparent"></div>
                    )}
                    {status === 'completed' && (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="3">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {status === 'error' && (
                      <span className="text-xs font-bold">!</span>
                    )}
                    {status === 'pending' && <div className="w-1.5 h-1.5 rounded-full bg-zinc-300 dark:bg-zinc-700"></div>}
                  </div>
                  <span className={`text-xs font-bold ${
                    status === 'completed' ? 'text-zinc-900 dark:text-white' :
                    status === 'loading' ? 'text-zinc-600 dark:text-zinc-300' :
                    status === 'error' ? 'text-red-700' : 'text-zinc-400'
                  }`}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Editor Display */}
        {isEditing && (
          <div className="space-y-4 animate-in fade-in zoom-in-95 duration-500">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 px-1">
              <div>
                <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Review & Edit Content</h3>
                <p className="text-sm text-zinc-500">Fine-tune the LaTeX content or render it as PDF.</p>
              </div>
              <button
                onClick={handleRender}
                disabled={isLoading}
                className="w-full sm:w-auto px-6 py-2.5 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-xl font-bold hover:scale-105 transition-all shadow-lg flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                   <div className="animate-spin rounded-full h-4 w-4 border-2 border-zinc-400 border-t-zinc-900 dark:border-zinc-500 dark:border-t-white"></div>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
                <span>Render PDF</span>
              </button>
            </div>
            <div className="relative border border-zinc-200 dark:border-zinc-800 rounded-3xl overflow-hidden shadow-inner bg-zinc-950">
              <textarea
                value={latexContent}
                onChange={(e) => setLatexContent(e.target.value)}
                className="w-full h-[500px] p-8 font-mono text-sm bg-transparent text-zinc-300 focus:outline-none transition-colors resize-none leading-relaxed"
                spellCheck={false}
              />
              <div className="absolute top-4 right-4 text-[10px] font-bold text-zinc-600 uppercase tracking-widest bg-zinc-900 px-2 py-1 rounded">
                LaTeX Editor
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-2xl p-6">
              <div className="flex items-start">
                <div className="flex-shrink-0 text-2xl">⚠️</div>
                <div className="ml-4">
                  <h3 className="text-lg font-bold text-red-800 dark:text-red-400 italic">Generation Failed</h3>
                  <p className="mt-1 text-red-700 dark:text-red-300/80">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* PDF Display */}
        {activePdfBlob && currentStep === 'complete' && (
          <div className="space-y-6 animate-in fade-in zoom-in-95 duration-700">
            <div className="flex justify-between items-center px-1">
              <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Generated Cover Letter</h3>
              <div className="flex gap-2">
                <button
                  onClick={handleDownload}
                  className="flex items-center space-x-2 px-6 py-2 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-xl font-bold hover:scale-105 transition-all shadow-lg"
                >
                  <span>Download PDF 📥</span>
                </button>
                <button
                  onClick={handleRegenerate}
                  className="px-4 py-2 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded-xl font-bold hover:text-zinc-900 dark:hover:text-white transition-all disabled:opacity-50"
                  disabled={isLoading}
                >
                  Redo 🔄
                </button>
              </div>
            </div>
            
            <div className="bg-zinc-100 dark:bg-zinc-950 p-4 rounded-3xl border border-zinc-200 dark:border-zinc-800 shadow-inner">
              <object data={previewUrl!} type="application/pdf" width="100%" height="800" className="rounded-2xl">
                <div className="p-12 text-center">
                  <p className="text-zinc-500 mb-4">Your browser does not support embedded PDFs.</p>
                  <a href={previewUrl!} className="text-zinc-900 dark:text-white font-bold underline">Download PDF instead</a>
                </div>
              </object>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-4 border-t border-zinc-100 dark:border-zinc-800">
          <button
            onClick={onPrev}
            className="w-full sm:w-auto px-8 py-3 bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-2xl font-bold hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all"
          >
            ← Back
          </button>
          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            {currentStep === 'complete' && (
              <button
                onClick={onNext}
                className="w-full sm:w-auto px-12 py-3 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-2xl font-bold hover:scale-105 transition-all shadow-xl"
              >
                Finish & Go Home 🏠
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { WizardData, ChatMessage } from '@/types';
import { generateCoverLetter, regenerateCoverLetter, compilePdf as compilePdfServer } from '@/lib/api';
import { compileLatexToPdf } from '@/lib/tex';

interface ClGenerationStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export function ClGenerationStep({ data, onUpdate, onNext, onPrev }: ClGenerationStepProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [clPdfUrl, setClPdfUrl] = useState<string | null>(null);
  const [showServerFallback, setShowServerFallback] = useState(false);

  useEffect(() => {
    if (data.application?.cl_latex && !data.clGeneration) {
      // CL is already generated, show completed chat history
      const completedHistory: ChatMessage[] = [
        {
          role: 'user',
          content: `Generate a cover letter for ${data.application.title} position at ${data.application.company}`,
          timestamp: new Date(Date.now() - 4000),
        },
        {
          role: 'assistant',
          content: 'Analyzing job requirements and crafting personalized cover letter...',
          timestamp: new Date(Date.now() - 3000),
        },
        {
          role: 'assistant',
          content: 'Tailoring content to highlight relevant experience and skills...',
          timestamp: new Date(Date.now() - 2000),
        },
        {
          role: 'assistant',
          content: 'Cover letter LaTeX generated successfully.',
          timestamp: new Date(Date.now() - 1000),
        },
      ];

      onUpdate({
        clGeneration: {
          isLoading: false,
          chatHistory: completedHistory,
          result: data.application.cl_latex,
        },
      });
    } else if (!data.clGeneration && data.application && !data.application.cl_latex) {
      // Start CL generation process
      generateCL();
    }
  }, [data.application, data.clGeneration]);

  const generateCL = async () => {
    if (!data.application?.id) return;

    setIsLoading(true);
    setError(null);

    const initialHistory: ChatMessage[] = [
      {
        role: 'user',
        content: `Generate a cover letter for ${data.application.title} position at ${data.application.company}`,
        timestamp: new Date(),
      },
    ];
    setChatHistory(initialHistory);

    try {
      // Add analyzing message
      setTimeout(() => {
        const analyzingHistory: ChatMessage[] = [
          ...initialHistory,
          {
            role: 'assistant',
            content: 'Analyzing job requirements and crafting personalized cover letter...',
            timestamp: new Date(),
          },
        ];
        setChatHistory(analyzingHistory);
      }, 500);

      // Add tailoring message
      setTimeout(() => {
        const tailoringHistory: ChatMessage[] = [
          ...initialHistory,
          {
            role: 'assistant',
            content: 'Analyzing job requirements and crafting personalized cover letter...',
            timestamp: new Date(Date.now() - 500),
          },
          {
            role: 'assistant',
            content: 'Tailoring content to highlight relevant experience and skills...',
            timestamp: new Date(),
          },
        ];
        setChatHistory(tailoringHistory);
      }, 1500);

      // Call the API
      const result = await generateCoverLetter({ application_id: data.application.id });

      // Add success message
      const finalHistory: ChatMessage[] = [
        ...initialHistory,
        {
          role: 'assistant',
          content: 'Analyzing job requirements and crafting personalized cover letter...',
          timestamp: new Date(Date.now() - 2000),
        },
        {
          role: 'assistant',
          content: 'Tailoring content to highlight relevant experience and skills...',
          timestamp: new Date(Date.now() - 500),
        },
        {
          role: 'assistant',
          content: 'Cover letter LaTeX generated successfully.',
          timestamp: new Date(),
        },
      ];
      setChatHistory(finalHistory);

      onUpdate({
        clGeneration: {
          isLoading: false,
          chatHistory: finalHistory,
          result: result.cl_latex,
        },
        application: {
          ...data.application,
          cl_latex: result.cl_latex,
        },
      });

      if (clPdfUrl) {
        URL.revokeObjectURL(clPdfUrl);
        setClPdfUrl(null);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate cover letter';
      setError(errorMessage);

      const errorHistory: ChatMessage[] = [
        ...chatHistory,
        {
          role: 'assistant',
          content: `Error: ${errorMessage}`,
          timestamp: new Date(),
        },
      ];
      setChatHistory(errorHistory);

      onUpdate({
        clGeneration: {
          isLoading: false,
          chatHistory: errorHistory,
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
    onUpdate({ clGeneration: undefined });

    const initialHistory: ChatMessage[] = [
      {
        role: 'user',
        content: `Regenerate cover letter for ${data.application.title} position at ${data.application.company}`,
        timestamp: new Date(),
      },
    ];
    setChatHistory(initialHistory);

    try {
      // Add analyzing message
      setTimeout(() => {
        const analyzingHistory: ChatMessage[] = [
          ...initialHistory,
          {
            role: 'assistant',
            content: 'Re-analyzing job requirements and crafting personalized cover letter...',
            timestamp: new Date(),
          },
        ];
        setChatHistory(analyzingHistory);
      }, 500);

      // Add tailoring message
      setTimeout(() => {
        const tailoringHistory: ChatMessage[] = [
          ...initialHistory,
          {
            role: 'assistant',
            content: 'Re-analyzing job requirements and crafting personalized cover letter...',
            timestamp: new Date(Date.now() - 500),
          },
          {
            role: 'assistant',
            content: 'Re-tailoring content to highlight relevant experience and skills...',
            timestamp: new Date(),
          },
        ];
        setChatHistory(tailoringHistory);
      }, 1500);

      // Call the regenerate API
      const result = await regenerateCoverLetter(data.application.id);

      // Add success message
      const finalHistory: ChatMessage[] = [
        ...initialHistory,
        {
          role: 'assistant',
          content: 'Re-analyzing job requirements and crafting personalized cover letter...',
          timestamp: new Date(Date.now() - 2000),
        },
        {
          role: 'assistant',
          content: 'Re-tailoring content to highlight relevant experience and skills...',
          timestamp: new Date(Date.now() - 500),
        },
        {
          role: 'assistant',
          content: 'Cover letter LaTeX regenerated successfully.',
          timestamp: new Date(),
        },
      ];
      setChatHistory(finalHistory);

      onUpdate({
        clGeneration: {
          isLoading: false,
          chatHistory: finalHistory,
          result: result.cl_latex,
        },
        application: {
          ...data.application,
          cl_latex: result.cl_latex,
        },
      });

      if (clPdfUrl) {
        URL.revokeObjectURL(clPdfUrl);
        setClPdfUrl(null);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to regenerate cover letter';
      setError(errorMessage);

      const errorHistory: ChatMessage[] = [
        ...chatHistory,
        {
          role: 'assistant',
          content: `Error: ${errorMessage}`,
          timestamp: new Date(),
        },
      ];
      setChatHistory(errorHistory);

      onUpdate({
        clGeneration: {
          isLoading: false,
          chatHistory: errorHistory,
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
      if (!data.application?.cl_latex) throw new Error('No cover letter LaTeX available');
      const blob = await compileLatexToPdf(data.application.cl_latex);
      const url = URL.createObjectURL(blob);
      if (clPdfUrl) URL.revokeObjectURL(clPdfUrl);
      setClPdfUrl(url);
      setShowServerFallback(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to render PDF';
      setError(msg);
      setShowServerFallback(true);
    }
  };

  const useServerFallback = async () => {
    if (!data.application?.id) return;
    try {
      const blob = await compilePdfServer(data.application.id, 'cl');
      const url = URL.createObjectURL(blob);
      if (clPdfUrl) URL.revokeObjectURL(clPdfUrl);
      setClPdfUrl(url);
      setShowServerFallback(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Server fallback failed';
      setError(msg);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Cover Letter Generation
          </h2>
          <p className="text-gray-600">
            Creating a tailored cover letter for the {data.extractedData?.title} position
          </p>
        </div>

        {/* Chat History */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Generation Process</h3>
          <div className="bg-gray-50 rounded-md p-4 max-h-64 overflow-y-auto">
            <div className="space-y-4">
              {chatHistory.map((message, index) => (
                <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white text-gray-800 border'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    <p className="text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white text-gray-800 border px-4 py-2 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm">Generating cover letter...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* CL Result */}
        {data.clGeneration?.result && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Generated Cover Letter (LaTeX)</h3>
            <div className="bg-gray-50 p-4 rounded-md max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-gray-700 text-sm font-mono">
                {data.clGeneration.result}
              </pre>
            </div>
          </div>
        )}
        {/* PDF viewer */}
        {clPdfUrl && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Rendered Cover Letter (PDF)</h3>
            <div className="bg-white p-2 rounded-md border">
              <object data={clPdfUrl} type="application/pdf" width="100%" height="600">
                <p>Your browser does not support embedded PDFs. <a href={clPdfUrl}>Download PDF</a>.</p>
              </object>
            </div>
            <div className="mt-2 flex space-x-2">
              <a href={clPdfUrl} download={`CoverLetter_${data.application?.company}_${data.application?.title}.pdf`} className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">Download PDF</a>
            </div>
          </div>
        )}

        {/* Success Message */}
        {data.clGeneration?.result && (
          <div className="mb-6">
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Application materials generated successfully!
                  </h3>
                  <div className="mt-2 text-sm text-green-700">
                    <p>
                      Your customized CV and cover letter have been generated for the {data.extractedData?.title} position at {data.extractedData?.company}.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between">
          <button
            onClick={onPrev}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
          <div className="flex space-x-4">
            {data.clGeneration?.result && (
              <button
                onClick={handleRegenerate}
                className="px-4 py-2 border border-orange-300 text-orange-700 rounded-md hover:bg-orange-50"
                disabled={isLoading}
              >
                Regenerate
              </button>
            )}
            {data.clGeneration?.error && (
              <button
                onClick={handleRegenerate}
                className="px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50"
                disabled={isLoading}
              >
                Retry
              </button>
            )}
            {data.clGeneration?.result && (
              <button
                onClick={renderPdf}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                Render PDF
              </button>
            )}
            {showServerFallback && (
              <button
                onClick={useServerFallback}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Use server fallback
              </button>
            )}
            {data.clGeneration?.result && (
              <button
                onClick={onNext}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

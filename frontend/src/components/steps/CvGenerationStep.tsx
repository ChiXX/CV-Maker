'use client';

import { useState, useEffect } from 'react';
import { WizardData, ChatMessage } from '@/types';
import { generateCv, regenerateCv, compilePdf as compilePdfServer } from '@/lib/api';
import { compileLatexToPdf } from '@/lib/tex';

interface CvGenerationStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export function CvGenerationStep({ data, onUpdate, onNext, onPrev }: CvGenerationStepProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cvPdfUrl, setCvPdfUrl] = useState<string | null>(null);
  const [showServerFallback, setShowServerFallback] = useState(false);

  useEffect(() => {
    if (data.application?.cv_latex && !data.cvGeneration) {
      // CV is already generated, show completed chat history
      const completedHistory: ChatMessage[] = [
        {
          role: 'user',
          content: `Generate a CV summary for ${data.application.title} position at ${data.application.company}`,
          timestamp: new Date(Date.now() - 3000),
        },
        {
          role: 'assistant',
          content: 'Analyzing job requirements and tailoring CV content...',
          timestamp: new Date(Date.now() - 2000),
        },
        {
          role: 'assistant',
          content: 'CV LaTeX generated successfully with optimized content.',
          timestamp: new Date(Date.now() - 1000),
        },
      ];

      onUpdate({
        cvGeneration: {
          isLoading: false,
          chatHistory: completedHistory,
          result: data.application.cv_latex,
        },
      });
    } else if (!data.cvGeneration && data.application && !data.application.cv_latex) {
      // Start CV generation process
      generateCV();
    }
  }, [data.application, data.cvGeneration]);

  const generateCV = async () => {
    if (!data.application?.id) return;

    setIsLoading(true);
    setError(null);

    const initialHistory: ChatMessage[] = [
      {
        role: 'user',
        content: `Generate a CV summary for ${data.application.title} position at ${data.application.company}`,
        timestamp: new Date(),
      },
    ];
    setChatHistory(initialHistory);

    try {
      // Add analyzing message
      setTimeout(() => {
        const analyzingHistory = [
          ...initialHistory,
          {
            role: 'assistant',
            content: 'Analyzing job requirements and tailoring CV content...',
            timestamp: new Date(),
          },
        ];
        setChatHistory(analyzingHistory);
      }, 500);

      // Call the API
      const result = await generateCv({ application_id: data.application.id });

      // Add success message
      const finalHistory = [
        ...initialHistory,
        {
          role: 'assistant',
          content: 'Analyzing job requirements and tailoring CV content...',
          timestamp: new Date(Date.now() - 500),
        },
        {
          role: 'assistant',
          content: 'CV LaTeX generated successfully with optimized content.',
          timestamp: new Date(),
        },
      ];
      setChatHistory(finalHistory);

      onUpdate({
        cvGeneration: {
          isLoading: false,
          chatHistory: finalHistory,
          result: result.cv_latex,
        },
        application: {
          ...data.application,
          cv_latex: result.cv_latex,
        },
      });

      // clear any previous pdf url
      if (cvPdfUrl) {
        URL.revokeObjectURL(cvPdfUrl);
        setCvPdfUrl(null);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate CV';
      setError(errorMessage);

      const errorHistory = [
        ...chatHistory,
        {
          role: 'assistant',
          content: `Error: ${errorMessage}`,
          timestamp: new Date(),
        },
      ];
      setChatHistory(errorHistory);

      onUpdate({
        cvGeneration: {
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
    onUpdate({ cvGeneration: undefined });

    const initialHistory: ChatMessage[] = [
      {
        role: 'user',
        content: `Regenerate CV summary for ${data.application.title} position at ${data.application.company}`,
        timestamp: new Date(),
      },
    ];
    setChatHistory(initialHistory);

    try {
      // Add analyzing message
      setTimeout(() => {
        const analyzingHistory = [
          ...initialHistory,
          {
            role: 'assistant',
            content: 'Re-analyzing job requirements and tailoring CV content...',
            timestamp: new Date(),
          },
        ];
        setChatHistory(analyzingHistory);
      }, 500);

      // Call the regenerate API
      const result = await regenerateCv(data.application.id);

      // Add success message
      const finalHistory = [
        ...initialHistory,
        {
          role: 'assistant',
          content: 'Re-analyzing job requirements and tailoring CV content...',
          timestamp: new Date(Date.now() - 500),
        },
        {
          role: 'assistant',
          content: 'CV LaTeX regenerated successfully with optimized content.',
          timestamp: new Date(),
        },
      ];
      setChatHistory(finalHistory);

      onUpdate({
        cvGeneration: {
          isLoading: false,
          chatHistory: finalHistory,
          result: result.cv_latex,
        },
        application: {
          ...data.application,
          cv_latex: result.cv_latex,
        },
      });

      if (cvPdfUrl) {
        URL.revokeObjectURL(cvPdfUrl);
        setCvPdfUrl(null);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to regenerate CV';
      setError(errorMessage);

      const errorHistory = [
        ...chatHistory,
        {
          role: 'assistant',
          content: `Error: ${errorMessage}`,
          timestamp: new Date(),
        },
      ];
      setChatHistory(errorHistory);

      onUpdate({
        cvGeneration: {
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
      if (!data.application?.cv_latex) throw new Error('No CV LaTeX available');
      const blob = await compileLatexToPdf(data.application.cv_latex);
      const url = URL.createObjectURL(blob);
      // revoke previous
      if (cvPdfUrl) URL.revokeObjectURL(cvPdfUrl);
      setCvPdfUrl(url);
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
      const blob = await compilePdfServer(data.application.id, 'cv');
      const url = URL.createObjectURL(blob);
      if (cvPdfUrl) URL.revokeObjectURL(cvPdfUrl);
      setCvPdfUrl(url);
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
            CV Generation
          </h2>
          <p className="text-gray-600">
            Creating a customized CV for the {data.extractedData?.title} position
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
                      <span className="text-sm">Generating CV...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* CV Result */}
        {data.cvGeneration?.result && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Generated CV (LaTeX)</h3>
            <div className="bg-gray-50 p-4 rounded-md max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-gray-700 text-sm font-mono">
                {data.cvGeneration.result}
              </pre>
            </div>
          </div>
        )}
        {/* PDF viewer */}
        {cvPdfUrl && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Rendered CV (PDF)</h3>
            <div className="bg-white p-2 rounded-md border">
              <object data={cvPdfUrl} type="application/pdf" width="100%" height="600">
                <p>Your browser does not support embedded PDFs. <a href={cvPdfUrl}>Download PDF</a>.</p>
              </object>
            </div>
            <div className="mt-2 flex space-x-2">
              <a href={cvPdfUrl} download={`CV_${data.application?.company}_${data.application?.title}.pdf`} className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">Download PDF</a>
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
            {data.cvGeneration?.result && (
              <button
                onClick={handleRegenerate}
                className="px-4 py-2 border border-orange-300 text-orange-700 rounded-md hover:bg-orange-50"
                disabled={isLoading}
              >
                Regenerate
              </button>
            )}
            {data.cvGeneration?.error && (
              <button
                onClick={handleRegenerate}
                className="px-4 py-2 border border-red-300 text-red-700 rounded-md hover:bg-red-50"
                disabled={isLoading}
              >
                Retry
              </button>
            )}
            {data.cvGeneration?.result && (
              <button
                onClick={onNext}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Next
              </button>
            )}
            {data.cvGeneration?.result && (
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
          </div>
        </div>
      </div>
    </div>
  );
}

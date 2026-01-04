'use client';

import { useState, useEffect } from 'react';
import { WizardData } from '@/types';
import { compilePdf as compilePdfServer } from '@/lib/api';

interface PdfDownloadStepProps {
  data: WizardData;
  onUpdate: (updates: Partial<WizardData>) => void;
  onPrev: () => void;
  onRestart: () => void;
}

export function PdfDownloadStep({ data, onUpdate, onPrev, onRestart }: PdfDownloadStepProps) {
  const [cvPdfUrl, setCvPdfUrl] = useState<string | null>(null);
  const [clPdfUrl, setClPdfUrl] = useState<string | null>(null);
  const [isRenderingCv, setIsRenderingCv] = useState(false);
  const [isRenderingCl, setIsRenderingCl] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Auto-render PDFs when component mounts if LaTeX is available
    if (data.application?.cv_latex && !cvPdfUrl) {
      renderCvPdf();
    }
    if (data.application?.cl_latex && !clPdfUrl) {
      renderClPdf();
    }
  }, [data.application]);

  const renderCvPdf = async () => {
    if (!data.application?.id) return;

    setIsRenderingCv(true);
    setError(null);

    try {
      const blob = await compilePdfServer(data.application.id, 'cv');
      const url = URL.createObjectURL(blob);
      if (cvPdfUrl) URL.revokeObjectURL(cvPdfUrl);
      setCvPdfUrl(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to render CV PDF';
      setError(msg);
    } finally {
      setIsRenderingCv(false);
    }
  };

  const renderClPdf = async () => {
    if (!data.application?.id) return;

    setIsRenderingCl(true);
    setError(null);

    try {
      const blob = await compilePdfServer(data.application.id, 'cl');
      const url = URL.createObjectURL(blob);
      if (clPdfUrl) URL.revokeObjectURL(clPdfUrl);
      setClPdfUrl(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to render cover letter PDF';
      setError(msg);
    } finally {
      setIsRenderingCl(false);
    }
  };


  const downloadAll = () => {
    if (cvPdfUrl) {
      const cvLink = document.createElement('a');
      cvLink.href = cvPdfUrl;
      cvLink.download = `CV_${data.application?.company}_${data.application?.title}.pdf`;
      cvLink.click();
    }

    if (clPdfUrl) {
      const clLink = document.createElement('a');
      clLink.href = clPdfUrl;
      clLink.download = `CoverLetter_${data.application?.company}_${data.application?.title}.pdf`;
      clLink.click();
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Download Your Application Materials
          </h2>
          <p className="text-gray-600">
            Your customized CV and cover letter are ready for download
          </p>
        </div>

        {/* Error Message */}
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
                  <h3 className="text-sm font-medium text-red-800">
                    PDF Rendering Error
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* CV Section */}
        <div className="mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">CV</h3>
          <div className="bg-white p-2 rounded-md border max-h-96 overflow-y-auto">
            {cvPdfUrl ? (
              <object data={cvPdfUrl} type="application/pdf" width="100%" height="400">
                <p>Your browser does not support embedded PDFs. <a href={cvPdfUrl}>Download PDF</a>.</p>
              </object>
            ) : (
              <div className="bg-gray-100 p-8 rounded-md text-center">
                {isRenderingCv ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <span className="text-gray-600">Rendering PDF...</span>
                  </div>
                ) : (
                  <p className="text-gray-500">PDF not rendered yet</p>
                )}
              </div>
            )}
          </div>

          {/* CV Action Buttons */}
          <div className="mt-4 flex space-x-2">
            {data.application?.cv_latex && (
              <button
                onClick={renderCvPdf}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                disabled={isRenderingCv}
              >
                {isRenderingCv ? 'Rendering...' : 'Render PDF'}
              </button>
            )}
            {cvPdfUrl && (
              <a
                href={cvPdfUrl}
                download={`CV_${data.application?.company}_${data.application?.title}.pdf`}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Download CV
              </a>
            )}
          </div>
        </div>

        {/* Cover Letter Section */}
        <div className="mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Cover Letter</h3>
          <div className="bg-white p-2 rounded-md border max-h-96 overflow-y-auto">
            {clPdfUrl ? (
              <object data={clPdfUrl} type="application/pdf" width="100%" height="400">
                <p>Your browser does not support embedded PDFs. <a href={clPdfUrl}>Download PDF</a>.</p>
              </object>
            ) : (
              <div className="bg-gray-100 p-8 rounded-md text-center">
                {isRenderingCl ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                    <span className="text-gray-600">Rendering PDF...</span>
                  </div>
                ) : (
                  <p className="text-gray-500">PDF not rendered yet</p>
                )}
              </div>
            )}
          </div>

          {/* CL Action Buttons */}
          <div className="mt-4 flex space-x-2">
            {data.application?.cl_latex && (
              <button
                onClick={renderClPdf}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                disabled={isRenderingCl}
              >
                {isRenderingCl ? 'Rendering...' : 'Render PDF'}
              </button>
            )}
            {clPdfUrl && (
              <a
                href={clPdfUrl}
                download={`CoverLetter_${data.application?.company}_${data.application?.title}.pdf`}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Download Cover Letter
              </a>
            )}
          </div>
        </div>

        {/* Success Message */}
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
                  Application materials ready!
                </h3>
                <div className="mt-2 text-sm text-green-700">
                  <p>
                    Your customized CV and cover letter for the {data.extractedData?.title} position at {data.extractedData?.company} are ready for download.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Final Action Buttons */}
        <div className="flex justify-between">
          <button
            onClick={onPrev}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Back
          </button>
          <div className="flex space-x-4">
            {(cvPdfUrl || clPdfUrl) && (
              <button
                onClick={downloadAll}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
              >
                Download All
              </button>
            )}
            <button
              onClick={onRestart}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Start New Application
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

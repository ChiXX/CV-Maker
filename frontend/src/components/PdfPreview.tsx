'use client';

import { useState, useEffect } from 'react';
import { compilePdf } from '@/lib/api';

interface PdfPreviewProps {
  applicationId: number;
  target: 'cv' | 'cl';
  filename?: string;
  className?: string;
}

export function PdfPreview({ applicationId, target, filename, className = '' }: PdfPreviewProps) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Auto-load PDF when component mounts
    loadPdf();
  }, [applicationId, target]);

  useEffect(() => {
    // Cleanup object URL when component unmounts
    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [objectUrl]);

  const loadPdf = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const blob = await compilePdf(applicationId, target);
      const url = URL.createObjectURL(blob);
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      setObjectUrl(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load PDF';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!objectUrl) return;

    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = filename || `${target}_document.pdf`;
    a.click();
  };

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-md p-4 ${className}`}>
        <p className="text-red-700">{error}</p>
        <button
          onClick={loadPdf}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`bg-gray-100 p-8 rounded-md text-center ${className}`}>
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Loading PDF...</span>
        </div>
      </div>
    );
  }

  if (!objectUrl) {
    return (
      <div className={`bg-gray-100 p-8 rounded-md text-center ${className}`}>
        <p className="text-gray-500">PDF not available</p>
        <button
          onClick={loadPdf}
          className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          Load PDF
        </button>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="bg-white p-2 rounded-md border max-h-96 overflow-y-auto mb-2">
        <iframe
          src={objectUrl}
          className="w-full h-80 border-0"
          title={`${target.toUpperCase()} Preview`}
        >
          <p>Your browser does not support embedded PDFs. <a href={objectUrl}>Download PDF</a>.</p>
        </iframe>
      </div>
      <button
        onClick={handleDownload}
        className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
      >
        Download {target.toUpperCase()}
      </button>
    </div>
  );
}

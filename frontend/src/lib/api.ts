import { JobExtractionRequest, JobExtractionResponse, CvGenerationRequest, CvGenerationResponse, ClGenerationRequest, ClGenerationResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function generateJobDescription(request: JobExtractionRequest): Promise<JobExtractionResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/job_description`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    try {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Failed to extract job details: ${response.statusText}`);
    } catch (e) {
      if (e instanceof Error && e.message.includes('detail')) {
        throw e;
      }
      const error = await response.text();
      throw new Error(`Failed to extract job details: ${error}`);
    }
  }

  return response.json();
}

export async function regenerateJobDescription(applicationId: number): Promise<JobExtractionResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/${applicationId}/job_description`, {
    method: 'PUT',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to regenerate job details: ${error}`);
  }

  return response.json();
}

export async function generateCv(request: CvGenerationRequest): Promise<CvGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/${request.application_id}/cv`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to generate CV: ${error}`);
  }

  return response.json();
}

export async function regenerateCv(applicationId: number): Promise<CvGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/${applicationId}/cv`, {
    method: 'PUT',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to regenerate CV: ${error}`);
  }

  return response.json();
}

export async function generateCoverLetter(request: ClGenerationRequest): Promise<ClGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/${request.application_id}/cl`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to generate cover letter: ${error}`);
  }

  return response.json();
}

export async function regenerateCoverLetter(applicationId: number): Promise<ClGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/generate/${applicationId}/cl`, {
    method: 'PUT',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to regenerate cover letter: ${error}`);
  }

  return response.json();
}

export async function compilePdf(applicationId: number, target: 'cv' | 'cl', rawContent?: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/generate/${applicationId}/compile_pdf/${target}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ raw_content: rawContent }),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to compile PDF: ${error}`);
  }
  
  return response.blob();
}

import { JobApplication, JobExtractionRequest, JobExtractionResponse, CvGenerationRequest, CvGenerationResponse, ClGenerationRequest, ClGenerationResponse, ApplicationStatus, ApplicationStats, JobApplicationCreate } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function createApplication(data: JobApplicationCreate): Promise<JobApplication> {
  const response = await fetch(`${API_BASE_URL}/applications`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create application: ${error}`);
  }

  return response.json();
}

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
export interface ListApplicationsOptions {
  skip?: number;
  limit?: number;
  status?: ApplicationStatus[];
  search?: string;
  include_archived?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export async function listApplications(options: ListApplicationsOptions = {}): Promise<JobApplication[]> {
  const params = new URLSearchParams();
  if (options.skip !== undefined) params.append('skip', options.skip.toString());
  if (options.limit !== undefined) params.append('limit', options.limit.toString());
  if (options.status) options.status.forEach(s => params.append('status', s));
  if (options.search) params.append('search', options.search);
  if (options.include_archived) params.append('include_archived', 'true');
  if (options.sort_by) params.append('sort_by', options.sort_by);
  if (options.sort_order) params.append('sort_order', options.sort_order);

  const response = await fetch(`${API_BASE_URL}/applications/?${params.toString()}`, {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to list applications: ${error}`);
  }

  return response.json();
}

export async function getApplicationStats(): Promise<ApplicationStats> {
  const response = await fetch(`${API_BASE_URL}/applications/stats`, {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get stats: ${error}`);
  }

  return response.json();
}

export async function getApplication(applicationId: number): Promise<JobApplication> {
  const response = await fetch(`${API_BASE_URL}/applications/${applicationId}`, {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get application: ${error}`);
  }

  return response.json();
}

export async function updateApplicationStatus(
  applicationId: number, 
  data: { status?: ApplicationStatus; comment?: string }
): Promise<JobApplication> {
  const response = await fetch(`${API_BASE_URL}/applications/${applicationId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to update application: ${error}`);
  }

  return response.json();
}

export async function deleteApplication(applicationId: number): Promise<{ detail: string }> {
  const response = await fetch(`${API_BASE_URL}/applications/${applicationId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to delete application: ${error}`);
  }

  return response.json();
}

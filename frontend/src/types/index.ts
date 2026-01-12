export type ApplicationStatus = 'archive' | 'submitted' | 'interviewing' | 'offered' | 'failed';

export interface JobApplication {
  id: number;
  job_url: string;
  company: string;
  title: string;
  jd_text: string;
  cv_latex?: string;
  cl_latex?: string;
  status: ApplicationStatus;
  comment?: string;
  updated_at: string;
}

export interface ApplicationStats {
  total: number;
  submitted: number;
  interviewing: number;
  offered: number;
  failed: number;
  archive: number;
}


export interface JobExtractionRequest {
  job_url: string;
}

export interface JobExtractionResponse {
  id: number;
  job_url: string;
  company: string;
  title: string;
  jd_text: string;
  status: ApplicationStatus;
  comment?: string;
  updated_at: string;
  warning?: string;
}

export interface CvGenerationRequest {
  application_id: number;
}

export interface CvGenerationResponse {
  raw_content: string;
  plan_steps?: string[];
}

export interface ClGenerationRequest {
  application_id: number;
}

export interface ClGenerationResponse {
  raw_content: string;
  plan_steps?: string[];
}

export interface WizardStep {
  id: number;
  title: string;
  description: string;
}

export interface GenerationState {
  isLoading: boolean;
  result?: string;
  error?: string;
  planSteps?: string[];
  currentStep?: number;
}

export type WizardData = {
  url: string;
  extractedData?: {
    company: string;
    title: string;
    jd_text: string;
  };
  cvGeneration?: GenerationState;
  clGeneration?: GenerationState;
  application?: JobApplication;
};

export interface JobApplication {
  id: number;
  job_url: string;
  company: string;
  title: string;
  jd_text: string;
  cv_latex?: string;
  cl_latex?: string;
  created_at: string;
  updated_at: string;
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
  created_at: string;
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

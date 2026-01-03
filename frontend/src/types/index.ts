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

export interface JobApplicationRequest {
  job_url: string;
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
}

export interface CvGenerationRequest {
  application_id: number;
}

export interface CvGenerationResponse {
  cv_latex: string;
}

export interface ClGenerationRequest {
  application_id: number;
}

export interface ClGenerationResponse {
  cl_latex: string;
}

export interface WizardStep {
  id: number;
  title: string;
  description: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface GenerationState {
  isLoading: boolean;
  chatHistory: ChatMessage[];
  result?: string;
  error?: string;
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

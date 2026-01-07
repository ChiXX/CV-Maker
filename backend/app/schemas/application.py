from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class JobApplicationRequest(BaseModel):
    job_url: str

class JobApplicationResponse(BaseModel):
    id: int
    job_url: str
    company: str
    title: str
    jd_text: str
    cv_latex: Optional[str]
    cl_latex: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobExtractionRequest(BaseModel):
    job_url: str

class JobExtractionResponse(BaseModel):
    id: int
    job_url: str
    company: str
    title: str
    jd_text: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CvGenerationRequest(BaseModel):
    application_id: int

class CvGenerationResponse(BaseModel):
    raw_content: str
    plan_steps: Optional[List[str]] = None

class ClGenerationRequest(BaseModel):
    application_id: int

class ClGenerationResponse(BaseModel):
    raw_content: str
    plan_steps: Optional[List[str]] = None

class PdfCompileResponse(BaseModel):
    detail: str

class CompilePdfRequest(BaseModel):
    raw_content: Optional[str] = None

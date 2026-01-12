import enum
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ApplicationStatus(str, enum.Enum):
    archive = "archive"
    submitted = "submitted"
    interviewing = "interviewing"
    offered = "offered"
    failed = "failed"

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
    status: ApplicationStatus
    comment: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    comment: Optional[str] = None

class JobApplicationCreate(BaseModel):
    job_url: str
    company: str
    title: str
    jd_text: str

class JobExtractionRequest(BaseModel):
    job_url: str

class JobExtractionResponse(BaseModel):
    id: Optional[int] = None
    job_url: str
    company: str
    title: str
    jd_text: str
    status: ApplicationStatus = ApplicationStatus.submitted
    comment: Optional[str] = None
    updated_at: datetime = datetime.utcnow()
    warning: Optional[str] = None
    error: Optional[str] = None

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

class ApplicationStats(BaseModel):
    total: int
    submitted: int
    interviewing: int
    offered: int
    failed: int
    archive: int

class PdfCompileResponse(BaseModel):
    detail: str

class CompilePdfRequest(BaseModel):
    raw_content: Optional[str] = None

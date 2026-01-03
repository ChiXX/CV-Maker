from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
from cv_generator import compile_cv_tex
from cl_generator import compile_cl_tex
from jd_generator import extract_jd_from_url_with_llm
from database import get_db_dependency, init_db, create_tables
from models import Application

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
)

# Initialize FastAPI app
app = FastAPI(
    title="CV Maker API",
    description="API for generating customized CV and cover letters from job descriptions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
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

class ApplicationListResponse(BaseModel):
    applications: List[JobApplicationResponse]

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/applications/", response_model=JobApplicationResponse)
async def create_application(
    request: JobApplicationRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Create a new job application by extracting JD from URL and generating CV/cover letter LaTeX
    """
    try:
        # Extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, request.job_url)

        # Create output directory
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)

        # Save JD text
        jd_txt_path = os.path.join(out_dir, f"{title}.txt")
        with open(jd_txt_path, "w", encoding="utf-8") as f:
            f.write(jd_text)

        # Generate LaTeX content (directly to database)
        cv_latex = compile_cv_tex(client, jd_text)
        cl_latex = compile_cl_tex(client, jd_text, company, title)

        # Create application record
        application = Application(
            jb_url=request.job_url,
            jd_text=jd_text,
            company=company,
            title=title,
            cv_latex=cv_latex,
            cl_latex=cl_latex
        )

        # Save to database
        db.add(application)
        db.commit()
        db.refresh(application)

        return JobApplicationResponse(
            id=application.id,
            job_url=application.jb_url,
            company=application.company,
            title=application.title,
            jd_text=application.jd_text,
            cv_latex=application.cv_latex,
            cl_latex=application.cl_latex,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create application: {str(e)}")

@app.get("/applications/", response_model=ApplicationListResponse)
async def list_applications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_dependency)
):
    """
    List all applications with pagination
    """
    applications = db.query(Application).offset(skip).limit(limit).all()

    return ApplicationListResponse(
        applications=[
            JobApplicationResponse(
                id=app.id,
                job_url=app.jb_url,
                company=app.company,
                title=app.title,
                jd_text=app.jd_text,
                cv_latex=app.cv_latex,
                cl_latex=app.cl_latex,
                created_at=app.created_at,
                updated_at=app.updated_at
            )
            for app in applications
        ]
    )

@app.get("/applications/{application_id}", response_model=JobApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get a specific application by ID
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return JobApplicationResponse(
        id=application.id,
        job_url=application.jb_url,
        company=application.company,
        title=application.title,
        jd_text=application.jd_text,
        cv_latex=application.cv_latex,
        cl_latex=application.cl_latex,
        created_at=application.created_at,
        updated_at=application.updated_at
    )

@app.delete("/applications/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Delete an application by ID
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()

    return {"message": "Application deleted successfully"}

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "CV Maker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

def main():
    """Main entry point for running the FastAPI server"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

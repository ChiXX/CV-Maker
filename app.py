from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import re
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
from cv_generator import compile_cv_tex
from cl_generator import compile_cl_tex
from shared_planner import Planner, Solver
from jd_generator import extract_jd_from_url_with_llm
from database import get_db_dependency, init_db, create_tables
from models import Application
from fastapi.responses import StreamingResponse
from fastapi import BackgroundTasks
import subprocess
import tempfile
import shutil
import io
from fastapi import Query


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

class CvGenerationRequest(BaseModel):
    application_id: int

class CvGenerationResponse(BaseModel):
    cv_latex: str
    plan_steps: Optional[List[str]] = None

class ClGenerationRequest(BaseModel):
    application_id: int
class ClGenerationResponse(BaseModel):
    cl_latex: str
    plan_steps: Optional[List[str]] = None



class PdfCompileResponse(BaseModel):
    detail: str

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/applications/extract", response_model=JobExtractionResponse)
async def extract_job_details(
    request: JobExtractionRequest,
    db: Session = Depends(get_db_dependency)
):
    """
    Extract job details from URL and create initial application record
    """
    try:
        # Check if URL already exists
        existing_application = db.query(Application).filter(Application.jb_url == request.job_url).first()
        if existing_application:
            # Return existing application instead of creating duplicate
            return JobExtractionResponse(
                id=existing_application.id,
                job_url=existing_application.jb_url,
                company=existing_application.company,
                title=existing_application.title,
                jd_text=existing_application.jd_text,
                created_at=existing_application.created_at,
                updated_at=existing_application.updated_at
            )

        # Extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, request.job_url)

        # Create output directory
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)


        # Create application record with only JD info
        application = Application(
            jb_url=request.job_url,
            jd_text=jd_text,
            company=company,
            title=title,
        )

        # Save to database
        db.add(application)
        db.commit()
        db.refresh(application)

        return JobExtractionResponse(
            id=application.id,
            job_url=application.jb_url,
            company=application.company,
            title=application.title,
            jd_text=application.jd_text,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract job details: {str(e)}")

@app.put("/applications/{application_id}/extract", response_model=JobExtractionResponse)
async def regenerate_job_details(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate job details for an existing application
    """
    try:
        # Get existing application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Re-extract job description from URL
        jd_text, company, title = extract_jd_from_url_with_llm(client, application.jb_url)

        # Update output directory and file
        today = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join("Applications", f"{today}-{company}")
        os.makedirs(out_dir, exist_ok=True)

        # Save updated JD text (sanitize title for filesystem safety)
        import re as _re
        safe_title = _re.sub(r'[\\/:"*?<>|]+', '_', title)
        jd_txt_path = os.path.join(out_dir, f"{safe_title}.txt")
        os.makedirs(os.path.dirname(jd_txt_path), exist_ok=True)
        with open(jd_txt_path, "w", encoding="utf-8") as f:
            f.write(jd_text)

        # Update application record
        application.jd_text = jd_text
        application.company = company
        application.title = title
        # Clear CV and CL since JD changed
        application.cv_latex = None
        application.cl_latex = None

        db.commit()
        db.refresh(application)

        return JobExtractionResponse(
            id=application.id,
            job_url=application.jb_url,
            company=application.company,
            title=application.title,
            jd_text=application.jd_text,
            created_at=application.created_at,
            updated_at=application.updated_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate job details: {str(e)}")


 


@app.post("/applications/{application_id}/cv", response_model=CvGenerationResponse)
async def generate_cv(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Generate CV LaTeX for an existing application
    """
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Generate CV LaTeX directly
        cv_latex, new_summary, plan_steps = compile_cv_tex(client, application.jd_text)
        # Update application
        application.cv_latex = cv_latex
        db.commit()

        return CvGenerationResponse(cv_latex=cv_latex, plan_steps=plan_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start CV generation: {str(e)}")

@app.put("/applications/{application_id}/cv", response_model=CvGenerationResponse)
async def regenerate_cv(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate CV LaTeX for an existing application (starts background generation and returns plan)
    """
    try:
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Generate CV LaTeX directly
        cv_latex, new_summary, plan_steps = compile_cv_tex(client, application.jd_text)

        # Update application
        application.cv_latex = cv_latex
        db.commit()

        return CvGenerationResponse(cv_latex=cv_latex, plan_steps=plan_steps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start CV regeneration: {str(e)}")

@app.post("/applications/{application_id}/cl", response_model=ClGenerationResponse)
async def generate_cover_letter(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Generate cover letter LaTeX for an existing application
    """
    try:
        # Get application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Generate CL LaTeX directly
        cl_latex, letter_body, plan_steps = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        # Update application
        application.cl_latex = cl_latex
        db.commit()

        return ClGenerationResponse(cl_latex=cl_latex, plan_steps=plan_steps)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cover letter: {str(e)}")

@app.put("/applications/{application_id}/cl", response_model=ClGenerationResponse)
async def regenerate_cover_letter(
    application_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Regenerate cover letter LaTeX for an existing application
    """
    try:
        # Get application
        application = db.query(Application).filter(Application.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Regenerate CL LaTeX and obtain plan steps
        cl_latex, _, plan_steps = compile_cl_tex(client, application.jd_text, application.company, application.title, application.cv_latex)

        # Update application
        application.cl_latex = cl_latex
        db.commit()

        return ClGenerationResponse(cl_latex=cl_latex, plan_steps=plan_steps)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate cover letter: {str(e)}")


@app.post("/applications/{application_id}/compile_pdf/{target}")
async def compile_pdf(
    application_id: int,
    target: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Compile PDF from LaTeX content using pdflatex
    target: 'cv' or 'cl' (CV or Cover Letter)
    """
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if target not in ['cv', 'cl']:
        raise HTTPException(status_code=400, detail="Target must be 'cv' or 'cl'")

    # Get LaTeX content
    latex_content = application.cv_latex if target == 'cv' else application.cl_latex
    if not latex_content:
        raise HTTPException(status_code=400, detail=f"No {target.upper()} content found")

    # Sanitize filename for Content-Disposition header
    import re as _re
    safe_company = _re.sub(r'[\\/:"*?<>|]+', '_', application.company)
    safe_title = _re.sub(r'[\\/:"*?<>|]+', '_', application.title)
    filename = f"{target}_{safe_company}_{safe_title}.pdf"

    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write LaTeX content to main.tex
            # Copy local LaTeX asset directories into the temp dir so pdflatex can find .cls, images, etc.
            try:
                project_root = os.getcwd()
                for src_dir in ["latex_cv", "latex_cl"]:
                    src_path = os.path.join(project_root, src_dir)
                    if os.path.exists(src_path) and os.path.isdir(src_path):
                        for root_dir, dirs, files in os.walk(src_path):
                            rel_root = os.path.relpath(root_dir, src_path)
                            dest_root = tmpdir if rel_root == "." else os.path.join(tmpdir, rel_root)
                            os.makedirs(dest_root, exist_ok=True)
                            for fname in files:
                                try:
                                    shutil.copy2(os.path.join(root_dir, fname), os.path.join(dest_root, fname))
                                except Exception:
                                    # ignore individual copy errors
                                    pass
            except Exception as e:
                print(f"Warning: failed to copy LaTeX assets: {e}")

            tex_path = os.path.join(tmpdir, "main.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Run pdflatex to compile PDF (allow errors but continue)
            proc = subprocess.run([
                "pdflatex",
                "-interaction=nonstopmode",
                f"-output-directory={tmpdir}",
                "main.tex",
            ], capture_output=True, text=True, cwd=tmpdir)

            pdf_path = os.path.join(tmpdir, "main.pdf")

            # Check if PDF was generated, even if there were warnings/errors
            if not os.path.exists(pdf_path):
                # Collect full debug information
                files_in_tmp = os.listdir(tmpdir)
                error_info = {
                    "message": "PDF file was not generated",
                    "return_code": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "temp_dir": tmpdir,
                    "files_in_temp_dir": files_in_tmp,
                }
                # Also save the .log and .tex contents if available for offline inspection
                try:
                    saved_debug_dir = os.path.join("Applications", "pdflatex_debug")
                    os.makedirs(saved_debug_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    debug_file = os.path.join(saved_debug_dir, f"debug-{application_id}-{timestamp}.json")
                    import json
                    with open(debug_file, "w", encoding="utf-8") as df:
                        json.dump(error_info, df, ensure_ascii=False, indent=2)
                    error_info["saved_debug_file"] = debug_file
                except Exception as e:
                    # ignore saving errors but note them
                    error_info["save_error"] = str(e)

                raise HTTPException(status_code=500, detail=error_info)

            # Read the PDF into memory before leaving the tempdir, to avoid the
            # TemporaryDirectory being removed before the response generator runs.
            try:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading generated PDF: {str(e)}")

            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF compilation failed: {str(e)}")







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
